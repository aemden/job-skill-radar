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

job-skill-radar/
├─ app/ # optional dashboard
│ └─ dashboard.py
├─ src/
│ ├─ ingest/
│ │ └─ load_raw.py
│ ├─ clean/
│ │ └─ normalize.py
│ └─ nlp/
│ ├─ extract_skills.py
│ └─ skills.yml
├─ data/
│ ├─ raw/ # gitignored (put Kaggle CSV here)
│ └─ sample/ # optional: commit a small sample for reproducibility
├─ warehouse/
│ └─ analytics.duckdb # gitignored (created locally)
├─ assets/ # screenshots/diagrams (optional)
├─ requirements.txt
├─ .gitignore
└─ README.md


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
