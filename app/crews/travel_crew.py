"""Crew orchestration: parallel Python data fetch + tool-free CrewAI synthesis + deterministic rendering."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import re

from crewai import Agent, Crew, Process, Task

from agents.accommodation_agent import accommodation_agent
from agents.planner_agent import planner_agent
from agents.recommendation_agent import recommendation_agent
from agents.transport_agent import transport_agent
from agents.weather_agent import weather_agent
from crews.report_renderer import coerce_task_model, render_report_markdown
from model.schemas import (
    AccommodationAdvice,
    AccommodationResult,
    DestinationGuideBasics,
    DestinationGuideResult,
    HotelOption,
    ResearchItem,
    RouteOption,
    TopPicksResult,
    TransportAdvice,
    TransportResult,
    TripDetails,
    WeatherAdvice,
    WeatherResult,
)
from model.settings import CREW_VERBOSE
from tasks.accommodation_task import create_accommodation_task
from tasks.planner_task import create_planner_task
from tasks.recommendation_task import create_guide_basics_task, create_top_picks_task
from tasks.transport_task import create_transport_task
from tasks.weather_task import create_weather_task
from tools.accommodation_tool import fetch_hotels
from tools.map_tool import fetch_route
from tools.search_tool import fetch_attractions_and_food, fetch_destination_guide
from tools.weather_tool import fetch_weather


def _without_tools(base: Agent) -> Agent:
    """Create a tool-free analytical clone so CrewAI skips native tool-calling loops."""
    return Agent(
        role=base.role,
        goal=base.goal,
        backstory=base.backstory,
        llm=base.llm,
        tools=[],
        max_iter=3,
        verbose=base.verbose,
    )


def _fill_missing_urls(items: list[ResearchItem], evidence: list[dict]) -> list[ResearchItem]:
    """Backfill missing source_url values from matching pre-fetched evidence snippets."""
    if not items or not evidence:
        return items
    default_url = next((e.get("url") for e in evidence if e.get("url")), None)
    fixed: list[ResearchItem] = []
    for item in items:
        url = (item.source_url or "").strip()
        if not re.match(r"^https?://", url, re.IGNORECASE):
            tokens = [w.lower() for w in re.findall(r"[a-zA-Z0-9]{4,}", item.name)]
            matched = next(
                (
                    e.get("url")
                    for e in evidence
                    if e.get("url")
                    and any(
                        tok in f"{e.get('title', '')} {e.get('snippet', '')}".lower()
                        for tok in tokens[:2]
                    )
                ),
                default_url,
            )
            item = item.model_copy(update={"source_url": matched})
        fixed.append(item)
    return fixed


def run_travel_plan(
    user_request: str | None = None,
    trip_details: TripDetails | None = None,
) -> str:
    """Fetch live travel data, run tool-free CrewAI agents for synthesis, and render Markdown."""
    if trip_details is None and not user_request:
        raise ValueError("Either user_request or trip_details must be provided.")

    resolved_trip = trip_details
    if resolved_trip is None:
        planner_t = create_planner_task()
        planner_crew = Crew(
            name="Trip Parser Crew",
            agents=[_without_tools(planner_agent)],
            tasks=[planner_t],
            process=Process.sequential,
            verbose=CREW_VERBOSE,
        )
        planner_crew.kickoff(inputs={"user_request": user_request or ""})
        resolved_trip = coerce_task_model(planner_t.output, TripDetails)
        if resolved_trip is None:
            raise RuntimeError("Failed to extract structured trip details.")

    # 1. Fetch all live providers in parallel in Python (fast, deterministic).
    with ThreadPoolExecutor(max_workers=5) as executor:
        f_weather = executor.submit(fetch_weather, resolved_trip.destination, resolved_trip.start_date)
        f_route = executor.submit(fetch_route, resolved_trip.source, resolved_trip.destination)
        f_hotels = executor.submit(
            fetch_hotels,
            resolved_trip.destination,
            resolved_trip.start_date,
            resolved_trip.end_date,
            resolved_trip.travelers,
            resolved_trip.budget_inr,
        )
        f_guide = executor.submit(
            fetch_destination_guide,
            resolved_trip.destination,
            resolved_trip.start_date,
            resolved_trip.end_date,
        )
        f_picks = executor.submit(fetch_attractions_and_food, resolved_trip.destination)

        raw_weather = f_weather.result()
        raw_route = f_route.result()
        raw_hotels = f_hotels.result()
        raw_guide = f_guide.result()
        raw_picks = f_picks.result()

    # 2. Build focused, tool-free CrewAI synthesis tasks (no native tool calling).
    agents: list[Agent] = []
    tasks: list[Task] = []

    weather_t: Task | None = None
    if not raw_weather.get("error") and raw_weather.get("temperature_c") is not None:
        w_agent = _without_tools(weather_agent)
        weather_t = create_weather_task(w_agent, raw_weather)
        agents.append(w_agent)
        tasks.append(weather_t)

    transport_t: Task | None = None
    if raw_route.get("transport_options"):
        t_agent = _without_tools(transport_agent)
        transport_t = create_transport_task(t_agent, raw_route)
        agents.append(t_agent)
        tasks.append(transport_t)

    accommodation_t: Task | None = None
    if raw_hotels.get("hotels"):
        a_agent = _without_tools(accommodation_agent)
        accommodation_t = create_accommodation_task(a_agent, raw_hotels)
        agents.append(a_agent)
        tasks.append(accommodation_t)

    guide_basics_t: Task | None = None
    if not raw_guide.get("error"):
        g_agent = _without_tools(recommendation_agent)
        guide_basics_t = create_guide_basics_task(g_agent, raw_guide)
        agents.append(g_agent)
        tasks.append(guide_basics_t)

    top_picks_t: Task | None = None
    if not raw_picks.get("error"):
        p_agent = _without_tools(recommendation_agent)
        top_picks_t = create_top_picks_task(p_agent, raw_picks)
        agents.append(p_agent)
        tasks.append(top_picks_t)

    if tasks:
        crew = Crew(
            name="Travel Crew",
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=CREW_VERBOSE,
        )
        crew.kickoff(inputs={"user_request": user_request or ""})

    # 3. Merge factual provider fields with CrewAI synthesis outputs.
    w_advice = coerce_task_model(weather_t.output, WeatherAdvice) if weather_t else None
    weather_res = WeatherResult(
        destination=raw_weather.get("destination", resolved_trip.destination),
        data_type=raw_weather.get("data_type", "unavailable"),
        requested_date=raw_weather.get("requested_date", resolved_trip.start_date),
        temperature_c=raw_weather.get("temperature_c"),
        humidity_percent=raw_weather.get("humidity_percent"),
        condition=raw_weather.get("condition"),
        recommendation=w_advice.recommendation if w_advice else None,
        error=raw_weather.get("error"),
    )

    t_advice = coerce_task_model(transport_t.output, TransportAdvice) if transport_t else None
    route_options = [RouteOption.model_validate(opt) for opt in raw_route.get("transport_options", [])]
    transport_res = TransportResult(
        source=raw_route.get("source", resolved_trip.source),
        destination=raw_route.get("destination", resolved_trip.destination),
        options=route_options,
        recommended_mode=(
            t_advice.recommended_mode
            if t_advice
            else (route_options[0].mode if route_options else None)
        ),
        recommendation_reason=t_advice.recommendation_reason if t_advice else None,
        google_maps_link=raw_route.get("google_maps_link", ""),
        error=raw_route.get("error"),
    )

    a_advice = coerce_task_model(accommodation_t.output, AccommodationAdvice) if accommodation_t else None
    hotel_options = [HotelOption.model_validate(h) for h in raw_hotels.get("hotels", [])]
    accommodation_res = AccommodationResult(
        destination=raw_hotels.get("destination", resolved_trip.destination),
        check_in=raw_hotels.get("check_in", resolved_trip.start_date),
        check_out=raw_hotels.get("check_out", resolved_trip.end_date),
        travelers=raw_hotels.get("travelers", resolved_trip.travelers),
        total_budget_inr=raw_hotels.get("total_budget_inr", resolved_trip.budget_inr),
        hotels=hotel_options,
        best_hotel=a_advice.best_hotel if a_advice else None,
        recommendation_reason=a_advice.recommendation_reason if a_advice else None,
        error=raw_hotels.get("error"),
    )

    basics_res = coerce_task_model(guide_basics_t.output, DestinationGuideBasics) if guide_basics_t else None
    picks_res = coerce_task_model(top_picks_t.output, TopPicksResult) if top_picks_t else None

    attractions = _fill_missing_urls(
        picks_res.attractions if picks_res else [],
        raw_picks.get("attractions_evidence", []),
    )
    food = _fill_missing_urls(
        picks_res.food if picks_res else [],
        raw_picks.get("food_evidence", []),
    )

    guide_res = DestinationGuideResult(
        destination=resolved_trip.destination,
        start_date=resolved_trip.start_date,
        end_date=resolved_trip.end_date,
        overview=basics_res.overview if basics_res else None,
        best_season=basics_res.best_season if basics_res else None,
        peak_tourist_season=basics_res.peak_tourist_season if basics_res else None,
        attractions=attractions,
        food=food,
        local_transportation=basics_res.local_transportation if basics_res else [],
        safety_and_etiquette=basics_res.safety_and_etiquette if basics_res else [],
        expenses=basics_res.expenses if basics_res else [],
        first_time_visitor_advice=basics_res.first_time_visitor_advice if basics_res else [],
        festivals=basics_res.festivals if basics_res else [],
    )

    return render_report_markdown(
        trip=resolved_trip,
        weather=weather_res,
        transport=transport_res,
        accommodation=accommodation_res,
        guide=guide_res,
    )
