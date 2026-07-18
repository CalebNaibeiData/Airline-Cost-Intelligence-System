import pandas as pd
import json
from pathlib import Path

def get_latest_file(folder):
    base_path = Path(f"data/raw/{folder}")
    files = list(base_path.glob("*.json"))

    if not files:
        raise FileNotFoundError(f"No files found in {base_path}")

    return str(max(files, key=lambda x: x.stat().st_mtime))

def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# Directories
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