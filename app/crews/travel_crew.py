from crewai import Crew, Process
from agents.planner_agent import planner_agent
from agents.weather_agent import weather_agent
from agents.transport_agent import transport_agent
from agents.accommodation_agent import accommodation_agent
from agents.recommendation_agent import recommendation_agent
from agents.report_agent import report_agent
from tasks.planner_task import planner_task
from tasks.weather_task import weather_task
from tasks.transport_task import transport_task
from tasks.accommodation_task import accommodation_task
from tasks.recommendation_task import recommendation_task
from tasks.report_task import report_task
from model.settings import CREW_VERBOSE

travel_crew = Crew(
    name = "Travel Crew",
    agents = [planner_agent, weather_agent, transport_agent, accommodation_agent, recommendation_agent, report_agent ],
    tasks = [planner_task, weather_task, transport_task, accommodation_task, recommendation_task, report_task],
    process = Process.sequential,
    verbose=CREW_VERBOSE,
)
