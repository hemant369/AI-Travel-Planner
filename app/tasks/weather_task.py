import json
from crewai import Agent, Task
from model.schemas import WeatherAdvice


def create_weather_task(agent: Agent, weather_data: dict) -> Task:
    """Create a fresh weather-advice Task using pre-fetched weather data."""
    return Task(
        description=f"""
        Given this factual weather data for {weather_data.get('destination')}:
        {json.dumps(weather_data, ensure_ascii=False)}

        Write a practical 1-2 sentence clothing, packing, and travel
        recommendation tailored to the temperature, humidity, and condition.
        """,
        expected_output="A WeatherAdvice object with a concise packing/travel recommendation.",
        agent=agent,
        async_execution=False,
        output_pydantic=WeatherAdvice,
    )
