"""HTTP interface for the travel-planning crew.

Run from the app directory with:
    python -m uvicorn api:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import logging
import re
import sys
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator


APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

app = FastAPI(title="Travel Planner API", version="1.0.0")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
logger = logging.getLogger(__name__)


def normalize_report(markdown: str) -> str:
    """Normalize model formatting without changing its factual content."""
    text = str(markdown or "").strip().replace("\r\n", "\n")
    text = re.sub(r"^```(?:markdown|md)?\s*\n", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n```\s*$", "", text)
    for name in ("Trip Overview", "Transportation", "Accommodation", "Destination Guide", "Best Time to Visit", "Top Attractions & Activities", "Local Food & Cuisine", "Travel Tips", "Festivals & Events"):
        text = re.sub(rf"^\s*#{{1,4}}\s+{re.escape(name)}\s*$", f"## {name}", text, flags=re.MULTILINE | re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def public_error_detail(exc: Exception) -> str:
    """Map internal failures to useful messages without leaking credentials."""
    message = str(exc).lower()
    if "ollama" in message or "connection refused" in message:
        return "The local Ollama model is unavailable. Start Ollama and verify OLLAMA_MODEL."
    if "api_key" in message or "api key" in message or "not configured" in message:
        return "A required travel-data API key is missing. Check the server environment configuration."
    if "timeout" in message or "timed out" in message:
        return "A travel-data provider took too long to respond. Please try again."
    if "empty report" in message or "none or empty" in message:
        return "The planning model returned an empty response. Please try again."
    return "Trip planning failed unexpectedly. Check the server logs and try again."


class TripRequest(BaseModel):
    source: str = Field(min_length=2, max_length=100)
    destination: str = Field(min_length=2, max_length=100)
    start_date: date
    end_date: date
    travelers: int = Field(ge=1, le=20)
    budget: int = Field(ge=1)

    @field_validator("source", "destination")
    @classmethod
    def clean_location(cls, value: str) -> str:
        return " ".join(value.split())

    @model_validator(mode="after")
    def validate_dates(self) -> "TripRequest":
        if self.end_date < self.start_date:
            raise ValueError("End date must be on or after start date.")
        return self

    def to_trip_details(self):
        from model.schemas import TripDetails

        duration = (self.end_date - self.start_date).days + 1
        return TripDetails(
            source=self.source,
            destination=self.destination,
            start_date=self.start_date.isoformat(),
            end_date=self.end_date.isoformat(),
            duration_days=duration,
            budget_inr=self.budget,
            travelers=self.travelers,
        )


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(APP_DIR / "static" / "index.html")


@app.get("/api/health", include_in_schema=False)
def health() -> dict[str, str]:
    """Lightweight container health check that does not invoke Ollama."""
    return {"status": "ok"}


@app.post("/api/trips/plan")
def plan_trip(trip: TripRequest) -> dict[str, object]:
    """Run the CrewAI workflow with structured TripDetails and return deterministic Markdown."""
    try:
        # Delay this import so opening the dashboard does not initialise the LLM.
        from crews.travel_crew import run_travel_plan

        raw_report = run_travel_plan(trip_details=trip.to_trip_details())
        report = normalize_report(raw_report)
        if not report:
            raise RuntimeError("The travel crew returned an empty report.")
        return {"trip": trip.model_dump(mode="json"), "report_markdown": report}
    except Exception as exc:
        logger.exception("Trip planning failed")
        raise HTTPException(
            status_code=500,
            detail=public_error_detail(exc),
        ) from exc
