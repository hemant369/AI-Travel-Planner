from crewai import Agent
from model.llm import llm
from model.settings import CREW_VERBOSE
from tools.search_tool import get_recommendations 

recommendation_agent = Agent(
    role="Destination Travel Expert",

    goal=(
        "Provide destination-specific travel insights using reliable web information."
    ),

    backstory=(
        "You are a travel expert who researches destinations before giving advice. "
        "Always use the Search Tool before answering."
    ),
    tools=[get_recommendations],
    llm=llm,
    verbose=CREW_VERBOSE,
)
