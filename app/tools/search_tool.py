"""Evidence-based destination research tools."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from crewai.tools import tool

from clients.tavily_client import TavilyClient
from clients.wikivoyage_client import WikivoyageClient


def _search_category(
    client: TavilyClient,
    category: str,
    query: str,
    limit: int,
    snippet_chars: int = 360,
) -> tuple[str, dict]:
    try:
        results = client.search(query, max_results=limit, snippet_chars=snippet_chars)
        return category, {"found": bool(results), "results": results}
    except Exception as exc:
        return category, {"found": False, "results": [], "error": str(exc)}


def _fetch_wikivoyage_overview(destination: str) -> tuple[str, dict]:
    try:
        results = WikivoyageClient().get_overview(destination)
        return "overview", {"found": bool(results), "results": results}
    except Exception as exc:
        return "overview", {"found": False, "results": [], "error": str(exc)}


def fetch_attractions_and_food(destination: str) -> dict:
    """Fetch evidence for top 10 attractions/activities and top 5 local food spots."""
    try:
        client = TavilyClient()
    except ValueError as exc:
        return {"destination": destination, "attractions_evidence": [], "food_evidence": [], "error": str(exc)}

    queries = {
        "attractions_sightseeing": (f"top 10 tourist attractions places to visit in {destination}", 6),
        "attractions_activities": (f"best things to do adventure sightseeing hidden gems in {destination}", 6),
        "food_dishes": (f"famous traditional local dishes street food in {destination}", 4),
        "food_restaurants": (f"best popular restaurants cafes food spots in {destination}", 4),
    }

    raw: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(_search_category, client, key, q, lim, 380)
            for key, (q, lim) in queries.items()
        ]
        for future in as_completed(futures):
            key, res = future.result()
            raw[key] = res

    def _merge(keys: list[str]) -> list[dict]:
        merged, seen = [], set()
        for k in keys:
            for item in raw.get(k, {}).get("results", []):
                if item["url"] not in seen:
                    seen.add(item["url"])
                    merged.append(item)
        return merged

    attractions = _merge(["attractions_sightseeing", "attractions_activities"])
    food = _merge(["food_dishes", "food_restaurants"])
    return {
        "destination": destination,
        "attractions_evidence": attractions[:10],
        "food_evidence": food[:7],
        "error": None if (attractions or food) else "No attractions or food research available.",
    }


def fetch_destination_guide(destination: str, start_date: str, end_date: str) -> dict:
    """Fetch overview, best season, local transport, safety, expenses, and local festivals."""
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

    try:
        month_name = date.fromisoformat(start_date).strftime("%B")
    except ValueError:
        month_name = ""

    plan = {
        "best_time": (f"best time to visit {destination} best season peak tourist season months", 3),
        "local_transportation": (f"local public transportation getting around {destination} travel advice", 2),
        "safety_and_etiquette": (f"{destination} tourist safety cultural etiquette first time visitor advice", 2),
        "expenses": (f"daily travel cost budget in {destination} in INR rupees hotel food transport", 3),
        "festivals": (f"famous festivals cultural events fairs in {destination} {month_name} annual", 3),
    }

    research = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(_search_category, client, category, query, limit, 340)
            for category, (query, limit) in plan.items()
        ]
        futures.append(executor.submit(_fetch_wikivoyage_overview, destination))
        for future in as_completed(futures):
            category, result = future.result()
            research[category] = result

    ordered = ["overview", *plan.keys()]
    research = {c: research[c] for c in ordered}
    error = None if any(s["found"] for s in research.values()) else "No destination guide research available."
    return {
        "destination": destination,
        "start_date": start_date,
        "end_date": end_date,
        "research": research,
        "error": error,
    }


@tool("Attractions & Food Research Tool")
def get_attractions_and_food(destination: str) -> dict:
    """Research top 10 attractions/activities and top 5 local food spots for a destination."""
    return fetch_attractions_and_food(destination)


@tool("Destination Guide Research Tool")
def get_destination_guide(destination: str, start_date: str, end_date: str) -> dict:
    """Research overview, best season, local transport, safety, expenses, and local festivals."""
    return fetch_destination_guide(destination, start_date, end_date)
