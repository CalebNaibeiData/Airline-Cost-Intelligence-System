import py_compile
files = [
    'airline_etl.py',
    'dags/airline_airflow_dags.py',
    'src/transform/transform_data.py',
    'src/transform/__init__.py',
    'src/extract/extract_flights.py',
    'src/load/load.py',
]
for path in files:
    py_compile.compile(path, doraise=True)
    print(f'OK {path}')
