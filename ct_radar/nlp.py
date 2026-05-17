import os
import json
import re
from typing import Dict, Any, List
import pandas as pd


def _find_eligibility_text(row: Dict[str, Any]) -> str:
    # Try common fields
    for key in ["EligibilityCriteria", "Eligibility", "DetailedDescription", "BriefSummary", "BriefDescription", "StudyDescription"]:
        v = row.get(key)
        if isinstance(v, str) and v.strip():
            return v
    # fallback: join text-like fields
    texts = []
    for k, v in row.items():
        if isinstance(v, str) and len(v) > 50:
            texts.append(v)
    return "\n\n".join(texts)


def _split_inclusion_exclusion(text: str) -> Dict[str, List[str]]:
    if not text:
        return {"inclusion": [], "exclusion": [], "other": []}

    # Normalize
    t = text.replace('\r', '\n')
    # attempt to find explicit Inclusion/Exclusion sections
    inc = []
    exc = []

    # heuristics: look for headings
    sections = re.split(r"\n{2,}", t)
    for sec in sections:
        low = sec.lower()
        if "inclusion" in low and len(sec) > 10:
            inc.append(sec.strip())
        elif "exclusion" in low and len(sec) > 10:
            exc.append(sec.strip())

    # fallback: find lines with include/exclude verbs
    if not inc or not exc:
        lines = [l.strip() for l in t.splitlines() if l.strip()]
        for ln in lines:
            lnl = ln.lower()
            if lnl.startswith("inclusion") or lnl.startswith("includes") or 'include' in lnl and len(lnl) > 30:
                inc.append(ln)
            if lnl.startswith("exclusion") or lnl.startswith("excludes") or 'exclude' in lnl and len(lnl) > 30:
                exc.append(ln)

    # last fallback: extract sentences containing key verbs
    if (not inc or not exc) and len(t) > 100:
        sents = re.split(r'[\.\n]', t)
        for s in sents:
            ls = s.strip().lower()
            if not ls:
                continue
            if 'include' in ls or 'eligible' in ls or 'eligib' in ls:
                if len(s.strip()) > 20:
                    inc.append(s.strip())
            if 'exclude' in ls or 'not eligible' in ls or 'exclud' in ls:
                if len(s.strip()) > 20:
                    exc.append(s.strip())

    return {"inclusion": inc, "exclusion": exc, "other": []}


def extract_eligibility(input_path: str, out_json: str):
    """Load studies from CSV(s), extract eligibility sections, save JSON.

    Output format:
    [ { 'NCTId': ..., 'inclusion': [...], 'exclusion': [...], 'source_field': 'EligibilityCriteria' }, ... ]
    """
    # load CSV(s)
    if os.path.isdir(input_path):
        files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.lower().endswith('.csv')]
    elif os.path.isfile(input_path):
        files = [input_path]
    else:
        raise FileNotFoundError(input_path)

    rows = []
    for f in files:
        try:
            df = pd.read_csv(f, dtype=str)
        except Exception:
            continue
        for _, r in df.iterrows():
            row = r.to_dict()
            text = _find_eligibility_text(row)
            parts = _split_inclusion_exclusion(text)
            rows.append({
                'NCTId': row.get('NCTId'),
                'inclusion': parts.get('inclusion', []),
                'exclusion': parts.get('exclusion', []),
                'source_text_present': bool(text),
            })

    os.makedirs(os.path.dirname(out_json) or '.', exist_ok=True)
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    return out_json


__all__ = ["extract_eligibility"]
