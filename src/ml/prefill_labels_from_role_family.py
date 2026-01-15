from __future__ import annotations

import argparse
import pandas as pd
import duckdb


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--table", default="stg_job_postings")
    p.add_argument("--labels-csv", default="labels/labels_sample.csv")
    p.add_argument("--out", default="labels/labels_sample_prefilled.csv")

    # schema
    p.add_argument("--id-col", default="job_id")
    p.add_argument("--label-col", default="role_family")
    args = p.parse_args()

    labels = pd.read_csv(args.labels_csv)
    labels["posting_id"] = labels["posting_id"].astype(str)

    con = duckdb.connect(args.db)
    map_df = con.execute(
        f"SELECT {args.id_col}::VARCHAR AS posting_id, {args.label_col}::VARCHAR AS role_family FROM {args.table}"
    ).df()

    merged = labels.merge(map_df, on="posting_id", how="left")
    merged["role_family_label"] = merged["role_family"].fillna("").astype(str).str.strip()

    # keep your labeling columns clean
    merged = merged.drop(columns=["role_family"])
    merged.to_csv(args.out, index=False)

    print(f"Wrote: {args.out}")
    print("Next: open it and (1) standardize labels to a small set, (2) fix obvious mistakes, (3) ensure no blanks.")


if __name__ == "__main__":
    main()
