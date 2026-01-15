from __future__ import annotations

import argparse
import pandas as pd

from .utils import connect_duckdb, fetch_postings


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--table", default="stg_job_postings")

    # YOUR schema:
    p.add_argument("--id-col", default="job_id")
    p.add_argument("--title-col", default="title")
    p.add_argument("--loc-col", default="location")
    p.add_argument("--desc-col", default="description_full")

    p.add_argument("--out", default="labels/labels_sample.csv")
    p.add_argument("--n", type=int, default=250)
    p.add_argument("--seed", type=int, default=42)
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

    sample = df.sample(n=min(args.n, len(df)), random_state=args.seed).copy()
    sample["role_family_label"] = ""  # fill manually
    sample = sample[["posting_id", "title", "location", "description", "role_family_label"]]
    sample.to_csv(args.out, index=False)
    print(f"Wrote: {args.out}")


if __name__ == "__main__":
    main()
