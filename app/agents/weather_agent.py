from crewai import Agent
from model.llm import llm
from model.settings import CREW_VERBOSE
from tools.weather_tool import get_weather

weather_agent = Agent(
    role="Weather Agent",
    goal="Provide accurate, real-time weather information for the travel destination "
         "and explain how the weather may affect the trip.",
    backstory="You are an experienced travel weather specialist. "
              "You always use the Weather Tool to obtain the latest weather information "
              "before making recommendations. "
              "You never guess or invent weather conditions.",
    llm=llm,
    tools=[get_weather],
    max_iter=5,
    verbose=CREW_VERBOSE,
)
