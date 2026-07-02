#!/usr/bin/env python
"""飞书知识库合同审核闭环 · 轮询编排脚本。

闭环流程（回应导师反馈二：打通飞书工具生态）：

    飞书知识库写入合同文档
        → 本脚本轮询检测新增文档
        → 读取文档内容（lark-cli docs +fetch）
        → 本地审核引擎审核（规则引擎 + 可选 LLM 终局决策）
        → 审核报告写回飞书知识库（wiki +node-create + docs +update）
        → 结构化记录写入多维表格（lark-cli base +record-upsert）
        → 主体画像写回飞书知识库（乙方档案：审核历史自动累积）
        → 小浣熊联网尽调后经 MCP write_due_diligence 回填画像尽调节

运行方式
--------
单次轮询（配合 cron 定时执行）::

    uv run python scripts/feishu_contract_loop.py

首次运行会列出知识库节点供确认；之后每次运行检测新增合同文档并审核写回。

配置
----
通过环境变量或 ``.env`` 配置（参见 ``.env.example`` 的飞书段）::

    FEISHU_WIKI_SPACE_ID       知识库空间 ID（lark-cli wiki +space-list 获取）
    FEISHU_CONTRACT_NODE       存放待审合同的父节点 token（留空则监控根节点）
    FEISHU_REPORT_NODE         审核报告挂载的父节点 token（留空则用 CONTRACT_NODE）
    FEISHU_BITABLE_APP         多维表格 app_token（用于结构化记录沉淀）
    FEISHU_BITABLE_TABLE       多维表格 table_id 或表名
    FEISHU_LOOP_REVIEW_MODE    审核模式：rules_only（默认，无需 API key）| rules_agent
    FEISHU_LOOP_LLM_PROVIDER   rules_agent 时使用的 LLM Provider（deepseek | sensenova，默认 deepseek）
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = Path(__file__).resolve().parent / ".feishu_loop_state.json"

# 把项目 src 加入 path，以便复用审核引擎
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv  # type: ignore


def _load_config() -> dict[str, str]:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    return {
        "space_id": os.environ.get("FEISHU_WIKI_SPACE_ID", ""),
        "contract_node": os.environ.get("FEISHU_CONTRACT_NODE", ""),
        "report_node": os.environ.get("FEISHU_REPORT_NODE", ""),
        "bitable_app": os.environ.get("FEISHU_BITABLE_APP", ""),
        "bitable_table": os.environ.get("FEISHU_BITABLE_TABLE", ""),
        "review_mode": os.environ.get("FEISHU_LOOP_REVIEW_MODE", "rules_only"),
        "llm_provider": os.environ.get("FEISHU_LOOP_LLM_PROVIDER", "deepseek"),
    }


def _lark_cli(
    args: list[str], dry_run: bool = False, stdin_data: str | None = None
) -> dict[str, Any]:
    """调用 lark-cli，返回解析后的 JSON。

    注意：不全局追加 ``--format json``——``docs +update``、``base +record-upsert``
    等命令不接受该 flag；lark-cli 默认即输出 JSON。命令可能在 JSON 前打印
    进度文本（如 "Found 1 node(s)"），故从首个 ``{`` 起解析。
    ``stdin_data`` 用于把超长内容经 ``--content -`` 管道传入，规避 @file 必须相对路径的限制。
    """
    cmd = ["lark-cli", *args]
    if dry_run:
        cmd.append("--dry-run")
    print(f"  $ {' '.join(cmd)}" + ("  (stdin)" if stdin_data is not None else ""))
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=180, input=stdin_data
    )
    if result.returncode != 0:
        raise RuntimeError(f"lark-cli 失败: {result.stderr.strip() or result.stdout.strip()}")
    out = result.stdout.strip()
    if not out:
        return {}
    idx = out.find("{")
    if idx < 0:
        return {"raw": out}
    try:
        return json.loads(out[idx:])
    except json.JSONDecodeError:
        return {"raw": out}


# ── 轮询触发端 ──────────────────────────────────────────────────


def list_wiki_nodes(space_id: str, parent_node: str = "") -> list[dict[str, Any]]:
    """列出知识库指定父节点下的子节点。"""
    args = ["wiki", "+node-list", "--space-id", space_id, "--as", "user", "--page-all"]
    if parent_node:
        args.extend(["--parent-node-token", parent_node])
    resp = _lark_cli(args)
    # 响应结构：data.nodes[] 每个含 node_token, obj_token, obj_type, title
    items = resp.get("data", {}).get("nodes", [])
    return items


def load_state() -> dict[str, Any]:
    """加载闭环状态。

    结构::

        {
          "processed": {node_token: {title, processed_at, report_url}},
          "profiles": {主体名: {node_token, obj_token, url,
                                contracts: [{title, date, conclusion, pass_rate,
                                             high_risk, report_url}],
                                due_diligence: {status, updated_at, findings_md}}}
        }

    兼容旧版扁平结构（直接是 processed 映射）。
    """
    if STATE_FILE.exists():
        raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if "processed" not in raw:
            raw = {"processed": raw, "profiles": {}}
        raw.setdefault("profiles", {})
        return raw
    return {"processed": {}, "profiles": {}}


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def detect_new_contracts(
    nodes: list[dict[str, Any]], processed: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    """检测未处理的合同文档节点（obj_type 为 docx/doc）。"""
    new_docs = []
    for node in nodes:
        node_token = node.get("node_token", "")
        obj_type = node.get("obj_type", "")
        title = node.get("title", "")
        if not node_token or node_token in processed:
            continue
        # 只处理文档类型（docx/doc），跳过文件夹、表格等
        if obj_type not in {"docx", "doc"}:
            continue
        # 跳过本闭环自己写回的审核报告与主体画像，避免把它们当成新合同反复审核
        # （docs +update --command overwrite 会用 H1 覆盖节点标题，
        # 故同时匹配「【…】」前缀与子串）
        if "审核报告" in title or "主体画像" in title:
            continue
        # 简单过滤：标题含「合同」或在合同目录下即视为待审合同
        new_docs.append(node)
    return new_docs


# ── 读取合同 ────────────────────────────────────────────────────


def fetch_doc_content(obj_token: str) -> str:
    """读取飞书文档内容，返回 Markdown 文本。"""
    args = [
        "docs", "+fetch",
        "--api-version", "v2",
        "--doc", obj_token,
        "--doc-format", "markdown",
        "--as", "user",
    ]
    resp = _lark_cli(args)
    # 响应结构：data.document.content（Markdown 字符串）
    content = resp.get("data", {}).get("document", {}).get("content", "") or ""
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False)


# ── 本地审核 ────────────────────────────────────────────────────


def run_audit(
    contract_text: str, file_name: str, review_mode: str, llm_provider: str = "deepseek"
) -> dict[str, Any]:
    """调用本地审核引擎（复用 GUI 的 _run_contract_review）。"""
    from local_crewai_demo.gui import _run_contract_review

    payload: dict[str, str] = {
        "reviewMode": review_mode,
        "contractText": contract_text,
        "fileName": file_name,
    }
    if review_mode == "rules_agent":
        payload["provider"] = llm_provider
    return _run_contract_review(payload, None)


# ── 沉淀端 · 报告文档 ────────────────────────────────────────────


def create_report_doc(
    report_md: str, title: str, parent_node: str, space_id: str
) -> dict[str, Any]:
    """在飞书知识库创建审核报告 docx 并写入 Markdown 内容。

    两步走（``docs +create --wiki-space`` 在当前 lark-cli 版本不会挂到 wiki 节点）：
    1. ``wiki +node-create`` 在空间内建一个 docx 节点（确保挂到 wiki，拿到 obj_token + url）；
    2. ``docs +update --command overwrite --doc-format markdown`` 把报告内容写入该 docx。
    """
    # 1. 在 wiki 建 docx 节点
    node_args = [
        "wiki", "+node-create",
        "--space-id", space_id,
        "--title", title,
        "--obj-type", "docx",
        "--as", "user",
    ]
    if parent_node:
        node_args.extend(["--parent-node-token", parent_node])
    node_resp = _lark_cli(node_args)
    node_data = node_resp.get("data", {})
    obj_token = node_data.get("obj_token", "")
    url = node_data.get("url", "")
    if not obj_token:
        raise RuntimeError(f"建报告节点失败: {node_resp}")

    # 2. 写入报告内容（经 stdin 传 --content -，规避 @file 必须相对路径的限制）
    up_args = [
        "docs", "+update",
        "--api-version", "v2",
        "--doc", obj_token,
        "--command", "overwrite",
        "--doc-format", "markdown",
        "--content", "-",
        "--as", "user",
    ]
    _lark_cli(up_args, stdin_data=report_md)
    return {"url": url, "obj_token": obj_token}


# ── 沉淀端 · 主体画像 ────────────────────────────────────────────


def extract_counterparty(audit_result: dict[str, Any]) -> str:
    """从审核结果提取乙方（对方主体）名称。"""
    try:
        audit = json.loads(audit_result.get("auditJson") or "{}")
    except json.JSONDecodeError:
        return ""
    fields = audit.get("fields", {})
    return str(fields.get("party_b") or "").strip()


def build_profile_markdown(name: str, profile: dict[str, Any]) -> str:
    """渲染主体画像文档（Markdown）。

    画像 = 合同审核历史（本地闭环自动累积）+ 联网尽调（小浣熊经 MCP 写入）。
    """
    contracts = profile.get("contracts", [])
    dd = profile.get("due_diligence", {})
    total = len(contracts)
    high_total = sum(int(c.get("high_risk", 0)) for c in contracts)

    lines = [
        f"# 【主体画像】{name}",
        "",
        f"- 更新时间：{datetime.now():%Y-%m-%d %H:%M}",
        f"- 累计审核合同：**{total} 份**　累计高风险命中：**{high_total} 项**",
        "",
        "## 一、合同审核历史（闭环自动沉淀）",
        "",
        "| 日期 | 合同 | 结论 | 通过率 | 高风险 | 报告 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in contracts:
        report_cell = f"[审核报告]({c['report_url']})" if c.get("report_url") else "—"
        lines.append(
            f"| {c.get('date', '')} | {c.get('title', '')} | {c.get('conclusion', '')} "
            f"| {c.get('pass_rate', '')}% | {c.get('high_risk', 0)} | {report_cell} |"
        )

    lines += ["", "## 二、联网尽调（小浣熊联网检索写入）", ""]
    status = dd.get("status", "pending")
    if status == "done" and dd.get("findings_md"):
        lines.append(f"> 更新于 {dd.get('updated_at', '')} · 来源：办公小浣熊联网检索")
        lines.append("")
        lines.append(str(dd["findings_md"]))
    else:
        lines.append(
            "_待尽调：由小浣熊定时任务联网检索该主体的工商、失信、涉诉与负面信息后，"
            "调用 MCP 工具 `write_due_diligence` 写入本节。_"
        )
    lines += [
        "",
        "---",
        "",
        "_本画像由飞书合同审核闭环自动维护：审核历史来自本地三层 skill，尽调来自小浣熊联网检索。_",
    ]
    return "\n".join(lines)


def upsert_profile_doc(
    state: dict[str, Any], config: dict[str, str], name: str
) -> dict[str, str]:
    """把主体画像写回飞书 wiki（不存在则建节点，存在则 overwrite）。"""
    profile = state["profiles"].setdefault(
        name, {"contracts": [], "due_diligence": {"status": "pending"}}
    )
    profile_md = build_profile_markdown(name, profile)

    if not profile.get("obj_token"):
        node_args = [
            "wiki", "+node-create",
            "--space-id", config["space_id"],
            "--title", f"【主体画像】{name}",
            "--obj-type", "docx",
            "--as", "user",
        ]
        parent = config["report_node"] or config["contract_node"]
        if parent:
            node_args.extend(["--parent-node-token", parent])
        node_resp = _lark_cli(node_args)
        node_data = node_resp.get("data", {})
        profile["node_token"] = node_data.get("node_token", "")
        profile["obj_token"] = node_data.get("obj_token", "")
        profile["url"] = node_data.get("url", "")
        if not profile["obj_token"]:
            raise RuntimeError(f"建主体画像节点失败: {node_resp}")

    up_args = [
        "docs", "+update",
        "--api-version", "v2",
        "--doc", profile["obj_token"],
        "--command", "overwrite",
        "--doc-format", "markdown",
        "--content", "-",
        "--as", "user",
    ]
    _lark_cli(up_args, stdin_data=profile_md)
    return {"url": profile.get("url", ""), "obj_token": profile["obj_token"]}


def record_contract_to_profile(
    state: dict[str, Any],
    config: dict[str, str],
    name: str,
    contract_entry: dict[str, Any],
) -> str:
    """把一次审核结果并入主体画像并写回飞书，返回画像 URL。"""
    profile = state["profiles"].setdefault(
        name, {"contracts": [], "due_diligence": {"status": "pending"}}
    )
    # 同名合同去重（重跑场景覆盖旧条目）
    profile["contracts"] = [
        c for c in profile["contracts"] if c.get("title") != contract_entry.get("title")
    ]
    profile["contracts"].append(contract_entry)
    result = upsert_profile_doc(state, config, name)
    return result.get("url", "")


def write_due_diligence(name: str, findings_md: str) -> dict[str, Any]:
    """写入联网尽调结果（供 MCP 工具调用，小浣熊完成检索后回填）。"""
    config = _load_config()
    state = load_state()
    if name not in state["profiles"]:
        return {
            "ok": False,
            "error": f"主体「{name}」不存在。可先跑 run_feishu_loop 生成画像，"
            f"当前已有主体：{list(state['profiles'])}",
        }
    profile = state["profiles"][name]
    profile["due_diligence"] = {
        "status": "done",
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "findings_md": findings_md,
    }
    result = upsert_profile_doc(state, config, name)
    save_state(state)
    return {"ok": True, "counterparty": name, "profile_url": result.get("url", "")}


def get_pending_due_diligence() -> list[dict[str, Any]]:
    """列出待尽调主体（供 MCP 工具调用，小浣熊据此逐一联网检索）。"""
    state = load_state()
    pending = []
    for name, profile in state["profiles"].items():
        if profile.get("due_diligence", {}).get("status") != "done":
            pending.append(
                {
                    "counterparty": name,
                    "contracts": [c.get("title", "") for c in profile.get("contracts", [])],
                    "profile_url": profile.get("url", ""),
                }
            )
    return pending


# ── 沉淀端 · 多维表格 ────────────────────────────────────────────


def write_bitable_record(
    bitable_app: str, table_id: str, record: dict[str, Any]
) -> dict[str, Any]:
    """把结构化审核记录写入多维表格。"""
    args = [
        "base", "+record-upsert",
        "--base-token", bitable_app,
        "--table-id", table_id,
        "--json", json.dumps(record, ensure_ascii=False),
        "--as", "user",
    ]
    return _lark_cli(args)


def build_bitable_record(audit_result: dict[str, Any], doc_url: str = "") -> dict[str, Any]:
    """从审核结果构建多维表格记录（字段名按通用合同审核表设计）。"""
    analytics = audit_result.get("analytics", {})
    token_profile = audit_result.get("tokenSavingsProfile", {})
    return {
        "合同文件": audit_result.get("fileName", ""),
        "总体结论": audit_result.get("report", "").split("\n")[0][:100] if audit_result.get("report") else "",
        "通过率": analytics.get("pass_rate", 0),
        "高风险数": analytics.get("risk_distribution", {}).get("高风险", 0),
        "中风险数": analytics.get("risk_distribution", {}).get("中风险", 0),
        "低风险数": analytics.get("risk_distribution", {}).get("低风险", 0),
        "Token消耗": token_profile.get("hybridTotalTokens", 0),
        "Token节省": token_profile.get("savingsPercent", 0),
        "审核时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "原文链接": doc_url,
        "审核报告": audit_result.get("report", "")[:2000],
    }


# ── 主编排 ──────────────────────────────────────────────────────


def run_once(dry_run: bool = False) -> dict[str, Any]:
    """执行一次轮询周期：检测新合同 → 审核 → 写回报告 + 多维表格。"""
    config = _load_config()
    if not config["space_id"]:
        return {"ok": False, "error": "未配置 FEISHU_WIKI_SPACE_ID"}

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 飞书合同审核闭环 · 轮询开始")
    print(f"  知识库: {config['space_id']}")
    print(f"  合同节点: {config['contract_node'] or '(根节点)'}")

    # 1. 列出知识库节点
    nodes = list_wiki_nodes(config["space_id"], config["contract_node"])
    print(f"  发现 {len(nodes)} 个节点")

    # 2. 检测新合同
    state = load_state()
    processed = state["processed"]
    new_docs = detect_new_contracts(nodes, processed)
    print(f"  待审合同: {len(new_docs)} 份（已处理 {len(processed)} 份）")

    if not new_docs:
        print("  无新增合同，本次轮询结束。")
        return {
            "ok": True,
            "new_contracts": 0,
            "processed": len(processed),
            "pending_due_diligence": get_pending_due_diligence(),
        }

    results = []
    report_node = config["report_node"] or config["contract_node"]

    for doc in new_docs:
        node_token = doc.get("node_token", "")
        obj_token = doc.get("obj_token", "")
        title = doc.get("title", "未命名合同")
        print(f"\n  ── 审核: {title} ({obj_token})")

        try:
            if dry_run:
                print("  [dry-run] 跳过实际审核和写回")
                results.append({"title": title, "status": "dry_run"})
                continue

            # 3. 读取合同内容
            contract_text = fetch_doc_content(obj_token)
            if not contract_text.strip():
                print("  ⚠ 文档内容为空，跳过")
                continue
            print(f"  读取合同: {len(contract_text)} 字符")

            # 4. 本地审核
            audit = run_audit(
                contract_text,
                title,
                config["review_mode"],
                config.get("llm_provider", "deepseek"),
            )
            if not audit.get("ok"):
                print(f"  ✗ 审核失败: {audit.get('error', '未知错误')}")
                continue
            print(f"  审核完成: {audit.get('fileName', title)}")

            # 5. 写回报告文档
            report_url = ""
            if config["space_id"]:
                report_title = f"【审核报告】{title} · {datetime.now():%Y%m%d}"
                report_resp = create_report_doc(
                    audit.get("report", ""),
                    report_title,
                    report_node,
                    config["space_id"],
                )
                report_url = report_resp.get("url", "")
                print(f"  报告已写回: {report_url or '(已创建)'}")

            # 6. 写入多维表格
            if config["bitable_app"] and config["bitable_table"]:
                record = build_bitable_record(audit, report_url)
                write_bitable_record(
                    config["bitable_app"], config["bitable_table"], record
                )
                print(f"  多维表格记录已写入: {config['bitable_table']}")

            # 7. 主体画像写回（乙方档案：审核历史自动沉淀 + 尽调占位待小浣熊回填）
            profile_url = ""
            counterparty = extract_counterparty(audit)
            if counterparty:
                analytics = audit.get("analytics", {})
                contract_entry = {
                    "title": title,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "conclusion": (
                        json.loads(audit.get("auditJson") or "{}").get(
                            "overall_conclusion", ""
                        )
                    ),
                    "pass_rate": analytics.get("pass_rate", 0),
                    "high_risk": analytics.get("risk_distribution", {}).get("高风险", 0),
                    "report_url": report_url,
                }
                profile_url = record_contract_to_profile(
                    state, config, counterparty, contract_entry
                )
                print(f"  主体画像已写回: {counterparty} → {profile_url or '(已更新)'}")
            else:
                print("  ⚠ 未识别乙方主体，跳过画像写回")

            # 8. 更新已处理状态
            processed[node_token] = {
                "title": title,
                "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "report_url": report_url,
            }
            results.append(
                {
                    "title": title,
                    "status": "ok",
                    "report_url": report_url,
                    "counterparty": counterparty,
                    "profile_url": profile_url,
                }
            )

        except Exception as exc:
            print(f"  ✗ 处理失败: {exc}")
            results.append({"title": title, "status": "error", "error": str(exc)})

    save_state(state)
    print(f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] 轮询结束: {len(results)} 份已处理")
    return {
        "ok": True,
        "new_contracts": len(new_docs),
        "results": results,
        "pending_due_diligence": get_pending_due_diligence(),
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="飞书知识库合同审核闭环 · 轮询编排")
    parser.add_argument("--dry-run", action="store_true", help="只列出节点，不执行审核和写回")
    parser.add_argument("--list-nodes", action="store_true", help="仅列出知识库节点（用于首次配置确认）")
    parser.add_argument(
        "--forget-node",
        metavar="NODE_TOKEN",
        help="从已处理状态中移除指定 node_token，便于重新审核（测试用）",
    )
    parser.add_argument(
        "--pending-dd",
        action="store_true",
        help="列出待联网尽调的主体（JSON），供小浣熊 Skill 编排使用",
    )
    parser.add_argument(
        "--write-dd",
        metavar="主体名",
        help="把尽调结论写回该主体画像；结论 Markdown 经 --findings-file 或 stdin 传入",
    )
    parser.add_argument(
        "--findings-file",
        metavar="PATH",
        help="尽调结论 Markdown 文件路径（配合 --write-dd；缺省从 stdin 读取）",
    )
    args = parser.parse_args()

    if args.pending_dd:
        pending = get_pending_due_diligence()
        print(json.dumps({"ok": True, "count": len(pending), "pending": pending}, ensure_ascii=False, indent=2))
        return

    if args.write_dd:
        if args.findings_file:
            findings_md = Path(args.findings_file).read_text(encoding="utf-8")
        else:
            findings_md = sys.stdin.read()
        if not findings_md.strip():
            print("错误: 尽调结论为空（用 --findings-file 或 stdin 传入 Markdown）")
            sys.exit(1)
        result = write_due_diligence(args.write_dd.strip(), findings_md)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result.get("ok"):
            sys.exit(1)
        return

    if args.forget_node:
        state = load_state()
        token = args.forget_node.strip()
        if token in state["processed"]:
            del state["processed"][token]
            save_state(state)
            print(f"已从状态文件移除: {token}")
        else:
            print(f"状态文件中未找到: {token}")
        return

    if args.list_nodes:
        config = _load_config()
        if not config["space_id"]:
            print("请先配置 FEISHU_WIKI_SPACE_ID（lark-cli wiki +space-list 获取）")
            sys.exit(1)
        nodes = list_wiki_nodes(config["space_id"], config["contract_node"])
        print(f"\n知识库 {config['space_id']} 节点列表（{len(nodes)} 个）:")
        for n in nodes:
            print(f"  {n.get('node_token', '?'):20s}  [{n.get('obj_type', '?'):8s}]  {n.get('title', '')}")
        print("\n将目标节点的 node_token 配置到 FEISHU_CONTRACT_NODE / FEISHU_REPORT_NODE")
        return

    result = run_once(dry_run=args.dry_run)
    if not result.get("ok"):
        print(f"\n错误: {result.get('error', '未知错误')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
