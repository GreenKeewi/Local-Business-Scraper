import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set
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

PLACE_DETAIL_FIELDS = "place_id,name,website,formatted_phone_number"
CSV_HEADERS = ["site_url", "business_name", "industry", "company_name", "city", "phone_number"]


def load_env_file(path: Path = Path(".env")) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if not key or not all(ch.isalnum() or ch == "_" for ch in key):
            continue
        if key not in os.environ:
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

    def parse_float(value: Optional[str], default: float) -> float:
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default

    pagination_delay = parse_float(os.environ.get("PAGINATION_DELAY_SECONDS", "2"), 2.0)
    detail_delay = parse_float(os.environ.get("DETAIL_DELAY_SECONDS", "0.1"), 0.1)
    search_delay = parse_float(os.environ.get("SEARCH_DELAY_SECONDS", "0.5"), 0.5)

    return {
        "api_key": api_key,
        "site_inclusion": site_inclusion,
        "output_file": output_file,
        "max_results_per_search": max_results,
        "pagination_delay": pagination_delay,
        "detail_delay": detail_delay,
        "search_delay": search_delay,
    }


def fetch_json(url: str, params: Dict[str, str]) -> Optional[Dict[str, object]]:
    encoded = f"{url}?{urlencode(params)}"
    request = Request(encoded, headers={"Accept": "application/json"})
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError) as exc:
        print(f"Request to {url} failed: {exc}", file=sys.stderr)
        return None


def search_places(
    api_key: str, industry: str, city: str, max_results: int, pagination_delay: float
) -> List[Dict[str, object]]:
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    query = f"{industry} in {city}"
    params: Dict[str, str] = {"query": query, "key": api_key}
    results: List[Dict[str, object]] = []
    next_page_token: Optional[str] = None

    while len(results) < max_results:
        if next_page_token:
            params["pagetoken"] = next_page_token
            time.sleep(pagination_delay)
        payload = fetch_json(url, params)
        if not payload or payload.get("status") not in {"OK", "ZERO_RESULTS"}:
            status = None if not payload else payload.get("status")
            print(f"Search '{query}' failed with status {status}", file=sys.stderr)
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
        "fields": PLACE_DETAIL_FIELDS,
    }
    payload = fetch_json(url, params)
    if payload and payload.get("status") == "OK":
        return payload.get("result", {})
    return {}


def main() -> None:
    config = get_config()
    api_key: str = config["api_key"]  # type: ignore[assignment]
    site_inclusion: bool = config["site_inclusion"]  # type: ignore[assignment]
    output_file = Path(config["output_file"])  # type: ignore[arg-type]
    max_results: int = config["max_results_per_search"]  # type: ignore[assignment]
    pagination_delay: float = config["pagination_delay"]  # type: ignore[assignment]
    detail_delay: float = config["detail_delay"]  # type: ignore[assignment]
    search_delay: float = config["search_delay"]  # type: ignore[assignment]

    seen_places: Set[str] = set()
    seen_by_name_city: Set[str] = set()

    with output_file.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
        writer.writeheader()

        for city in CITIES:
            for industry in INDUSTRIES:
                print(f"Searching '{industry}' in {city}...")
                places = search_places(api_key, industry, city, max_results, pagination_delay)
                for place in places:
                    place_id = place.get("place_id")
                    if not place_id or place_id in seen_places:
                        continue

                    details = fetch_place_details(api_key, place_id)
                    if not details:
                        print(f"No details found for place_id={place_id}", file=sys.stderr)
                        time.sleep(detail_delay)
                        continue
                    website = str(details.get("website") or "")
                    name = str(details.get("name") or place.get("name") or "").strip()
                    phone = str(details.get("formatted_phone_number") or "")

                    if not name:
                        continue
                    if not site_inclusion and not website:
                        continue

                    # Deduplicate by name + city combination
                    dedup_key = f"{name}|{city}"
                    if dedup_key in seen_by_name_city:
                        continue

                    seen_places.add(place_id)
                    seen_by_name_city.add(dedup_key)
                    writer.writerow(
                        {
                            "site_url": website,
                            "business_name": name,
                            "industry": industry,
                            "company_name": name,  # mirrors business_name per output spec
                            "city": city,
                            "phone_number": phone,
                        }
                    )
                    time.sleep(detail_delay)
                time.sleep(search_delay)
            csvfile.flush()
            print(f"Completed city {city}. Total rows: {len(seen_places)}")

if __name__ == "__main__":
    main()
