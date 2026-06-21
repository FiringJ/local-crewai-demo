import os

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


def _agent_llm() -> LLM | None:
    """Optional SenseNova native web search for due-diligence aligned with the workflow."""
    if os.environ.get("SENSENOVA_SEARCH_ENABLE", "").lower() not in {"1", "true", "yes"}:
        return None
    model = os.environ.get("MODEL", "openai/SenseChat-5")
    if model.startswith("openai/"):
        model = f"hosted_vllm/{model.split('/', 1)[1]}"
    return LLM(
        model=model,
        base_url=os.environ.get("BASE_URL") or os.environ.get("OPENAI_BASE_URL"),
        api_key=os.environ.get("SENSENOVA_API_KEY") or os.environ.get("OPENAI_API_KEY"),
        additional_params={"extra_body": {"search_enable": True}},
    )


@CrewBase
class LocalCrewaiDemo():
    """Contract review crew."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def contract_auditor(self) -> Agent:
        llm = _agent_llm()
        kwargs: dict = {
            "config": self.agents_config['contract_auditor'],  # type: ignore[index]
            "verbose": True,
        }
        if llm is not None:
            kwargs["llm"] = llm
        return Agent(**kwargs)

    @agent
    def briefing_specialist(self) -> Agent:
        llm = _agent_llm()
        kwargs: dict = {
            "config": self.agents_config['briefing_specialist'],  # type: ignore[index]
            "verbose": True,
        }
        if llm is not None:
            kwargs["llm"] = llm
        return Agent(**kwargs)

    @task
    def contract_audit_report_task(self) -> Task:
        return Task(
            config=self.tasks_config['contract_audit_report_task'], # type: ignore[index]
            output_file='report.md'
        )

    @task
    def executive_briefing_task(self) -> Task:
        return Task(
            config=self.tasks_config['executive_briefing_task'], # type: ignore[index]
            output_file='briefing.md'
        )

    @crew
    def crew(self) -> Crew:
        """Create the contract review crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
