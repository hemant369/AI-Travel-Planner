from crewai import Agent

from model.llm import llm
from model.settings import CREW_VERBOSE
from tools.map_tool import get_route

transport_agent = Agent(
    role="Travel Logistics Specialist",
    goal=(
        "Provide accurate route information between the source "
        "and destination using real map data."
    ),
    backstory=(
        "You are a travel logistics expert. "
        "Always use the Maps Tool before answering. "
        "Never estimate distance or travel duration."
    ),
    llm=llm,
    tools=[get_route],
    max_iter=5,
    verbose=CREW_VERBOSE,
)
