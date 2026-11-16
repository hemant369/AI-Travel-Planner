from concurrent.futures import ThreadPoolExecutor
import re
from crewai.tools import tool
from clients.serper_client import SerperClient

_PRICE_RE = re.compile(r"(?:₹|INR|Rs\.?)\s*([\d,]{3,7})", re.IGNORECASE)


def _clean_text(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = " ".join(str(value).replace("|", "-").split())
    return cleaned or None


def _extract_valid_price(search_data: dict) -> str | None:
    """Extract a realistic nightly INR price (300 - 200,000) from search results."""
    candidates: list[int] = []
    for item in search_data.get("organic", []):
        price_range = (item.get("priceRange") or "").strip()
        text = " ".join([
            item.get("title") or "",
            item.get("snippet") or "",
            price_range,
        ])
        for match in _PRICE_RE.finditer(text):
            try:
                amount = int(match.group(1).replace(",", ""))
            except ValueError:
                continue
            if 300 <= amount <= 200_000:
                candidates.append(amount)
    if not candidates:
        return None
    # Prefer the median-low realistic nightly price among matched snippets
    candidates.sort()
    chosen = candidates[len(candidates) // 2]
    return f"~₹{chosen:,} / night (est.)"


def _lookup_hotel_price(
    hotel_name: str,
    destination: str,
    check_in: str,
    check_out: str,
) -> str | None:
    try:
        client = SerperClient()
        search_data = client.search_hotel_price_for_place(
            hotel_name, destination, check_in, check_out
        )
        return _extract_valid_price(search_data)
    except Exception:
        return None


def fetch_hotels(
    destination: str,
    check_in: str,
    check_out: str,
    travelers: int,
    total_budget_inr: int,
) -> dict:
    """Search hotels using destination, dates, party size, and total budget."""
    try:
        client = SerperClient()
        data = client.search_hotels(
            destination,
            check_in,
            check_out,
            travelers,
            total_budget_inr,
        )

        raw_places = data.get("places", [])[:5]

        # Enrich missing hotel prices in parallel using Serper Web Search
        missing_indices = [
            idx for idx, place in enumerate(raw_places)
            if not (place.get("price") or place.get("priceLevel")) and place.get("title")
        ]
        fetched_prices: dict[int, str | None] = {}
        if missing_indices:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    idx: executor.submit(
                        _lookup_hotel_price,
                        raw_places[idx]["title"],
                        destination,
                        check_in,
                        check_out,
                    )
                    for idx in missing_indices
                }
                for idx, future in futures.items():
                    fetched_prices[idx] = future.result()

        hotels = []
        for idx, place in enumerate(raw_places):
            price = (
                place.get("price")
                or place.get("priceLevel")
                or fetched_prices.get(idx)
            )
            hotels.append(
                {
                    "name": _clean_text(place.get("title")),
                    "rating": place.get("rating"),
                    "reviews": place.get("reviews"),
                    "price_per_night": _clean_text(price),
                    "address": _clean_text(place.get("address")),
                    "website": place.get("website"),
                }
            )

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


@tool("Accommodation Tool")
def search_hotels(
    destination: str,
    check_in: str,
    check_out: str,
    travelers: int,
    total_budget_inr: int,
) -> dict:
    """Search hotels using destination, dates, party size, and total budget."""
    return fetch_hotels(destination, check_in, check_out, travelers, total_budget_inr)
