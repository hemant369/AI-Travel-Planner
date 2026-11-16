import os
import requests
from datetime import date, datetime, timezone

from dotenv import load_dotenv
from crewai.tools import tool

load_dotenv()

_SESSION = requests.Session()

_WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _fetch_open_meteo(city: str, travel_date: str) -> dict:
    """Fetch up to 16-day forecast from Open-Meteo (free, no API key)."""
    geo_resp = _SESSION.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=10,
    )
    geo_resp.raise_for_status()
    places = geo_resp.json().get("results") or []
    if not places:
        return {
            "destination": city,
            "requested_date": travel_date,
            "data_type": "unavailable",
            "error": f"Could not geocode '{city}' for Open-Meteo forecast.",
        }

    lat = places[0]["latitude"]
    lon = places[0]["longitude"]
    forecast_resp = _SESSION.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "hourly": "relative_humidity_2m",
            "timezone": "auto",
            "start_date": travel_date,
            "end_date": travel_date,
        },
        timeout=10,
    )
    forecast_resp.raise_for_status()
    payload = forecast_resp.json()
    daily = payload.get("daily") or {}
    t_max = (daily.get("temperature_2m_max") or [None])[0]
    t_min = (daily.get("temperature_2m_min") or [None])[0]
    code = (daily.get("weather_code") or [None])[0]

    hourly_hum = [
        h for h in ((payload.get("hourly") or {}).get("relative_humidity_2m") or [])
        if h is not None
    ]
    humidity = int(round(sum(hourly_hum) / len(hourly_hum))) if hourly_hum else None

    if t_max is None or t_min is None:
        return {
            "destination": city,
            "requested_date": travel_date,
            "data_type": "unavailable",
            "error": "No Open-Meteo forecast was returned for the requested date.",
        }

    avg_temp = round((t_max + t_min) / 2, 1)
    condition = _WMO_CODES.get(code, "Mixed conditions")
    return {
        "destination": city,
        "requested_date": travel_date,
        "data_type": "forecast",
        "temperature_c": avg_temp,
        "humidity_percent": humidity,
        "condition": f"{condition} (range {t_min}°C to {t_max}°C)",
    }


def fetch_weather(city: str, travel_date: str) -> dict:
    """Fetch current or near-term forecast weather (up to 16 days ahead) for a travel date."""
    try:
        requested = date.fromisoformat(travel_date)
    except ValueError:
        return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": "Travel date must use YYYY-MM-DD."}

    today = datetime.now(timezone.utc).date()
    days_ahead = (requested - today).days
    if days_ahead < 0:
        return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": "Historical weather is not available from the configured provider."}
    if days_ahead > 15:
        return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": "The travel date is outside the 16-day forecast window; use seasonal destination guidance instead."}

    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key or days_ahead > 5:
        try:
            return _fetch_open_meteo(city, travel_date)
        except requests.exceptions.RequestException as e:
            return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": f"Failed to connect to Open-Meteo: {e}"}

    data_type = "current" if days_ahead == 0 else "forecast"
    url = f"https://api.openweathermap.org/data/2.5/{'weather' if days_ahead == 0 else 'forecast'}"
    params = {"q": city, "appid": api_key, "units": "metric"}

    try:
        response = _SESSION.get(url, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        if days_ahead == 0:
            data = payload
        else:
            candidates = [item for item in payload.get("list", []) if item.get("dt_txt", "").startswith(travel_date)]
            if not candidates:
                return _fetch_open_meteo(city, travel_date)
            data = min(candidates, key=lambda item: abs(int(item.get("dt_txt", "00:00:00")[11:13]) - 12))

        return {
            "destination": city,
            "requested_date": travel_date,
            "data_type": data_type,
            "temperature_c": data["main"]["temp"],
            "humidity_percent": data["main"]["humidity"],
            "condition": data["weather"][0]["description"],
        }

    except (requests.exceptions.RequestException, KeyError):
        try:
            return _fetch_open_meteo(city, travel_date)
        except requests.exceptions.RequestException as e:
            return {"destination": city, "requested_date": travel_date, "data_type": "unavailable", "error": f"Weather lookup failed: {e}"}


@tool("Weather Tool")
def get_weather(city: str, travel_date: str) -> dict:
    """
    Fetch current or near-term forecast weather (up to 16 days ahead) for a travel date.
    """
    return fetch_weather(city, travel_date)
