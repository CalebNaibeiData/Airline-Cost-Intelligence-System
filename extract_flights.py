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

def fetch_flights_data(date):
    params = {
        "access_key": os.getenv("AVIATIONSTACK_API_KEY"),
        "date": date.strftime("%Y-%m-%d"),
        "limit": 500
    }

    response = requests.get(API_URL, params=params)
    data = response.json()

    return data

today = datetime.now()

raw_data = fetch_flights_data(today)

print(type(raw_data))
print(raw_data.keys())


