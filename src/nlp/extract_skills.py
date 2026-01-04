import pathlib
import re
from typing import Dict, List, Tuple

import duckdb
import pandas as pd
import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "warehouse" / "analytics.duckdb"
SKILLS_PATH = REPO_ROOT / "src" / "nlp" / "skills.yml"

def load_skills() -> Dict[str, List[str]]:
    with open(SKILLS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def compile_patterns(skills: Dict[str, List[str]]) -> Dict[str, List[Tuple[str, re.Pattern]]]:
    compiled: Dict[str, List[Tuple[str, re.Pattern]]] = {}
    for category, items in skills.items():
        compiled[category] = []
        for skill in items:
            s = skill.lower().strip()
            # Word boundary-ish matching:
            # - allow spaces in skills (e.g., "power bi", "github actions")
            # - escape regex characters
            escaped = re.escape(s)
            # match as a standalone token sequence
            pat = re.compile(r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])", re.IGNORECASE)
            compiled[category].append((s, pat))
    return compiled

def main() -> None:
    skills = load_skills()
    patterns = compile_patterns(skills)

    con = duckdb.connect(str(DB_PATH))
    jobs = con.execute("SELECT job_id, title, description_full FROM stg_job_postings").df()
    con.close()

    rows = []
    for _, r in jobs.iterrows():
        text = f"{r['title']} {r['description_full']}".lower()
        job_id = r["job_id"]

        found = set()
        for category, pats in patterns.items():
            for skill, pat in pats:
                if pat.search(text):
                    found.add((job_id, skill, category))

        rows.extend(list(found))

    out = pd.DataFrame(rows, columns=["job_id", "skill", "category"])

    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE OR REPLACE TABLE job_skills AS SELECT * FROM out")
    con.close()

    print(f"job_skills rows: {len(out):,}")
    print(out.head(15).to_string(index=False))

if __name__ == "__main__":
    main()
