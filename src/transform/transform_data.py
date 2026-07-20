import pandas as pd


def flatten_flight_json(data):
    flights = data.get("data", []) if isinstance(data, dict) else []
    return pd.DataFrame(flights)


def clean_flights(data):
    if data is None:
        return pd.DataFrame()

    if isinstance(data, dict):
        data = flatten_flight_json(data)

    if getattr(data, "empty", True):
        return data

    cleaned = data.copy()

    if "airline" in cleaned.columns:
        cleaned["airline"] = cleaned["airline"].apply(
            lambda x: x.get("iata") if isinstance(x, dict) else None
        )

    if "departure" in cleaned.columns:
        cleaned["departure_airport"] = cleaned["departure"].apply(
            lambda x: x.get("iata") if isinstance(x, dict) else None
        )
        cleaned["departure_time"] = cleaned["departure"].apply(
            lambda x: x.get("scheduled") if isinstance(x, dict) else None
        )

    if "arrival" in cleaned.columns:
        cleaned["arrival_airport"] = cleaned["arrival"].apply(
            lambda x: x.get("iata") if isinstance(x, dict) else None
        )
        cleaned["arrival_time"] = cleaned["arrival"].apply(
            lambda x: x.get("scheduled") if isinstance(x, dict) else None
        )

    if "flight" in cleaned.columns:
        cleaned["flight_number"] = cleaned["flight"].apply(
            lambda x: x.get("number") if isinstance(x, dict) else None
        )

    selected_columns = [
        "flight_date",
        "flight_status",
        "airline",
        "flight_number",
        "departure_airport",
        "arrival_airport",
        "departure_time",
        "arrival_time",
    ]
    available_columns = [col for col in selected_columns if col in cleaned.columns]
    return cleaned[available_columns].copy()


__all__ = ["flatten_flight_json", "clean_flights"]