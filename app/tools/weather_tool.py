import os
import requests
from datetime import date, datetime, timezone

from dotenv import load_dotenv
from crewai.tools import tool

load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")


@tool("Weather Tool")
def get_weather(city: str, travel_date: str) -> dict:
    """
    Fetch current or near-term forecast weather for a travel date.
    """
    if not API_KEY:
        return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": "WEATHER_API_KEY is not configured."}

    try:
        requested = date.fromisoformat(travel_date)
    except ValueError:
        return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": "Travel date must use YYYY-MM-DD."}

    today = datetime.now(timezone.utc).date()
    days_ahead = (requested - today).days
    if days_ahead < 0:
        return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": "Historical weather is not available from the configured provider."}
    if days_ahead > 5:
        return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": "The travel date is outside the five-day forecast window; use seasonal destination guidance instead."}

    data_type = "current" if days_ahead == 0 else "forecast"
    url = f"https://api.openweathermap.org/data/2.5/{'weather' if days_ahead == 0 else 'forecast'}"
    params = {"q": city, "appid": API_KEY, "units": "metric"}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        if days_ahead == 0:
            data = payload
        else:
            candidates = [item for item in payload.get("list", []) if item.get("dt_txt", "").startswith(travel_date)]
            if not candidates:
                return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": "No forecast was returned for the requested date."}
            data = min(candidates, key=lambda item: abs(int(item.get("dt_txt", "00:00:00")[11:13]) - 12))

        return {
            "destination": city,
            "requested_date": travel_date,
            "data_type": data_type,
            "temperature_c": data["main"]["temp"],
            "humidity_percent": data["main"]["humidity"],
            "condition": data["weather"][0]["description"],
        }

    except requests.exceptions.HTTPError as e:
        return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": f"Weather API returned an error: {e}"}
    except requests.exceptions.RequestException as e:
        return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": f"Failed to connect to Weather API: {e}"}
    except KeyError as e:
        return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": f"Unexpected API response. Missing field: {e}"}
