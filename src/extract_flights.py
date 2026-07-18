import requests
import pandas as pd
import os
import json
from datetime import datetime
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

API_URL = "http://api.aviationstack.com/v1/flights"

DB_URI = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

TABLE_NAME = "flights"

def fetch_flights_data(date: datetime) -> dict:
    api_key = os.getenv("AVIATIONSTACK_API_KEY")

    if not api_key:
        raise ValueError("Missing API key")
    
    params = {
        "access_key": os.getenv("AVIATIONSTACK_API_KEY"),
        "date": date.strftime("%Y-%m-%d"),
        "limit": 500
    }

    response = requests.get(API_URL, params=params)
    response.raise_for_status()

    return response.json()



