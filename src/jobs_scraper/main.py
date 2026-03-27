from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .config import load_settings
from .email_finder import find_email_from_website
from .exporter import export_csv, export_json
from .google_places import get_place_details, nearby_search_city_grid, text_search_places
from .models import BusinessRecord


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect business leads by city and category."
    )
    parser.add_argument("--city", help="City, state or country. Example: Denver, CO")
    parser.add_argument("--query", help="Business category. Example: restaurants")
    parser.add_argument("--max-results", type=int, help="Maximum number of businesses")
    parser.add_argument(
        "--mode",
        choices=["text", "city-grid"],
        default="text",
        help="Search strategy: text (fast, ~60 max) or city-grid (broader city coverage)",
    )
    parser.add_argument(
        "--place-type",
        default="restaurant",
        help="Google place type used in city-grid mode (example: restaurant)",
    )
    parser.add_argument(
        "--radius-meters",
        type=int,
        default=1200,
        help="Nearby Search radius in meters for city-grid mode",
    )
    parser.add_argument(
        "--city-span-km",
        type=float,
        default=24.0,
        help="Approximate city scan width in km for city-grid fallback mode",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Folder where CSV/JSON files are written",
    )
    parser.add_argument(
        "--skip-email-crawl",
        action="store_true",
        help="Skip website crawl for email extraction",
    )
    return parser


def scrape_businesses(
    *,
    city: str,
    query: str,
    max_results: int,
    mode: str,
    place_type: str,
    radius_meters: int,
    city_span_km: float,
    output_dir: Path,
    skip_email_crawl: bool,
) -> tuple[Path, Path, int]:
    settings = load_settings()
    if mode == "city-grid":
        places = nearby_search_city_grid(
            api_key=settings.google_maps_api_key,
            city=city,
            keyword=query,
            place_type=place_type,
            max_results=max_results,
            radius_meters=radius_meters,
            city_span_km=city_span_km,
            timeout_seconds=settings.timeout_seconds,
        )
    else:
        places = text_search_places(
            api_key=settings.google_maps_api_key,
            query=query,
            city=city,
            max_results=max_results,
            timeout_seconds=settings.timeout_seconds,
        )

    rows: list[BusinessRecord] = []
    for place in places:
        place_id = place.get("place_id", "")
        if not place_id:
            continue

        details = get_place_details(
            api_key=settings.google_maps_api_key,
            place_id=place_id,
            timeout_seconds=settings.timeout_seconds,
        )
        website = details.get("website")
        email = None
        if website and not skip_email_crawl:
            email = find_email_from_website(
                site_url=website, timeout_seconds=settings.timeout_seconds
            )

        rows.append(
            BusinessRecord(
                company_name=details.get("name") or place.get("name", ""),
                category_query=query,
                city=city,
                phone=details.get("formatted_phone_number"),
                email=email,
                website=website,
                address=details.get("formatted_address")
                or place.get("formatted_address"),
                google_place_id=place_id,
            )
        )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_city = city.replace(" ", "_").replace(",", "")
    safe_query = query.replace(" ", "_")
    base_name = f"{safe_query}_{safe_city}_{stamp}"
    csv_file = output_dir / f"{base_name}.csv"
    json_file = output_dir / f"{base_name}.json"

    export_csv(rows, csv_file)
    export_json(rows, json_file)
    return csv_file, json_file, len(rows)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        settings = load_settings()
        city = args.city or settings.default_city
        query = args.query or settings.default_query
        max_results = args.max_results or settings.max_results
        output_dir = Path(args.output_dir)
        csv_file, json_file, total = scrape_businesses(
            city=city,
            query=query,
            max_results=max_results,
            mode=args.mode,
            place_type=args.place_type,
            radius_meters=args.radius_meters,
            city_span_km=args.city_span_km,
            output_dir=output_dir,
            skip_email_crawl=args.skip_email_crawl,
        )
    except ValueError as exc:
        raise SystemExit(f"Error: {exc}") from exc

    print(f"Saved {total} records")
    print(f"CSV:  {csv_file}")
    print(f"JSON: {json_file}")


if __name__ == "__main__":
    main()

