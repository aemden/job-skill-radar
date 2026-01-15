from __future__ import annotations

import argparse
import pandas as pd
import joblib
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

from .utils import connect_duckdb, fetch_postings, make_text


def save_confusion_matrix(cm, labels, out_path: str) -> None:
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111)
    im = ax.imshow(cm, interpolation="nearest")
    ax.figure.colorbar(im, ax=ax)

    ax.set(
        xticks=range(len(labels)),
        yticks=range(len(labels)),
        xticklabels=labels,
        yticklabels=labels,
        ylabel="True",
        xlabel="Predicted",
        title="Role Family Confusion Matrix",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    thresh = cm.max() / 2.0 if cm.max() else 0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j, i, str(cm[i, j]),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black",
            )

    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", required=True)
    p.add_argument("--table", default="stg_job_postings")

    # YOUR schema:
    p.add_argument("--id-col", default="job_id")
    p.add_argument("--title-col", default="title")
    p.add_argument("--loc-col", default="location")
    p.add_argument("--desc-col", default="description_full")

    p.add_argument("--labels-csv", required=True)
    p.add_argument("--model-out", default="models/role_family_clf.joblib")
    p.add_argument("--report-out", default="reports/role_family_eval.md")
    p.add_argument("--cm-out", default="reports/role_family_confusion.png")
    p.add_argument("--errors-out", default="reports/role_family_errors.csv")
    p.add_argument("--test-size", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    labels = pd.read_csv(args.labels_csv)
    labels["role_family_label"] = labels["role_family_label"].fillna("").astype(str).str.strip()
    labels = labels[labels["role_family_label"] != ""].copy()
    if labels.empty:
        raise SystemExit("No labeled rows found. Fill role_family_label in labels CSV first.")

    con = connect_duckdb(args.db)
    df = fetch_postings(
        con,
        table=args.table,
        id_col=args.id_col,
        title_col=args.title_col,
        loc_col=args.loc_col,
        desc_col=args.desc_col,
    )

    merged = df.merge(labels[["posting_id", "role_family_label"]], on="posting_id", how="inner")
    if merged.empty:
        raise SystemExit("No overlap between labels posting_id and table job_id (posting_id).")

    X = make_text(merged)
    y = merged["role_family_label"].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=args.test_size,
        random_state=args.seed,
        stratify=y if y.nunique() > 1 else None,
    )

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
        )),
        ("clf", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
        )),
    ])

    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    classes = sorted(y.unique().tolist())
    cm = confusion_matrix(y_test, y_pred, labels=classes)
    save_confusion_matrix(cm, classes, args.cm_out)

    report_text = classification_report(y_test, y_pred, zero_division=0)

    # Save model
    joblib.dump(pipe, args.model_out)

    # Save errors
    test_df = merged.loc[X_test.index].copy()
    test_df["pred_label"] = y_pred
    test_df["correct"] = test_df["pred_label"] == test_df["role_family_label"]

    # add confidence if possible
    try:
        proba = pipe.predict_proba(X_test)
        test_df["pred_confidence"] = proba.max(axis=1)
    except Exception:
        test_df["pred_confidence"] = None

    errors = test_df[~test_df["correct"]].sort_values("pred_confidence", ascending=False)
    errors[["posting_id", "title", "location", "role_family_label", "pred_label", "pred_confidence", "description"]].to_csv(
        args.errors_out, index=False
    )

    # Write markdown report
    with open(args.report_out, "w", encoding="utf-8") as f:
        f.write("# Role Family Classifier Evaluation\n\n")
        f.write(f"- Labeled rows used: {len(merged)}\n")
        f.write(f"- Classes: {', '.join(classes)}\n")
        f.write(f"- Split: {int((1-args.test_size)*100)}/{int(args.test_size*100)}\n\n")
        f.write("## Classification Report\n\n")
        f.write("```text\n")
        f.write(report_text)
        f.write("\n```\n\n")
        f.write("## Artifacts\n\n")
        f.write(f"- Model: {args.model_out}\n")
        f.write(f"- Confusion matrix: {args.cm_out}\n")
        f.write(f"- Error examples: {args.errors_out}\n")

    print("Done.")
    print("Model:", args.model_out)
    print("Report:", args.report_out)


if __name__ == "__main__":
    main()
