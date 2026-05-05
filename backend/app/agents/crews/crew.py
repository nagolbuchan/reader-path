import os
from crewai import Crew, Process
from crewai_tools import SerperDevTool
from crewai import Agent, Task  

from .tools import ask_human   

search_tool = SerperDevTool()

def create_crew(topic: str):
    agents = Agent.from_yaml("crew/agents.yaml")
    tasks = Task.from_yaml("crew/tasks.yaml")

    #Tool assignment -- this should be accomplished in the yaml config
    # agents["librarian_assistant"].tools = [ask_human]

    crew = Crew(
        agents=list(agents.values()),
        tasks=[tasks["librarian_task"], tasks["reviewer_task"], tasks["course_creator_task"]],
        process=Process.sequential,
        verbose=True,
        memory=True,        
    )

    return crew


# For testing
if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "Medieval Literature"
    
    crew = create_crew(topic)
    result = crew.kickoff(inputs={"topic": topic})
    print(result)