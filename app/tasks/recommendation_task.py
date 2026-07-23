from crewai import Task
from tasks.planner_task import planner_task
from agents.recommendation_agent import recommendation_agent
from model.schemas import DestinationGuideResult

recommendation_task = Task(
    description="""
    Using the structured Planner Task output, call the Recommendation Research
    Tool exactly once with destination, start_date, and end_date.

    Convert the tool evidence into DestinationGuideResult. Populate:

    1. Best time to visit
       - Best Visiting Seasons
       - Peak Tourist Season

    2. Attractions and activities

    3. Local food and cuisine

    4. Local transportation
    5. Safety and cultural etiquette
    6. Estimated expenses
    7. First-time visitor advice

    8. Festivals and events relevant to the selected dates

      Use ONLY facts present in the tool snippets. Do not use prior knowledge.
      Every ResearchItem must preserve the evidence URL in source_url. Do not
      turn a search-result title into a factual claim unless its snippet supports
      the claim. Leave lists empty when found is false; never invent placeholders.

      Include the source URL for each claim so the output can be verified.
      Return data matching DestinationGuideResult exactly.
    """,

    expected_output="A DestinationGuideResult object supported by source URLs.",

    agent=recommendation_agent,
    context=[planner_task],
    async_execution=True,
    output_pydantic=DestinationGuideResult,
)
