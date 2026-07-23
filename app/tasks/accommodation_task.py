from crewai import Task
from agents.accommodation_agent import accommodation_agent
from model.schemas import AccommodationResult
from tasks.planner_task import planner_task

accommodation_task = Task(
    description="""
    Call the Accommodation Tool with the planner's destination, start date,
    end date, travelers, and total trip budget. Recommend only returned hotels.
    Do not claim availability and never invent missing prices. Return data matching
    AccommodationResult exactly; preserve tool errors.
    """,
    expected_output="An AccommodationResult object containing up to five factual hotel options.",
    context=[planner_task],
    agent=accommodation_agent,
    async_execution=True,
    output_pydantic=AccommodationResult,
)
