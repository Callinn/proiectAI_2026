import os
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
import requests

CT_V2_BASE = "https://clinicaltrials.gov/api/v2/studies"
CT_V1_BASE = "https://clinicaltrials.gov/api/query/study_fields"

DEFAULT_FIELDS = [
    "NCTId",
    "Condition",
    "BriefTitle",
    "OverallStatus",
    "Phase",
    "StartDate",
    "CompletionDate",
    "LocationCountry",
    "LocationCity",
    "EnrollmentCount",
]


def _join_list(value):
    if isinstance(value, list):
        return "; ".join([str(v) for v in value if v not in (None, "")])
    return value


def _phase_to_query(phase: Optional[str]) -> Optional[str]:
    if not phase:
        return None
    text = phase.strip().upper().replace(" ", "")
    text = text.replace("PHASE", "PHASE")
    if text in {"PHASE1", "PHASE2", "PHASE3", "PHASE4", "PHASE1/2", "PHASE2/3"}:
        return text
    m = re.search(r"PHASE\s*([1-4])", phase, flags=re.I)
    if m:
        return f"PHASE{m.group(1)}"
    return phase.strip().upper()


def build_v2_query(disease: str, phase: Optional[str] = None) -> str:
    disease = (disease or "").strip()
    if not disease:
        raise ValueError("disease is required")
    return disease


def _sanitize_query_term(query_term: Optional[str]) -> Optional[str]:
    """Remove any old API-v2 phase syntax and keep only the disease term."""
    if not query_term:
        return None
    cleaned = re.sub(r"\s+AND\s+AREA\[Phase\].*$", "", query_term, flags=re.I).strip()
    return cleaned or None


def _matches_phase(phase_value: str, phase_filter: Optional[str]) -> bool:
    if not phase_filter:
        return True
    if not phase_value:
        return False
    target = _phase_to_query(phase_filter)
    if not target:
        return True
    value = phase_value.upper().replace(" ", "")
    value = value.replace("/", "")
    target_norm = target.upper().replace(" ", "").replace("/", "")
    return target_norm in value


def _pick(module: Dict[str, Any], path: Iterable[str], default=None):
    cur: Any = module
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return cur if cur is not None else default


def _first(lst, default=None):
    if isinstance(lst, list) and lst:
        return lst[0]
    return default


def _flatten_v2_study(study: Dict[str, Any]) -> Dict[str, Any]:
    protocol = study.get("protocolSection", {}) if isinstance(study, dict) else {}
    derived = study.get("derivedSection", {}) if isinstance(study, dict) else {}

    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    description = protocol.get("descriptionModule", {})
    conditions = protocol.get("conditionsModule", {})
    design = protocol.get("designModule", {})
    eligibility = protocol.get("eligibilityModule", {})
    locations_module = protocol.get("contactsLocationsModule", {})
    outcomes = protocol.get("outcomesModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})

    locations = locations_module.get("locations", []) or []
    locations_joined = [
        ", ".join([str(v) for v in [loc.get("facility"), loc.get("city"), loc.get("state"), loc.get("country")] if v])
        for loc in locations
    ]

    phases = design.get("phases", []) or []
    phase = "; ".join(phases)

    primary_outcomes = outcomes.get("primaryOutcomes", []) or []
    primary_outcome_text = "; ".join(
        [
            f"{o.get('measure', '')} | {o.get('timeFrame', '')}".strip(" |")
            for o in primary_outcomes
        ]
    )

    return {
        "NCTId": identification.get("nctId"),
        "OrgStudyId": _pick(identification, ["orgStudyIdInfo", "id"]),
        "BriefTitle": identification.get("briefTitle"),
        "OfficialTitle": identification.get("officialTitle"),
        "OverallStatus": status.get("overallStatus"),
        "LastKnownStatus": status.get("lastKnownStatus"),
        "StartDate": _pick(status, ["startDateStruct", "date"]),
        "PrimaryCompletionDate": _pick(status, ["primaryCompletionDateStruct", "date"]),
        "CompletionDate": _pick(status, ["completionDateStruct", "date"]),
        "StudyType": design.get("studyType"),
        "Phase": phase,
        "EnrollmentCount": _pick(design, ["enrollmentInfo", "count"]),
        "Condition": _join_list(conditions.get("conditions", [])),
        "Keywords": _join_list(conditions.get("keywords", [])),
        "BriefSummary": description.get("briefSummary"),
        "DetailedDescription": description.get("detailedDescription"),
        "EligibilityCriteria": eligibility.get("eligibilityCriteria"),
        "HealthyVolunteers": eligibility.get("healthyVolunteers"),
        "Sex": eligibility.get("sex"),
        "MinimumAge": eligibility.get("minimumAge"),
        "StdAges": _join_list(eligibility.get("stdAges", [])),
        "Locations": _join_list(locations_joined),
        "LocationCountry": _join_list([loc.get("country") for loc in locations if loc.get("country")]),
        "LocationCity": _join_list([loc.get("city") for loc in locations if loc.get("city")]),
        "LocationFacility": _join_list([loc.get("facility") for loc in locations if loc.get("facility")]),
        "PrimaryOutcomes": primary_outcome_text,
        "LeadSponsor": _pick(sponsor, ["leadSponsor", "name"]),
        "LeadSponsorClass": _pick(sponsor, ["leadSponsor", "class"]),
        "VersionHolder": _pick(derived, ["miscInfoModule", "versionHolder"]),
    }


def _fetch_v2_page(query_term: str, page_size: int = 100, page_token: Optional[str] = None) -> Dict[str, Any]:
    params = {
        "query.term": query_term,
        "pageSize": page_size,
    }
    if page_token:
        params["pageToken"] = page_token
    resp = requests.get(CT_V2_BASE, params=params, timeout=45)
    resp.raise_for_status()
    return resp.json()


def fetch_studies_v2(
    disease: str,
    phase: Optional[str] = None,
    max_results: int = 100,
    page_size: int = 100,
    query_term: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch studies from ClinicalTrials.gov API v2 and flatten the nested JSON structure."""
    query_term = _sanitize_query_term(query_term) or build_v2_query(disease, None)
    rows: List[Dict[str, Any]] = []
    page_token: Optional[str] = None

    while len(rows) < max_results:
        payload = _fetch_v2_page(query_term, page_size=page_size, page_token=page_token)
        studies = payload.get("studies", []) or []
        for study in studies:
            flat = _flatten_v2_study(study)
            if _matches_phase(flat.get("Phase", ""), phase):
                rows.append(flat)
                if len(rows) >= max_results:
                    break
        page_token = payload.get("nextPageToken") or payload.get("nextPage")
        if not page_token or not studies:
            break

    return pd.DataFrame(rows)


def fetch_studies(disease: str, phase: str = None, max_results: int = 100, query_term: Optional[str] = None):
    """Backward-compatible wrapper that now uses ClinicalTrials.gov API v2."""
    return fetch_studies_v2(disease, phase, max_results=max_results, query_term=query_term)


def fetch_and_save_studies(
    disease: str,
    phase: str = None,
    max_results: int = 100,
    out_dir: str = "data/raw",
    query_term: Optional[str] = None,
):
    os.makedirs(out_dir, exist_ok=True)
    df = fetch_studies_v2(disease, phase, max_results=max_results, query_term=query_term)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_disease = (disease or "query").replace(" ", "_")
    safe_phase = (phase or "all").replace(" ", "_")
    if query_term:
        query_term = _sanitize_query_term(query_term) or query_term
        safe_disease = re.sub(r"[^A-Za-z0-9_\-]+", "_", query_term[:60]) or "query"
    fname_csv = f"{safe_disease}_{safe_phase}_{timestamp}.csv"
    path_csv = os.path.join(out_dir, fname_csv)
    df.to_csv(path_csv, index=False)
    # also keep the raw v2 JSON for traceability
    raw_json_path = os.path.join(out_dir, f"{safe_disease}_{safe_phase}_{timestamp}.json")
    try:
        payload = _fetch_v2_page((query_term or build_v2_query(disease, None)), page_size=min(max_results, 100))
        with open(raw_json_path, "w", encoding="utf-8") as f:
            import json as _json
            _json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return path_csv
