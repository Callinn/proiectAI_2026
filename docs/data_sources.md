# Real data sources and how to add them

This project is designed to use real public clinical trial data. No fake or synthetic data is required for the demo.

## Primary source

### ClinicalTrials.gov API
Use the public API to fetch studies by disease and phase.

Example endpoint used by the project:

- `https://clinicaltrials.gov/api/query/study_fields`

The app already supports fetching data through:

```bash
python main.py ingest --disease "type 2 diabetes" --phase "Phase 2" --max 200 --normalize
```

This command downloads real studies and saves them as CSV files under `data/raw/`.

## Optional additional sources

If you want to extend the project later, you can also use:

- ClinicalTrials.gov downloadable study exports
- EU Clinical Trials Register / CTIS public pages, if you build your own scraper or parser
- WHO ICTRP summaries, where accessible via public pages or licensed access
- Curated CSV files from domain collaborators, as long as they contain real trial metadata

## How to add real data to the project

### Option 1: Fetch directly from the API
This is the recommended path.

1. Start the app or use the CLI.
2. Run the ingest command.
3. The raw CSV is written to `data/raw/`.
4. Run metrics, visualizations, and snapshot generation on that output.

### Option 2: Drop your own CSV in `data/raw/`
If you already have a real dataset, place a CSV file in `data/raw/` with at least these columns:

- `NCTId`
- `Condition`
- `BriefTitle`
- `OverallStatus`
- `Phase`
- `StartDate`
- `CompletionDate`
- `LocationCountry`
- `LocationCity`
- `EnrollmentCount`

Then run:

```bash
python main.py metrics --input data/raw --out data/metrics/feasibility.json
python main.py visualize --input data/raw --type trend --out outputs/trend.html
python main.py visualize --input data/raw --type map --out outputs/country_map.html
python main.py table --input data/raw --out outputs/studies_table.html
python main.py extract --input data/raw --out outputs/eligibility.json
python main.py snapshot --metrics data/metrics/feasibility.json --trend outputs/trend.html --map outputs/country_map.html --table outputs/studies_table.html --out outputs/snapshot.html
```

## Notes on data quality

- Use real trial records only.
- Prefer consistent disease naming and phase labels.
- If your CSV has different column names, map them before running the pipeline.

## Quick checklist

- Data exists in `data/raw/`.
- CSV includes real trial rows.
- Ingestion or upload step completed.
- Metrics and visuals run without errors.
