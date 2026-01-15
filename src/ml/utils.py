from __future__ import annotations

import duckdb
import pandas as pd


def connect_duckdb(db_path: str) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(db_path, read_only=False)


def fetch_postings(
    con: duckdb.DuckDBPyConnection,
    table: str,
    id_col: str,
    title_col: str,
    loc_col: str,
    desc_col: str,
    limit: int | None = None,
) -> pd.DataFrame:
    sql = f"""
    SELECT
      {id_col} AS posting_id,
      {title_col} AS title,
      {loc_col} AS location,
      {desc_col} AS description
    FROM {table}
    """
    if limit is not None:
        sql += f" LIMIT {int(limit)}"

    df = con.execute(sql).df()
    for c in ["title", "location", "description"]:
        df[c] = df[c].fillna("").astype(str)
    df["posting_id"] = df["posting_id"].astype(str)
    return df


def make_text(df: pd.DataFrame) -> pd.Series:
    return (df["title"] + " " + df["description"]).str.strip()
