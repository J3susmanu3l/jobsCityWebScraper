from __future__ import annotations

from math import cos, radians
from typing import Any
import time
import requests


TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def _raise_on_bad_status(payload: dict[str, Any], operation: str) -> None:
    status = payload.get("status", "")
    error_message = payload.get("error_message", "")
    if status in {"REQUEST_DENIED", "INVALID_REQUEST", "OVER_QUERY_LIMIT"}:
        details = f"{status}: {error_message}".strip(": ")
        raise ValueError(f"{operation} failed. {details}")


def text_search_places(
    *,
    api_key: str,
    query: str,
    city: str,
    max_results: int,
    timeout_seconds: int,
) -> list[dict[str, Any]]:
    all_results: list[dict[str, Any]] = []
    next_page_token: str | None = None
    full_query = f"{query} in {city}"

    while len(all_results) < max_results:
        params = {
            "key": api_key,
            "query": full_query,
        }
        if next_page_token:
            # Google may return INVALID_REQUEST if pagetoken is used too soon.
            time.sleep(2)
            params["pagetoken"] = next_page_token

        attempts = 0
        while True:
            response = requests.get(TEXT_SEARCH_URL, params=params, timeout=timeout_seconds)
            response.raise_for_status()
            payload = response.json()
            status = payload.get("status", "")

            # Pagetoken often needs a few seconds before it becomes valid.
            if next_page_token and status == "INVALID_REQUEST" and attempts < 5:
                attempts += 1
                time.sleep(2)
                continue
            break

        if status in {"REQUEST_DENIED", "OVER_QUERY_LIMIT"}:
            _raise_on_bad_status(payload, "Google Places Text Search")
        if status == "INVALID_REQUEST":
            if next_page_token:
                # If pagination token keeps failing, return what we already have.
                break
            _raise_on_bad_status(payload, "Google Places Text Search")
        if status == "ZERO_RESULTS":
            break

        results = payload.get("results", [])
        all_results.extend(results)

        next_page_token = payload.get("next_page_token")
        if not next_page_token:
            break

    return all_results[:max_results]


def get_place_details(
    *, api_key: str, place_id: str, timeout_seconds: int
) -> dict[str, Any]:
    params = {
        "key": api_key,
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website",
    }
    response = requests.get(DETAILS_URL, params=params, timeout=timeout_seconds)
    response.raise_for_status()
    payload = response.json()
    _raise_on_bad_status(payload, "Google Place Details")
    return payload.get("result", {})


def get_city_viewport(
    *, api_key: str, city: str, timeout_seconds: int
) -> tuple[float, float, float, float]:
    params = {"key": api_key, "address": city}
    response = requests.get(GEOCODE_URL, params=params, timeout=timeout_seconds)
    response.raise_for_status()
    payload = response.json()
    _raise_on_bad_status(payload, "Google Geocode")
    results = payload.get("results", [])
    if not results:
        raise ValueError(f"Google Geocode failed. No results for city '{city}'.")

    viewport = results[0].get("geometry", {}).get("viewport", {})
    northeast = viewport.get("northeast", {})
    southwest = viewport.get("southwest", {})
    return (
        float(southwest.get("lat")),
        float(southwest.get("lng")),
        float(northeast.get("lat")),
        float(northeast.get("lng")),
    )


def get_city_center_from_places(
    *, api_key: str, city: str, timeout_seconds: int
) -> tuple[float, float]:
    params = {"key": api_key, "query": city}
    response = requests.get(TEXT_SEARCH_URL, params=params, timeout=timeout_seconds)
    response.raise_for_status()
    payload = response.json()
    _raise_on_bad_status(payload, "Google Places Text Search")
    results = payload.get("results", [])
    if not results:
        raise ValueError(f"City center lookup failed. No results for city '{city}'.")
    location = results[0].get("geometry", {}).get("location", {})
    return float(location.get("lat")), float(location.get("lng"))


def approximate_viewport_from_center(
    *,
    center_lat: float,
    center_lng: float,
    city_span_km: float,
) -> tuple[float, float, float, float]:
    half_span_m = (city_span_km * 1000.0) / 2.0
    lat_delta = half_span_m / 111_000.0
    lng_delta = half_span_m / (111_000.0 * max(0.2, cos(radians(center_lat))))
    return (
        center_lat - lat_delta,
        center_lng - lng_delta,
        center_lat + lat_delta,
        center_lng + lng_delta,
    )


def _generate_grid_points(
    *,
    south_lat: float,
    west_lng: float,
    north_lat: float,
    east_lng: float,
    radius_meters: int,
) -> list[tuple[float, float]]:
    # Use overlap so nearby search circles cover gaps.
    step_meters = max(300, int(radius_meters * 1.2))
    lat_step = step_meters / 111_000.0
    center_lat = (south_lat + north_lat) / 2.0
    lng_step = step_meters / (111_000.0 * max(0.2, cos(radians(center_lat))))

    points: list[tuple[float, float]] = []
    lat = south_lat
    while lat <= north_lat:
        lng = west_lng
        while lng <= east_lng:
            points.append((round(lat, 6), round(lng, 6)))
            lng += lng_step
        lat += lat_step
    return points


def _nearby_search_page(
    *,
    api_key: str,
    location: str | None,
    radius_meters: int | None,
    place_type: str | None,
    keyword: str | None,
    pagetoken: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    params: dict[str, Any] = {"key": api_key}
    if pagetoken:
        params["pagetoken"] = pagetoken
    else:
        params["location"] = location
        params["radius"] = radius_meters
        if place_type:
            params["type"] = place_type
        if keyword:
            params["keyword"] = keyword
    response = requests.get(NEARBY_SEARCH_URL, params=params, timeout=timeout_seconds)
    response.raise_for_status()
    return response.json()


def nearby_search_city_grid(
    *,
    api_key: str,
    city: str,
    keyword: str,
    place_type: str,
    max_results: int,
    radius_meters: int,
    city_span_km: float,
    timeout_seconds: int,
) -> list[dict[str, Any]]:
    try:
        south_lat, west_lng, north_lat, east_lng = get_city_viewport(
            api_key=api_key, city=city, timeout_seconds=timeout_seconds
        )
    except ValueError:
        center_lat, center_lng = get_city_center_from_places(
            api_key=api_key, city=city, timeout_seconds=timeout_seconds
        )
        south_lat, west_lng, north_lat, east_lng = approximate_viewport_from_center(
            center_lat=center_lat,
            center_lng=center_lng,
            city_span_km=city_span_km,
        )
    points = _generate_grid_points(
        south_lat=south_lat,
        west_lng=west_lng,
        north_lat=north_lat,
        east_lng=east_lng,
        radius_meters=radius_meters,
    )

    dedup: dict[str, dict[str, Any]] = {}
    for lat, lng in points:
        if len(dedup) >= max_results:
            break
        location = f"{lat},{lng}"
        next_page_token: str | None = None
        while len(dedup) < max_results:
            if next_page_token:
                time.sleep(2)
            payload = _nearby_search_page(
                api_key=api_key,
                location=location,
                radius_meters=radius_meters,
                place_type=place_type,
                keyword=keyword,
                pagetoken=next_page_token,
                timeout_seconds=timeout_seconds,
            )
            status = payload.get("status", "")
            if status == "INVALID_REQUEST" and next_page_token:
                # Token not ready yet.
                time.sleep(2)
                payload = _nearby_search_page(
                    api_key=api_key,
                    location=location,
                    radius_meters=radius_meters,
                    place_type=place_type,
                    keyword=keyword,
                    pagetoken=next_page_token,
                    timeout_seconds=timeout_seconds,
                )
                status = payload.get("status", "")

            if status in {"REQUEST_DENIED", "OVER_QUERY_LIMIT"}:
                _raise_on_bad_status(payload, "Google Nearby Search")
            if status in {"ZERO_RESULTS", "INVALID_REQUEST"}:
                break

            for place in payload.get("results", []):
                place_id = place.get("place_id")
                if place_id:
                    dedup[place_id] = place
                    if len(dedup) >= max_results:
                        break

            next_page_token = payload.get("next_page_token")
            if not next_page_token:
                break

    return list(dedup.values())[:max_results]

