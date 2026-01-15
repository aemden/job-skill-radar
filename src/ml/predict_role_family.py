from __future__ import annotations

import argparse
import joblib
import pandas as pd

from .utils import connect_duckdb, fetch_postings, make_text


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--table", default="stg_job_postings")

    # YOUR schema:
    p.add_argument("--id-col", default="job_id")
    p.add_argument("--title-col", default="title")
    p.add_argument("--loc-col", default="location")
    p.add_argument("--desc-col", default="description_full")

    p.add_argument("--model", default="models/role_family_clf.joblib")
    p.add_argument("--out-table", default="pred_role_family")
    args = p.parse_args()

    con = connect_duckdb(args.db)
    df = fetch_postings(
        con,
        table=args.table,
        id_col=args.id_col,
        title_col=args.title_col,
        loc_col=args.loc_col,
        desc_col=args.desc_col,
    )

    model = joblib.load(args.model)
    X = make_text(df)

    pred = model.predict(X)
    try:
        proba = model.predict_proba(X)
        conf = proba.max(axis=1)
    except Exception:
        conf = [None] * len(df)

    out = pd.DataFrame({
        "posting_id": df["posting_id"].astype(str),
        "pred_role_family": pred.astype(str),
        "pred_confidence": conf,
    })

    con.register("out_df", out)
    con.execute(f"CREATE OR REPLACE TABLE {args.out_table} AS SELECT * FROM out_df")
    con.unregister("out_df")

    print(f"Wrote {len(out)} rows to {args.out_table}")


if __name__ == "__main__":
    main()
