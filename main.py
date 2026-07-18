from datetime import datetime
from src.extract_flights import fetch_flights_data
from src.transform import flatten_flight_json, clean_flights
from src.load import load


def run_pipeline():
    today = datetime.now()

    # Extract
    raw_data = fetch_flights_data(today)
    print("✅ Extract done")

    # Transform
    df = flatten_flight_json(raw_data)
    df = clean_flights(df)
    print(f"✅ Transform done: {len(df)} rows")

    # Load
    load(df)
    print("✅ Load done")


if __name__ == "__main__":
    run_pipeline()