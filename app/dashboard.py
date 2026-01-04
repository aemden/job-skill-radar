import duckdb
import pandas as pd
import streamlit as st

DB_PATH = "warehouse/analytics.duckdb"

st.set_page_config(page_title="Job Skill Radar", layout="wide")
st.title("Job Skill Radar")
st.caption("Skills extracted from job titles + full descriptions (Indeed snapshot)")

@st.cache_data
def load_jobs():
    con = duckdb.connect(DB_PATH)
    jobs = con.execute("SELECT job_id, title, company, location, posted_date, role_family FROM stg_job_postings").df()
    con.close()
    return jobs

@st.cache_data
def load_skills():
    con = duckdb.connect(DB_PATH)
    skills = con.execute("SELECT job_id, skill, category FROM job_skills").df()
    con.close()
    return skills

jobs = load_jobs()
skills = load_skills()

# ---- Sidebar filters ----
st.sidebar.header("Filters")

role_options = ["all"] + sorted(jobs["role_family"].dropna().unique().tolist())
role_choice = st.sidebar.selectbox("Role family", role_options, index=0)

# Location filter (simple substring match)
location_text = st.sidebar.text_input("Location contains (optional)", value="")

# Date filter (if posted_date parsed)
min_date = jobs["posted_date"].dropna().min()
max_date = jobs["posted_date"].dropna().max()

use_dates = pd.notna(min_date) and pd.notna(max_date)
if use_dates:
    date_range = st.sidebar.date_input("Posted date range", value=(min_date, max_date))
else:
    date_range = None
    st.sidebar.info("Posted dates could not be parsed for this dataset; date filtering disabled.")

# ---- Apply filters ----
f_jobs = jobs.copy()

if role_choice != "all":
    f_jobs = f_jobs[f_jobs["role_family"] == role_choice]

if location_text.strip():
    f_jobs = f_jobs[f_jobs["location"].fillna("").str.contains(location_text.strip(), case=False, na=False)]

if use_dates and isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    f_jobs = f_jobs[(f_jobs["posted_date"] >= start) & (f_jobs["posted_date"] <= end)]

# Join skills to filtered jobs
f = skills.merge(f_jobs[["job_id", "role_family", "posted_date"]], on="job_id", how="inner")

# ---- Layout ----
col1, col2, col3 = st.columns(3)
col1.metric("Jobs (filtered)", f_jobs["job_id"].nunique())
col2.metric("Skill mentions", len(f))
col3.metric("Unique skills", f["skill"].nunique())

st.divider()

left, right = st.columns([1, 1])

with left:
    st.subheader("Top skills (filtered)")
    top_n = st.slider("Top N", 10, 50, 20, 5)
    top = (
        f.groupby("skill", as_index=False)
        .size()
        .rename(columns={"size": "mentions"})
        .sort_values("mentions", ascending=False)
        .head(top_n)
    )
    st.dataframe(top, use_container_width=True, height=520)

with right:
    st.subheader("Skill trend")
    skill_list = sorted(f["skill"].dropna().unique().tolist())
    if skill_list and use_dates:
        chosen_skill = st.selectbox("Choose a skill", skill_list, index=0)
        trend = f[f["skill"] == chosen_skill].copy()
        trend["posted_date"] = pd.to_datetime(trend["posted_date"])
        by_day = trend.groupby(trend["posted_date"].dt.date).size().reset_index(name="mentions")
        st.line_chart(by_day, x="posted_date", y="mentions")
    else:
        st.info("Trend chart requires parsed posted_date values.")

st.divider()

st.subheader("Top skills by role family (filtered)")
by_role = (
    f.groupby(["role_family", "skill"], as_index=False)
    .size()
    .rename(columns={"size": "mentions"})
)
# show top 10 per role
by_role["rank"] = by_role.groupby("role_family")["mentions"].rank(method="first", ascending=False)
by_role_top = by_role[by_role["rank"] <= 10].sort_values(["role_family", "mentions"], ascending=[True, False])
st.dataframe(by_role_top.drop(columns=["rank"]), use_container_width=True)
