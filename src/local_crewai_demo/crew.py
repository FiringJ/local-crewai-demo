from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

@CrewBase
class LocalCrewaiDemo():
    """Contract review crew."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def contract_auditor(self) -> Agent:
        return Agent(
            config=self.agents_config['contract_auditor'], # type: ignore[index]
            verbose=True
        )

    @agent
    def briefing_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['briefing_specialist'], # type: ignore[index]
            verbose=True
        )

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
