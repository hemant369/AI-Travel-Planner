"""Typed contracts shared by CrewAI tasks."""
from pydantic import BaseModel, Field, field_validator


class TripDetails(BaseModel):
    source: str
    destination: str
    start_date: str
    end_date: str
    duration_days: int = Field(ge=1)
    budget_inr: int = Field(ge=1)
    travelers: int = Field(ge=1)


class WeatherResult(BaseModel):
    destination: str
    data_type: str
    requested_date: str
    temperature_c: float | None = None
    humidity_percent: int | None = None
    condition: str | None = None
    recommendation: str | None = None
    error: str | None = None

    @field_validator("temperature_c", "humidity_percent", "condition", mode="before")
    @classmethod
    def _unwrap_scalar(cls, value):
        if isinstance(value, list):
            return value[0] if value else None
        return value


class HotelOption(BaseModel):
    name: str
    rating: float | None = None
    reviews: int | None = None
    price_per_night: str | None = None
    address: str | None = None
    website: str | None = None


class AccommodationResult(BaseModel):
    destination: str
    check_in: str
    check_out: str
    travelers: int
    total_budget_inr: int
    hotels: list[HotelOption] = Field(default_factory=list)
    best_hotel: str | None = None
    recommendation_reason: str | None = None
    error: str | None = None


class RouteOption(BaseModel):
    mode: str
    distance_km: float
    estimated_duration: str


class TransportResult(BaseModel):
    source: str
    destination: str
    options: list[RouteOption] = Field(default_factory=list)
    recommended_mode: str | None = None
    recommendation_reason: str | None = None
    google_maps_link: str
    error: str | None = None


class WeatherAdvice(BaseModel):
    recommendation: str


class TransportAdvice(BaseModel):
    recommended_mode: str
    recommendation_reason: str


class AccommodationAdvice(BaseModel):
    best_hotel: str
    recommendation_reason: str


class ResearchItem(BaseModel):
    name: str
    description: str
    source_url: str | None = None


class TopPicksResult(BaseModel):
    destination: str
    attractions: list[ResearchItem] = Field(default_factory=list)
    food: list[ResearchItem] = Field(default_factory=list)
    error: str | None = None


class DestinationGuideBasics(BaseModel):
    destination: str
    start_date: str
    end_date: str
    overview: str | None = None
    best_season: str | None = None
    peak_tourist_season: str | None = None
    local_transportation: list[ResearchItem] = Field(default_factory=list)
    safety_and_etiquette: list[ResearchItem] = Field(default_factory=list)
    expenses: list[ResearchItem] = Field(default_factory=list)
    first_time_visitor_advice: list[ResearchItem] = Field(default_factory=list)
    festivals: list[ResearchItem] = Field(default_factory=list)
    error: str | None = None


class DestinationGuideResult(BaseModel):
    destination: str
    start_date: str
    end_date: str
    overview: str | None = None
    best_season: str | None = None
    peak_tourist_season: str | None = None
    attractions: list[ResearchItem] = Field(default_factory=list)
    food: list[ResearchItem] = Field(default_factory=list)
    local_transportation: list[ResearchItem] = Field(default_factory=list)
    safety_and_etiquette: list[ResearchItem] = Field(default_factory=list)
    expenses: list[ResearchItem] = Field(default_factory=list)
    first_time_visitor_advice: list[ResearchItem] = Field(default_factory=list)
    festivals: list[ResearchItem] = Field(default_factory=list)
    error: str | None = None
