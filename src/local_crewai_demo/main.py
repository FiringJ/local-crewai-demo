#!/usr/bin/env python
import sys
import warnings

from datetime import datetime
from pathlib import Path

from local_crewai_demo.contract_review import (
    audit_contract_text,
    audit_json,
    extract_text_from_file,
    extract_text_with_profile,
    rule_reference_json,
)
from local_crewai_demo.crew import LocalCrewaiDemo
from local_crewai_demo.gui import _load_knowledge_context, _load_rules_definition, _extract_token_usage
from local_crewai_demo.pdf_markdown import build_token_savings_profile, token_savings_markdown

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CONTRACT = PROJECT_ROOT / "knowledge" / "sample_contract.txt"


def _build_inputs(contract_path: Path) -> dict[str, str]:
    contract_text = extract_text_from_file(contract_path)
    audit = audit_contract_text(contract_text, contract_path.name)
    return {
        "file_name": contract_path.name,
        "contract_text": contract_text[:30000],
        "audit_evidence_json": audit_json(audit),
        "rule_reference_json": rule_reference_json(audit),
        "knowledge_context": _load_knowledge_context(),
        "current_date": datetime.now().strftime("%Y-%m-%d"),
    }


def _print_token_report(result: object, contract_path: Path) -> None:
    """命令行模式下打印本次审核的实际 token 消耗与架构节省对比。"""
    usage = _extract_token_usage(result)
    if usage:
        print("\n" + "=" * 60)
        print("本次审核 Token 消耗（CrewAI 实测）")
        print("=" * 60)
        print(f"  prompt_tokens:      {usage.get('prompt_tokens', 0)}")
        print(f"  completion_tokens:  {usage.get('completion_tokens', 0)}")
        print(f"  total_tokens:       {usage.get('total_tokens', 0)}")
        print(f"  successful_requests:{usage.get('successful_requests', 0)}")
        print(f"  估算成本(元):        {usage.get('estimated_cost_cny', 0)}")

    # 架构级节省对比
    try:
        md_text, raw_text, _ = extract_text_with_profile(
            contract_path,
            knowledge_context=_load_knowledge_context(),
            rule_reference=rule_reference_json(
                audit_contract_text(extract_text_from_file(contract_path), contract_path.name)
            ),
            rules_definition_text=_load_rules_definition(),
        )
        profile = build_token_savings_profile(
            raw_text=raw_text,
            markdown_text=md_text,
            rule_reference_json=rule_reference_json(
                audit_contract_text(md_text, contract_path.name)
            ),
            knowledge_context=_load_knowledge_context(),
            rules_definition_text=_load_rules_definition(),
        )
        print("\n" + token_savings_markdown(profile))
    except Exception:
        pass


def run():
    """
    Run the contract audit crew.
    """
    contract_path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else SAMPLE_CONTRACT
    inputs = _build_inputs(contract_path)

    try:
        result = LocalCrewaiDemo().crew().kickoff(inputs=inputs)
        _print_token_report(result, contract_path)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = _build_inputs(SAMPLE_CONTRACT)
    try:
        LocalCrewaiDemo().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        LocalCrewaiDemo().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = _build_inputs(SAMPLE_CONTRACT)

    try:
        LocalCrewaiDemo().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    contract_text = str(trigger_payload.get("contract_text") or "")
    file_name = str(trigger_payload.get("file_name") or "trigger_contract.txt")
    if not contract_text:
        raise Exception("Trigger payload must include contract_text.")

    audit = audit_contract_text(contract_text, file_name)
    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "file_name": file_name,
        "contract_text": contract_text[:30000],
        "audit_evidence_json": audit_json(audit),
        "rule_reference_json": rule_reference_json(audit),
        "knowledge_context": _load_knowledge_context(),
        "current_date": datetime.now().strftime("%Y-%m-%d"),
    }

    try:
        result = LocalCrewaiDemo().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
