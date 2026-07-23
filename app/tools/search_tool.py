"""Evidence-based destination research tool."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from crewai.tools import tool

from clients.tavily_client import TavilyClient


def _query_plan(destination: str, start_date: str, end_date: str) -> dict[str, tuple[str, int]]:
    dates = f"from {start_date} to {end_date}"
    return {
        "best_time": (f"{destination} weather seasons peak tourist season travel {dates}", 3),
        "attractions": (f"best attractions hidden gems and things to do in {destination}", 5),
        "food": (f"signature local dishes restaurants and food streets in {destination}", 4),
        "local_transportation": (f"local public transportation getting around {destination} travel advice", 3),
        "safety_and_etiquette": (f"{destination} tourist safety cultural etiquette first time visitor advice", 3),
        "expenses": (f"typical daily tourist expenses food local transport activities in {destination}", 3),
        "festivals": (f"festivals cultural events in {destination} around {start_date} {end_date}", 4),
    }


def _search_category(client: TavilyClient, category: str, query: str, limit: int) -> tuple[str, dict]:
    try:
        results = client.search(query, max_results=limit)
        return category, {"found": bool(results), "results": results}
    except Exception as exc:
        return category, {"found": False, "results": [], "error": str(exc)}


@tool("Recommendation Research Tool")
def get_recommendations(destination: str, start_date: str, end_date: str) -> dict:
    """Research a destination for the user's selected travel dates.

    Returns stable evidence categories. Every result contains a title, source URL,
    and snippet. Failed categories are marked unavailable instead of aborting the
    complete destination guide.
    """
    try:
        client = TavilyClient()
    except ValueError as exc:
        return {
            "destination": destination,
            "start_date": start_date,
            "end_date": end_date,
            "research": {},
            "error": str(exc),
        }

    plan = _query_plan(destination, start_date, end_date)
    research = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(_search_category, client, category, query, limit)
            for category, (query, limit) in plan.items()
        ]
        for future in as_completed(futures):
            category, result = future.result()
            research[category] = result

    # Preserve a deterministic order for the model and logs despite concurrency.
    research = {category: research[category] for category in plan}
    if not any(section["found"] for section in research.values()):
        error = "No destination research was available from the configured provider."
    else:
        error = None
    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "research": research,
        "error": error,
    }
