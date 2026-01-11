# Local Business Scraper

Generates a CSV of Canadian local service businesses by iterating over predefined industries and cities.

## Configuration

Create a `.env` file in the project root:

```
GOOGLE_API_KEY=<your_google_places_api_key>
SITE_INCLUSION=true
OUTPUT_FILE=local_businesses.csv
MAX_RESULTS_PER_SEARCH=200
PAGINATION_DELAY_SECONDS=2
DETAIL_DELAY_SECONDS=0.1
SEARCH_DELAY_SECONDS=0.5
```

- `SITE_INCLUSION=false` skips businesses without a website.  
- `MAX_RESULTS_PER_SEARCH` limits how many results are requested per industry/city search.
- The delay settings help tune request pacing for Google Places API pagination, place details, and search loops.

## Run

```bash
python scraper.py
```

The script outputs a single CSV with columns: `site_url,business_name,industry,company_name,city`.
