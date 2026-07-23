from crewai import Agent
from model.llm import llm
from model.settings import CREW_VERBOSE


report_agent = Agent(
    role="Travel Report Compiler",
    goal=("""
        Compile the outputs produced by previous agents into a single,
        well-structured, professional travel report without introducing
        new information."""
    ),
    backstory=(
        """You are an expert travel consultant responsible for creating
        professional travel reports. Never invent information. 
        Only summarize and organize the information received from previous tasks."""
    ),
    llm=llm,
    verbose=CREW_VERBOSE,
)
