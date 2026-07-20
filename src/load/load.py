from pathlib import Path


def load(df):
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "flights_loaded.csv"
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")
    return str(output_path)
