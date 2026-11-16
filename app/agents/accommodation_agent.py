from crewai import Agent
from model.llm import llm
from model.settings import CREW_VERBOSE
from tools.accommodation_tool import search_hotels

accommodation_agent = Agent(
    role="Accommodation Specialist",
    goal="Recommend factual hotels suitable for the trip dates, party size, and budget.",
    backstory=("You are an accommodation specialist. Always call the Accommodation Tool. "
               "Never invent hotel names, availability, prices, or ratings."),
    llm=llm,
    tools=[search_hotels],
    max_iter=5,
    verbose=CREW_VERBOSE,
)
