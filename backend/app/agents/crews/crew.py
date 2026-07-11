from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

from .tools import ask_human

@CrewBase
class ReaderPathCrew:
    """Crew for generating structured learning courses"""

    agents_config = "agents.yaml"
    tasks_config = "tasks.yaml"

    @agent
    def librarian_assistant(self) -> Agent:
        return Agent(
            config=self.agents_config['librarian_assistant'],
            verbose=True,
            # tools=[ask_human]
        )

    @agent
    def librarian(self) -> Agent:
        return Agent(
            config=self.agents_config['librarian'],
            verbose=True,
            tools=[SerperDevTool()]
        )

    @agent
    def reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config['reviewer'],
            verbose=True,
            tools=[SerperDevTool()]
        )

    @agent
    def course_creator(self) -> Agent:
        return Agent(
            config=self.agents_config['course_creator'],
            verbose=True
        )

    @task
    def librarian_task(self) -> Task:
        return Task(config=self.tasks_config['librarian_task'])

    @task
    def reviewer_task(self) -> Task:
        return Task(config=self.tasks_config['reviewer_task'])

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
            memory=True,
        )