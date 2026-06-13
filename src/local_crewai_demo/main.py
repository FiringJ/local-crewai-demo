#!/usr/bin/env python
import sys
import warnings

from datetime import datetime
from pathlib import Path

from local_crewai_demo.contract_review import audit_contract_text, audit_json, extract_text_from_file
from local_crewai_demo.crew import LocalCrewaiDemo

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
        "current_date": datetime.now().strftime("%Y-%m-%d"),
    }


def run():
    """
    Run the contract audit crew.
    """
    contract_path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else SAMPLE_CONTRACT
    inputs = _build_inputs(contract_path)

    try:
        LocalCrewaiDemo().crew().kickoff(inputs=inputs)
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
        "current_date": datetime.now().strftime("%Y-%m-%d"),
    }

    try:
        result = LocalCrewaiDemo().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
