import json
from crewai import Agent, Task
from model.schemas import TransportAdvice


def create_transport_task(agent: Agent, route_data: dict) -> Task:
    """Create a fresh transport-recommendation Task using pre-fetched route data."""
    return Task(
        description=f"""
        Given these factual road route options from {route_data.get('source')} to {route_data.get('destination')}:
        {json.dumps(route_data.get('transport_options', []), ensure_ascii=False)}

        Choose the best `recommended_mode` from the provided options only and
        provide a concise 1-sentence `recommendation_reason` comparing distance/duration.
        """,
        expected_output="A TransportAdvice object selecting recommended_mode and recommendation_reason.",
        agent=agent,
        async_execution=False,
        output_pydantic=TransportAdvice,
    )
