from urllib.parse import quote_plus

from crewai.tools import tool
from clients.maps_client import MapsClient


def _parse_route(route_data: dict) -> dict:
    """
    Parse a Google Routes API response into a simplified format.
    """
    routes = route_data.get("routes", [])
    if not routes:
        raise ValueError("No route found.")

    route = routes[0]
    distance_km = round(route.get("distanceMeters", 0) / 1000, 2)
    duration_str = route.get("duration", "0s")
    total_seconds = int(duration_str.rstrip("s").split(".")[0])
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    return {
        "distance_km": distance_km,
        "estimated_duration": f"{hours} hr {minutes} min",
    }


def fetch_route(source: str, destination: str) -> dict:
    """Retrieve road transportation options between source and destination."""
    google_maps_link = (
        "https://www.google.com/maps/dir/"
        f"{quote_plus(source)}/{quote_plus(destination)}"
    )

    try:
        client = MapsClient()
    except ValueError as exc:
        return {
            "source": source,
            "destination": destination,
            "transport_options": [],
            "google_maps_link": google_maps_link,
            "error": str(exc),
        }

    transport_options = []

    # Driving Route
    try:
        car_data = client.compute_route(
            source=source,
            destination=destination,
            travel_mode=MapsClient.DRIVE,
        )
        car_route = _parse_route(car_data)
        transport_options.append({"mode": "Driving (Car)", **car_route})
    except Exception as e:
        car_error = str(e)

    # Motorcycle Route
    try:
        bike_data = client.compute_route(
            source=source,
            destination=destination,
            travel_mode=MapsClient.TWO_WHEELER,
        )
        bike_route = _parse_route(bike_data)
        transport_options.append({"mode": "Motorcycle", **bike_route})
    except Exception as e:
        bike_error = str(e)

    result = {
        "source": source,
        "destination": destination,
        "transport_options": transport_options,
        "google_maps_link": google_maps_link,
    }
    if not transport_options:
        result["error"] = "No route options were available."
    if "car_error" in locals():
        result["driving_error"] = car_error
    if "bike_error" in locals():
        result["motorcycle_error"] = bike_error
    return result


@tool("Maps Tool")
def get_route(source: str, destination: str) -> dict:
    """Retrieve road transportation options between two locations."""
    return fetch_route(source, destination)
