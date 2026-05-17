# Usage — Clinical Trial Radar (Stage 1)

Prerequisites

- Python 3.9+ recommended
- Create virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Basic workflow

1. Ingest studies for a disease and phase:

```bash
python main.py ingest --disease "type 2 diabetes" --phase "Phase 2" --max 200 --normalize
```

Outputs: CSV files are written to `data/raw/`.

2. Compute metrics (save to JSON):

```bash
python main.py metrics --input data/raw --out data/metrics/feasibility.json
```

3. Visualize results:

- Trend:
```bash
python main.py visualize --input data/raw --type trend --out outputs/trend.html
```

- Country map:
```bash
python main.py visualize --input data/raw --type map --out outputs/country_map.html
```

4. Normalize single term interactively:

```bash
python main.py normalize "t2dm"
```

Notes

- To re-run ingestion with updated parameters, remove or archive previous `data/raw/` files.
- For large-scale retrieval, implement paging and store a consolidated DB.
