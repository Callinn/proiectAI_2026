import os
import json
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional

# Tools mapping
from .ingest import fetch_and_save_studies
from .normalize import normalize_disease
from .metrics import compute_metrics_from_path, save_metrics
from .visualize import plot_trend, plot_country_choropleth, save_trend_png, save_map_png
from .table import generate_studies_table
from .nlp import extract_eligibility
from .export import generate_snapshot

# Optional LLM client (Ollama)
try:
    import ollama
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False


SYSTEM_PROMPT = (
    "You are an orchestration agent for Clinical Trial Radar. "
    "Available actions: ingest (disease, phase, max, out_dir), normalize (term), metrics (input,out), "
    "visualize (type, input, out), table (input,out), extract (input,out), snapshot (metrics, trend,map,table,out,pptx). "
    "Respond with JSON only: {\"steps\": [{\"action\": \"ingest\", \"args\": {...}}, ...]}. "
    "Use deterministic output and do not include markdown or prose."
)


class Agent:
    def __init__(self, llm_provider: Optional[str] = None, model: Optional[str] = None):
        # llm_provider can be 'ollama' or None
        self.llm = llm_provider if (llm_provider and OLLAMA_AVAILABLE) else None
        self.model = model or os.environ.get('OLLAMA_MODEL', 'mistral')

    def plan_with_llm(self, instruction: str) -> List[Dict[str, Any]]:
        if not self.llm:
            raise RuntimeError('LLM provider not configured')
        try:
            resp = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": instruction},
                ],
                options={
                    'temperature': 0.0,
                    'top_p': 1.0,
                },
                format='json',
            )
            text = resp['message']['content']
            data = json.loads(text)
            steps = data.get('steps', [])
            return steps
        except Exception as e:
            raise RuntimeError(f'LLM planning failed: {e}')

    def rule_based_plan(self, instruction: str) -> List[Dict[str, Any]]:
        # Very simple heuristic: look for keywords and build steps
        inst = instruction.lower()
        steps = []
        if 'ingest' in inst or 'fetch' in inst or 'search' in inst:
            # try to extract disease and phase heuristically
            # naive: find quoted phrases
            import re
            quoted = re.findall(r'"([^"]+)"', instruction)
            disease = quoted[0] if quoted else 'diabetes'
            phase = None
            if 'phase 2' in inst:
                phase = 'Phase 2'
            steps.append({'action': 'ingest', 'args': {'disease': disease, 'phase': phase, 'max_results': 200, 'out_dir': 'data/raw'}})
        # then metrics
        if 'metric' in inst or 'feasibil' in inst or 'trend' in inst:
            steps.append({'action': 'metrics', 'args': {'input': 'data/raw', 'out': 'data/metrics/feasibility.json'}})
        # visualize
        if 'map' in inst:
            steps.append({'action': 'visualize', 'args': {'type': 'map', 'input': 'data/raw', 'out': 'outputs/country_map.html'}})
        if 'trend' in inst:
            steps.append({'action': 'visualize', 'args': {'type': 'trend', 'input': 'data/raw', 'out': 'outputs/trend.html'}})
        # table
        if 'table' in inst or 'list' in inst:
            steps.append({'action': 'table', 'args': {'input': 'data/raw', 'out': 'outputs/studies_table.html'}})
        # snapshot
        if 'snapshot' in inst or 'report' in inst:
            steps.append({'action': 'snapshot', 'args': {'metrics': 'data/metrics/feasibility.json', 'trend':'outputs/trend.html','map':'outputs/country_map.html','table':'outputs/studies_table.html','out':'outputs/snapshot.html'}})
        return steps

    def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        action = step.get('action')
        args = step.get('args', {}) or {}
        try:
            if action == 'ingest':
                path = fetch_and_save_studies(args.get('disease'), args.get('phase'), max_results=args.get('max_results',100), out_dir=args.get('out_dir','data/raw'))
                return {'status':'ok','result': path, 'artifact': path}
            if action == 'normalize':
                canon = normalize_disease(args.get('term'))
                return {'status':'ok','result': canon}
            if action == 'metrics':
                metrics = compute_metrics_from_path(args.get('input'))
                out = args.get('out')
                if out:
                    save_metrics(metrics, out)
                    return {'status':'ok','result': out, 'artifact': out}
                return {'status':'ok','result': metrics}
            if action == 'visualize':
                t = args.get('type')
                if t == 'trend':
                    # compute trend from metrics
                    df_path = args.get('input')
                    import pandas as _pd
                    from .metrics import trend_over_time
                    df = compute_metrics_from_path(df_path) if isinstance(df_path, str) and os.path.isdir(df_path) else None
                    # prefer to compute via compute_metrics_from_path
                    if df and isinstance(df, dict) and df.get('trend_by_start_year'):
                        df_tr = _pd.DataFrame(df['trend_by_start_year'])
                        out = plot_trend(df_tr, args.get('out'))
                        return {'status':'ok','result': out, 'artifact': out}
                    else:
                        # fallback: run metric then plot
                        metrics = compute_metrics_from_path(args.get('input'))
                        import pandas as _pd
                        df_tr = _pd.DataFrame(metrics.get('trend_by_start_year', []))
                        out = plot_trend(df_tr, args.get('out'))
                        return {'status':'ok','result': out, 'artifact': out}
                if t == 'map':
                    metrics = compute_metrics_from_path(args.get('input'))
                    import pandas as _pd
                    df_cr = _pd.DataFrame(metrics.get('crowdedness', []))
                    out = plot_country_choropleth(df_cr, args.get('out'))
                    return {'status':'ok','result': out, 'artifact': out}
            if action == 'table':
                out = generate_studies_table(args.get('input'), args.get('out'))
                return {'status':'ok','result': out, 'artifact': out}
            if action == 'extract':
                out = extract_eligibility(args.get('input'), args.get('out'))
                return {'status':'ok','result': out, 'artifact': out}
            if action == 'snapshot':
                out = generate_snapshot(args.get('metrics'), {'trend': args.get('trend'),'map': args.get('map'),'table': args.get('table')}, args.get('out'))
                return {'status':'ok','result': out, 'artifact': out}
            return {'status':'error','error': f'Unknown action: {action}'}
        except Exception as e:
            tb = traceback.format_exc()
            return {'status':'error','error': str(e), 'trace': tb}

    def run(self, instruction: str, use_llm: bool = False) -> Dict[str, Any]:
        """Main entry: plan and execute steps for a natural-language instruction.

        If use_llm=True and Ollama is configured, the agent will ask the local model to plan.
        Otherwise uses rule-based planner.
        Returns an execution report.
        """
        if use_llm and OLLAMA_AVAILABLE:
            try:
                steps = self.plan_with_llm(instruction)
            except Exception as e:
                steps = self.rule_based_plan(instruction)
        else:
            steps = self.rule_based_plan(instruction)

        report = {'instruction': instruction, 'steps': steps, 'results': [], 'artifacts': []}
        for s in steps:
            r = self.execute_step(s)
            report['results'].append({'step': s, 'result': r})
            artifact = r.get('artifact')
            if artifact and artifact not in report['artifacts']:
                report['artifacts'].append(artifact)
            # simple stop on error
            if r.get('status') == 'error':
                report['error'] = r
                break
        return report

    def run_demo_workflow(self, disease: str = "diabetes", phase: str = "Phase 2") -> Dict[str, Any]:
        """Run a real end-to-end workflow without exposing JSON to the user interface."""
        safe_disease = disease or "diabetes"
        safe_phase = phase or "Phase 2"
        project_root = Path(__file__).resolve().parents[1]
        raw_dir = project_root / 'data' / 'raw'
        metrics_dir = project_root / 'data' / 'metrics'
        outputs_dir = project_root / 'outputs'
        raw_dir.mkdir(parents=True, exist_ok=True)
        metrics_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        warnings: List[str] = []
        ingest_path: Optional[str] = None
        input_path = str(raw_dir)

        def _to_rel(path_value: Optional[str]) -> Optional[str]:
            if not path_value:
                return None
            try:
                return str(Path(path_value).resolve().relative_to(project_root)).replace('\\', '/')
            except Exception:
                return str(path_value).replace('\\', '/')

        try:
            ingest_path = fetch_and_save_studies(safe_disease, safe_phase, max_results=200, out_dir=str(raw_dir))
            input_path = ingest_path
        except Exception as exc:
            warnings.append(f"Ingest failed: {exc}")
            fallback_csvs = sorted(raw_dir.glob('*.csv'), key=lambda p: p.stat().st_mtime, reverse=True)
            if fallback_csvs:
                input_path = str(fallback_csvs[0])
                warnings.append(f"Using latest cached CSV: {input_path}")

        try:
            metrics = compute_metrics_from_path(input_path)
        except Exception as exc:
            warnings.append(f"Metrics failed: {exc}")
            metrics = {
                'crowdedness': [],
                'cycle_time': {'n': 0},
                'trend_by_start_year': [],
                'n_total_studies': 0,
            }

        metrics_path = str(metrics_dir / 'feasibility.json')
        save_metrics(metrics, metrics_path)

        import pandas as _pd
        trend_path = str(outputs_dir / 'trend.html')
        map_path = str(outputs_dir / 'country_map.html')
        table_path = str(outputs_dir / 'studies_table.html')
        snapshot_path = str(outputs_dir / 'snapshot.html')

        trend_df = _pd.DataFrame(metrics.get('trend_by_start_year', []))
        crowd_df = _pd.DataFrame(metrics.get('crowdedness', []))

        if not trend_df.empty:
            plot_trend(trend_df, trend_path)
        else:
            Path(trend_path).parent.mkdir(parents=True, exist_ok=True)
            Path(trend_path).write_text(
                "<html><body><h2>No trend data for current filters.</h2></body></html>",
                encoding='utf-8'
            )
        if not crowd_df.empty:
            plot_country_choropleth(crowd_df, map_path)
        else:
            Path(map_path).parent.mkdir(parents=True, exist_ok=True)
            Path(map_path).write_text(
                "<html><body><h2>No geographic data for current filters.</h2></body></html>",
                encoding='utf-8'
            )

        try:
            generate_studies_table(input_path, table_path)
        except Exception as exc:
            warnings.append(f"Table generation failed: {exc}")
            Path(table_path).parent.mkdir(parents=True, exist_ok=True)
            Path(table_path).write_text(
                "<html><body><h2>No studies table available for current filters.</h2></body></html>",
                encoding='utf-8'
            )

        try:
            generate_snapshot(metrics_path, {'trend': trend_path, 'map': map_path, 'table': table_path}, snapshot_path)
        except Exception as exc:
            warnings.append(f"Snapshot generation failed: {exc}")
            Path(snapshot_path).parent.mkdir(parents=True, exist_ok=True)
            Path(snapshot_path).write_text(
                "<html><body><h2>Snapshot unavailable.</h2></body></html>",
                encoding='utf-8'
            )

        artifacts = [
            _to_rel(ingest_path),
            _to_rel(metrics_path),
            _to_rel(trend_path),
            _to_rel(map_path),
            _to_rel(table_path),
            _to_rel(snapshot_path),
        ]
        artifacts = [a for a in artifacts if a]

        summary = {
            'disease': safe_disease,
            'phase': safe_phase,
            'ingest_path': _to_rel(ingest_path),
            'input_path': _to_rel(input_path),
            'metrics_path': _to_rel(metrics_path),
            'trend_path': _to_rel(trend_path),
            'map_path': _to_rel(map_path),
            'table_path': _to_rel(table_path),
            'snapshot_path': _to_rel(snapshot_path),
            'n_total_studies': metrics.get('n_total_studies', 0),
            'crowdedness_regions': len(metrics.get('crowdedness', [])),
            'trend_points': len(metrics.get('trend_by_start_year', [])),
            'artifacts': artifacts,
            'warnings': warnings,
        }
        return summary


def example_usage():
    ag = Agent(llm_provider='ollama' if OLLAMA_AVAILABLE else None)
    instr = 'Ingest studies for "type 2 diabetes" Phase 2, compute metrics, produce trend and map and snapshot'
    rep = ag.run(instr, use_llm=False)
    print(json.dumps(rep, indent=2))


if __name__ == '__main__':
    example_usage()
