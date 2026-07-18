from sqlalchemy import create_engine
import pandas as pd
import os
from dotenv import load_dotenv
from pathlib import Path



load_dotenv()


DB_URI = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

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