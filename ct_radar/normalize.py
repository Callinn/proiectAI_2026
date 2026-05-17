import os
import json
import difflib
from typing import Optional

DATA_FILE = os.path.join(os.path.dirname(__file__), "disease_terms.json")
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        _TERMS = json.load(f).get("canonical", {})
except FileNotFoundError:
    _TERMS = {}

_SYNONYM_TO_CANON = {}
for canon, syns in _TERMS.items():
    # include canonical name itself
    all_forms = [canon] + syns
    for s in all_forms:
        key = s.lower()
        if key not in _SYNONYM_TO_CANON:
            _SYNONYM_TO_CANON[key] = canon


def normalize_disease(term: str, threshold: float = 0.6) -> Optional[str]:
    """Return a canonical disease term for the given input or None if not found.

    Uses exact synonym lookup then difflib close matching as fallback.
    """
    if not term:
        return None
    t = term.strip().lower()
    if t in _SYNONYM_TO_CANON:
        return _SYNONYM_TO_CANON[t]

    # fuzzy match against synonyms and canonical names
    keys = list(_SYNONYM_TO_CANON.keys())
    match = difflib.get_close_matches(t, keys, n=1, cutoff=threshold)
    if match:
        return _SYNONYM_TO_CANON[match[0]]

    canon_match = difflib.get_close_matches(t, list(_TERMS.keys()), n=1, cutoff=threshold)
    if canon_match:
        return canon_match[0]

    return None


__all__ = ["normalize_disease"]
