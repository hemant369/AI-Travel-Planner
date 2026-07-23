from crewai.tools import tool
from clients.serper_client import SerperClient


@tool("Accommodation Tool")
def search_hotels(
    destination: str,
    check_in: str,
    check_out: str,
    travelers: int,
    total_budget_inr: int,
) -> dict:
    """
    Search hotels using destination, dates, party size, and total budget.
    """
    try:
        data = SerperClient().search_hotels(
            destination,
            check_in,
            check_out,
            travelers,
            total_budget_inr,
        )

        hotels = [
            {
                "name": place.get("title"),
                "rating": place.get("rating"),
                "reviews": place.get("reviews"),
                "price_per_night": place.get("price") or place.get("priceLevel"),
                "address": place.get("address"),
                "website": place.get("website"),
            }
            for place in data.get("places", [])[:5]
        ]

        return {
            "destination": destination,
            "check_in": check_in,
            "check_out": check_out,
            "travelers": travelers,
            "total_budget_inr": total_budget_inr,
            "hotels": hotels,
        }

    except Exception as exc:
        return {
            "destination": destination,
            "check_in": check_in,
            "check_out": check_out,
            "travelers": travelers,
            "total_budget_inr": total_budget_inr,
            "hotels": [],
            "error": f"Accommodation search failed: {exc}",
        }
