from crewai import Agent
from model.llm import llm
from model.settings import CREW_VERBOSE
from tools.search_tool import get_attractions_and_food, get_destination_guide

recommendation_agent = Agent(
    role="Destination Travel Expert",
    goal=(
        "Provide destination-specific travel insights using reliable web information."
    ),
    backstory=(
        "You are a travel expert who researches destinations before giving advice. "
        "Always call the provided research tools before answering and preserve source URLs."
    ),
    tools=[get_attractions_and_food, get_destination_guide],
    llm=llm,
    max_iter=5,
    verbose=CREW_VERBOSE,
)
