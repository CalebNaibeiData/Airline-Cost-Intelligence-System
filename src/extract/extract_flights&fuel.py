import requests
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import time

load_dotenv()

AVIATION_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
FUEL_API_KEY = os.getenv("FUEL_API_KEY")

if not AVIATION_API_KEY:
    raise ValueError("Missing AVIATIONSTACK_API_KEY in .env")

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
            print(f"Retry {attempt+1}: {e}")
            time.sleep(2 ** attempt)

    raise Exception("API request failed after retries")


def save_json(data, folder, prefix):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = BASE_DIR / folder / f"{prefix}_{timestamp}.json"

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Saved: {file_path}")
    return str(file_path)


def extract_flights():
    print("Fetching flights data...")

    params = {
        "access_key": AVIATION_API_KEY,
        "limit": 500
    }

    data = fetch_with_retry(FLIGHT_API_URL, params=params)

    return save_json(data, "flights", "flights")


def extract_fuel():
    print("Fetching fuel data...")

    headers = {
        "Authorization": f"Token {FUEL_API_KEY}"
    }

    params = {
        "by_code": "BRENT_CRUDE_USD"
    }

    data = fetch_with_retry(FUEL_API_URL, params=params, headers=headers)

    return save_json(data, "fuel", "fuel")


def run_extract():
    flights_file = extract_flights()
    fuel_file = extract_fuel()

    return {
        "flights": flights_file,
        "fuel": fuel_file
    }


if __name__ == "__main__":
    files = run_extract()
    print("Done:", files)