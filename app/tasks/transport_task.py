from crewai import Task

from agents.transport_agent import transport_agent
from tasks.planner_task import planner_task
from model.schemas import TransportResult


transport_task = Task(
    description="""
    Using the Maps Tool, retrieve all available transportation options.
    Format the response using EXACTLY the following structure:

    ## Transportation
    **Source:** <source>
    **Destination:** <destination>
    ### Available Transportation Options

    #### Option 1
    - Mode:
    - Distance:
    - Estimated Duration:

    #### Option 2
    - Mode:
    - Distance:
    - Estimated Duration:

    ### Recommended Transportation
    - Recommended Mode:
    - Reason:

    ### Navigation
    - Google Maps Link:

    Rules:
    - If only one transportation option is available (e.g., motorcycle route
    unsupported in this region), include only that option and omit the
    unused Option slot entirely — do not fabricate a second option.
    """,

    expected_output="""
    A transportation summary containing:

    - Source
    - Destination
    - Available transportation options
        - Transport mode
        - Distance
        - Estimated duration
    - Recommended transportation option
    - Google Maps navigation link
    """,

    agent=transport_agent,
    context=[planner_task],
    async_execution=True,
    output_pydantic=TransportResult,
)
