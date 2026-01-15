# Job Skill Radar (Indeed Data Jobs Snapshot)

Job Skill Radar turns messy job postings into a **queryable skills dataset**. It ingests a Kaggle/Indeed snapshot, cleans and standardizes fields, extracts skills from full descriptions using a YAML taxonomy, and stores analytics-ready tables in **DuckDB**. A Streamlit dashboard (optional) can sit on top for interactive exploration.

Built to demonstrate **Data Engineering + Analytics**: ingestion → staging model → text-to-structured extraction → warehouse tables → repeatable analysis.

---

## What this project does

1. **Ingests** a Kaggle dataset of US data job postings (Indeed snapshot) into DuckDB (`raw_job_postings`)
2. **Normalizes** raw fields into a clean staging table (`stg_job_postings`)
   - stable `job_id` key (hash-based)
   - parsed `posted_date` (handles strings like “3 days ago”, “30+ days ago”)
   - basic `role_family` classification from job titles (data_engineer / data_analyst / data_scientist / etc.)
3. **Extracts skills** from full job descriptions into a structured table (`job_skills`)
   - uses a curated YAML taxonomy (`skills.yml`)
   - regex matching for transparent, controllable extraction
4. Enables analytics like:
   - **Top skills overall** (SQL, Python, AWS, etc.)
   - **Top skills by role family** (DE vs Analyst vs DS)
   - **Skill trends over time** (based on parsed posting dates)

---

## Tech Stack

- Python (pandas)
- DuckDB (local analytics warehouse)
- YAML skills taxonomy + regex extraction
- Streamlit (optional dashboard)

---

## Project Structure

```text
job-skill-radar/
├─ app/                      # optional dashboard
│  └─ dashboard.py
├─ src/
│  ├─ ingest/
│  │  └─ load_raw.py
│  ├─ clean/
│  │  └─ normalize.py
│  └─ nlp/
│     ├─ extract_skills.py
│     └─ skills.yml
├─ data/
│  ├─ raw/                   # gitignored (put Kaggle CSV here)
│  └─ sample/                # optional: commit a small sample for reproducibility
├─ warehouse/
│  └─ analytics.duckdb        # gitignored (created locally)
├─ assets/                   # screenshots/diagrams (optional)
├─ requirements.txt
├─ .gitignore
└─ README.md
```


---

## Data

Source: Kaggle dataset of data-related job postings scraped from Indeed (snapshot).  
Raw data is **not committed** to GitHub.

Place the downloaded CSV here:
data/raw/job_postings.csv


Expected columns (from this dataset):
- `Title`, `Company`, `Location`, `Rating`, `Date`, `Salary`, `Description`, `Links`, `Descriptions`

---

## Setup (Windows PowerShell)

From the repo root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```


## ML Add-on: Role Family Classification (Baseline NLP Model)

This repo includes a lightweight ML component that predicts a job’s **role family** from the **job title + full description**, then writes predictions back into DuckDB to power downstream analytics.

### What it does
- Builds a supervised text classifier using **TF-IDF + Logistic Regression**
- Evaluates performance with a **classification report** + **confusion matrix**
- Produces an **error set** for manual review (false positives/negatives)
- Runs inference on all staged postings and writes results to DuckDB table: `pred_role_family`

### Where to look (project tour)
- **Training + evaluation:** `src/ml/train_role_family.py`
- **Inference + DuckDB writeback:** `src/ml/predict_role_family.py`
- **Label sample generator:** `src/ml/make_labels_sample.py`
- **Outputs / artifacts:**
  - `reports/role_family_eval.md`
  - `reports/role_family_confusion.png`
  - `reports/role_family_errors.csv`
  - `models/role_family_clf.joblib`

### Data + schema used
DuckDB: `warehouse/analytics.duckdb`

Postings table: `stg_job_postings` (cleaned/staged)
- `job_id` (id)
- `title`
- `location`
- `description_full`

### How to run (end-to-end)

### How to run (end-to-end)

This project supports an end-to-end workflow: generate a labeling sample, prefill + standardize labels, train/evaluate a baseline NLP model, run inference on all postings, and write predictions back into DuckDB.

```bash
# 0) Install dependencies (one-time)
pip install -r requirements.txt
# or: pip install duckdb pandas scikit-learn joblib matplotlib

# 1) Generate a labeling sample (creates labels/labels_sample.csv)
python -m src.ml.make_labels_sample --db warehouse/analytics.duckdb --table stg_job_postings --n 250

# 2) Prefill labels from the existing role_family column (creates labels/labels_sample_prefilled.csv)
python -m src.ml.prefill_labels_from_role_family --db warehouse/analytics.duckdb --table stg_job_postings --labels-csv labels/labels_sample.csv

# 3) Standardize labels into a small canonical set (creates labels/labels_sample_final.csv)
# Example mapping used here: bi -> bi_analyst, data_scientist -> ml_engineer, blanks -> other
python -c "import pandas as pd; df=pd.read_csv('labels/labels_sample_prefilled.csv'); df['role_family_label']=df['role_family_label'].fillna('').astype(str).str.strip().str.lower(); df['role_family_label']=df['role_family_label'].replace({'bi':'bi_analyst','data_scientist':'ml_engineer'}); df.loc[df['role_family_label']=='','role_family_label']='other'; df.to_csv('labels/labels_sample_final.csv', index=False); print(df['role_family_label'].value_counts())"

# 4) Train + evaluate (writes model + evaluation artifacts)
python -m src.ml.train_role_family --db warehouse/analytics.duckdb --table stg_job_postings --labels-csv labels/labels_sample_final.csv

# 5) Predict all postings + write to DuckDB table pred_role_family
python -m src.ml.predict_role_family --db warehouse/analytics.duckdb --table stg_job_postings

# 6) Sanity-check prediction distribution
python -c "import duckdb; con=duckdb.connect('warehouse/analytics.duckdb'); print(con.execute('SELECT pred_role_family, COUNT(*) cnt FROM pred_role_family GROUP BY 1 ORDER BY cnt DESC').fetchall())"


