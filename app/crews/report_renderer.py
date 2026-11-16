"""Deterministic Markdown report renderer from structured Pydantic task outputs."""

from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel

from model.schemas import (
    AccommodationResult,
    DestinationGuideResult,
    ResearchItem,
    TransportResult,
    TripDetails,
    WeatherResult,
)

T = TypeVar("T", bound=BaseModel)
MISSING = "Information not available"


def coerce_task_model(task_output, model_cls: type[T]) -> T | None:
    """Extract a Pydantic model from a CrewAI TaskOutput safely."""
    if task_output is None:
        return None
    pydantic_val = getattr(task_output, "pydantic", None)
    if isinstance(pydantic_val, model_cls):
        return pydantic_val
    json_dict = getattr(task_output, "json_dict", None)
    if isinstance(json_dict, dict):
        try:
            return model_cls.model_validate(json_dict)
        except Exception:
            pass
    raw = str(getattr(task_output, "raw", "") or "").strip()
    if raw:
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()
        try:
            return model_cls.model_validate(json.loads(raw))
        except Exception:
            pass
    return None


def _val(value: object) -> str:
    if value is None:
        return MISSING
    text = " ".join(str(value).split())
    return text if text else MISSING


def _cell(value: object) -> str:
    """Sanitize a table cell so pipes and newlines cannot break Markdown columns."""
    text = _val(value)
    return text.replace("|", "-")


def _is_http_url(url: str | None) -> bool:
    return bool(url and re.match(r"^https?://", url.strip(), re.IGNORECASE))


def _format_research_bullets(items: list[ResearchItem]) -> list[str]:
    if not items:
        return [f"- {MISSING}"]
    lines = []
    for item in items:
        name = _val(item.name)
        desc = _val(item.description)
        text = f"- **{name}:** {desc}" if desc != MISSING else f"- **{name}**"
        if _is_http_url(item.source_url):
            text += f" ([Source]({item.source_url.strip()}))"
        lines.append(text)
    return lines


def _format_numbered_items(items: list[ResearchItem], limit: int) -> list[str]:
    if not items:
        return [f"1. **{MISSING}** - {MISSING}"]
    lines = []
    for idx, item in enumerate(items[:limit], start=1):
        name = _val(item.name)
        desc = _val(item.description)
        line = f"{idx}. **{name}** - {desc}"
        if _is_http_url(item.source_url):
            line += f" ([Source]({item.source_url.strip()}))"
        lines.append(line)
    return lines


def render_report_markdown(
    trip: TripDetails,
    weather: WeatherResult | None,
    transport: TransportResult | None,
    accommodation: AccommodationResult | None,
    guide: DestinationGuideResult | None,
) -> str:
    """Render the final trip report deterministically without an extra LLM call."""
    if weather and not weather.error and weather.temperature_c is not None:
        temp_str = f"{weather.temperature_c}°C"
        hum_str = f"{weather.humidity_percent}%" if weather.humidity_percent is not None else MISSING
        cond_str = _val(weather.condition)
        rec_str = _val(weather.recommendation)
        glance_weather = f"{cond_str}, {temp_str}"
    else:
        temp_str = MISSING
        hum_str = MISSING
        cond_str = MISSING
        rec_str = weather.error if (weather and weather.error) else MISSING
        glance_weather = "Weather unavailable"

    options = transport.options if transport else []
    glance_transport = (
        transport.recommended_mode
        if (transport and transport.recommended_mode)
        else (options[0].mode if options else "Road travel")
    )

    lines = [
        f"# {trip.source} to {trip.destination} Trip Report",
        "",
        (
            f"> **At a glance:** {trip.travelers} traveler(s) | "
            f"{trip.start_date} to {trip.end_date} | {glance_transport} | "
            f"{glance_weather} | Budget: INR {trip.budget_inr:,}"
        ),
        "",
        "## Trip Overview",
        f"- **Source:** {trip.source}",
        f"- **Destination:** {trip.destination}",
        f"- **Travel Dates:** {trip.start_date} to {trip.end_date} ({trip.duration_days} day(s))",
        f"- **Number of Travelers:** {trip.travelers}",
        f"- **Budget:** INR {trip.budget_inr:,}",
        "",
        "### Weather & Packing",
        f"- **Temperature:** {temp_str}",
        f"- **Humidity:** {hum_str}",
        f"- **Condition:** {cond_str}",
        "",
        f"> **Travel Recommendation:** {rec_str}",
        "",
        "## Transportation",
    ]

    if options:
        lines.extend([
            "| Option | Mode | Distance | Estimated Time |",
            "|---|---|---:|---:|",
        ])
        for idx, opt in enumerate(options, start=1):
            lines.append(f"| {idx} | {_cell(opt.mode)} | {opt.distance_km} km | {_cell(opt.estimated_duration)} |")
        lines.append("")
    else:
        lines.append(MISSING)
        lines.append("")

    rec_mode = _val(transport.recommended_mode if transport else None)
    rec_reason = _val(transport.recommendation_reason if transport else None)
    lines.append(f"**Recommended:** {rec_mode} - {rec_reason}")
    lines.append("")
    if transport and _is_http_url(transport.google_maps_link):
        lines.append(f"[Open in Google Maps]({transport.google_maps_link})")
    lines.append("")

    lines.append("## Accommodation")
    hotels = accommodation.hotels if accommodation else []
    if hotels:
        lines.extend([
            "| Hotel | Rating | Price / Night | Address | Booking Link |",
            "|---|---:|---:|---|---|",
        ])
        for h in hotels[:5]:
            rating = str(h.rating) if h.rating is not None else MISSING
            price = _cell(h.price_per_night)
            address = _cell(h.address)
            link = f"[View]({h.website.strip()})" if _is_http_url(h.website) else MISSING
            lines.append(f"| {_cell(h.name)} | {rating} | {price} | {address} | {link} |")
        lines.append("")
    else:
        lines.append(MISSING)
        lines.append("")

    best_hotel = _val(accommodation.best_hotel if accommodation else None)
    hotel_reason = _val(accommodation.recommendation_reason if accommodation else None)
    lines.append(f"**Best Recommended Hotel:** {best_hotel}")
    lines.append("")
    lines.append(f"**Reason:** {hotel_reason}")
    lines.append("")

    lines.append("## Destination Guide")
    lines.append(_val(guide.overview if guide else None))
    lines.append("")

    lines.append("## Best Time to Visit")
    lines.append(f"- **Best Season:** {_val(guide.best_season if guide else None)}")
    lines.append(f"- **Peak Tourist Season:** {_val(guide.peak_tourist_season if guide else None)}")
    lines.append("")

    lines.append("## Top Attractions & Activities")
    lines.extend(_format_numbered_items(guide.attractions if guide else [], 10))
    lines.append("")

    lines.append("## Local Food & Cuisine")
    lines.extend(_format_numbered_items(guide.food if guide else [], 5))
    lines.append("")

    lines.append("## Travel Tips")
    lines.append("### Local Transportation")
    lines.extend(_format_research_bullets(guide.local_transportation if guide else []))
    lines.append("")
    lines.append("### Safety & Cultural Etiquette")
    lines.extend(_format_research_bullets(guide.safety_and_etiquette if guide else []))
    lines.append("")
    lines.append("### Estimated Expenses (INR)")
    lines.extend(_format_research_bullets(guide.expenses if guide else []))
    lines.append("")
    lines.append("### First-Time Visitor Advice")
    lines.extend(_format_research_bullets(guide.first_time_visitor_advice if guide else []))
    lines.append("")

    lines.append("## Festivals & Events")
    lines.extend(_format_research_bullets(guide.festivals if guide else []))

    return "\n".join(lines).strip()
