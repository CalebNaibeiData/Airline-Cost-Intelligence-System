 
import logging
from datetime import datetime, timedelta
from pathlib import Path
 
from airflow import DAG
from airflow.operators.python import PythonOperator
 
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
 

def extract_flights(**context) -> str:
    logging.info("Extracting flights data")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    file_path = RAW_DIR / "flights.json"
 
    
    file_path.write_text('{"flights": []}')
 
    logging.info("Saved flights file: %s", file_path)
    return str(file_path)
 
 
def extract_fuel(**context) -> str:
    logging.info("Extracting fuel data")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    file_path = RAW_DIR / "fuel.json"
 
   
   
 
    logging.info("Saved fuel file: %s", file_path)
    return str(file_path)
 
 
def run_transform(**context) -> str:
    logging.info("Transform step started")
    ti = context["ti"]
    flights_file = ti.xcom_pull(task_ids="extract_flights")
    fuel_file = ti.xcom_pull(task_ids="extract_fuel")
 
    if not flights_file or not fuel_file:
        raise ValueError("Missing input files from extract tasks")
 
    logging.info("Flights file: %s", flights_file)
    logging.info("Fuel file: %s", fuel_file)
 
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ts = context["ts_nodash"]
    output_file = PROCESSED_DIR / f"processed_{ts}.csv"
 
    with open(output_file, "w") as f:
        f.write("source\nflights+fuel\n")
 
    logging.info("Saved processed file: %s", output_file)
    return str(output_file)
 

def load(**context) -> None:
    logging.info("Load step started")
    ti = context["ti"]
    processed_file = ti.xcom_pull(task_ids="transform")
 
    if not processed_file:
        raise ValueError("No processed file received from transform task")
 
    logging.info("Loading file: %s", processed_file)
 
   
    logging.info("Load completed")
 

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}
 
with DAG(
    dag_id="flights_fuel_etl",
    default_args=default_args,
    start_date=datetime(2026, 7, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["etl"],
) as dag:
 
    extract_flights_task = PythonOperator(
        task_id="extract_flights",
        python_callable=extract_flights,
    )
 
    extract_fuel_task = PythonOperator(
        task_id="extract_fuel",
        python_callable=extract_fuel,
    )
 
    transform_task = PythonOperator(
        task_id="transform",
        python_callable=run_transform,
    )
 
    load_task = PythonOperator(
        task_id="load",
        python_callable=load,
    )
 
    [extract_flights_task, extract_fuel_task] >> transform_task >> load_task