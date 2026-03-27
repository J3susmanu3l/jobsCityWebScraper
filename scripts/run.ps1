param(
  [string]$City = "Denver, CO",
  [string]$Query = "restaurants",
  [int]$MaxResults = 40,
  [ValidateSet("text", "city-grid")]
  [string]$Mode = "text"
)

python -m jobs_scraper.main --city $City --query $Query --max-results $MaxResults --mode $Mode

