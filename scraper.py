import csv
import json
import os
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

INDUSTRIES: List[str] = [
    "Law Firm",
    "Dental Clinic",
    "Orthodontist",
    "Physiotherapy Clinic",
    "Chiropractor",
    "Med Spa",
    "Roofing Company",
    "HVAC Company",
    "Plumber",
    "Electrician",
    "Landscaping Company",
    "Pest Control Service",
    "Home Renovation Contractor",
    "Accounting Firm",
    "Real Estate Agency",
    "Auto Repair Shop",
    "Cleaning Service",
    "IT Support Company",
]

CITIES: List[str] = [
    "Toronto, ON",
    "Mississauga, ON",
    "Brampton, ON",
    "Markham, ON",
    "Vaughan, ON",
    "Hamilton, ON",
    "London, ON",
    "Kitchener, ON",
    "Waterloo, ON",
    "Guelph, ON",
    "Oakville, ON",
    "Burlington, ON",
    "Milton, ON",
    "Ottawa, ON",
    "Montreal, QC",
    "Quebec City, QC",
    "Laval, QC",
    "Vancouver, BC",
    "Surrey, BC",
    "Burnaby, BC",
    "Richmond, BC",
    "Victoria, BC",
    "Kelowna, BC",
    "Calgary, AB",
    "Edmonton, AB",
    "Red Deer, AB",
    "Winnipeg, MB",
    "Regina, SK",
    "Saskatoon, SK",
    "Halifax, NS",
    "Moncton, NB",
    "Fredericton, NB",
    "Charlottetown, PE",
    "St. John’s, NL",
]


def load_env_file(path: Path = Path(".env")) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key and key not in os.environ:
            os.environ[key] = value


def get_config() -> Dict[str, object]:
    load_env_file()
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is required in environment or .env file.")

    site_inclusion = os.environ.get("SITE_INCLUSION", "true").lower() == "true"
    output_file = os.environ.get("OUTPUT_FILE", "local_businesses.csv")
    try:
        max_results = int(os.environ.get("MAX_RESULTS_PER_SEARCH", "200"))
    except ValueError:
        max_results = 200

    return {
        "api_key": api_key,
        "site_inclusion": site_inclusion,
        "output_file": output_file,
        "max_results_per_search": max_results,
    }


def fetch_json(url: str, params: Dict[str, str]) -> Optional[Dict[str, object]]:
    encoded = f"{url}?{urlencode(params)}"
    request = Request(encoded, headers={"Accept": "application/json"})
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError):
        return None


def search_places(api_key: str, industry: str, city: str, max_results: int) -> List[Dict[str, object]]:
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    query = f"{industry} in {city}"
    params: Dict[str, str] = {"query": query, "key": api_key}
    results: List[Dict[str, object]] = []
    next_page_token: Optional[str] = None

    while len(results) < max_results:
        if next_page_token:
            params["pagetoken"] = next_page_token
            time.sleep(2)
        payload = fetch_json(url, params)
        if not payload or payload.get("status") not in {"OK", "ZERO_RESULTS"}:
            break
        batch = payload.get("results", [])
        results.extend(batch)
        if payload.get("next_page_token") and len(results) < max_results:
            next_page_token = payload["next_page_token"]
            continue
        break

    return results[:max_results]


def fetch_place_details(api_key: str, place_id: str) -> Dict[str, object]:
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "key": api_key,
        "fields": "place_id,name,website",
    }
    payload = fetch_json(url, params)
    if payload and payload.get("status") == "OK":
        return payload.get("result", {})
    return {}


def write_csv(path: Path, rows: Iterable[Dict[str, str]]) -> None:
    headers = ["site_url", "business_name", "industry", "company_name", "city"]
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    config = get_config()
    api_key: str = config["api_key"]  # type: ignore[assignment]
    site_inclusion: bool = config["site_inclusion"]  # type: ignore[assignment]
    output_file = Path(config["output_file"])  # type: ignore[arg-type]
    max_results: int = config["max_results_per_search"]  # type: ignore[assignment]

    seen_places: set[str] = set()
    output_rows: List[Dict[str, str]] = []

    for city in CITIES:
        for industry in INDUSTRIES:
            places = search_places(api_key, industry, city, max_results)
            for place in places:
                place_id = place.get("place_id")
                if not place_id or place_id in seen_places:
                    continue

                details = fetch_place_details(api_key, place_id)
                website = str(details.get("website") or "")
                name = str(details.get("name") or place.get("name") or "").strip()

                if not name:
                    continue
                if not website and not site_inclusion:
                    continue

                seen_places.add(place_id)
                output_rows.append(
                    {
                        "site_url": website,
                        "business_name": name,
                        "industry": industry,
                        "company_name": name,
                        "city": city,
                    }
                )

    write_csv(output_file, output_rows)


if __name__ == "__main__":
    main()
