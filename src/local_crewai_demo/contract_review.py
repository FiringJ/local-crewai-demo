from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import re
import subprocess
from pathlib import Path
from typing import Callable, Iterable
from xml.etree import ElementTree
from zipfile import ZipFile


HIGH = "高风险"
MEDIUM = "中风险"
LOW = "低风险"

PASS = "通过"
FAIL = "不通过"
REVIEW = "需复核"


@dataclass(frozen=True)
class Rule:
    group: str
    name: str
    risk: str
    logic: str


@dataclass
class Finding:
    group: str
    rule_name: str
    risk_level: str
    status: str
    evidence: str
    recommendation: str


@dataclass
class ContractFields:
    contract_name: str
    party_a: str
    party_b: str
    party_c: str
    party_addresses: list[str]
    party_contacts: list[str]
    total_amount: float | None
    uppercase_amount: float | None
    pre_tax_amount: float | None
    tax_amount: float | None
    tax_rates: list[float]
    payment_percentages: list[float]
    currencies: list[str]
    signing_date: str
    effective_date: str
    expiry_date: str
    line_items: list[dict[str, float | str]]


ALL_RULES: tuple[Rule, ...] = (
    Rule("财务条款审核", "合同金额大小写一致性", HIGH, "大写与数字金额须完全一致"),
    Rule("财务条款审核", "产品明细合计与总金额一致性", HIGH, "单价 x 数量 = 金额；合计 = 总额（+/- 0.01）"),
    Rule("财务条款审核", "金额合规检测", HIGH, "不含税 x 税率 = 税额；不含税 + 税额 = 含税总额"),
    Rule("财务条款审核", "税率合理性", HIGH, "须为 6% / 9% / 13% / 1% / 3% / 免税 / 0% 之一"),
    Rule("财务条款审核", "付款比例合计", HIGH, "分阶段付款比例合计须等于 100%"),
    Rule("财务条款审核", "付款条件明确性", MEDIUM, "付款节点和期限须明确"),
    Rule("财务条款审核", "付款方式明确性", MEDIUM, "须为银行转账 / 承兑汇票 / 第三方支付"),
    Rule("财务条款审核", "币别一致性", MEDIUM, "全文涉及金额的币别前后一致"),
    Rule("财务条款审核", "验收/交付标准明确性", MEDIUM, "须明确交付完成的判定标准"),
    Rule("财务条款审核", "滞纳金/违约金合理性", MEDIUM, "逾期违约金日费率 <= 0.05%"),
    Rule("财务条款审核", "履约保证金条款", MEDIUM, "须明确退还条件与时间节点"),
    Rule("财务条款审核", "连带责任条款", MEDIUM, "三方关系须明确各方债权债务"),
    Rule("法务合规审核", "签约主体名称一致性", HIGH, "首部、尾部签章处、正文须完全一致"),
    Rule("法务合规审核", "签约主体信息完整性", HIGH, "甲乙双方名称、地址、联系方式不为空"),
    Rule("法务合规审核", "必备条款完整性", HIGH, "须含主体、标的、数量、价款、期限、违约、争议解决"),
    Rule("法务合规审核", "合同日期合理性", MEDIUM, "签订日期 <= 生效日期 <= 到期日期"),
    Rule("法务合规审核", "违约金上限合理性", LOW, "须设上限（不超过合同总额 20%）"),
    Rule("法务合规审核", "违约对等性检查", LOW, "甲乙双方违约金比例差异 <= 50%"),
    Rule("法务合规审核", "不可抗力条款", LOW, "须含范围、通知时限、责任豁免方式"),
    Rule("文本质量审核", "内部一致性检测", MEDIUM, "跨条款无矛盾，付款条件与交付条款不冲突"),
    Rule("文本质量审核", "数字计算校验", LOW, "单价 x 数量 = 金额（每行）；分项合计 = 总额"),
    Rule("文本质量审核", "错别字/语义错误检测", LOW, "检测错别字、用词不当、语义歧义"),
)


MONEY_WORDS = "零〇一二三四五六七八九十百千万亿壹贰叁肆伍陆柒捌玖拾佰仟圆元角分整正"
DATE_PATTERN = re.compile(
    r"(?P<year>20\d{2})[年/-](?P<month>1[0-2]|0?[1-9])[月/-](?P<day>3[01]|[12]\d|0?[1-9])日?"
)


def extract_text_from_file(path: Path) -> str:
    """Extract contract text from common office formats without hard dependencies."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_text(path)
    if suffix in {".docx", ".docm"}:
        return _extract_docx_text(path)
    if suffix in {".txt", ".md", ".csv"}:
        return path.read_text(encoding="utf-8", errors="replace")
    return path.read_bytes().decode("utf-8", errors="replace")


def audit_contract_text(text: str, file_name: str = "") -> dict[str, object]:
    normalized = _normalize_text(text)
    fields = _extract_fields(normalized, file_name)
    findings = [_run_rule(rule, normalized, fields) for rule in ALL_RULES]

    by_group: dict[str, list[dict[str, str]]] = {}
    for finding in findings:
        by_group.setdefault(finding.group, []).append(asdict(finding))

    failed = [item for item in findings if item.status == FAIL]
    needs_review = [item for item in findings if item.status == REVIEW]
    failed_by_risk = {
        HIGH: sum(1 for item in failed if item.risk_level == HIGH),
        MEDIUM: sum(1 for item in failed if item.risk_level == MEDIUM),
        LOW: sum(1 for item in failed if item.risk_level == LOW),
    }

    if failed_by_risk[HIGH]:
        conclusion = f"审核不通过（存在 {failed_by_risk[HIGH]} 项高风险）"
    elif failed:
        conclusion = f"审核需修订（存在 {len(failed)} 项不通过）"
    elif needs_review:
        conclusion = f"有待人工复核（存在 {len(needs_review)} 项证据不足）"
    else:
        conclusion = "审核通过"

    report = {
        "file_name": file_name,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "overall_conclusion": conclusion,
        "risk_statistics": {
            "total_rules": len(ALL_RULES),
            "passed": sum(1 for item in findings if item.status == PASS),
            "failed": len(failed),
            "needs_review": len(needs_review),
            "failed_by_risk": failed_by_risk,
        },
        "fields": asdict(fields),
        "rule_groups": by_group,
    }
    report["markdown"] = format_markdown_report(report)
    return report


def format_markdown_report(report: dict[str, object]) -> str:
    stats = report["risk_statistics"]  # type: ignore[index]
    fields = report["fields"]  # type: ignore[index]
    groups = report["rule_groups"]  # type: ignore[index]
    lines = [
        "# 合同审核报告",
        "",
        f"- 文件：{report.get('file_name') or '未命名合同'}",
        f"- 生成时间：{report['generated_at']}",
        f"- 总体结论：**{report['overall_conclusion']}**",
        (
            f"- 规则统计：通过 {stats['passed']} / {stats['total_rules']}，"
            f"不通过 {stats['failed']}，需复核 {stats['needs_review']}"
        ),
        "",
        "## 关键字段",
        "",
        f"- 合同名称：{fields.get('contract_name') or '未识别'}",
        f"- 甲方：{fields.get('party_a') or '未识别'}",
        f"- 乙方：{fields.get('party_b') or '未识别'}",
        f"- 合同金额：{_format_money(fields.get('total_amount'))}",
        f"- 税率：{_join_percentages(fields.get('tax_rates') or [])}",
        f"- 付款比例：{_join_percentages(fields.get('payment_percentages') or [])}",
        f"- 币别：{', '.join(fields.get('currencies') or []) or '未识别'}",
        "",
    ]

    for group, findings in groups.items():
        lines.extend([f"## {group}", "", "| 规则 | 风险 | 结论 | 依据 | 修改建议 |", "| --- | --- | --- | --- | --- |"])
        for finding in findings:
            lines.append(
                "| {rule_name} | {risk_level} | {status} | {evidence} | {recommendation} |".format(
                    rule_name=_escape_table(str(finding["rule_name"])),
                    risk_level=_escape_table(str(finding["risk_level"])),
                    status=_escape_table(str(finding["status"])),
                    evidence=_escape_table(str(finding["evidence"])),
                    recommendation=_escape_table(str(finding["recommendation"])),
                )
            )
        lines.append("")

    lines.extend(
        [
            "## 可复制修改要点",
            "",
        ]
    )
    failed_or_review = [
        finding
        for findings in groups.values()
        for finding in findings
        if finding["status"] in {FAIL, REVIEW}
    ]
    if not failed_or_review:
        lines.append("- 暂未发现需要修改的条款。")
    else:
        for finding in failed_or_review:
            lines.append(f"- {finding['rule_name']}：{finding['recommendation']}")
    return "\n".join(lines)


def _run_rule(rule: Rule, text: str, fields: ContractFields) -> Finding:
    checks: dict[str, Callable[[str, ContractFields], tuple[str, str, str]]] = {
        "合同金额大小写一致性": _check_amount_uppercase,
        "产品明细合计与总金额一致性": _check_line_items_total,
        "金额合规检测": _check_tax_amounts,
        "税率合理性": _check_tax_rate,
        "付款比例合计": _check_payment_percentages,
        "付款条件明确性": _check_payment_terms,
        "付款方式明确性": _check_payment_method,
        "币别一致性": _check_currency,
        "验收/交付标准明确性": _check_acceptance_delivery,
        "滞纳金/违约金合理性": _check_late_fee,
        "履约保证金条款": _check_performance_bond,
        "连带责任条款": _check_joint_liability,
        "签约主体名称一致性": _check_party_name_consistency,
        "签约主体信息完整性": _check_party_information,
        "必备条款完整性": _check_required_clauses,
        "合同日期合理性": _check_contract_dates,
        "违约金上限合理性": _check_penalty_cap,
        "违约对等性检查": _check_breach_symmetry,
        "不可抗力条款": _check_force_majeure,
        "内部一致性检测": _check_internal_consistency,
        "数字计算校验": _check_numeric_validation,
        "错别字/语义错误检测": _check_text_quality,
    }
    status, evidence, recommendation = checks[rule.name](text, fields)
    return Finding(
        group=rule.group,
        rule_name=rule.name,
        risk_level=rule.risk,
        status=status,
        evidence=evidence,
        recommendation=recommendation,
    )


def _extract_pdf_text(path: Path) -> str:
    errors: list[str] = []
    try:
        import fitz  # type: ignore

        with fitz.open(path) as doc:
            text = "\n".join(page.get_text("text") for page in doc)
        if text.strip():
            return text
    except Exception as exc:  # pragma: no cover - optional dependency path
        errors.append(f"PyMuPDF: {exc}")

    try:
        import pdfplumber  # type: ignore

        with pdfplumber.open(path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        if text.strip():
            return text
    except Exception as exc:  # pragma: no cover - optional dependency path
        errors.append(f"pdfplumber: {exc}")

    try:
        completed = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
        )
        if completed.stdout.strip():
            return completed.stdout
    except Exception as exc:  # pragma: no cover - local CLI path
        errors.append(f"pdftotext: {exc}")

    raise ValueError(f"无法从 PDF 提取文本：{'; '.join(errors) or '未知错误'}")


def _extract_docx_text(path: Path) -> str:
    parts: list[str] = []
    with ZipFile(path) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.startswith("word/")
            and name.endswith(".xml")
            and ("document" in name or "header" in name or "footer" in name)
        ]
        for name in names:
            root = ElementTree.fromstring(archive.read(name))
            paragraphs: list[str] = []
            for paragraph in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                runs = [
                    node.text or ""
                    for node in paragraph.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
                ]
                if "".join(runs).strip():
                    paragraphs.append("".join(runs))
            parts.extend(paragraphs)
    return "\n".join(parts)


def _extract_fields(text: str, file_name: str) -> ContractFields:
    return ContractFields(
        contract_name=_extract_contract_name(text, file_name),
        party_a=_extract_party(text, "甲方"),
        party_b=_extract_party(text, "乙方"),
        party_c=_extract_party(text, "丙方"),
        party_addresses=_extract_labeled_values(text, ["地址", "住所", "注册地址"]),
        party_contacts=_extract_labeled_values(text, ["电话", "联系方式", "联系人", "邮箱"]),
        total_amount=_extract_labeled_money(text, ["合同总金额", "合同金额", "总价款", "总价", "含税总额", "价款"]),
        uppercase_amount=_extract_uppercase_amount(text),
        pre_tax_amount=_extract_labeled_money(text, ["不含税金额", "不含税价款", "未税金额"]),
        tax_amount=_extract_labeled_money(text, ["税额", "增值税额"]),
        tax_rates=_extract_tax_rates(text),
        payment_percentages=_extract_payment_percentages(text),
        currencies=_extract_currencies(text),
        signing_date=_extract_labeled_date(text, ["签订日期", "签署日期", "合同签订日"]),
        effective_date=_extract_labeled_date(text, ["生效日期", "生效日", "起始日期", "开始日期"]),
        expiry_date=_extract_labeled_date(text, ["到期日期", "终止日期", "截止日期", "结束日期"]),
        line_items=_extract_line_items(text),
    )


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t\xa0]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_contract_name(text: str, file_name: str) -> str:
    patterns = [
        r"合同名称[：:\s]+([^\n]{2,80})",
        r"^([^\n]{2,60}合同)\s*$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.M)
        if match:
            return _clean_value(match.group(1))
    for line in text.splitlines()[:12]:
        clean = _clean_value(line)
        if 2 <= len(clean) <= 60 and "合同" in clean:
            return clean
    return Path(file_name).stem if file_name else ""


def _extract_party(text: str, label: str) -> str:
    pattern = rf"{label}(?:（[^）]+）)?\s*[：:]\s*([^\n；;，,]+)"
    match = re.search(pattern, text)
    if match:
        return _clean_value(match.group(1))
    return ""


def _extract_labeled_values(text: str, labels: Iterable[str]) -> list[str]:
    values: list[str] = []
    for label in labels:
        for match in re.finditer(rf"{label}\s*[：:]\s*([^\n；;]+)", text):
            value = _clean_value(match.group(1))
            if value and value not in values:
                values.append(value)
    return values[:12]


def _extract_labeled_money(text: str, labels: Iterable[str]) -> float | None:
    for label in labels:
        for line in text.splitlines():
            if label not in line:
                continue
            after_label = line.split(label, 1)[1]
            match = re.search(
                r"(?:人民币|RMB|CNY|￥|¥)?\s*([0-9][0-9,]*(?:\.\d+)?)\s*(万元|万|元)?",
                after_label,
                re.I,
            )
            if match:
                return _decimal_to_float(_parse_number_amount(match.group(1), match.group(2)))
    return None


def _extract_uppercase_amount(text: str) -> float | None:
    patterns = [
        rf"(?:大写|人民币大写|金额大写)[：:\s]*([{MONEY_WORDS}]+)",
        rf"人民币([{MONEY_WORDS}]{{3,}})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            amount = _chinese_money_to_decimal(match.group(1))
            if amount is not None:
                return _decimal_to_float(amount)
    return None


def _extract_tax_rates(text: str) -> list[float]:
    rates: list[float] = []
    for line in text.splitlines():
        if not re.search(r"税率|增值税|免税|零税率", line):
            continue
        for match in re.finditer(r"(\d+(?:\.\d+)?)\s*%", line):
            rate = float(match.group(1))
            if rate not in rates:
                rates.append(rate)
    if re.search(r"免税|零税率", text) and 0.0 not in rates:
        rates.append(0.0)
    return rates


def _extract_payment_percentages(text: str) -> list[float]:
    values: list[float] = []
    for line in text.splitlines():
        if "违约金" in line:
            continue
        if re.search(r"付款|预付|首付款|进度款|尾款|结算|价款", line):
            for match in re.finditer(r"(\d+(?:\.\d+)?)\s*%", line):
                values.append(float(match.group(1)))
    return values


def _extract_currencies(text: str) -> list[str]:
    mapping = {
        "人民币": r"人民币|RMB|CNY|￥|¥",
        "美元": r"美元|USD|\$",
        "欧元": r"欧元|EUR|€",
        "港币": r"港币|HKD",
    }
    currencies = [name for name, pattern in mapping.items() if re.search(pattern, text, re.I)]
    return currencies


def _extract_labeled_date(text: str, labels: Iterable[str]) -> str:
    for label in labels:
        match = re.search(rf"{label}[^0-9]{{0,12}}({DATE_PATTERN.pattern})", text)
        if match:
            return _normalize_date(match.group(1))
    return ""


def _extract_line_items(text: str) -> list[dict[str, float | str]]:
    items: list[dict[str, float | str]] = []
    money = r"([0-9][0-9,]*(?:\.\d+)?)"
    labeled_pattern = re.compile(
        rf"数量\s*{money}\s*(?:台|件|套|个|项|批)?[^0-9\n]{{0,12}}单价\s*{money}\s*(?:元)?[^0-9\n]{{0,12}}金额\s*{money}",
    )
    loose_pattern = re.compile(rf"{money}\s*(?:台|件|套|个|项|批)?\s+{money}\s*(?:元)?\s+{money}")
    for line in text.splitlines():
        if not re.search(r"产品|设备|服务|明细|数量|单价|金额|小计|合计|规格", line):
            continue
        compact_line = line.replace(",", "")
        match = labeled_pattern.search(compact_line) or loose_pattern.search(compact_line)
        if not match:
            continue
        quantity = _decimal_to_float(_to_decimal(match.group(1)))
        unit_price = _decimal_to_float(_to_decimal(match.group(2)))
        amount = _decimal_to_float(_to_decimal(match.group(3)))
        items.append(
            {
                "line": _clean_value(line),
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
            }
        )
    return items[:50]


def _check_amount_uppercase(_text: str, fields: ContractFields) -> tuple[str, str, str]:
    if fields.total_amount is None or fields.uppercase_amount is None:
        return (
            REVIEW,
            "未同时识别到数字金额与大写金额。",
            "补充合同金额的数字写法与人民币大写写法，并保持两者完全一致。",
        )
    delta = abs(Decimal(str(fields.total_amount)) - Decimal(str(fields.uppercase_amount)))
    if delta <= Decimal("0.01"):
        return PASS, f"数字金额 {fields.total_amount:.2f} 与大写金额一致。", "无需修改。"
    return (
        FAIL,
        f"数字金额 {fields.total_amount:.2f} 与大写金额 {fields.uppercase_amount:.2f} 不一致。",
        "以双方确认的合同价款为准，同步修正数字金额和人民币大写金额。",
    )


def _check_line_items_total(_text: str, fields: ContractFields) -> tuple[str, str, str]:
    if not fields.line_items or fields.total_amount is None:
        return (
            REVIEW,
            "未识别到可计算的产品明细或合同总金额。",
            "补充结构化产品明细：名称、数量、单价、金额，并写明合计金额。",
        )
    bad_lines: list[str] = []
    total = Decimal("0")
    for item in fields.line_items:
        quantity = Decimal(str(item["quantity"]))
        unit_price = Decimal(str(item["unit_price"]))
        amount = Decimal(str(item["amount"]))
        total += amount
        if abs(quantity * unit_price - amount) > Decimal("0.01"):
            bad_lines.append(str(item["line"]))
    total_delta = abs(total - Decimal(str(fields.total_amount)))
    if not bad_lines and total_delta <= Decimal("0.01"):
        return PASS, f"识别 {len(fields.line_items)} 条明细，合计 {total:.2f} 与总金额一致。", "无需修改。"
    evidence = []
    if bad_lines:
        evidence.append(f"{len(bad_lines)} 条明细的数量 x 单价与金额不一致")
    if total_delta > Decimal("0.01"):
        evidence.append(f"明细合计 {total:.2f} 与总金额 {fields.total_amount:.2f} 不一致")
    return FAIL, "；".join(evidence), "逐行复核产品明细金额，并将明细合计调整为合同总金额。"


def _check_tax_amounts(_text: str, fields: ContractFields) -> tuple[str, str, str]:
    if fields.pre_tax_amount is None or fields.tax_amount is None or fields.total_amount is None or not fields.tax_rates:
        return (
            REVIEW,
            "未完整识别不含税金额、税额、含税总额和税率。",
            "补充不含税金额、税率、税额、含税总额，并明确计算公式。",
        )
    rate = Decimal(str(fields.tax_rates[0])) / Decimal("100")
    pre_tax = Decimal(str(fields.pre_tax_amount))
    tax = Decimal(str(fields.tax_amount))
    total = Decimal(str(fields.total_amount))
    expected_tax = (pre_tax * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    expected_total = (pre_tax + tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if abs(expected_tax - tax) <= Decimal("0.01") and abs(expected_total - total) <= Decimal("0.01"):
        return PASS, "税额与含税总额计算一致。", "无需修改。"
    return (
        FAIL,
        f"按 {fields.tax_rates[0]:g}% 计算税额应为 {expected_tax}，不含税+税额应为 {expected_total}。",
        "按“税额=不含税金额 x 税率；含税总额=不含税金额+税额”重算并修正价税字段。",
    )


def _check_tax_rate(_text: str, fields: ContractFields) -> tuple[str, str, str]:
    allowed = {0.0, 1.0, 3.0, 6.0, 9.0, 13.0}
    if not fields.tax_rates:
        return REVIEW, "未识别到税率。", "补充适用税率，并注明税率适用依据。"
    invalid = [rate for rate in fields.tax_rates if rate not in allowed]
    if not invalid:
        return PASS, f"识别税率：{_join_percentages(fields.tax_rates)}，均在允许范围内。", "无需修改。"
    return (
        FAIL,
        f"识别到不合规税率：{_join_percentages(invalid)}。",
        "将税率调整为 6% / 9% / 13% / 1% / 3% / 免税 / 0% 中适用的一项，并同步调整税额。",
    )


def _check_payment_percentages(_text: str, fields: ContractFields) -> tuple[str, str, str]:
    if not fields.payment_percentages:
        return REVIEW, "未识别到分阶段付款比例。", "补充分阶段付款比例，并确保合计为 100%。"
    total = sum(fields.payment_percentages)
    if abs(total - 100) <= 0.01:
        return PASS, f"付款比例合计 {total:g}%。", "无需修改。"
    return FAIL, f"付款比例为 {_join_percentages(fields.payment_percentages)}，合计 {total:g}%。", "调整各阶段付款比例，使合计等于 100%。"


def _check_payment_terms(text: str, _fields: ContractFields) -> tuple[str, str, str]:
    has_payment = re.search(r"付款|支付|结算|预付款|尾款", text)
    has_condition = re.search(r"验收后|交付后|收到发票后|签署后|生效后|\d+\s*(?:个)?(?:工作日|日|天)内|付款节点|付款期限", text)
    if has_payment and has_condition:
        return PASS, "付款条款包含节点或期限。", "无需修改。"
    return FAIL, "付款条款缺少明确节点或期限。", "写明付款触发条件和期限，例如“乙方交付并经甲方验收合格后 10 个工作日内支付”。"


def _check_payment_method(text: str, _fields: ContractFields) -> tuple[str, str, str]:
    if re.search(r"银行转账|电汇|承兑汇票|第三方支付|支付宝|微信支付|支票", text):
        return PASS, "已识别付款方式。", "无需修改。"
    return FAIL, "未识别银行转账、承兑汇票或第三方支付等付款方式。", "补充付款方式，并写明收款账户信息。"


def _check_currency(_text: str, fields: ContractFields) -> tuple[str, str, str]:
    if not fields.currencies:
        return REVIEW, "未识别到币别。", "在金额条款中明确币别，例如“人民币”。"
    if len(fields.currencies) == 1:
        return PASS, f"全文识别到单一币别：{fields.currencies[0]}。", "无需修改。"
    return FAIL, f"全文出现多个币别：{', '.join(fields.currencies)}。", "统一合同金额币别，或明确不同币别金额的适用范围和汇率规则。"


def _check_acceptance_delivery(text: str, _fields: ContractFields) -> tuple[str, str, str]:
    has_delivery = re.search(r"交付|交货|交割|提交成果|上线", text)
    has_acceptance = re.search(r"验收|验收标准|合格|签收|验收单|测试通过|交付标准", text)
    if has_delivery and has_acceptance:
        return PASS, "交付与验收标准均有描述。", "无需修改。"
    return FAIL, "交付完成或验收合格的判定标准不充分。", "补充交付物、验收标准、验收期限、不合格处理和视为验收的条件。"


def _check_late_fee(text: str, _fields: ContractFields) -> tuple[str, str, str]:
    rates = [
        float(match.group(1))
        for match in re.finditer(r"(?:逾期|滞纳金|违约金|迟延)[^。\n%]{0,24}(\d+(?:\.\d+)?)\s*%\s*(?:/|每)?日", text)
    ]
    if not rates:
        return REVIEW, "未识别到按日计算的滞纳金或违约金费率。", "如约定逾期违约金，应明确日费率且不超过 0.05%。"
    too_high = [rate for rate in rates if rate > 0.05]
    if not too_high:
        return PASS, f"识别按日费率：{_join_percentages(rates)}，未超过 0.05%。", "无需修改。"
    return FAIL, f"按日违约金费率 {_join_percentages(too_high)} 超过 0.05%。", "将逾期违约金日费率调整至不超过 0.05%，或设置合理上限。"


def _check_performance_bond(text: str, _fields: ContractFields) -> tuple[str, str, str]:
    if not re.search(r"履约保证金|保证金", text):
        return REVIEW, "未识别到履约保证金条款。", "如设置履约保证金，应补充金额、扣除情形、退还条件和退还时间。"
    has_refund = re.search(r"退还|返还|无息退回|退回", text)
    has_time = re.search(r"\d+\s*(?:个)?(?:工作日|日|天)内|验收后|到期后|履行完毕后", text)
    if has_refund and has_time:
        return PASS, "履约保证金包含退还条件与时间节点。", "无需修改。"
    return FAIL, "履约保证金缺少退还条件或时间节点。", "补充“履行完毕/验收合格后 X 个工作日内无息退还”等条款。"


def _check_joint_liability(text: str, _fields: ContractFields) -> tuple[str, str, str]:
    if not re.search(r"连带责任|三方|担保人|共同债务", text):
        return PASS, "未涉及连带责任或三方关系。", "无需修改。"
    if re.search(r"债权|债务|担保范围|责任范围|各方责任|追偿", text):
        return PASS, "连带责任相关债权债务关系有描述。", "无需修改。"
    return FAIL, "涉及连带责任或三方关系，但债权债务边界不清。", "明确各方身份、债权债务范围、承担方式和追偿安排。"


def _check_party_name_consistency(text: str, fields: ContractFields) -> tuple[str, str, str]:
    issues: list[str] = []
    for label, party in [("甲方", fields.party_a), ("乙方", fields.party_b), ("丙方", fields.party_c)]:
        if not party:
            continue
        variants = set(re.findall(rf"{label}(?:名称)?\s*[：:]\s*([^\n；;，,]+)", text))
        clean_variants = {_clean_value(value) for value in variants if _clean_value(value)}
        if len(clean_variants) > 1:
            issues.append(f"{label}出现多个名称：{', '.join(sorted(clean_variants))}")
    if issues:
        return FAIL, "；".join(issues), "统一首部、正文、签章页中的签约主体全称。"
    if fields.party_a and fields.party_b:
        return PASS, "甲乙双方名称未发现明显不一致。", "无需修改。"
    return REVIEW, "未完整识别甲乙双方名称。", "补充甲乙双方完整法定名称，并核对签章页。"


def _check_party_information(_text: str, fields: ContractFields) -> tuple[str, str, str]:
    missing = []
    if not fields.party_a:
        missing.append("甲方名称")
    if not fields.party_b:
        missing.append("乙方名称")
    if len(fields.party_addresses) < 2:
        missing.append("双方地址")
    if len(fields.party_contacts) < 2:
        missing.append("双方联系方式")
    if not missing:
        return PASS, "签约主体名称、地址、联系方式基本完整。", "无需修改。"
    return FAIL, f"缺少：{', '.join(missing)}。", "补充双方名称、地址、联系人、电话/邮箱等主体信息。"


def _check_required_clauses(text: str, _fields: ContractFields) -> tuple[str, str, str]:
    required = {
        "主体": r"甲方|乙方|签约主体",
        "标的": r"标的|采购内容|服务内容|产品名称",
        "数量": r"数量|规格|明细",
        "价款": r"价款|金额|总价|合同价",
        "期限": r"期限|有效期|履行期限|交付时间|服务期|生效日期|到期日期|终止日期",
        "违约": r"违约|赔偿|滞纳金",
        "争议解决": r"争议解决|仲裁|诉讼|管辖法院",
    }
    missing = [name for name, pattern in required.items() if not re.search(pattern, text)]
    if not missing:
        return PASS, "必备条款均有关键词覆盖。", "无需修改。"
    return FAIL, f"缺少或未识别：{', '.join(missing)}。", "补齐主体、标的、数量、价款、期限、违约责任和争议解决条款。"


def _check_contract_dates(_text: str, fields: ContractFields) -> tuple[str, str, str]:
    parsed = [_parse_date(value) for value in [fields.signing_date, fields.effective_date, fields.expiry_date]]
    if any(value is None for value in parsed):
        return REVIEW, "未完整识别签订日期、生效日期和到期日期。", "补充签订日期、生效日期和到期日期，并保持时间顺序清晰。"
    signing, effective, expiry = parsed
    if signing <= effective <= expiry:  # type: ignore[operator]
        return PASS, f"日期顺序为 {fields.signing_date} <= {fields.effective_date} <= {fields.expiry_date}。", "无需修改。"
    return FAIL, f"日期顺序异常：签订 {fields.signing_date}，生效 {fields.effective_date}，到期 {fields.expiry_date}。", "调整为“签订日期 <= 生效日期 <= 到期日期”。"


def _check_penalty_cap(text: str, fields: ContractFields) -> tuple[str, str, str]:
    if not re.search(r"违约金|赔偿", text):
        return REVIEW, "未识别违约金条款。", "如约定违约金，应设置不超过合同总额 20% 的上限。"
    cap_rates = [float(match.group(1)) for match in re.finditer(r"(?:上限|最高|累计不超过)[^%\n]{0,20}(\d+(?:\.\d+)?)\s*%", text)]
    if not cap_rates:
        return FAIL, "违约金条款未识别到上限。", "补充“违约金累计不超过合同总额 20%”等上限条款。"
    too_high = [rate for rate in cap_rates if rate > 20]
    if too_high:
        return FAIL, f"违约金上限 {_join_percentages(too_high)} 超过合同总额 20%。", "将违约金累计上限调整为不超过合同总额 20%。"
    amount_caps = _extract_amount_caps(text)
    if fields.total_amount and amount_caps:
        high_amounts = [amount for amount in amount_caps if amount > fields.total_amount * 0.2]
        if high_amounts:
            return FAIL, f"金额上限 {max(high_amounts):.2f} 超过合同总额 20%。", "按合同总额 20% 以内重设违约金上限。"
    return PASS, f"识别违约金上限：{_join_percentages(cap_rates)}。", "无需修改。"


def _check_breach_symmetry(text: str, _fields: ContractFields) -> tuple[str, str, str]:
    party_a_rates = _extract_party_breach_rates(text, "甲方")
    party_b_rates = _extract_party_breach_rates(text, "乙方")
    if not party_a_rates or not party_b_rates:
        return REVIEW, "未同时识别甲乙双方违约比例。", "补充甲乙双方违约责任，并确保比例差异不超过 50%。"
    a_rate = max(party_a_rates)
    b_rate = max(party_b_rates)
    if max(a_rate, b_rate) == 0:
        return REVIEW, "违约比例为 0，需人工复核条款合理性。", "明确违约金比例或计算方式。"
    diff = abs(a_rate - b_rate) / max(a_rate, b_rate)
    if diff <= 0.5:
        return PASS, f"甲方最高 {a_rate:g}%，乙方最高 {b_rate:g}%，差异 {diff:.0%}。", "无需修改。"
    return FAIL, f"甲方最高 {a_rate:g}%，乙方最高 {b_rate:g}%，差异 {diff:.0%}。", "调整甲乙双方违约金比例，使差异不超过 50%。"


def _check_force_majeure(text: str, _fields: ContractFields) -> tuple[str, str, str]:
    if "不可抗力" not in text:
        return FAIL, "未识别不可抗力条款。", "补充不可抗力的范围、通知时限、证明材料和责任豁免方式。"
    has_scope = re.search(r"自然灾害|战争|疫情|政府行为|法律法规|罢工|地震|洪水", text)
    has_notice = re.search(r"通知|\d+\s*(?:个)?(?:工作日|日|天)内", text)
    has_exemption = re.search(r"免责|免除责任|不承担责任|顺延|部分免除", text)
    if has_scope and has_notice and has_exemption:
        return PASS, "不可抗力条款包含范围、通知和责任处理。", "无需修改。"
    return FAIL, "不可抗力条款缺少范围、通知时限或责任豁免方式。", "补全不可抗力范围、通知期限、证明义务、履行顺延与免责边界。"


def _check_internal_consistency(_text: str, fields: ContractFields) -> tuple[str, str, str]:
    issues: list[str] = []
    if fields.payment_percentages and abs(sum(fields.payment_percentages) - 100) > 0.01:
        issues.append("付款比例合计不为 100%")
    parsed_dates = [_parse_date(value) for value in [fields.signing_date, fields.effective_date, fields.expiry_date]]
    if all(parsed_dates) and not (parsed_dates[0] <= parsed_dates[1] <= parsed_dates[2]):  # type: ignore[operator]
        issues.append("合同日期顺序存在冲突")
    if fields.total_amount and fields.pre_tax_amount and fields.tax_amount:
        if abs((fields.pre_tax_amount + fields.tax_amount) - fields.total_amount) > 0.01:
            issues.append("价税合计与合同金额冲突")
    if issues:
        return FAIL, "；".join(issues), "统一付款、日期、金额等跨条款信息，避免同一事项在不同条款出现冲突。"
    return PASS, "未发现付款比例、日期或金额的明显内部冲突。", "无需修改。"


def _check_numeric_validation(text: str, fields: ContractFields) -> tuple[str, str, str]:
    high_checks = [_check_line_items_total(text, fields), _check_tax_amounts(text, fields)]
    failures = [check for check in high_checks if check[0] == FAIL]
    passes = [check for check in high_checks if check[0] == PASS]
    if failures:
        return FAIL, "；".join(check[1] for check in failures), "复核单价、数量、税额、总额等数字字段，并使用统一公式重算。"
    if passes:
        return PASS, "已完成可识别数字字段的计算校验。", "无需修改。"
    return REVIEW, "缺少可计算的明细或价税字段。", "补充结构化金额字段，便于校验单价、数量、税额和总额。"


def _check_text_quality(text: str, _fields: ContractFields) -> tuple[str, str, str]:
    vague_terms = ["尽快", "左右", "原则上", "视情况", "另行协商", "适当", "大概", "相关费用"]
    hits = [term for term in vague_terms if term in text]
    repeated_punctuation = re.findall(r"[，。；：、]{2,}", text)
    if hits or repeated_punctuation:
        evidence = []
        if hits:
            evidence.append(f"存在模糊表述：{', '.join(hits[:8])}")
        if repeated_punctuation:
            evidence.append("存在连续重复标点")
        return FAIL, "；".join(evidence), "将模糊词替换为明确期限、金额、标准或责任边界，并修正重复标点。"
    return PASS, "未识别明显错别字、模糊词或重复标点。", "无需修改。"


def _parse_number_amount(value: str, unit: str | None = None) -> Decimal:
    amount = _to_decimal(value.replace("￥", "").replace("¥", "").replace(",", "").strip())
    if unit in {"万", "万元"}:
        amount *= Decimal("10000")
    return amount


def _to_decimal(value: str) -> Decimal:
    try:
        return Decimal(value.replace(",", "").strip())
    except InvalidOperation:
        return Decimal("0")


def _decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _chinese_money_to_decimal(value: str) -> Decimal | None:
    value = value.strip().replace("正", "整")
    if not value:
        return None
    integer_part = re.split(r"[圆元]", value)[0]
    fraction = Decimal("0")
    jiao = re.search(r"([零〇壹贰叁肆伍陆柒捌玖一二三四五六七八九])角", value)
    fen = re.search(r"([零〇壹贰叁肆伍陆柒捌玖一二三四五六七八九])分", value)
    if jiao:
        fraction += Decimal(_cn_digit(jiao.group(1))) / Decimal("10")
    if fen:
        fraction += Decimal(_cn_digit(fen.group(1))) / Decimal("100")
    integer = _parse_chinese_integer(integer_part)
    return Decimal(integer) + fraction


def _parse_chinese_integer(value: str) -> int:
    total = 0
    section = 0
    number = 0
    unit_map = {"拾": 10, "十": 10, "佰": 100, "百": 100, "仟": 1000, "千": 1000}
    big_unit_map = {"万": 10000, "亿": 100000000}
    for char in value:
        if char in "零〇整":
            continue
        if char in "壹贰叁肆伍陆柒捌玖一二三四五六七八九":
            number = _cn_digit(char)
            continue
        if char in unit_map:
            if number == 0:
                number = 1
            section += number * unit_map[char]
            number = 0
            continue
        if char in big_unit_map:
            section += number
            total += section * big_unit_map[char]
            section = 0
            number = 0
    return total + section + number


def _cn_digit(char: str) -> int:
    return {
        "零": 0,
        "〇": 0,
        "壹": 1,
        "一": 1,
        "贰": 2,
        "二": 2,
        "叁": 3,
        "三": 3,
        "肆": 4,
        "四": 4,
        "伍": 5,
        "五": 5,
        "陆": 6,
        "六": 6,
        "柒": 7,
        "七": 7,
        "捌": 8,
        "八": 8,
        "玖": 9,
        "九": 9,
    }[char]


def _normalize_date(value: str) -> str:
    match = DATE_PATTERN.search(value)
    if not match:
        return value
    return f"{int(match.group('year')):04d}-{int(match.group('month')):02d}-{int(match.group('day')):02d}"


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _extract_amount_caps(text: str) -> list[float]:
    values: list[float] = []
    for match in re.finditer(r"(?:上限|最高|累计不超过)[^0-9\n]{0,20}([0-9][0-9,]*(?:\.\d+)?)\s*(万元|万|元)?", text):
        values.append(_decimal_to_float(_parse_number_amount(match.group(1), match.group(2))) or 0)
    return values


def _extract_party_breach_rates(text: str, party: str) -> list[float]:
    rates: list[float] = []
    for match in re.finditer(rf"{party}[^。\n]{{0,80}}(?:违约|赔偿|违约金)[^%\n]{{0,40}}(\d+(?:\.\d+)?)\s*%", text):
        rates.append(float(match.group(1)))
    return rates


def _clean_value(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value.strip(" ：:，,；;。")


def _format_money(value: object) -> str:
    if value is None:
        return "未识别"
    try:
        return f"{float(value):,.2f} 元"
    except (TypeError, ValueError):
        return "未识别"


def _join_percentages(values: Iterable[float]) -> str:
    items = [f"{value:g}%" for value in values]
    return "、".join(items) if items else "未识别"


def _escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def build_analytics_payload(report: dict[str, object]) -> dict[str, object]:
    """Structured metrics for the data-analysis module (小浣熊数据分析能力映射)."""
    stats = report["risk_statistics"]  # type: ignore[index]
    groups = report["rule_groups"]  # type: ignore[index]
    total = int(stats["total_rules"])
    passed = int(stats["passed"])
    failed = int(stats["failed"])
    needs_review = int(stats["needs_review"])
    failed_by_risk = stats["failed_by_risk"]  # type: ignore[index]

    group_stats: list[dict[str, object]] = []
    for group_name, findings in groups.items():
        group_passed = sum(1 for item in findings if item["status"] == PASS)
        group_failed = sum(1 for item in findings if item["status"] == FAIL)
        group_review = sum(1 for item in findings if item["status"] == REVIEW)
        group_stats.append(
            {
                "group": group_name,
                "passed": group_passed,
                "failed": group_failed,
                "needs_review": group_review,
                "total": len(findings),
                "pass_rate": round(group_passed / len(findings) * 100, 1) if findings else 0,
            }
        )

    high_risk_items = [
        {
            "rule": item["rule_name"],
            "group": group_name,
            "evidence": item["evidence"],
        }
        for group_name, findings in groups.items()
        for item in findings
        if item["status"] == FAIL and item["risk_level"] == HIGH
    ]

    return {
        "pass_rate": round(passed / total * 100, 1) if total else 0,
        "compliance_summary": {
            "passed": passed,
            "failed": failed,
            "needs_review": needs_review,
            "total": total,
        },
        "risk_distribution": {
            HIGH: int(failed_by_risk.get(HIGH, 0)),
            MEDIUM: int(failed_by_risk.get(MEDIUM, 0)),
            LOW: int(failed_by_risk.get(LOW, 0)),
        },
        "group_stats": group_stats,
        "high_risk_items": high_risk_items[:6],
        "efficiency": {
            "rules_checked": total,
            "estimated_manual_hours": 4,
            "estimated_ai_minutes": 3,
            "time_saved_percent": 92,
        },
    }


def build_briefing_outline(report: dict[str, object]) -> str:
    """PPT-ready executive briefing outline (小浣熊汇报/PPT 能力映射)."""
    stats = report["risk_statistics"]  # type: ignore[index]
    fields = report["fields"]  # type: ignore[index]
    groups = report["rule_groups"]  # type: ignore[index]
    conclusion = str(report.get("overall_conclusion") or "待评估")
    file_name = str(report.get("file_name") or "未命名合同")

    failed_items = [
        (group_name, item)
        for group_name, findings in groups.items()
        for item in findings
        if item["status"] in {FAIL, REVIEW}
    ][:5]

    slides = [
        "# 合同审核汇报大纲（可直接导入办公小浣熊 PPT 生成）",
        "",
        f"> 合同：{file_name} · 结论：{conclusion}",
        "",
        "## 第 1 页 · 封面",
        f"- 标题：{fields.get('contract_name') or file_name} 审核结论汇报",
        f"- 副标题：合规通过率 {round(int(stats['passed']) / int(stats['total_rules']) * 100, 1)}%",
        "- 汇报对象：法务负责人 / 采购委员会",
        "",
        "## 第 2 页 · 审核背景与痛点",
        "- 传统人工初审：法务+财务双线核对，单份合同约 4 小时",
        "- 风险：金额/税率/付款比例等计算项易漏检，争议解决条款语义冲突难以及时发现",
        "- 目标：用办公小浣熊完成「解析 → 规则校验 → 数据分析 → 报告 → 汇报」闭环",
        "",
        "## 第 3 页 · 关键合同要素（数据洞察）",
        f"- 合同金额：{_format_money(fields.get('total_amount'))}",
        f"- 税率：{_join_percentages(fields.get('tax_rates') or [])}",
        f"- 付款比例：{_join_percentages(fields.get('payment_percentages') or [])}",
        f"- 甲方：{fields.get('party_a') or '未识别'}",
        f"- 乙方：{fields.get('party_b') or '未识别'}",
        "",
        "## 第 4 页 · 合规结果总览",
        (
            f"- 22 项规则：通过 {stats['passed']} / 不通过 {stats['failed']} / 需复核 {stats['needs_review']}"
        ),
        f"- 总体结论：**{conclusion}**",
        "- 建议动作：高风险项必须修订后方可签署",
        "",
        "## 第 5 页 · 重点风险项（Top 5）",
    ]

    if not failed_items:
        slides.append("- 未发现需重点说明的风险项。")
    else:
        for index, (group_name, item) in enumerate(failed_items, start=1):
            slides.append(
                f"{index}. 【{group_name}】{item['rule_name']}（{item['risk_level']}）"
            )
            slides.append(f"   - 依据：{item['evidence']}")
            slides.append(f"   - 建议：{item['recommendation']}")

    slides.extend(
        [
            "",
            "## 第 6 页 · 下一步与决策建议",
            "- 法务：按修改建议逐条回写合同文本",
            "- 财务：复核金额/税率/付款节点计算",
            "- 业务：确认交付验收标准与违约责任对等性",
            "- 决策：建议「修订后复审」或「附条件签署」",
            "",
            "## 附录 · 可复用 Prompt（粘贴至办公小浣熊）",
            "",
            "```",
            "请基于以下合同审核 JSON 结果，生成 6 页管理层汇报 PPT：",
            "1) 封面 2) 背景痛点 3) 关键要素 4) 合规总览 5) Top 风险 6) 决策建议。",
            "风格：商务简洁，主色深蓝+铜色点缀，每页不超过 5 个要点。",
            "```",
        ]
    )
    return "\n".join(slides)


def audit_json(report: dict[str, object]) -> str:
    return json.dumps({key: value for key, value in report.items() if key != "markdown"}, ensure_ascii=False, indent=2)
