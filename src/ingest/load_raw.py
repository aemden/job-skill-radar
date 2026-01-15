import pathlib
import duckdb
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW_PATH = REPO_ROOT / "data" / "raw" / "job_postings.csv"
DB_PATH = REPO_ROOT / "warehouse" / "analytics.duckdb"

def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw file not found: {RAW_PATH}")

    df = pd.read_csv(RAW_PATH)
    print(f"Loaded raw rows: {len(df):,} | cols: {len(df.columns)}")
    print("Columns:", list(df.columns))

    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE OR REPLACE TABLE raw_job_postings AS SELECT * FROM df")
    con.close()

    print(f"Wrote DuckDB table raw_job_postings to {DB_PATH}")

if __name__ == "__main__":
    main()
