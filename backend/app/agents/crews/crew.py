from typing import Any, Callable, Optional

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from app.agents.crews.tools import search_and_validate_books

@CrewBase
class ReaderPathCrew:
    """Crew for generating structured learning courses"""

    agents_config = "agents.yaml"
    tasks_config = "tasks.yaml"

    # Set before calling reader_path_crew() to enable file / step logging.
    _output_log_file: Optional[str] = None
    _step_callback: Optional[Callable[..., Any]] = None

    @agent
    def librarian_assistant(self) -> Agent:
        return Agent(
            config=self.agents_config['librarian_assistant'],
            verbose=True,
            llm="gpt-4o-mini",
        )

    @agent
    def librarian(self) -> Agent:
        return Agent(
            config=self.agents_config['librarian'],
            verbose=True,
            llm="gpt-4o-mini",
            tools=[search_and_validate_books]
        )

    # Reviewer + raw SerperDevTool stay unused. Web search is gated inside
    # search_and_validate_books so the model never sees unvalidated snippets.

    @agent
    def course_creator(self) -> Agent:
        return Agent(
            config=self.agents_config['course_creator'],
            verbose=True,
            llm="gpt-4o-mini",
        )

    @task
    def librarian_task(self) -> Task:
        return Task(config=self.tasks_config['librarian_task'])

    # @task
    # def reviewer_task(self) -> Task:
    #     return Task(config=self.tasks_config['reviewer_task'])

    @task
    def course_creator_task(self) -> Task:
        return Task(config=self.tasks_config['course_creator_task'])

    @crew
    def reader_path_crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            output_log_file=self._output_log_file,
            step_callback=self._step_callback,
            # memory=True,
        )