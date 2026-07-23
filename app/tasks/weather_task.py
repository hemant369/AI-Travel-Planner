from crewai import Task

from agents.weather_agent import weather_agent
from tasks.planner_task import planner_task
from model.schemas import WeatherResult


weather_task = Task(
    description = """
        Using the travel information provided by the planner,
        call the Weather Tool with the destination and travel start date. Do not provide weather for the source city, transit cities,
        or any other location.
        Never substitute today's weather for a future date. Preserve unavailable
        forecast errors and provide advice only when weather data exists.""",
    expected_output = """
        A weather report containing:\n"
            - Destination\n
            - Temperature (°C)\n
            - Humidity (%)\n
            - Weather condition\n
            - Travel recommendation""",
    agent = weather_agent,
    context = [planner_task],
    async_execution=True,
    output_pydantic=WeatherResult,
)
