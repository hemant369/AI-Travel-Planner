from crewai import Task
from agents.planner_agent import planner_agent
from model.schemas import TripDetails

planner_task = Task(
    description="""
    Analyze the following travel request: {user_request}
    Extract all important travel information into a structured format. 
    Correctly identify the source, destination, travel start date, travel duration, travel end date, budget, and number of travelers. 
    Ensure that the extracted information is accurate and complete.

    Don't left out any important details. 
    If any information is missing or unclear, make reasonable assumptions based on the context provided in the request.
    """,
    expected_output="""
    A structured summary containing:
    - Source
    - Destination
    - Travel Start Date
    - Travel Duration
    - Travel End Date
    - Budget
    - Number of travelers
    """,
    agent=planner_agent,
    output_pydantic=TripDetails,
)
