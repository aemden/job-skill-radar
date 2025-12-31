# Job Skill Radar (Indeed Data Jobs Snapshot)

End-to-end data pipeline that ingests job postings, cleans/normalizes fields, extracts skills from full job descriptions, and stores analytics-ready tables in DuckDB. Includes quick queries for skill trends by role.

This project is designed to demonstrate practical **Data Engineering + Analytics** skills: reproducible ingestion, data modeling foundations, text processing, and queryable outputs.

---

## What this project does

1. **Ingest** a Kaggle dataset of US data job postings (Indeed snapshot)
2. **Normalize** raw fields into a clean staging table (`stg_job_postings`)
3. **Extract skills** from full job descriptions into a structured table (`job_skills`)
4. Enable analytics like:
   - Top skills overall
   - Top skills by role family (Data Engineer vs Analyst vs Scientist)
   - Skill counts by company/location (easy to add next)

---

## Tech Stack

- Python (pandas)
- DuckDB (local analytics warehouse)
- YAML skills taxonomy
- (Coming next) dbt models + tests
- (Coming next) Streamlit dashboard

---

## Data

Source: Kaggle dataset of data-related job postings scraped from Indeed (snapshot).  
**Note:** Raw data is not committed. A small sample file can be committed to `data/sample/` for reproducible runs.

Expected raw columns (from this dataset):
- `Title`, `Company`, `Location`, `Rating`, `Date`, `Salary`, `Description`, `Links`, `Descriptions`

---

## Project Structure

job-skill-radar/
src/
ingest/
load_raw.py # loads CSV into DuckDB as raw_job_postings
clean/
normalize.py # builds stg_job_postings with stable schema + job_id
nlp/
skills.yml # skills taxonomy
extract_skills.py # builds job_skills from title + full descriptions
data/
raw/ # raw dataset (gitignored)
sample/ # optional small sample committed to repo
warehouse/
analytics.duckdb # local DuckDB database (gitignored)
