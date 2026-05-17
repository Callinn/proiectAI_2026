# Architecture — Clinical Trial Radar (Stage 1)

Overview

Clinical Trial Radar is built as a small modular Python package with the following components:

- `ct_radar.ingest` — retrieves study fields from ClinicalTrials.gov and saves raw CSVs.
- `ct_radar.normalize` — maps input disease terms to canonical terms (synonym mapping + fuzzy matching).
- `ct_radar.metrics` — computes feasibility metrics: crowdedness, cycle times, trends.
- `ct_radar.visualize` — generates interactive HTML visualizations (trend plots, choropleth map).
- `main.py` — CLI wrapper exposing `ingest`, `normalize`, `metrics`, `visualize` commands.

Data flow

1. User calls `ingest` to fetch studies for a disease/phase → CSVs in `data/raw/`.
2. `metrics` loads CSV(s) → computes crowdedness, cycle time estimates, and trends.
3. `visualize` reads metrics and generates HTML outputs for exploration.

Extensibility points

- Add a persistent storage layer (SQLite/Postgres) to index studies and avoid repeated downloads.
- Replace the simple `disease_terms.json` with an external terminology service (MeSH/UMLS) or integrate `rapidfuzz` for higher-quality fuzzy matching.
- Add NLP module (`ct_radar.nlp`) for eligibility criteria extraction using `spaCy` or transformer models.
- Add a lightweight web UI (Flask/FastAPI + React) or Jupyter Dashboards for interactive filtering.

Security & privacy

- The prototype uses only public registry data (ClinicalTrials.gov). Ensure no PHI is ingested or saved.
