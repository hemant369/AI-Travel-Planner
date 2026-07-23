"""Strict final-report contract used by the API crew."""

from crewai import Task

from agents.report_agent import report_agent
from tasks.accommodation_task import accommodation_task
from tasks.planner_task import planner_task
from tasks.recommendation_task import recommendation_task
from tasks.transport_task import transport_task
from tasks.weather_task import weather_task


REPORT_TEMPLATE = """
# <Source> to <Destination> Trip Report

> **At a glance:** <travelers> travelers | <dates> | <transport> | <weather> | Budget: INR <budget>

## Trip Overview
- **Source:** <value>
- **Destination:** <value>
- **Travel Dates:** <value>
- **Number of Travelers:** <value>
- **Budget:** <value>

### Weather & Packing
- **Temperature:** <value>
- **Humidity:** <value>
- **Condition:** <value>
- **Travel Recommendation:** <value>

## Transportation
| Option | Mode | Distance | Estimated Time |
|---|---|---:|---:|
| 1 | <value> | <value> | <value> |

**Recommended:** <mode> - <reason>

[Open in Google Maps](<URL>)

## Accommodation
| Hotel | Rating | Price / Night | Address | Booking Link |
|---|---:|---:|---|---|
| <name> | <value> | <value> | <value> | [View](<URL>) |

**Best Recommended Hotel:** <name>

**Reason:** <value>

## Destination Guide
<brief sourced introduction>

## Best Time to Visit
- **Best Season:** <value>
- **Peak Tourist Season:** <value>

## Top Attractions & Activities
- **<name>** - <description> ([Source](<URL>))

## Local Food & Cuisine
- **Signature Dishes:** <value with source links>
- **Popular Restaurants / Food Streets:** <value with source links>

## Travel Tips
- **Local Transportation:** <value>
- **Safety:** <value>
- **Estimated Expenses:** <value>
- **Cultural Etiquette:** <value>
- **First-Time Visitor Advice:** <value>

## Festivals & Events
- **Major Festivals:** <value with source links>
- **Seasonal / Cultural Events:** <value with source links>
"""


report_task = Task(
    description=f"""
    Compile one professional Markdown report using only the five context task
    outputs. Do not research, infer, calculate, or invent facts.

    Follow this template exactly. Keep every level-two heading, in this order:

    {REPORT_TEMPLATE}

    Formatting rules:
    - Return raw Markdown only: no preamble, commentary, or code fence.
    - Use exactly one H1 title. Every main section must use ##, not ###.
    - Use Markdown tables with the same number of cells as header columns.
    - Include only transport options and hotels actually returned by tools.
    - Never print tool errors as recommendations.
    - Preserve source and booking URLs as Markdown links.
    - For every missing value write exactly "Information not available".
    - Use "INR" for money and plain hyphens where typography is uncertain.
    - Context may contain Pydantic/JSON objects. Render their values faithfully;
      never expose schema syntax or JSON in the final report.
    """,
    expected_output="A raw Markdown report matching REPORT_TEMPLATE exactly.",
    context=[planner_task, weather_task, transport_task, accommodation_task, recommendation_task],
    agent=report_agent,
)
