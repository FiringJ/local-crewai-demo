#!/usr/bin/env python
"""真实 A/B 实测：纯 LLM 从头审 vs 混合架构（规则引擎 + LLM 复核）。

两种架构对同一份合同真实调用 LLM，token 用量取 API 返回的 usage 字段，
不做任何估算，用于回答「省 17.6% token 是怎么来的」——给出实测依据。

  架构 A · 纯 LLM（2 轮）：
    轮 1：合同全文 + 知识库红线 + 26 条规则定义 → 逐项检查结论
    轮 2：轮 1 结论 + 合同全文 → 终局审核报告
  架构 B · 混合（1 轮，本作品）：
    本地规则引擎（0 token）先出 26 项结论 JSON
    单轮：合同 + 知识库红线 + 规则结论 JSON → 复核 + 终局报告

用法：
  uv run python scripts/token_ab_test.py [合同文件路径]
  默认合同：knowledge/real_based_hospital_contract.txt
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv  # type: ignore

load_dotenv(PROJECT_ROOT / ".env")

from openai import OpenAI  # type: ignore

from local_crewai_demo.contract_review import audit_contract_text, rule_reference_json
from local_crewai_demo.gui import _load_knowledge_context, _load_rules_definition


def _client() -> tuple[OpenAI, str]:
    """优先 SenseChat，缺 key 时用 DeepSeek 平替（同为 OpenAI 兼容协议）。"""
    if os.environ.get("SENSENOVA_API_KEY"):
        return (
            OpenAI(
                api_key=os.environ["SENSENOVA_API_KEY"],
                base_url=os.environ.get("BASE_URL", "https://api.sensenova.cn/compatible-mode/v2"),
            ),
            os.environ.get("MODEL", "SenseChat-5").removeprefix("openai/"),
        )
    return (
        OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com"),
        "deepseek-chat",
    )


def _chat(client: OpenAI, model: str, system: str, user: str) -> tuple[str, dict[str, int]]:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2,
    )
    usage = resp.usage
    return resp.choices[0].message.content or "", {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
    }


def main() -> None:
    contract_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        PROJECT_ROOT / "knowledge" / "real_based_hospital_contract.txt"
    )
    contract = contract_path.read_text(encoding="utf-8")
    kb = _load_knowledge_context()
    rules_def = _load_rules_definition()

    client, model = _client()
    print(f"合同: {contract_path.name} ({len(contract)} 字符) | 模型: {model}\n")

    # ── 架构 A · 纯 LLM 两轮 ──
    sys_a = "你是企业合同审核专家。严格按照给定的审核规则逐项检查合同，输出每一项的编号、结论（通过/不通过/需复核）、证据与建议。"
    round1_user = (
        f"# 审核规则（26 项）\n{rules_def}\n\n# 法务红线知识库\n{kb}\n\n"
        f"# 待审合同全文\n{contract}\n\n请逐项（R01-R26）检查并输出结论。金额、税率、付款比例等数值项必须自行计算核对。"
    )
    out1, u1 = _chat(client, model, sys_a, round1_user)

    round2_user = (
        f"# 逐项检查结论\n{out1}\n\n# 合同全文（供引用原文）\n{contract}\n\n"
        "请汇总为终局审核报告：总体结论、通过率、高中低风险分布、重点风险项（引用合同原文）、修改建议。"
    )
    out2, u2 = _chat(client, model, sys_a, round2_user)

    a_total = u1["total_tokens"] + u2["total_tokens"]
    print(f"[A 纯 LLM · 轮1 逐项检查] prompt={u1['prompt_tokens']} completion={u1['completion_tokens']} total={u1['total_tokens']}")
    print(f"[A 纯 LLM · 轮2 汇总报告] prompt={u2['prompt_tokens']} completion={u2['completion_tokens']} total={u2['total_tokens']}")
    print(f"[A 合计] {a_total}\n")

    # ── 架构 B · 混合单轮 ──
    audit = audit_contract_text(contract, contract_path.name)
    rule_ref = rule_reference_json(audit)
    sys_b = (
        "你是企业合同审核专家。本地规则引擎已完成 26 项精确检查（数值类用 Decimal 精确计算，结论可信），"
        "你只需复核其结论、修正可能的语义误报，并输出终局审核报告（引用合同原文）。"
    )
    round_b_user = (
        f"# 规则引擎结论（26 项，JSON）\n{rule_ref}\n\n# 法务红线知识库\n{kb}\n\n"
        f"# 合同全文（供复核与引用）\n{contract}\n\n请输出终局审核报告：总体结论、风险分布、重点风险项、修改建议。"
    )
    out_b, ub = _chat(client, model, sys_b, round_b_user)

    print(f"[B 混合 · 单轮复核+报告] prompt={ub['prompt_tokens']} completion={ub['completion_tokens']} total={ub['total_tokens']}")
    print(f"[B 规则引擎 26 项检查] 0 token（本地 Decimal 计算）")
    print(f"[B 合计] {ub['total_tokens']}\n")

    savings = a_total - ub["total_tokens"]
    pct = round(savings / a_total * 100, 1)
    print(f"实测节省: {savings} tokens（{pct}%）  [A={a_total} → B={ub['total_tokens']}]")

    result = {
        "contract": contract_path.name,
        "model": model,
        "arch_a_pure_llm": {"round1": u1, "round2": u2, "total": a_total},
        "arch_b_hybrid": {"llm": ub, "rule_engine_tokens": 0, "total": ub["total_tokens"]},
        "savings_tokens": savings,
        "savings_percent": pct,
    }
    out_path = PROJECT_ROOT / "outputs" / "token-ab-result.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n结果已写入 {out_path}")


if __name__ == "__main__":
    main()
