from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import SerperDevTool,PDFSearchTool
from dotenv import load_dotenv
from pathlib import Path
from tools.custom_tool import SearchTool
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

load_dotenv()
file_path = Path.joinpath(Path.cwd(),"knowledge","dspy.pdf")
llm = LLM(
    model="ollama/qwen2.5:7b",
    base_url="http://localhost:11434",
    temperature=0.3,          # lower = more reliable tool-call formatting
)
@CrewBase
class AgenticRag():
    """AgenticRag crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    def __init__(self,pdf_tool):
        self.searchTool = pdf_tool
    @agent
    def retriever_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['retriever_agent'],
            verbose=True,
            llm=llm,
            tools=[self.searchTool, SerperDevTool()]
        )

    @agent
    def response_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['response_agent'],
            llm=llm,
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config['retrieval_task'])

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['response_task'],
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
    

if __name__ == "__main__":
    ag = AgenticRag()
    ag.crew().kickoff(inputs={"query": "What is a dspy ?"})