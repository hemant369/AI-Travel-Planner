from crewai import Task

from agents.planner_agent import planner_agent
from model.schemas import TripDetails


def create_planner_task() -> Task:
    """Create a fresh planner Task for free-text trip requests."""
    return Task(
        description="""
        Analyze the following travel request: {user_request}
        Extract all important travel information into TripDetails:
        source, destination, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD),
        duration_days, budget_inr, and travelers.
        """,
        expected_output="A structured TripDetails object.",
        agent=planner_agent,
        output_pydantic=TripDetails,
    )
