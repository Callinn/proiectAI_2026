# Evaluation & KPIs — Clinical Trial Radar (Stage 1)

Suggested KPIs

- Time saved: Average time reduction for initial feasibility scans (minutes per study).
- Coverage: Percentage of relevant studies identified vs a gold set (recall).
- Precision: Fraction of retrieved studies that are relevant.
- Consistency: Variation in outputs between repeated runs for same query (format/fields).
- Usability: Time-to-first-insight for a non-expert user.

Validation tests

- Unit tests for `normalize_disease()` with a range of synonyms.
- End-to-end test: ingest a small curated disease query and compare counts against ClinicalTrials.gov manual results.
- Metric sanity checks: ensure `n_total_studies` > 0 and `median_days` is within plausible range for completed studies.

Manual evaluation

- Have domain experts review 20–50 sampled studies and mark relevance / eligibility extraction accuracy.
- Collect feedback on recommended countries and whether they match operational expectations.

Next steps for evaluation

- Add automated test harness (pytest) and CI (GitHub Actions) for running ingest + metrics on small sample data.
- Add dashboards to track KPIs over time (number of runs, coverage improvements after tuning synonyms).
