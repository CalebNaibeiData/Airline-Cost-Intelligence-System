import pandas as pd


def flatten_flight_json(raw_json: dict) -> pd.DataFrame:
    records = raw_json.get("data", [])
    return pd.json_normalize(records)


def clean_flights(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates()

    df.columns = [c.strip().lower().replace(".", "_") for c in df.columns]

    if "departure_iata" in df.columns and "arrival_iata" in df.columns:
        df = df.dropna(subset=["departure_iata", "arrival_iata"])

    if "flight_date" in df.columns:
        df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")

    return df