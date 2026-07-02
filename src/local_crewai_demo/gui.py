from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from email.parser import BytesParser
from email.policy import default
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import tempfile
import traceback
import webbrowser

from dotenv import load_dotenv

from local_crewai_demo.contract_review import (
    ALL_RULES,
    audit_contract_text,
    audit_json,
    build_analytics_payload,
    build_briefing_outline,
    extract_text_from_file,
    extract_text_with_profile,
    rule_reference_json,
)
from local_crewai_demo.crew import LocalCrewaiDemo
from local_crewai_demo.pdf_markdown import (
    TokenSavingsProfile,
    build_token_savings_profile,
    token_savings_markdown,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_WEB_DIR = Path(__file__).resolve().parent / "web"
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
WEB_DIR = FRONTEND_DIST_DIR if FRONTEND_DIST_DIR.exists() else LEGACY_WEB_DIR

PROVIDERS = {
    "sensenova": {
        "label": "办公小浣熊 / SenseNova",
        "model": "openai/SenseChat-5",
        "base_url": "https://api.sensenova.cn/compatible-mode/v2",
        "api_key_env": "SENSENOVA_API_KEY",
        "api_key_placeholder": "商汤 SenseNova API Key",
    },
    "lmstudio": {
        "label": "LM Studio（本地）",
        "model": "hosted_vllm/gemma-4-e4b-it",
        "base_url": "http://127.0.0.1:1234/v1",
        "api_key_env": "VLLM_API_KEY",
        "api_key_placeholder": "lm-studio",
    },
    "openai": {
        "label": "OpenAI",
        "model": "openai/gpt-4o-mini",
        "base_url": "",
        "api_key_env": "OPENAI_API_KEY",
        "api_key_placeholder": "",
    },
    "anthropic": {
        "label": "Anthropic",
        "model": "anthropic/claude-sonnet-4-5",
        "base_url": "",
        "api_key_env": "ANTHROPIC_API_KEY",
        "api_key_placeholder": "",
    },
    "gemini": {
        "label": "Gemini",
        "model": "gemini/gemini-2.5-flash",
        "base_url": "",
        "api_key_env": "GEMINI_API_KEY",
        "api_key_placeholder": "",
    },
    "deepseek": {
        "label": "DeepSeek",
        "model": "deepseek/deepseek-chat",
        "base_url": "",
        "api_key_env": "DEEPSEEK_API_KEY",
        "api_key_placeholder": "",
    },
    "openrouter": {
        "label": "OpenRouter",
        "model": "openrouter/openai/gpt-4o-mini",
        "base_url": "",
        "api_key_env": "OPENROUTER_API_KEY",
        "api_key_placeholder": "",
    },
    "custom": {
        "label": "Custom OpenAI Compatible",
        "model": "hosted_vllm/model-name",
        "base_url": "http://127.0.0.1:8000/v1",
        "api_key_env": "VLLM_API_KEY",
        "api_key_placeholder": "dummy",
    },
}

REVIEW_MODES = {
    "rules_agent": "智能审核（规则参考 + 大模型决策，推荐）",
    "rules_only": "仅规则参考层（离线预览，无大模型）",
}

COMPETITION = {
    "event": "商汤小浣熊 OPC 高手创造赛",
    "scene": "企业合同审查持续运营工作流",
    "tagline": "定时任务 + 办公小浣熊能力矩阵，跑通法务审查流水线",
    "pain_point": "传统审查来一份审一份，单份约 4 小时；主体风险与法规变化无法持续沉淀",
    "value_proposition": "每日 09:00 自动拉合同、联网尽调、知识库闭环；周五 17:00 周报 PPT；单份约 3 分钟",
    "capabilities": [
        {
            "id": "schedule",
            "module": "定时任务",
            "label": "每日拉合同 / 每周法规与周报",
            "icon": "schedule",
        },
        {
            "id": "agent",
            "module": "Agent",
            "label": "单份合同多步编排",
            "icon": "agent",
        },
        {
            "id": "doc",
            "module": "文档处理",
            "label": "合同解析与字段抽取",
            "icon": "doc",
        },
        {
            "id": "web",
            "module": "联网检索",
            "label": "乙方主体尽调（工商/涉诉）",
            "icon": "web",
        },
        {
            "id": "kb",
            "module": "知识库",
            "label": "红线 @复核 + 案例沉淀",
            "icon": "kb",
        },
        {
            "id": "da",
            "module": "数据分析",
            "label": "合规率、风险分布、周报趋势",
            "icon": "da",
        },
        {
            "id": "copy",
            "module": "文案",
            "label": "SenseChat 审核报告",
            "icon": "copy",
        },
        {
            "id": "ppt",
            "module": "汇报/PPT",
            "label": "单份汇报 + 周报 PPT 大纲",
            "icon": "ppt",
        },
    ],
    "submission_doc": "docs/OPC_SUBMISSION.md",
    "screenshot_doc": "docs/SCREENSHOT_CHECKLIST.md",
    "weekly_ppt_doc": "docs/WEEKLY_BRIEFING_PPT.md",
    "prompts_doc": "prompts/xiaohuanxiong_core_prompts.md",
    "demo_role": "工作流中的审核节点：规则参考层 + 大模型终局报告",
}

WORKFLOW_TEMPLATE = [
    {"id": "schedule", "module": "定时任务", "label": "工作日 09:00 拉取待审合同（网页端）"},
    {"id": "agent", "module": "Agent", "label": "编排解析→尽调→复核→报告"},
    {"id": "doc", "module": "文档处理", "label": "解析合同并抽取关键字段"},
    {"id": "web", "module": "联网检索", "label": "乙方工商/涉诉/负面尽调"},
    {"id": "kb", "module": "知识库", "label": "@知识库 红线复核 + 案例沉淀"},
    {"id": "rules", "module": "证据层", "label": "规则参考层（维度初筛，供大模型复核）"},
    {"id": "da", "module": "数据分析", "label": "合规率与风险分布洞察"},
    {"id": "copy", "module": "文案", "label": "生成 Markdown 审核报告"},
    {"id": "ppt", "module": "汇报", "label": "单份大纲 / 周五周报 PPT"},
]


def _read_report(path: Path, previous_mtime: float) -> str:
    if not path.exists() or path.stat().st_mtime <= previous_mtime:
        return ""
    return path.read_text(encoding="utf-8")


def _knowledge_sources() -> list[dict[str, str]]:
    knowledge_dir = PROJECT_ROOT / "knowledge"
    sources: list[dict[str, str]] = []
    for path in sorted(knowledge_dir.glob("*")):
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        sources.append(
            {
                "name": path.name,
                "path": str(path.relative_to(PROJECT_ROOT)),
                "size": str(path.stat().st_size),
            }
        )
    return sources


def _load_knowledge_context(max_chars: int = 12000) -> str:
    chunks: list[str] = []
    for item in _knowledge_sources():
        path = PROJECT_ROOT / item["path"]
        if not path.exists():
            continue
        chunks.append(f"### {item['name']}\n{path.read_text(encoding='utf-8', errors='replace')}")
    return "\n\n".join(chunks)[:max_chars]


def _load_rules_definition() -> str:
    """加载 26 条规则定义全文，用于量化纯 LLM 场景需要把规则作为输入的 token 成本。"""
    rules_path = PROJECT_ROOT / "knowledge" / "contract_audit_rules.md"
    if rules_path.exists():
        return rules_path.read_text(encoding="utf-8", errors="replace")
    return ""


# SenseChat-5 / GPT-4o 量级的参考单价（元 / 1K tokens），用于成本估算展示。
_TOKEN_PRICE_PER_K = {"input": 0.035, "output": 0.105}


def _extract_token_usage(result: object) -> dict[str, object]:
    """从 CrewOutput.token_usage（UsageMetrics）提取实际 token 消耗。"""
    usage = getattr(result, "token_usage", None)
    if usage is None:
        return {}
    fields = (
        "total_tokens",
        "prompt_tokens",
        "cached_prompt_tokens",
        "completion_tokens",
        "reasoning_tokens",
        "cache_creation_tokens",
        "successful_requests",
    )
    out: dict[str, object] = {}
    for f in fields:
        out[f] = int(getattr(usage, f, 0) or 0)
    prompt = int(out.get("prompt_tokens", 0) or 0)
    completion = int(out.get("completion_tokens", 0) or 0)
    out["estimated_cost_cny"] = round(
        prompt / 1000 * _TOKEN_PRICE_PER_K["input"] + completion / 1000 * _TOKEN_PRICE_PER_K["output"],
        4,
    )
    return out


def _build_token_savings(
    contract_text: str,
    raw_text: str,
    audit: dict[str, object],
    knowledge_context: str,
    rules_definition: str,
) -> tuple[TokenSavingsProfile, str]:
    """构建 token 节省 profile 和可展示的 Markdown 摘要。"""
    rule_ref = rule_reference_json(audit)
    profile = build_token_savings_profile(
        raw_text=raw_text or contract_text,
        markdown_text=contract_text,
        rule_reference_json=rule_ref,
        knowledge_context=knowledge_context,
        rules_definition_text=rules_definition,
    )
    return profile, token_savings_markdown(profile)


def _workflow_steps(agent_used: bool) -> list[dict[str, str]]:
    steps: list[dict[str, str]] = []
    for template in WORKFLOW_TEMPLATE:
        step_id = template["id"]
        provider = "本地引擎"
        if step_id in {"schedule", "web"}:
            provider = "办公小浣熊网页端"
        elif step_id == "agent" and agent_used:
            provider = "办公小浣熊 Agent"
        elif step_id in {"kb", "copy", "ppt"} and agent_used:
            provider = "办公小浣熊 / SenseChat-5"
        elif step_id == "kb" and not agent_used:
            provider = "本地知识库"
        elif step_id == "rules":
            provider = "本地规则引擎（证据层）"
        steps.append({**template, "provider": provider, "status": "completed"})
    return steps


def _rules_config() -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for rule in ALL_RULES:
        groups.setdefault(rule.group, []).append(
            {
                "code": rule.code,
                "name": rule.name,
                "risk": rule.risk,
                "contract_types": rule.contract_types,
                "legal_basis": rule.legal_basis,
                "logic": rule.logic,
            }
        )
    return groups


def _configure_llm_environment(provider_key: str, payload: dict[str, str]) -> tuple[str, str]:
    provider = PROVIDERS.get(provider_key, PROVIDERS["sensenova"])
    model = str(payload.get("model") or provider["model"]).strip()
    base_url = str(payload.get("baseUrl") or provider["base_url"]).strip()
    api_key = str(payload.get("apiKey") or "").strip()

    if provider_key == "sensenova" and not model.startswith("openai/"):
        model = f"openai/{model}"

    os.environ["MODEL"] = model
    os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
    os.environ["CREWAI_TRACING_ENABLED"] = "false"
    os.environ.pop("OPENAI_BASE_URL", None)
    os.environ.pop("OPENAI_API_BASE", None)
    os.environ.pop("BASE_URL", None)
    os.environ.pop("API_BASE", None)

    if base_url:
        os.environ["BASE_URL"] = base_url
        os.environ["API_BASE"] = base_url
        os.environ["OPENAI_BASE_URL"] = base_url

    api_key_env = str(provider["api_key_env"])
    resolved_key = api_key or os.environ.get(api_key_env, "")
    if resolved_key:
        os.environ[api_key_env] = resolved_key
    if provider_key in {"sensenova", "custom", "lmstudio", "openai"} and resolved_key:
        os.environ["OPENAI_API_KEY"] = resolved_key
    elif provider_key in {"lmstudio", "custom"}:
        os.environ.setdefault(api_key_env, str(provider["api_key_placeholder"]) or "dummy")

    return model, base_url


def _run_contract_review(payload: dict[str, str], upload: tuple[str, bytes] | None) -> dict[str, object]:
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    mode = payload.get("reviewMode") or "rules_agent"
    previous_cwd = Path.cwd()
    previous_env = os.environ.copy()
    output_path = Path(tempfile.gettempdir()) / (
        f"contract-audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            contract_text = payload.get("contractText", "").strip()
            file_name = payload.get("fileName", "pasted_contract.txt").strip() or "pasted_contract.txt"
            raw_text = contract_text  # 粘贴文本时 raw == md

            if upload:
                uploaded_name, content = upload
                file_name = Path(uploaded_name).name or "uploaded_contract"
                temp_path = Path(temp_dir) / file_name
                temp_path.write_bytes(content)
                # PDF 走结构化 Markdown，同时拿到 raw 纯文本用于 token 对比
                contract_text, raw_text, _ = extract_text_with_profile(temp_path)

            if not contract_text:
                return {
                    "ok": False,
                    "error": "请上传合同文件，或粘贴合同正文。",
                    "traceback": "",
                }

            audit = audit_contract_text(contract_text, file_name)
            fallback_report = str(audit["markdown"])
            analytics = build_analytics_payload(audit)
            briefing = build_briefing_outline(audit)
            output_path.write_text(fallback_report, encoding="utf-8")

            # token 节省量化（规则引擎 vs 纯 LLM 架构对比）
            rules_definition = _load_rules_definition()
            knowledge_context = _load_knowledge_context()
            token_profile, token_savings_md = _build_token_savings(
                contract_text, raw_text, audit, knowledge_context, rules_definition
            )

            if mode == "rules_only":
                return {
                    "ok": True,
                    "mode": mode,
                    "model": "",
                    "fileName": file_name,
                    "report": fallback_report,
                    "auditJson": audit_json(audit),
                    "ruleReferenceJson": rule_reference_json(audit),
                    "analytics": analytics,
                    "briefing": briefing,
                    "tokenSavings": token_savings_md,
                    "tokenSavingsProfile": {
                        "savingsTokens": token_profile.savings_tokens,
                        "savingsPercent": token_profile.savings_percent,
                        "hybridTotalTokens": token_profile.scenarios[1].total_tokens,
                        "pureLlmTotalTokens": token_profile.scenarios[0].total_tokens,
                    },
                    "workflow": _workflow_steps(agent_used=False),
                    "knowledgeSources": _knowledge_sources(),
                    "reportPath": str(output_path),
                    "logs": "规则参考层 + 数据分析 + 汇报大纲已完成（无大模型终局报告；请使用「智能审核」模式获取完整结论）。",
                }

            os.chdir(PROJECT_ROOT)
            provider_key = str(payload.get("provider") or "sensenova")
            model, _base_url = _configure_llm_environment(provider_key, payload)

            report_file = PROJECT_ROOT / "report.md"
            briefing_file = PROJECT_ROOT / "briefing.md"
            previous_report_mtime = report_file.stat().st_mtime if report_file.exists() else 0
            previous_briefing_mtime = briefing_file.stat().st_mtime if briefing_file.exists() else 0
            inputs = {
                "file_name": file_name,
                "contract_text": contract_text[:30000],
                "audit_evidence_json": audit_json(audit),
                "rule_reference_json": rule_reference_json(audit),
                "knowledge_context": knowledge_context,
                "current_date": datetime.now().strftime("%Y-%m-%d"),
            }

            buffer = io.StringIO()
            with redirect_stdout(buffer), redirect_stderr(buffer):
                result = LocalCrewaiDemo().crew().kickoff(inputs=inputs)

            # 捕获 CrewAI 实际 token 消耗（导师反馈：跑一次任务消耗多少 token）
            token_usage = _extract_token_usage(result)

            report = _read_report(report_file, previous_report_mtime) or str(result)
            briefing = (
                _read_report(briefing_file, previous_briefing_mtime) or build_briefing_outline(audit)
            )
            output_path.write_text(report, encoding="utf-8")
            return {
                "ok": True,
                "mode": mode,
                "model": model,
                "fileName": file_name,
                "report": report,
                "auditJson": audit_json(audit),
                "ruleReferenceJson": rule_reference_json(audit),
                "analytics": analytics,
                "briefing": briefing,
                "tokenUsage": token_usage,
                "tokenSavings": token_savings_md,
                "tokenSavingsProfile": {
                    "savingsTokens": token_profile.savings_tokens,
                    "savingsPercent": token_profile.savings_percent,
                    "hybridTotalTokens": token_profile.scenarios[1].total_tokens,
                    "pureLlmTotalTokens": token_profile.scenarios[0].total_tokens,
                },
                "workflow": _workflow_steps(agent_used=True),
                "knowledgeSources": _knowledge_sources(),
                "reportPath": str(output_path),
                "logs": buffer.getvalue(),
            }
    except Exception:
        fallback = locals().get("fallback_report", "")
        audit_obj = locals().get("audit")
        token_profile_obj = locals().get("token_profile")
        return {
            "ok": bool(fallback),
            "mode": "rules_fallback",
            "model": payload.get("model", ""),
            "fileName": locals().get("file_name", ""),
            "report": fallback,
            "auditJson": audit_json(audit_obj) if audit_obj else "",
            "ruleReferenceJson": rule_reference_json(audit_obj) if audit_obj else "",
            "analytics": build_analytics_payload(audit_obj) if audit_obj else {},
            "briefing": build_briefing_outline(audit_obj) if audit_obj else "",
            "tokenSavings": locals().get("token_savings_md", ""),
            "tokenSavingsProfile": {
                "savingsTokens": token_profile_obj.savings_tokens,
                "savingsPercent": token_profile_obj.savings_percent,
                "hybridTotalTokens": token_profile_obj.scenarios[1].total_tokens,
                "pureLlmTotalTokens": token_profile_obj.scenarios[0].total_tokens,
            } if token_profile_obj else {},
            "workflow": _workflow_steps(agent_used=False),
            "knowledgeSources": _knowledge_sources(),
            "reportPath": str(output_path) if fallback else "",
            "logs": traceback.format_exc(limit=8),
            "error": "" if fallback else "合同审核失败。",
        }
    finally:
        os.chdir(previous_cwd)
        os.environ.clear()
        os.environ.update(previous_env)


def _parse_multipart(content_type: str, body: bytes) -> tuple[dict[str, str], tuple[str, bytes] | None]:
    message = BytesParser(policy=default).parsebytes(
        b"Content-Type: "
        + content_type.encode("utf-8")
        + b"\r\nMIME-Version: 1.0\r\n\r\n"
        + body
    )
    fields: dict[str, str] = {}
    upload: tuple[str, bytes] | None = None
    if not message.is_multipart():
        return fields, upload
    for part in message.iter_parts():
        if part.get_content_disposition() != "form-data":
            continue
        params = dict(part.get_params(header="content-disposition", unquote=True) or [])
        name = str(params.get("name") or "")
        filename = params.get("filename")
        raw = part.get_payload(decode=True) or b""
        if filename and name == "contract":
            upload = (str(filename), raw)
        elif name:
            fields[name] = raw.decode(part.get_content_charset() or "utf-8", errors="replace")
    return fields, upload


class GuiHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self) -> None:
        if self.path == "/api/config":
            self._send_json(
                {
                    "providers": PROVIDERS,
                    "reviewModes": REVIEW_MODES,
                    "rules": _rules_config(),
                    "competition": COMPETITION,
                    "knowledgeSources": _knowledge_sources(),
                    "defaults": {
                        "provider": "sensenova",
                        "reviewMode": "rules_agent",
                    },
                }
            )
            return

        clean_path = self.path.split("?", 1)[0]
        if clean_path.startswith("/api/"):
            self.send_error(404)
            return

        relative = clean_path.lstrip("/")
        candidate = WEB_DIR / relative
        if relative and candidate.is_file():
            super().do_GET()
            return

        if WEB_DIR.name == "dist":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/feishu-loop":
            self._handle_feishu_loop()
            return
        if self.path != "/api/review":
            self.send_error(404)
            return

        length = int(self.headers.get("content-length", "0"))
        body = self.rfile.read(length)
        content_type = self.headers.get("content-type", "")

        if content_type.startswith("multipart/form-data"):
            payload, upload = _parse_multipart(content_type, body)
        else:
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
                upload = None
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return

        self._send_json(_run_contract_review(payload, upload))

    def _handle_feishu_loop(self) -> None:
        """HTTP 触发飞书合同审核闭环（webhook fallback）。"""
        length = int(self.headers.get("content-length", "0"))
        body = self.rfile.read(length)
        dry_run = False
        if body:
            try:
                payload = json.loads(body.decode("utf-8"))
                dry_run = bool(payload.get("dryRun"))
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
                return
        try:
            import sys

            scripts_dir = PROJECT_ROOT / "scripts"
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))
            import feishu_contract_loop as loop  # type: ignore[import-untyped]

            result = loop.run_once(dry_run=dry_run)
            self._send_json({"ok": True, **result})
        except Exception as exc:
            self._send_json(
                {
                    "ok": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )

    def _send_json(self, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the contract audit browser GUI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    port = int(os.environ.get("PORT", str(args.port)))
    host = os.environ.get("HOST", "0.0.0.0" if os.environ.get("PORT") else args.host)
    no_open = args.no_open or bool(os.environ.get("PORT") or os.environ.get("RENDER"))

    if WEB_DIR == LEGACY_WEB_DIR:
        print(
            "Frontend build not found. Run `cd frontend && npm install && npm run build` "
            "to use the React + shadcn UI. Falling back to legacy static files."
        )

    server = ThreadingHTTPServer((host, port), GuiHandler)
    local_url = f"http://{host}:{port}"
    public_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if public_url and not public_url.startswith("http"):
        public_url = f"https://{public_url}"
    if not args.no_open and not no_open:
        webbrowser.open(local_url)
    print(f"Contract audit GUI is running at {local_url}")
    if public_url:
        print(f"Public URL: {public_url}")
    print(f"Serving UI from {WEB_DIR}")
    server.serve_forever()


if __name__ == "__main__":
    main()
