from datetime import date, timedelta

import hashlib
import pathlib
import re

import duckdb
import pandas as pd

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "warehouse" / "analytics.duckdb"

def _clean_text(x):
    if pd.isna(x):
        return ""
    s = str(x)
    s = s.replace("\r", " ").replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _make_job_id(row) -> str:
    key = "|".join([
        _clean_text(row.get("Title")),
        _clean_text(row.get("Company")),
        _clean_text(row.get("Location")),
        _clean_text(row.get("Date")),
        _clean_text(row.get("Links")),
    ])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

def _role_family(title: str) -> str:
    t = title.lower()
    # simple rules; you'll refine later
    if "data engineer" in t:
        return "data_engineer"
    if "data analyst" in t or "business analyst" in t:
        return "data_analyst"
    if "data scientist" in t:
        return "data_scientist"
    if "machine learning" in t:
        return "ml_engineer"
    if "bi " in t or "business intelligence" in t:
        return "bi"
    return "other"

def parse_indeed_date(s: str, reference: date) -> date | None:
    """
    Convert Indeed-style strings like:
      - '30+ days ago'
      - '3 days ago'
      - '1 day ago'
      - 'Today'
      - 'Just posted'
    into a real date using a reference date (dataset snapshot date).
    """
    if s is None:
        return None
    t = str(s).strip().lower()
    if not t:
        return None

    # common exact-ish strings
    if "today" in t or "just posted" in t:
        return reference

    # patterns like "30+ days ago", "3 days ago", "1 day ago"
    m = re.search(r"(\d+)\s*\+?\s*day", t)
    if m:
        days = int(m.group(1))
        return reference - timedelta(days=days)

    # fallback: try normal parsing
    dt = pd.to_datetime(s, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.date()


def main() -> None:
    con = duckdb.connect(str(DB_PATH))

    df = con.execute("SELECT * FROM raw_job_postings").df()

    # Drop index-like column if present
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    # Clean text fields
    for col in ["Title", "Company", "Location", "Salary", "Description", "Links", "Descriptions", "Date"]:
        if col in df.columns:
            df[col] = df[col].apply(_clean_text)

    # Create job_id
    df["job_id"] = df.apply(_make_job_id, axis=1)

    # The dataset is a snapshot from Nov 20, 2022 (per Kaggle description)
    reference_date = date(2022, 11, 20)
    df["posted_date_raw"] = df["Date"]
    df["posted_date"] = df["Date"].apply(lambda x: parse_indeed_date(x, reference_date))

    # Role family
    df["role_family"] = df["Title"].apply(_role_family)

    # Prefer full description if available
    df["description_full"] = df.get("Descriptions", "").fillna("").apply(_clean_text)
    df["description_short"] = df.get("Description", "").fillna("").apply(_clean_text)

    # Keep a clean set of columns for downstream
    out = df[[
        "job_id",
        "Title",
        "Company",
        "Location",
        "Rating",
        "posted_date",
        "posted_date_raw",
        "Salary",
        "Links",
        "description_short",
        "description_full",
        "role_family",
    ]].rename(columns={
        "Title": "title",
        "Company": "company",
        "Location": "location",
        "Rating": "rating",
        "Salary": "salary_raw",
        "Links": "job_link",
    })

    # Dedupe on job_id
    out = out.drop_duplicates(subset=["job_id"]).reset_index(drop=True)

    con.execute("CREATE OR REPLACE TABLE stg_job_postings AS SELECT * FROM out")
    con.close()

    print(f"stg_job_postings rows: {len(out):,}")
    print(out.head(3).to_string(index=False))

if __name__ == "__main__":
    main()
