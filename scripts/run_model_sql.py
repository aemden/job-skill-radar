import duckdb

con = duckdb.connect("warehouse/analytics.duckdb")

q1 = """
SELECT
  sjp.location,
  pr.pred_role_family,
  COUNT(*) AS postings
FROM stg_job_postings sjp
JOIN pred_role_family pr
  ON sjp.job_id::VARCHAR = pr.posting_id
GROUP BY 1,2
ORDER BY 1,3 DESC
LIMIT 50;
"""

q2 = """
SELECT
  pr.pred_role_family,
  js.skill,
  COUNT(*) AS mentions
FROM pred_role_family pr
JOIN job_skills js
  ON pr.posting_id = js.job_id::VARCHAR
GROUP BY 1,2
ORDER BY 1,3 DESC
LIMIT 50;
"""

print("\n=== Role mix by location (top 50) ===")
print(con.execute(q1).df())

print("\n=== Skill demand by predicted role (top 50) ===")
print(con.execute(q2).df())
