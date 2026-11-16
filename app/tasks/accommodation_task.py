import json
from crewai import Agent, Task
from model.schemas import AccommodationAdvice


def create_accommodation_task(agent: Agent, hotel_data: dict) -> Task:
    """Create a fresh accommodation-selection Task using pre-fetched hotel data."""
    return Task(
        description=f"""
        Compare ALL hotels in {hotel_data.get('destination')} below for {hotel_data.get('travelers')} traveler(s)
        with total trip budget INR {hotel_data.get('total_budget_inr')}:
        {json.dumps(hotel_data.get('hotels', []), ensure_ascii=False)}

        Select `best_hotel` using the exact `name` of the single hotel from the
        entire list that gives the BEST balance of high rating and affordability
        relative to the trip budget (do not ignore higher-rated, lower-priced
        options further down the list). Write a concise factual
        `recommendation_reason` comparing its rating and price against the alternatives.
        """,
        expected_output="An AccommodationAdvice object with best_hotel and recommendation_reason.",
        agent=agent,
        async_execution=False,
        output_pydantic=AccommodationAdvice,
    )
