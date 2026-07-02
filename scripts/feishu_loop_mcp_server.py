#!/usr/bin/env python
"""飞书合同审核闭环 · MCP Server（供办公小浣熊桌面端 MCP 连接器调用）。

暴露工具：
- ``run_feishu_loop``：轮询飞书知识库 → 三层 skill 审核 → 报告写回 + 多维表格
- ``audit_contract_text``：对粘贴的合同正文做本地审核（不读写飞书）

小浣熊 MCP 连接器配置示例见 ``docs/XIAOHUANXIONG_MCP_SETUP.md``。

运行::

    uv run python scripts/feishu_loop_mcp_server.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(PROJECT_ROOT / ".env", override=False)

import feishu_contract_loop as loop  # noqa: E402

mcp = FastMCP(
    "feishu-contract-loop",
    instructions=(
        "企业合同审查飞书闭环：检测知识库新增合同，经三层 skill（PDF结构化·规则引擎·LLM复核）"
        "审核后写回报告、多维表格与主体画像。标准编排：\n"
        "1) run_feishu_loop 审核新合同（返回 pending_due_diligence 待尽调主体清单）；\n"
        "2) 对每个待尽调主体用你的联网检索能力查工商/失信/涉诉/负面信息；\n"
        "3) write_due_diligence 把尽调结论（Markdown，附来源链接）写回该主体画像。"
    ),
)


@mcp.tool(
    name="run_feishu_loop",
    description=(
        "执行一次飞书合同审核闭环：轮询知识库新增 docx → 本地三层 skill 审核 "
        "→ 审核报告写回 wiki → 结构化记录写入多维表格 → 主体画像写回（审核历史）。"
        "返回 JSON 含 pending_due_diligence（待联网尽调的主体清单），"
        "调用方应对其逐一联网检索后用 write_due_diligence 回填。"
    ),
)
def run_feishu_loop(dry_run: bool = False) -> str:
    """触发飞书知识库合同审核闭环（单次轮询）。"""
    result = loop.run_once(dry_run=dry_run)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    name="get_pending_due_diligence",
    description=(
        "列出待联网尽调的合同对方主体（乙方）。调用方（小浣熊）应对每个主体"
        "联网检索工商、失信、涉诉、负面信息，再调用 write_due_diligence 写回。"
    ),
)
def get_pending_due_diligence() -> str:
    """列出待尽调主体。"""
    pending = loop.get_pending_due_diligence()
    return json.dumps(
        {"ok": True, "count": len(pending), "pending": pending},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool(
    name="write_due_diligence",
    description=(
        "把联网尽调结论写回主体画像（飞书 wiki 文档「【主体画像】<主体名>」）。"
        "findings_md 为 Markdown：应包含工商状态、失信/涉诉、负面信息小节，"
        "每条结论附来源链接；查不到公开信息时如实写明，不得编造。"
    ),
)
def write_due_diligence(counterparty: str, findings_md: str) -> str:
    """写入尽调结论并更新飞书画像文档。"""
    result = loop.write_due_diligence(counterparty, findings_md)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    name="audit_contract_text",
    description=(
        "对合同 Markdown/纯文本做本地审核（不读写飞书）。"
        "返回规则引擎结论、通过率、Token 节省与 LLM 报告（rules_agent 模式）。"
    ),
)
def audit_contract_text_tool(
    contract_text: str,
    file_name: str = "pasted_contract.txt",
    review_mode: str = "rules_agent",
) -> str:
    """审核粘贴的合同正文。"""
    config = loop._load_config()
    mode = review_mode or config.get("review_mode", "rules_agent")
    provider = config.get("llm_provider", "deepseek")
    result = loop.run_audit(contract_text, file_name, mode, provider)
    # 截断过长 report 便于 MCP 回传
    report = result.get("report", "")
    if isinstance(report, str) and len(report) > 4000:
        result = dict(result)
        result["report"] = report[:4000] + "\n\n…（报告已截断，完整版见飞书 wiki）"
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(
    name="list_feishu_wiki_nodes",
    description="列出飞书知识库指定目录下的节点（用于确认待审合同位置）。",
)
def list_feishu_wiki_nodes() -> str:
    """列出知识库节点。"""
    config = loop._load_config()
    if not config["space_id"]:
        return json.dumps({"ok": False, "error": "未配置 FEISHU_WIKI_SPACE_ID"}, ensure_ascii=False)
    nodes = loop.list_wiki_nodes(config["space_id"], config["contract_node"])
    return json.dumps({"ok": True, "count": len(nodes), "nodes": nodes}, ensure_ascii=False, indent=2)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
