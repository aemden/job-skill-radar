from __future__ import annotations

import argparse
import pandas as pd


def norm(s: str) -> str:
    return str(s).strip().lower()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="in_path", default="labels/labels_sample_prefilled.csv")
    p.add_argument("--out", dest="out_path", default="labels/labels_sample_final.csv")
    args = p.parse_args()

    df = pd.read_csv(args.in_path)

    # Map common role-family variants to a small canonical set.
    # You may need to tweak this mapping based on your value_counts output.
    mapping = {
        "data analyst": "data_analyst",
        "analytics": "data_analyst",
        "business intelligence": "bi_analyst",
        "bi analyst": "bi_analyst",
        "business analyst": "bi_analyst",

        "data engineer": "data_engineer",
        "analytics engineer": "data_engineer",

        "machine learning engineer": "ml_engineer",
        "ml engineer": "ml_engineer",
        "data scientist": "ml_engineer",

        "software engineer": "software_engineer",
        "backend engineer": "software_engineer",
        "full stack engineer": "software_engineer",
        "full-stack engineer": "software_engineer",

        "product manager": "pm_analytics",
        "product analytics": "pm_analytics",
        "analytics pm": "pm_analytics",

        "other": "other",
        "unknown": "other",
        "": "other",
        "nan": "other",
    }

    df["role_family_label"] = df["role_family_label"].fillna("").apply(norm)

    # Apply mapping; anything unmapped -> other (safe + simple)
    df["role_family_label"] = df["role_family_label"].apply(lambda x: mapping.get(x, "other"))

    df.to_csv(args.out_path, index=False)
    print(f"Wrote standardized labels to: {args.out_path}")
    print(df["role_family_label"].value_counts())


if __name__ == "__main__":
    main()
