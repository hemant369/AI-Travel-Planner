import json
from crewai import Agent, Task
from model.schemas import DestinationGuideBasics, TopPicksResult


def create_guide_basics_task(agent: Agent, guide_data: dict) -> Task:
    """Create a fresh destination basics & tips Task from pre-fetched research."""
    return Task(
        description=f"""
        Using ONLY the pre-fetched research evidence below for {guide_data.get('destination')}
        ({guide_data.get('start_date')} to {guide_data.get('end_date')}):
        {json.dumps(guide_data.get('research', {}), ensure_ascii=False)}

        Populate DestinationGuideBasics:
        - `destination`: "{guide_data.get('destination')}"
        - `start_date`: "{guide_data.get('start_date')}"
        - `end_date`: "{guide_data.get('end_date')}"
        - `overview`: Brief 2-3 sentence introduction from `overview` or snippets.
        - `best_season` and `peak_tourist_season`: Extract recommended seasons/months
          and peak tourist months from `best_time` snippets.
        - `local_transportation`, `safety_and_etiquette`, `expenses`,
          `first_time_visitor_advice`: Concise sourced items from snippets.
          CRITICAL FOR CURRENCY: NEVER replace `$` with `₹` 1:1 (for example,
          never turn `$5-$10` into `₹5-₹10`). Prefer INR/₹ figures directly from
          snippets; if a snippet only quotes USD (`$`), convert using 1 USD ≈ ₹85
          or explicitly note the USD amount alongside the INR estimate.
        - `festivals`: Include famous annual/seasonal festivals and cultural
          events celebrated in or near {guide_data.get('destination')} (especially
          around {guide_data.get('start_date')}); omit unrelated cities.

        For EVERY ResearchItem, populate `name`, a factual `description`, and
        copy the exact `url` into `source_url`. Do not invent facts.
        """,
        expected_output="A DestinationGuideBasics object supported by source URLs.",
        agent=agent,
        async_execution=False,
        output_pydantic=DestinationGuideBasics,
    )


def create_top_picks_task(agent: Agent, picks_data: dict) -> Task:
    """Create a focused Task to extract Top 10 Attractions and Top 5 Local Food items."""
    evidence = {
        "attractions_evidence": picks_data.get("attractions_evidence", []),
        "food_evidence": picks_data.get("food_evidence", []),
    }
    return Task(
        description=f"""
        Using ONLY the pre-fetched search snippets below for {picks_data.get('destination')}:
        {json.dumps(evidence, ensure_ascii=False)}

        Populate TopPicksResult:
        - `destination`: "{picks_data.get('destination')}"
        1. `attractions`: Extract **10 completely unique** attractions or activities
           from `attractions_evidence`. Do NOT repeat the same landmark under two
           different names (e.g. avoid listing both "Jakhu Temple" and "Hanuman
           Mandir Jakhoo" or both "Viceregal Lodge" and "IIAS"). If one snippet
           mentions multiple places, create a separate ResearchItem for each and
           reuse that snippet's `url` as `source_url`.
        2. `food`: Extract **5 distinct** signature regional dishes, street foods,
           or iconic local cafes/restaurants in {picks_data.get('destination')} from
           `food_evidence` (prefer local specialties over generic items), and copy
           the exact `url` into `source_url`.

        Every ResearchItem MUST have `name`, a factual `description`, and a valid
        `source_url` from the evidence above.
        """,
        expected_output="A TopPicksResult object with 10 unique attractions and 5 food items, each with description and source_url.",
        agent=agent,
        async_execution=False,
        output_pydantic=TopPicksResult,
    )
