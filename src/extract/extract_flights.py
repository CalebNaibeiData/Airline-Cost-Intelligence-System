import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

AVIATION_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
FUEL_API_KEY = os.getenv("FUEL_API_KEY")

FLIGHT_API_URL = "http://api.aviationstack.com/v1/flights"
FUEL_API_URL = "https://api.oilpriceapi.com/v1/prices/latest"

BASE_DIR = Path("data/raw")
(BASE_DIR / "flights").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "fuel").mkdir(parents=True, exist_ok=True)


def fetch_with_retry(url, params=None, headers=None, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Retry {attempt + 1}: {e}")
            time.sleep(2 ** attempt)
    raise Exception("API request failed after retries")


def save_json(data, folder, prefix):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = BASE_DIR / folder / f"{prefix}_{timestamp}.json"
    with open(file_path, "w") as handle:
        json.dump(data, handle, indent=4)
    print(f"Saved: {file_path}")
    return str(file_path)


def extract_flights():
    print("Fetching flights data...")
    if not AVIATION_API_KEY:
        raise ValueError("Missing AVIATIONSTACK_API_KEY in .env")

    params = {"access_key": AVIATION_API_KEY, "limit": 100}
    data = fetch_with_retry(FLIGHT_API_URL, params=params)
    return save_json(data, "flights", "flights")


def extract_fuel():
    print("Fetching fuel data...")
    if not FUEL_API_KEY:
        raise ValueError("Missing FUEL_API_KEY in .env")

    headers = {"Authorization": f"Token {FUEL_API_KEY}"}
    params = {"by_code": "BRENT_CRUDE_USD"}
    data = fetch_with_retry(FUEL_API_URL, params=params, headers=headers)
    return save_json(data, "fuel", "fuel")


def fetch_flights_data(today=None):
    flights_dir = BASE_DIR / "flights"
    latest_file = None
    if flights_dir.exists():
        candidates = list(flights_dir.glob("*.json"))
        if candidates:
            latest_file = max(candidates, key=lambda path: path.stat().st_mtime)

    if latest_file is not None:
        with open(latest_file, "r") as handle:
            return json.load(handle)

    return extract_flights()
