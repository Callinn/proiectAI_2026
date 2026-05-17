import argparse
import json
import os
from ct_radar import run_webapp
from ct_radar import fetch_and_save_studies, normalize_disease
from ct_radar import compute_metrics_from_path, save_metrics, plot_trend, plot_country_choropleth, generate_studies_table
from ct_radar import save_trend_png, save_map_png


def main():
    parser = argparse.ArgumentParser(description="Clinical Trial Radar - Stage1 prototype")
    sub = parser.add_subparsers(dest="cmd")

    ingest = sub.add_parser("ingest", help="Ingest studies from ClinicalTrials.gov")
    ingest.add_argument("--disease", required=True, help="Disease or condition to search for")
    ingest.add_argument("--phase", required=False, help="Study phase filter (e.g. \"Phase 2\")")
    ingest.add_argument("--query", required=False, help="Raw ClinicalTrials.gov query.term to use directly")
    ingest.add_argument("--max", type=int, default=100, help="Maximum number of studies to fetch")
    ingest.add_argument("--out", default="data/raw", help="Output directory for raw data")
    ingest.add_argument("--normalize", action="store_true", help="Normalize disease term before querying")

    norm = sub.add_parser("normalize", help="Normalize a disease term to a canonical name")
    norm.add_argument("term", help="Input disease term to normalize")
    metrics = sub.add_parser("metrics", help="Compute feasibility metrics from CSV or data directory")
    metrics.add_argument("--input", required=True, help="CSV file or directory with CSV files")
    metrics.add_argument("--out", required=False, help="Output JSON file for metrics")

    vis = sub.add_parser("visualize", help="Create visualizations from input data or computed metrics")
    vis.add_argument("--input", required=True, help="CSV file or directory with CSV files")
    vis.add_argument("--type", required=True, choices=["trend", "map"], help="Visualization type: trend or map")
    vis.add_argument("--out", required=True, help="Output HTML file path for the visualization")

    tablep = sub.add_parser("table", help="Generate interactive studies table as HTML")
    tablep.add_argument("--input", required=True, help="CSV file or directory with CSV files")
    tablep.add_argument("--out", required=True, help="Output HTML file path for the table")
    nlp = sub.add_parser("extract", help="Extract eligibility criteria from studies and save JSON")
    nlp.add_argument("--input", required=True, help="CSV file or directory with CSV files")
    nlp.add_argument("--out", required=True, help="Output JSON file for extracted criteria")
    snap = sub.add_parser("snapshot", help="Generate a snapshot report (HTML and optional PPTX)")
    snap.add_argument("--metrics", required=True, help="Metrics JSON file OR input directory to compute metrics")
    snap.add_argument("--trend", required=False, help="Path to trend HTML file")
    snap.add_argument("--map", required=False, help="Path to map HTML file")
    snap.add_argument("--table", required=False, help="Path to table HTML file")
    snap.add_argument("--out", required=True, help="Output HTML snapshot path")
    snap.add_argument("--pptx", required=False, help="Optional output PPTX path (requires python-pptx and images)")

    args = parser.parse_args()
    if args.cmd == "ingest":
        query_term = args.disease
        if args.normalize:
            canon = normalize_disease(args.disease)
            if canon:
                print(f"Normalized '{args.disease}' -> '{canon}'")
                query_term = canon
            else:
                print(f"Could not normalize '{args.disease}', using original term")
        raw_query = args.query
        if raw_query:
            print(f"Using raw query.term: {raw_query}")
        path = fetch_and_save_studies(query_term, args.phase, max_results=args.max, out_dir=args.out, query_term=raw_query)
        print(f"Saved studies to: {path}")
    elif args.cmd == "normalize":
        canon = normalize_disease(args.term)
        if canon:
            print(f"'{args.term}' -> '{canon}'")
        else:
            print(f"No canonical mapping found for '{args.term}'")
    elif args.cmd == "metrics":
        metrics_data = compute_metrics_from_path(args.input)
        if args.out:
            save_metrics(metrics_data, args.out)
            print(f"Metrics saved to: {args.out}")
        else:
            print(json.dumps(metrics_data, indent=2, ensure_ascii=False))
    elif args.cmd == "visualize":
        metrics_data = compute_metrics_from_path(args.input)
        if args.type == "trend":
            trend = metrics_data.get("trend_by_start_year", [])
            df = None
            try:
                import pandas as _pd
                df = _pd.DataFrame(trend)
            except Exception:
                df = None
            if df is None or df.empty:
                print("No trend data available to plot")
            else:
                out = plot_trend(df, args.out)
                print(f"Trend plot saved to: {out}")
        elif args.type == "map":
            crowded = metrics_data.get("crowdedness", [])
            try:
                import pandas as _pd
                df = _pd.DataFrame(crowded)
            except Exception:
                df = None
            if df is None or df.empty:
                print("No crowdedness data available to plot")
            else:
                out = plot_country_choropleth(df, args.out)
                print(f"Country choropleth saved to: {out}")
    elif args.cmd == "table":
        out = generate_studies_table(args.input, args.out)
        print(f"Studies table saved to: {out}")
    elif args.cmd == "extract":
        from ct_radar import extract_eligibility
        out = extract_eligibility(args.input, args.out)
        print(f"Eligibility extraction saved to: {out}")
    elif args.cmd == "snapshot":
        from ct_radar import generate_snapshot, generate_snapshot_pptx, compute_metrics_from_path
        metrics_arg = args.metrics
        # if metrics_arg is a directory, compute metrics
        if os.path.isdir(metrics_arg):
            metrics = compute_metrics_from_path(metrics_arg)
        else:
            # assume file path
            metrics = metrics_arg
        viz = {"trend": args.trend, "map": args.map, "table": args.table}
        # if PPTX requested and images missing, try to create PNGs from metrics
        pngs = {}
        if args.pptx:
            try:
                # ensure metrics dict available
                if isinstance(metrics, str):
                    # load JSON
                    import json as _json
                    with open(metrics, 'r', encoding='utf-8') as f:
                        metrics_dict = _json.load(f)
                else:
                    metrics_dict = metrics

                # create trend png if not provided
                if not viz.get('trend'):
                    trend = metrics_dict.get('trend_by_start_year', [])
                    if trend:
                        import pandas as _pd
                        df_tr = _pd.DataFrame(trend)
                        trend_png = os.path.join(os.path.dirname(args.out) or '.', 'trend.png')
                        save_trend_png(df_tr, trend_png)
                        pngs['trend'] = trend_png
                        viz['trend'] = trend_png

                # create map png if not provided
                if not viz.get('map'):
                    crowd = metrics_dict.get('crowdedness', [])
                    if crowd:
                        import pandas as _pd
                        df_cr = _pd.DataFrame(crowd)
                        map_png = os.path.join(os.path.dirname(args.out) or '.', 'map.png')
                        save_map_png(df_cr, map_png)
                        pngs['map'] = map_png
                        viz['map'] = map_png
            except Exception as e:
                print('Warning: failed to auto-generate PNGs for PPTX:', e)

        out = generate_snapshot(metrics, viz, args.out)
        print(f"Snapshot HTML saved to: {out}")
        if args.pptx:
            # try to include images if provided
            images = []
            for k in ['trend','map','table']:
                p = viz.get(k)
                # accept PNG images too
                if p and os.path.exists(p) and p.lower().endswith(('.png','.jpg','.jpeg')):
                    images.append(p)
            ppt = generate_snapshot_pptx(metrics, images, args.pptx)
            if ppt:
                print(f"Snapshot PPTX saved to: {ppt}")
            else:
                print("python-pptx not available; PPTX not created.")
    else:
        url = run_webapp()
        print(f"Opened local agent UI: {url}")


if __name__ == "__main__":
    main()
