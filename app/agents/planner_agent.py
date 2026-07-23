from crewai import Agent
from model.llm import llm
from model.settings import CREW_VERBOSE


planner_agent = Agent(
    role = "Travel Planner",
    goal = "Understand the user's travel request and convert it into structured travel information.",
    backstory = "You are an experienced travel planner."
        "Your job is to carefully analyze user requests "
        "and extract all important travel details.",
    llm = llm,
    verbose=CREW_VERBOSE,
)
