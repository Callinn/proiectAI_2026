import os
import json
import pandas as pd
from typing import Dict, Any


def _read_csv_file(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def load_input(path: str) -> pd.DataFrame:
    """Load a CSV file or concatenate all CSVs in a directory."""
    if os.path.isdir(path):
        files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith('.csv')]
        dfs = []
        for f in files:
            try:
                dfs.append(_read_csv_file(f))
            except Exception:
                continue
        if not dfs:
            return pd.DataFrame()
        return pd.concat(dfs, ignore_index=True)
    elif os.path.isfile(path):
        return _read_csv_file(path)
    else:
        raise FileNotFoundError(path)


def compute_crowdedness(df: pd.DataFrame, country_field: str = "LocationCountry") -> pd.DataFrame:
    """Compute number of recruiting studies per country.

    Returns a DataFrame with columns: Country, RecruitingCount, TotalCount
    """
    if df.empty:
        return pd.DataFrame(columns=["Country", "RecruitingCount", "TotalCount"])

    df_country = df.copy()
    df_country[country_field] = df_country[country_field].fillna("Unknown")

    recruiting_mask = df_country["OverallStatus"].str.contains("Recruiting", na=False, case=False)
    recruited = df_country[recruiting_mask].groupby(country_field).size().rename("RecruitingCount")
    total = df_country.groupby(country_field).size().rename("TotalCount")

    result = pd.concat([recruited, total], axis=1).fillna(0).reset_index()
    result = result.rename(columns={country_field: "Country"})
    result["RecruitingCount"] = result["RecruitingCount"].astype(int)
    result["TotalCount"] = result["TotalCount"].astype(int)
    result = result.sort_values(by="RecruitingCount", ascending=False)
    return result


def estimate_cycle_time(df: pd.DataFrame, start_field: str = "StartDate", end_field: str = "CompletionDate") -> Dict[str, Any]:
    """Estimate typical cycle times (in days) from start to completion.

    Returns a summary dict with median, mean, std, n_samples.
    """
    if df.empty:
        return {"n": 0}

    s = pd.to_datetime(df[start_field], errors="coerce")
    e = pd.to_datetime(df[end_field], errors="coerce")
    mask = s.notna() & e.notna()
    diffs = (e[mask] - s[mask]).dt.days.dropna()
    if diffs.empty:
        return {"n": 0}
    return {
        "n": int(diffs.count()),
        "median_days": float(diffs.median()),
        "mean_days": float(diffs.mean()),
        "std_days": float(diffs.std()),
    }


def trend_over_time(df: pd.DataFrame, date_field: str = "StartDate") -> pd.DataFrame:
    """Compute number of studies started per year."""
    if df.empty:
        return pd.DataFrame()
    dates = pd.to_datetime(df[date_field], errors="coerce")
    years = dates.dt.year.fillna(0).astype(int)
    result = years.value_counts().sort_index().rename_axis("Year").reset_index(name="Count")
    result = result[result["Year"] > 0]
    return result


def compute_metrics_from_path(path: str) -> Dict[str, Any]:
    df = load_input(path)
    crowded = compute_crowdedness(df)
    cycle = estimate_cycle_time(df)
    trend = trend_over_time(df)

    metrics = {
        "crowdedness": crowded.to_dict(orient="records"),
        "cycle_time": cycle,
        "trend_by_start_year": trend.to_dict(orient="records"),
        "n_total_studies": int(len(df)),
    }
    return metrics


def save_metrics(metrics: Dict[str, Any], out_path: str):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)


__all__ = [
    "load_input",
    "compute_crowdedness",
    "estimate_cycle_time",
    "trend_over_time",
    "compute_metrics_from_path",
    "save_metrics",
]
