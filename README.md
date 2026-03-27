# Jobs/Business Scraper Starter

This project collects local business data for a chosen city and category, then exports:

- company name
- phone number
- email (from website crawl when available)
- website
- address
- Google place id

## Important note

This starter uses the **Google Places API** for listing/place details instead of browser automation scraping, which is generally more stable and compliance-friendly. You are responsible for using APIs and collected data according to the providers' terms and local laws.

## Project structure

```text
jobsWebScraper/
  src/jobs_scraper/
    config.py
    email_finder.py
    exporter.py
    google_places.py
    main.py
    models.py
  tests/
  scripts/
  output/
  .env.example
  pyproject.toml
  README.md
```

## 1) Requirements

- Python 3.10+
- A Google Maps Platform API key with Places API enabled

## 2) Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
copy .env.example .env
```

Then open `.env` and set `GOOGLE_MAPS_API_KEY`.

## 3) Run

```bash
python -m jobs_scraper.main --city "Denver, CO" --query "restaurants" --max-results 50
```

For broader city coverage (near-complete strategy):

```bash
python -m jobs_scraper.main --city "Denver, CO" --query "restaurants" --mode city-grid --place-type restaurant --radius-meters 1200 --max-results 1000 --skip-email-crawl
```

Notes:

- `text` mode is fast but usually capped around 60.
- `city-grid` mode scans many points across the city and deduplicates by `place_id`.
- If Geocoding API is not enabled, city-grid falls back to Places-based center + `--city-span-km`.
- Start with `--skip-email-crawl` for speed, then enrich emails in a second run if needed.

Or PowerShell helper:

```powershell
.\scripts\run.ps1 -City "Denver, CO" -Query "restaurants" -MaxResults 50
```

City grid via script:

```powershell
.\scripts\run.ps1 -City "Denver, CO" -Query "restaurants" -MaxResults 500 -Mode "city-grid"
```

## 4) Output

Files are generated in `output/`:

- `*.csv`
- `*.json`

## 5) Common examples

```bash
python -m jobs_scraper.main --city "Austin, TX" --query "roofing companies" --max-results 80
python -m jobs_scraper.main --city "Chicago, IL" --query "dental clinic" --skip-email-crawl
```

## 6) Next upgrades (optional)

- Add deduplication by domain + phone
- Add retries/backoff for rate limits
- Add proxy support for website crawling
- Add SQLite/PostgreSQL persistence
- Add Dockerfile and scheduled runs

