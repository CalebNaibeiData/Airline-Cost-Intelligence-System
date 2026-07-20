import json
import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine

from src.extract.extract_flights import fetch_flights_data
from src.load.load import load
from src.transform import clean_flights, flatten_flight_json


# -----------------------
# ENV SETUP
# -----------------------
load_dotenv()

DB_URI = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

AVIATION_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
FUEL_API_KEY = os.getenv("FUEL_API_KEY")

if not AVIATION_API_KEY:
    raise ValueError("Missing AVIATIONSTACK_API_KEY")


FLIGHT_API_URL = "http://api.aviationstack.com/v1/flights"
FUEL_API_URL = "https://api.oilpriceapi.com/v1/prices/latest"


# -----------------------
# PATHS
# -----------------------
BASE_DIR = Path("data/raw")
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

(BASE_DIR / "flights").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "fuel").mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------
# HELPERS
# -----------------------
def fetch_with_retry(url, params=None, headers=None, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            print(f"Retry {attempt + 1}: {error}")
            time.sleep(2 ** attempt)

    raise Exception("API request failed after retries")


def save_json(data, folder, prefix):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = BASE_DIR / folder / f"{prefix}_{timestamp}.json"

    with open(file_path, "w") as handle:
        json.dump(data, handle, indent=4)

    print(f"Saved: {file_path}")
    return str(file_path)


def get_latest_file(folder):
    base_path = RAW_DIR / folder
    files = list(base_path.glob("*.json"))

    if not files:
        raise FileNotFoundError(f"No files found in {base_path}")

    return max(files, key=lambda x: x.stat().st_mtime)


def load_json(file_path):
    with open(file_path, "r") as handle:
        return json.load(handle)


# -----------------------
# EXTRACT
# -----------------------
def extract_flights():
    print("Fetching flights data...")
    params = {"access_key": AVIATION_API_KEY, "limit": 100}
    data = fetch_with_retry(FLIGHT_API_URL, params=params)
    return save_json(data, "flights", "flights")


def extract_fuel():
    print("Fetching fuel data...")
    headers = {"Authorization": f"Token {FUEL_API_KEY}"}
    params = {"by_code": "BRENT_CRUDE_USD"}
    data = fetch_with_retry(FUEL_API_URL, params=params, headers=headers)
    return save_json(data, "fuel", "fuel")


def run_extract():
    flights_file = extract_flights()
    fuel_file = extract_fuel()
    return {"flights": flights_file, "fuel": fuel_file}


# -----------------------
# TRANSFORM
# -----------------------
def clean_fuel(data):
    prices = data.get("data", {})
    df = pd.DataFrame([prices])

    if df.empty:
        print("No fuel data found")
        return df

    df = df.rename(columns={"price": "fuel_price_usd"})
    df["fuel_type"] = "BRENT_CRUDE"
    return df[["fuel_price_usd", "fuel_type"]]


def join_data(flights_df, fuel_df):
    if flights_df.empty or fuel_df.empty:
        print("One dataset is empty")
        return pd.DataFrame()

    fuel_price = fuel_df.iloc[0]["fuel_price_usd"]
    flights_df["fuel_price_usd"] = fuel_price
    return flights_df


def run_transform(files_dict=None):
    if files_dict is None:
        files_dict = {
            "flights": get_latest_file("flights"),
            "fuel": get_latest_file("fuel"),
        }

    flights_raw = load_json(files_dict["flights"])
    fuel_raw = load_json(files_dict["fuel"])

    flights_df = clean_flights(flights_raw)
    fuel_df = clean_fuel(fuel_raw)

    final_df = join_data(flights_df, fuel_df)

    print("Final rows:", len(final_df))
    return final_df


# -----------------------
# LOAD (OPTIONAL HELPER)
# -----------------------
def load_to_postgres(csv_path=None):
    engine = create_engine(DB_URI)

    if csv_path:
        df = pd.read_csv(csv_path)
    else:
        files = list(PROCESSED_DIR.glob("*.csv"))

        if not files:
            raise FileNotFoundError("No processed CSV files found")

        latest_file = max(files, key=lambda x: x.stat().st_mtime)
        df = pd.read_csv(latest_file)

    df.to_sql(
        "airline_data",
        engine,
        if_exists="append",
        index=False,
    )

    engine.dispose()
    print("Data loaded to PostgreSQL")


# -----------------------
# OPTIONAL LOCAL TEST
# -----------------------
if __name__ == "__main__":
    files = run_extract()
    df = run_transform(files)

    if not df.empty:
        out = PROCESSED_DIR / "test_output.csv"
        df.to_csv(out, index=False)
        load_to_postgres(out)s