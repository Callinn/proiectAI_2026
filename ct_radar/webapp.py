import threading
import webbrowser
from pathlib import Path
from typing import Any, Dict

from flask import Flask, Response, abort, jsonify, request, send_file

from .agent import Agent


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FILE_DIRS = [PROJECT_ROOT / "data", PROJECT_ROOT / "outputs"]
DEFAULT_DISEASE = "diabetes"
DEFAULT_PHASE = "Phase 2"


HTML = """<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Clinical Trial Radar</title>
  <style>
    :root {
      --bg:#0b1220; --panel:#111827; --panel2:#0f172a; --border:#233044; --text:#e5eefc; --muted:#94a3b8;
      --accent:#2dd4bf; --accent2:#38bdf8; --good:#4ade80; --warn:#f59e0b; --shadow:0 18px 55px rgba(0,0,0,.34);
    }
    * { box-sizing: border-box; }
    body {
      margin:0; font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      background: radial-gradient(circle at top, #12203a, var(--bg) 55%); color: var(--text); min-height: 100vh;
    }
    .wrap { max-width: 1200px; margin: 0 auto; padding: 24px; }
    .hero, .panel { background: rgba(17,24,39,.94); border:1px solid var(--border); border-radius: 22px; box-shadow: var(--shadow); }
    .hero { padding: 24px; }
    .top { display:flex; justify-content:space-between; gap:16px; align-items:flex-start; flex-wrap:wrap; }
    .title { margin:0; font-size: 34px; line-height: 1.05; }
    .subtitle { margin: 10px 0 0; color: var(--muted); line-height:1.6; max-width: 820px; }
    .badges { display:flex; gap:8px; flex-wrap:wrap; margin-top: 14px; }
    .badge { border:1px solid var(--border); background: rgba(15,23,42,.9); color: var(--muted); padding: 7px 10px; border-radius: 999px; font-size: 12px; }
    .grid { display:grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }
    .panel { padding: 18px; }
    .label { display:block; font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin-bottom: 6px; }
    input {
      width: 100%; padding: 12px 14px; border-radius: 14px; border:1px solid var(--border); background: #0b1220; color: var(--text);
      font-size: 15px;
    }
    .row { display:flex; gap:12px; flex-wrap: wrap; margin-top: 12px; }
    button {
      border:0; border-radius: 14px; padding: 12px 16px; font-weight: 700; cursor:pointer;
      background: linear-gradient(135deg, var(--accent), #16a34a); color:#052e16;
    }
    button.secondary { background: linear-gradient(135deg, var(--accent2), #0284c7); color:#082f49; }
    button.ghost { background: #0b1220; color: var(--text); border: 1px solid var(--border); }
    .status { margin-top: 10px; color: #bbf7d0; min-height: 22px; }
    .summary { display:grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 14px; }
    .stat { background: rgba(11,18,32,.85); border:1px solid var(--border); border-radius: 18px; padding: 14px; }
    .stat .k { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }
    .stat .v { margin-top: 8px; font-size: 22px; font-weight: 800; }
    .links { display:flex; gap:10px; flex-wrap:wrap; margin-top: 10px; }
    .link { display:inline-block; text-decoration:none; color:#dbeafe; background: rgba(56,189,248,.12); border:1px solid rgba(56,189,248,.28); padding: 8px 10px; border-radius: 10px; }
    .results { display:grid; gap: 16px; margin-top: 16px; }
    .section-title { margin:0 0 8px; font-size: 18px; }
    iframe { width:100%; height:520px; border:1px solid var(--border); border-radius: 16px; background:#fff; }
    .small { color: var(--muted); font-size: 13px; line-height: 1.55; }
    .footer { margin-top: 18px; text-align:center; color: var(--muted); font-size: 12px; }
    @media (max-width: 960px) {
      .grid, .summary { grid-template-columns: 1fr; }
      .title { font-size: 28px; }
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"hero\">
      <div class=\"top\">
        <div>
          <h1 class=\"title\">Clinical Trial Radar</h1>
          <p class=\"subtitle\">O aplicație simplă pentru analiză fezabilitate: primește boala și faza studiului, colectează date reale din ClinicalTrials.gov, generează trend, hartă, tabel și snapshot. Pentru utilizator final nu afișează JSON, ci rezultate și linkuri către fișiere.</p>
          <div class=\"badges\">
            <div class=\"badge\">Real data</div>
            <div class=\"badge\">Trend chart</div>
            <div class=\"badge\">Country map</div>
            <div class=\"badge\">Studies table</div>
            <div class=\"badge\">Snapshot export</div>
          </div>
        </div>
        <div class=\"panel\" style=\"min-width:280px;\">
          <div class=\"small\"><b>How it works</b><br>1. Enter disease and phase.<br>2. Click <b>Run analysis</b>.<br>3. Open generated reports from the links below.</div>
        </div>
      </div>
    </div>

    <div class=\"grid\">
      <div class=\"panel\">
        <label class=\"label\">Disease</label>
        <input id=\"disease\" value=\"{{ disease }}\" />
        <label class=\"label\" style=\"margin-top:12px;\">Phase</label>
        <input id=\"phase\" value=\"{{ phase }}\" />
        <div class=\"row\">
          <button onclick=\"runAnalysis()\">Run analysis</button>
          <button class=\"secondary\" onclick=\"loadDefault()\">Load default</button>
          <button class=\"ghost\" onclick=\"refreshLatest()\">Refresh latest</button>
        </div>
        <div id=\"status\" class=\"status\">Ready.</div>
        <div class=\"small\" style=\"margin-top:10px;\">The app generates real outputs in <code>outputs/</code> and <code>data/raw/</code>.</div>
      </div>

      <div class=\"panel\">
        <h3 class=\"section-title\">Results</h3>
        <div class=\"summary\">
          <div class=\"stat\"><div class=\"k\">Studies</div><div class=\"v\" id=\"nStudies\">-</div></div>
          <div class=\"stat\"><div class=\"k\">Trend points</div><div class=\"v\" id=\"nTrend\">-</div></div>
          <div class=\"stat\"><div class=\"k\">Regions</div><div class=\"v\" id=\"nRegions\">-</div></div>
        </div>
        <div class=\"links\" id=\"links\"></div>
      </div>
    </div>

    <div class=\"results\">
      <div class=\"panel\">
        <h3 class=\"section-title\">Trend chart</h3>
        <div class=\"small\">Evolution in time of studies recruiting vs completed is available in the generated trend report.</div>
        <iframe id=\"trendFrame\" src=\"\"></iframe>
      </div>
      <div class=\"panel\">
        <h3 class=\"section-title\">Geographic map</h3>
        <div class=\"small\">Distribution of studies by country, with country-level crowding signal.</div>
        <iframe id=\"mapFrame\" src=\"\"></iframe>
      </div>
    </div>

    <div class=\"footer\">Clinical Trial Radar • Local demo using real ClinicalTrials.gov data</div>
  </div>

<script>
function loadDefault() {
  document.getElementById('disease').value = '{{ disease }}';
  document.getElementById('phase').value = '{{ phase }}';
}

async function postJson(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || ('HTTP ' + res.status));
  return data;
}

function toFileRoute(path) {
  const normalized = String(path || '').split('\\\\').join('/');
  const encodedPath = normalized
    .split('/')
    .filter(Boolean)
    .map((part) => encodeURIComponent(part))
    .join('/');
  return '/files/' + encodedPath;
}

function setLinks(artifacts) {
  const links = document.getElementById('links');
  links.innerHTML = '';
  for (const a of artifacts || []) {
    const normalized = String(a || '').split('\\\\').join('/');
    const el = document.createElement('a');
    el.className = 'link';
    el.href = toFileRoute(normalized);
    el.target = '_blank';
    el.textContent = normalized.split('/').pop();
    links.appendChild(el);
  }
}

function setSummary(report) {
  document.getElementById('nStudies').textContent = report.n_total_studies ?? '-';
  document.getElementById('nTrend').textContent = report.trend_points ?? '-';
  document.getElementById('nRegions').textContent = report.crowdedness_regions ?? '-';
}

function setFrames(report) {
  if (report.trend_path) document.getElementById('trendFrame').src = toFileRoute(report.trend_path);
  if (report.map_path) document.getElementById('mapFrame').src = toFileRoute(report.map_path);
}

async function runAnalysis() {
  const disease = document.getElementById('disease').value.trim();
  const phase = document.getElementById('phase').value.trim();
  const status = document.getElementById('status');
  status.textContent = 'Running analysis...';
  try {
    const data = await postJson('/api/run-analysis', { disease, phase });
    status.textContent = 'Analysis completed successfully.';
    setSummary(data.report || {});
    setLinks(data.report.artifacts || []);
    setFrames(data.report || {});
    if (Array.isArray(data.report?.warnings) && data.report.warnings.length > 0) {
      status.textContent = 'Completed with warnings: ' + data.report.warnings.join(' | ');
    }
  } catch (err) {
    status.textContent = 'Error: ' + err.message;
  }
}

async function refreshLatest() {
  const status = document.getElementById('status');
  status.textContent = 'Loading latest analysis...';
  try {
    const res = await fetch('/api/latest');
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || 'No latest analysis yet.');
    setSummary(data.report || {});
    setLinks(data.report.artifacts || []);
    setFrames(data.report || {});
    document.getElementById('status').textContent = 'Latest analysis loaded.';
  } catch (err) {
    status.textContent = 'No cached analysis yet. Click Run analysis.';
  }
}

window.addEventListener('DOMContentLoaded', () => {
  refreshLatest().then(() => {}).catch(() => {});
  setTimeout(() => {
    const status = document.getElementById('status');
    if (status && status.textContent.includes('No cached analysis')) {
      runAnalysis();
    }
  }, 300);
});
</script>
</body>
</html>"""


def create_app() -> Flask:
    app = Flask(__name__)
    # prefer local Ollama LLM when available; Agent will set self.llm only if OLLAMA_AVAILABLE
    agent = Agent(llm_provider='ollama', model="mistral")
    latest_report: Dict[str, Any] = {}

    @app.get("/")
    def index() -> str:
        return (
            HTML.replace("{{ disease }}", DEFAULT_DISEASE)
            .replace("{{ phase }}", DEFAULT_PHASE)
        )

    @app.get("/api/latest")
    def latest() -> Any:
        if not latest_report:
            return jsonify({"ok": False, "error": "No analysis yet", "report": {}})
        return jsonify({"ok": True, "report": latest_report})

    @app.get("/favicon.ico")
    def favicon() -> Response:
        return Response(status=204)

    @app.get("/.well-known/appspecific/com.chrome.devtools.json")
    def chrome_devtools_probe() -> Response:
      return Response(status=204)

    @app.get("/files/<path:file_path>")
    def files(file_path: str):
        requested = (PROJECT_ROOT / file_path).resolve()
        for root in ALLOWED_FILE_DIRS:
            root_resolved = root.resolve()
            if str(requested).startswith(str(root_resolved)) and requested.is_file():
                return send_file(requested)
        abort(404)

    @app.post("/api/run-analysis")
    def run_analysis() -> Any:
        nonlocal latest_report
        payload: Dict[str, Any] = request.get_json(force=True, silent=True) or {}
        disease = (payload.get("disease") or DEFAULT_DISEASE).strip() or DEFAULT_DISEASE
        phase = (payload.get("phase") or DEFAULT_PHASE).strip() or DEFAULT_PHASE
        try:
            report = agent.run_demo_workflow(disease=disease, phase=phase)
            latest_report = report
            return jsonify({"ok": True, "report": report})
        except Exception as exc:
            return jsonify({"ok": False, "error": str(exc)}), 500

    @app.get("/api/health")
    def health() -> Any:
        return jsonify({"ok": True, "ready": True})

    return app



def run_webapp(host: str = "127.0.0.1", port: int = 5005, open_browser: bool = True) -> str:
    app = create_app()
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    app.run(host=host, port=port, debug=False, use_reloader=False)
    return f"http://{host}:{port}"


if __name__ == "__main__":
    print(run_webapp())
