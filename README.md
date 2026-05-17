# Clinical Trial Radar - Stage 1 Prototype

Small prototype to ingest clinical trials data from ClinicalTrials.gov and produce a feasibility snapshot.

Quickstart

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run ingestion (example):

```bash
python main.py ingest --disease "diabetes" --phase "Phase 2" --max 100
```

Outputs are saved under `data/raw/` as CSV files.

Documentation

See the `docs/` folder for detailed documentation: usage, architecture, and evaluation guidance.

- [docs/README.md](docs/README.md)
- [docs/data_sources.md](docs/data_sources.md)

Examples

- Ingest studies and generate a trend plot:

```bash
python main.py ingest --disease "diabetes" --phase "Phase 2" --max 100 --normalize
python main.py visualize --input data/raw --type trend --out outputs/trend.html

Agent UI

Run `python main.py` with no arguments to open the local browser UI. It sends your prompt to Ollama (`mistral`) and returns a deterministic JSON plan.

Local LLM (recommended) — Ollama + Mistral

If you prefer a free local LLM on Windows, see `docs/ollama_setup.md` for the Ollama setup and `docs/agent_prompt.md` for the system prompt + few-shot examples to produce JSON plans. The agent uses the local Ollama API when `use_llm=True`.
```
