import requests
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import time
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime
from src.extract.extract_flights import fetch_flights_data
from src.transform import flatten_flight_json, clean_flights
from src.load.load import load



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
        "limit": 100
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


def get_latest_file(folder):
    base_path = Path(f"data/raw/{folder}")
    files = list(base_path.glob("*.json"))

    if not files:
        raise FileNotFoundError(f"No files found in {base_path}")

    return str(max(files, key=lambda x: x.stat().st_mtime))

def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def get_latest_file(folder):
    base_path = RAW_DIR / folder
    files = list(base_path.glob("*.json"))

    if not files:
        raise FileNotFoundError(f"No files found in {base_path}")

    return max(files, key=lambda x: x.stat().st_mtime)


def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def clean_flights(data):
    flights = data.get("data", [])
    df = pd.DataFrame(flights)

    if df.empty:
        print("No flight data found")
        return df

    # Flatten nested fields safely
    df["airline"] = df["airline"].apply(lambda x: x.get("iata") if isinstance(x, dict) else None)
    df["departure_airport"] = df["departure"].apply(lambda x: x.get("iata") if isinstance(x, dict) else None)
    df["arrival_airport"] = df["arrival"].apply(lambda x: x.get("iata") if isinstance(x, dict) else None)

    df["departure_time"] = df["departure"].apply(lambda x: x.get("scheduled") if isinstance(x, dict) else None)
    df["arrival_time"] = df["arrival"].apply(lambda x: x.get("scheduled") if isinstance(x, dict) else None)

    # Keep only useful columns
    df = df[
        [
            "flight_date",
            "flight_status",
            "airline",
            "flight",
            "departure_airport",
            "arrival_airport",
            "departure_time",
            "arrival_time",
        ]
    ]

    # Extract flight number safely
    df["flight_number"] = df["flight"].apply(lambda x: x.get("number") if isinstance(x, dict) else None)

    df.drop(columns=["flight"], inplace=True)

    return df


def run_transform():
    print("Starting transform...")

    file_path = get_latest_file("flights")
    print(f"Using file: {file_path}")

    data = load_json(file_path)

    df = clean_flights(data)

    if df.empty:
        print("No data to save")
        return

    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = PROCESSED_DIR / f"flights_processed_{timestamp}.csv"

    df.to_csv(output_file, index=False)

    print(f"Saved: {output_file}")


if __name__ == "__main__":
    run_transform()

def clean_flights(data):
    # Aviationstack returns data inside "data"
    flights = data.get("data", [])

    df = pd.DataFrame(flights)

    if df.empty:
        print("No flight data found")
        return df

    # Flatten nested columns
    df["airline"] = df["airline"].apply(lambda x: x.get("iata") if isinstance(x, dict) else None)
    df["departure"] = df["departure"].apply(lambda x: x.get("iata") if isinstance(x, dict) else None)
    df["arrival"] = df["arrival"].apply(lambda x: x.get("iata") if isinstance(x, dict) else None)

    # Select useful columns
    df = df[["flight_date", "airline", "departure", "arrival"]]

    # Clean
    df = df.dropna()
    df = df.drop_duplicates()

    df.columns = [
        "flight_date",
        "airline_code",
        "departure_iata",
        "arrival_iata"
    ]

    return df



def clean_fuel(data):
    # Oil API structure
    prices = data.get("data", {})

    df = pd.DataFrame([prices])  # single row

    if df.empty:
        print("No fuel data found")
        return df

    # Example: adjust depending on API response
    df = df.rename(columns={
        "price": "fuel_price_usd"
    })

    df["fuel_type"] = "BRENT_CRUDE"

    return df[["fuel_price_usd", "fuel_type"]]




def join_data(flights_df, fuel_df):
    if flights_df.empty or fuel_df.empty:
        print("One dataset is empty")
        return pd.DataFrame()

    # Add fuel price to every flight
    fuel_price = fuel_df.iloc[0]["fuel_price_usd"]

    flights_df["fuel_price_usd"] = fuel_price

    return flights_df



def run_transform(files_dict):
    flights_raw = load_json(files_dict["flights"])
    fuel_raw = load_json(files_dict["fuel"])

    flights_df = clean_flights(flights_raw)
    fuel_df = clean_fuel(fuel_raw)

    final_df = join_data(flights_df, fuel_df)

    print("Final rows:", len(final_df))
    print(final_df.head())

    return final_df


if __name__ == "__main__":
    files = {
    "flights": get_latest_file("flights"),
    "fuel": get_latest_file("fuel")
}

    df = run_transform(files)



engine = create_engine(DB_URI)


file = max(Path("data/processed").glob("*.csv"), key=lambda x: x.stat().st_mtime)
df = pd.read_csv(file)

df.to_sql(
    "airline_data",
    engine,
    if_exists="append",
    index=False
)

print("Data loaded to PostgreSQL")



def run_pipeline():
    today = datetime.now()

    # Extract
    raw_data = fetch_flights_data(today)
    print("Extract done")

    # Transform
    df = flatten_flight_json(raw_data)
    df = clean_flights(df)
    print(f"Transform done: {len(df)} rows")

    # Load
    load(df)
    print("Load done")


if __name__ == "__main__":
    run_pipeline()