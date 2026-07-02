"""PDF → 结构化 Markdown 转换 + token 量化工具。

设计动机
--------
导师反馈：合同审核场景里，把 PDF 转成 Markdown 喂给下游，能显著节省 token 和上下文成本。
本模块把这个价值点落地成可度量、可复用的 skill 层：

1. ``pdf_to_markdown`` —— 用 PyMuPDF 结构化提取（字体大小聚类识别标题层级、
   ``find_tables`` 识别表格），输出精简 Markdown，而不是 ``get_text("text")``
   那种丢失版面结构的纯文本流。
2. ``estimate_tokens`` —— 用 tiktoken 精确估算文本 token 数。
3. ``build_token_savings_profile`` —— 量化「纯 LLM 从头审」vs「规则引擎证据层 +
   LLM 终局决策」两种架构的 token 消耗差异，把混合架构的节省讲成数字。

下游 ``contract_review.extract_text_from_file`` 对 PDF 调用 ``pdf_to_markdown``，
让规则引擎和 LLM 拿到的都是结构化 Markdown。
"""

from __future__ import annotations

import re
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import tiktoken


_ENCODER: tiktoken.Encoding | None = None


def _encoder() -> tiktoken.Encoding:
    global _ENCODER
    if _ENCODER is None:
        try:
            _ENCODER = tiktoken.encoding_for_model("gpt-4o")
        except KeyError:
            _ENCODER = tiktoken.get_encoding("cl100k_base")
    return _ENCODER


def estimate_tokens(text: str) -> int:
    """估算文本 token 数（tiktoken cl100k_base，对齐 GPT-4o / SenseChat 量级）。

    对中文合同文本，cl100k_base 每 token 约 1.5–2 个汉字，与主流商用模型量级接近，
    用于架构级 token 节省对比足够准确。
    """
    if not text:
        return 0
    return len(_encoder().encode(text))


def pdf_to_markdown(path: Path) -> str:
    """把 PDF 转成结构化 Markdown。

    识别策略：
    - 字体大小聚类：统计每页字号分布，出现最多的视为正文，明显更大的视为标题；
    - 表格：优先用 ``page.find_tables()`` 提取，输出 Markdown 表格语法；
    - 段落：同 block 内连续行合并为一段，避免纯文本流那种逐行断裂。

    降级：PyMuPDF 结构化提取拿不到内容时，回退到纯文本 + 去冗余空白。
    """
    import fitz  # type: ignore

    pages: list[str] = []
    with fitz.open(path) as doc:
        for page in doc:
            pages.append(_page_to_markdown(page))
    body = "\n\n---\n\n".join(p for p in pages if p.strip())
    if body.strip():
        return body
    # 降级：结构化提取无内容时回退纯文本
    with fitz.open(path) as doc:
        return "\n".join(page.get_text("text") for page in doc)


def _page_to_markdown(page) -> str:
    table_bboxes: list[tuple[float, float, float, float]] = []
    table_mds: list[str] = []
    try:
        for tbl in page.find_tables():
            table_bboxes.append(tuple(tbl.bbox))
            table_mds.append(_rows_to_md_table(tbl.extract()))
    except Exception:
        pass

    page_dict = page.get_text("dict")
    blocks = [b for b in page_dict.get("blocks", []) if b.get("type") == 0]
    if not blocks:
        return "\n\n".join(table_mds)

    body_size = _infer_body_size(blocks)
    out: list[str] = []
    for block in blocks:
        bbox = tuple(block.get("bbox", (0, 0, 0, 0)))
        if _bbox_in_any(bbox, table_bboxes):
            continue
        spans = _collect_spans(block)
        if not spans:
            continue
        avg_size = statistics.mean(s["size"] for s in spans)
        text = _merge_block_text(spans)
        if not text.strip():
            continue
        if _looks_like_heading(text, avg_size, body_size):
            level = _heading_level(avg_size, body_size)
            out.append(f"{'#' * level} {text.strip()}")
        else:
            out.append(text.strip())

    if table_mds:
        out.extend(table_mds)
    return "\n\n".join(out)


def _infer_body_size(blocks: list[dict]) -> float:
    sizes: list[float] = []
    for block in blocks:
        for s in _collect_spans(block):
            sizes.append(s["size"])
    if not sizes:
        return 11.0
    # 出现频率最高的字号区间（0.5 容差聚类）即正文
    buckets: dict[float, list[float]] = {}
    for size in sizes:
        key = round(size * 2) / 2
        buckets.setdefault(key, []).append(size)
    body_key = max(buckets, key=lambda k: len(buckets[k]))
    return statistics.mean(buckets[body_key])


def _collect_spans(block: dict) -> list[dict]:
    spans: list[dict] = []
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            text = (span.get("text") or "").strip()
            if text:
                spans.append({"text": span["text"], "size": span.get("size", 11.0)})
    return spans


def _merge_block_text(spans: list[dict]) -> str:
    # 同 block 内按出现顺序合并，行尾标点不额外加空格
    parts: list[str] = []
    for span in spans:
        parts.append(span["text"])
    text = "".join(parts)
    return re.sub(r"[ \t]+", " ", text).strip()


def _looks_like_heading(text: str, size: float, body_size: float) -> bool:
    text = text.strip()
    if not text or len(text) > 40:
        return False
    if size < body_size + 1.5:
        return False
    # 标题通常不以句号/逗号结尾
    if text.endswith(("。", "，", "；", "、", ".", ",")):
        return False
    # 含「合同」「条」「章」「节」「附件」等结构词的短行大概率是标题
    structural = ("合同", "条款", "条", "章", "节", "附件", "附录", "第", "甲乙", "一、", "二、", "三、")
    if any(text.startswith(w) or text.endswith(w) for w in structural):
        return True
    # 纯数字编号或短标题
    if re.fullmatch(r"[第\d一二三四五六七八九十百]+[章节条]", text):
        return True
    return True


def _heading_level(size: float, body_size: float) -> int:
    ratio = size / body_size if body_size else 1
    if ratio >= 1.8:
        return 1
    if ratio >= 1.4:
        return 2
    return 3


def _rows_to_md_table(rows: list[list[str | None]]) -> str:
    clean = [[(c or "").replace("\n", " ").strip() for c in row] for row in rows if any(c for c in row)]
    if not clean:
        return ""
    width = max(len(r) for r in clean)
    clean = [r + [""] * (width - len(r)) for r in clean]
    header = clean[0]
    body = clean[1:] if len(clean) > 1 else []
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _bbox_in_any(bbox: tuple, table_bboxes: list[tuple]) -> bool:
    bx0, by0, bx1, by1 = bbox
    for tx0, ty0, tx1, ty1 in table_bboxes:
        # block 中心落在表格 bbox 内即视为被表格覆盖
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        if tx0 <= cx <= tx1 and ty0 <= cy <= ty1:
            return True
    return False


# ── token 节省量化 ──────────────────────────────────────────────


@dataclass
class TokenScenario:
    name: str
    rounds: int
    contract_tokens: int
    knowledge_tokens: int
    rule_tokens: int
    output_tokens: int
    total_tokens: int
    notes: str


@dataclass
class TokenSavingsProfile:
    raw_text_chars: int
    markdown_chars: int
    markdown_tokens: int
    rule_reference_tokens: int
    rules_definition_tokens: int
    knowledge_context_tokens: int
    scenarios: list[TokenScenario]
    recommended_scenario: str
    savings_tokens: int
    savings_percent: float


def build_token_savings_profile(
    raw_text: str,
    markdown_text: str,
    rule_reference_json: str,
    knowledge_context: str,
    rules_definition_text: str = "",
    pure_llm_conclusion_tokens: int = 3500,
    pure_llm_report_tokens: int = 2500,
    hybrid_output_tokens: int = 2500,
) -> TokenSavingsProfile:
    """量化两种审核架构的 token 消耗，体现混合架构的节省。

    场景 A · 纯 LLM 从头审（2 轮）：
      - 轮 1 逐项检查：input = 合同全文 + 知识库 + 26 条规则定义，
        output = 26 项结论 + 推理链；
      - 轮 2 汇总报告：input = 轮 1 结论 + 合同全文（引用原文），
        output = 审核报告。
      LLM 既要读全文、又要从头对每条规则做数值/语义判断，且数值类检查
      （金额大小写、税率、付款比例）容易出错，可能需要自我校验。

    场景 B · 混合架构（本作品，1 轮）：
      - 本地规则引擎零 token 完成 26 项结构化检查（Decimal 精确计算数值类）；
      - LLM 单轮复核：input = 合同 Markdown + 知识库 + 规则结论 JSON，
        output = 终局报告（复核 + 修正误报 + 引用原文）。

    返回的 ``savings_percent`` 即导师要的「节省多少 token」的数字答案。

    Args:
        rules_definition_text: 26 条规则定义全文（纯 LLM 场景需作为检查指令输入）。
        pure_llm_conclusion_tokens: 场景 A 轮 1 输出（26 项结论 + 推理）。
        pure_llm_report_tokens: 场景 A 轮 2 输出（报告）。
        hybrid_output_tokens: 场景 B 输出（复核 + 终局报告）。
    """
    raw_tokens = estimate_tokens(raw_text)
    md_tokens = estimate_tokens(markdown_text)
    rule_ref_tokens = estimate_tokens(rule_reference_json)
    rules_def_tokens = estimate_tokens(rules_definition_text) if rules_definition_text else rule_ref_tokens
    kb_tokens = estimate_tokens(knowledge_context)

    # 场景 A：2 轮，合同读 2 次
    a_input = 2 * raw_tokens + kb_tokens + rules_def_tokens
    a_output = pure_llm_conclusion_tokens + pure_llm_report_tokens
    scenario_a = TokenScenario(
        name="纯 LLM 从头审（2 轮：检查 + 报告）",
        rounds=2,
        contract_tokens=2 * raw_tokens,
        knowledge_tokens=kb_tokens,
        rule_tokens=rules_def_tokens,
        output_tokens=a_output,
        total_tokens=a_input + a_output,
        notes="LLM 需读规则定义 → 逐项推理 26 条 → 二轮汇总报告；数值类检查易错",
    )

    # 场景 B：1 轮，规则引擎已出结论
    b_input = md_tokens + kb_tokens + rule_ref_tokens
    scenario_b = TokenScenario(
        name="混合架构（规则引擎 + LLM 终局决策，1 轮）",
        rounds=1,
        contract_tokens=md_tokens,
        knowledge_tokens=kb_tokens,
        rule_tokens=rule_ref_tokens,
        output_tokens=hybrid_output_tokens,
        total_tokens=b_input + hybrid_output_tokens,
        notes="规则引擎零 token 做 26 项检查 → LLM 单轮复核结论 + 出报告",
    )

    savings = scenario_a.total_tokens - scenario_b.total_tokens
    savings_pct = round(savings / scenario_a.total_tokens * 100, 1) if scenario_a.total_tokens else 0.0

    return TokenSavingsProfile(
        raw_text_chars=len(raw_text),
        markdown_chars=len(markdown_text),
        markdown_tokens=md_tokens,
        rule_reference_tokens=rule_ref_tokens,
        rules_definition_tokens=rules_def_tokens,
        knowledge_context_tokens=kb_tokens,
        scenarios=[scenario_a, scenario_b],
        recommended_scenario=scenario_b.name,
        savings_tokens=max(savings, 0),
        savings_percent=max(savings_pct, 0.0),
    )


def token_savings_json(profile: TokenSavingsProfile) -> str:
    import json
    return json.dumps(asdict(profile), ensure_ascii=False, indent=2)


def token_savings_markdown(profile: TokenSavingsProfile) -> str:
    """把 token 节省对比渲染成可贴进报告的 Markdown 表格。"""
    lines = [
        "## Token 消耗对比（混合架构 vs 纯 LLM）",
        "",
        f"- 原始合同：{profile.raw_text_chars} 字符",
        f"- 结构化 Markdown：{profile.markdown_chars} 字符（{profile.markdown_tokens} tokens）",
        f"- 规则引擎结论 JSON：{profile.rule_reference_tokens} tokens",
        f"- 26 条规则定义：{profile.rules_definition_tokens} tokens（纯 LLM 场景需作为输入）",
        f"- 知识库上下文：{profile.knowledge_context_tokens} tokens",
        "",
        "| 架构 | 轮次 | 合同输入 | 知识库 | 规则(定义/结论) | 输出 | 合计 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for s in profile.scenarios:
        lines.append(
            f"| {s.name} | {s.rounds} | {s.contract_tokens} | {s.knowledge_tokens} | "
            f"{s.rule_tokens} | {s.output_tokens} | **{s.total_tokens}** |"
        )
    lines.extend([
        "",
        f"> 推荐架构：**{profile.recommended_scenario}**",
        f"> 单次审核节省约 **{profile.savings_tokens} tokens**（**{profile.savings_percent}%**）",
        f"> 规则引擎 26 项检查零 token 成本（Decimal 精确计算数值类），"
        f"LLM 侧仅消费 {profile.scenarios[1].total_tokens} tokens 做终局复核。",
    ])
    return "\n".join(lines)
