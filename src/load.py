import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

TABLE_NAME = "flights"

DB_URI = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)


def load(df: pd.DataFrame):
    if df.empty:
        print("No data to load")
        return

    engine = create_engine(DB_URI)

    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="append",
        index=False
    )

    print(f"Loaded {len(df)} rows")