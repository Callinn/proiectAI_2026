import os
import webbrowser
from pathlib import Path
from typing import Optional


DASHBOARD_HTML = """<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<title>Clinical Trial Radar</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }}
  .wrap {{ max-width: 1000px; margin: 0 auto; padding: 40px 24px; }}
  .hero {{ background: linear-gradient(135deg, #111827, #1e293b); padding: 28px; border-radius: 20px; box-shadow: 0 12px 40px rgba(0,0,0,.35); }}
  h1 {{ margin: 0 0 8px; font-size: 36px; }}
  p {{ line-height: 1.6; color: #cbd5e1; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 22px; }}
  .card {{ background: #111827; border: 1px solid #334155; border-radius: 16px; padding: 18px; }}
  code, pre {{ background: #0b1220; color: #93c5fd; padding: 2px 6px; border-radius: 6px; }}
  .btn {{ display:inline-block; margin-top: 8px; padding: 10px 14px; border-radius: 10px; background:#22c55e; color:#052e16; text-decoration:none; font-weight:700; }}
  .muted {{ color: #94a3b8; font-size: 14px; }}
</style>
</head>
<body>
  <div class='wrap'>
    <div class='hero'>
      <h1>Clinical Trial Radar</h1>
      <p>Agent AI local, orientat pe planificare și orchestration pentru fezabilitatea studiilor clinice. Rulează ingestia, metricele, vizualizările și snapshot-ul din CLI, iar rezultatele apar în fișiere HTML locale.</p>
      <p class='muted'>Dacă vrei agentul local, setează Ollama cu modelul <code>mistral</code> și rulează comenzi din terminal.</p>
    </div>

    <div class='grid'>
      <div class='card'>
        <h3>1. Ingest</h3>
        <p>Descarcă studii din ClinicalTrials.gov.</p>
        <code>python main.py ingest --disease "diabetes" --phase "Phase 2"</code>
      </div>
      <div class='card'>
        <h3>2. Metrics</h3>
        <p>Calculează crowdedness, cycle time și trend.</p>
        <code>python main.py metrics --input data/raw --out data/metrics/feasibility.json</code>
      </div>
      <div class='card'>
        <h3>3. Visualize</h3>
        <p>Trend chart, hartă și tabel interactiv.</p>
        <code>python main.py visualize --input data/raw --type trend --out outputs/trend.html</code>
      </div>
      <div class='card'>
        <h3>4. Agent</h3>
        <p>Planner local prin Ollama, output JSON determinist.</p>
        <code>from ct_radar import Agent</code>
      </div>
    </div>
  </div>
</body>
</html>"""


def build_dashboard(out_path: str = "outputs/index.html") -> str:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DASHBOARD_HTML, encoding="utf-8")
    return str(path)


def open_dashboard(out_path: str = "outputs/index.html") -> str:
    path = build_dashboard(out_path)
    webbrowser.open(Path(path).resolve().as_uri())
    return path


__all__ = ["build_dashboard", "open_dashboard"]
