import os
import pandas as pd
import plotly.express as px
from typing import Optional

try:
    import pycountry
except Exception:
    pycountry = None
try:
    import plotly.io as pio
except Exception:
    pio = None


def _country_to_iso3(name: str) -> Optional[str]:
    if not name or not pycountry:
        return None
    try:
        c = pycountry.countries.lookup(name)
        return c.alpha_3
    except Exception:
        # try partial match
        try:
            for c in pycountry.countries:
                if name.lower() in c.name.lower():
                    return c.alpha_3
        except Exception:
            pass
    return None


def plot_trend(trend_df: pd.DataFrame, out_html: str):
    """Plot trend over time (Year vs Count) and save as interactive HTML."""
    if trend_df.empty:
        raise ValueError("Empty trend data")
    fig = px.line(trend_df, x="Year", y="Count", markers=True, title="Studies started per year")
    os.makedirs(os.path.dirname(out_html) or ".", exist_ok=True)
    fig.write_html(out_html)
    return out_html


def save_trend_png(trend_df: pd.DataFrame, out_png: str):
    """Save trend plot as PNG using kaleido (Plotly write_image)."""
    if trend_df.empty:
        raise ValueError("Empty trend data")
    fig = px.line(trend_df, x="Year", y="Count", markers=True, title="Studies started per year")
    os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
    # requires kaleido
    fig.write_image(out_png)
    return out_png


def plot_country_choropleth(crowded_df: pd.DataFrame, out_html: str, value_field: str = "RecruitingCount"):
    """Create a choropleth of recruiting counts per country and save as HTML."""
    if crowded_df.empty:
        raise ValueError("Empty crowdedness data")
    df = crowded_df.copy()
    df["iso_alpha"] = df["Country"].apply(lambda c: _country_to_iso3(c) or "")
    df = df[df["iso_alpha"] != ""]
    fig = px.choropleth(df, locations="iso_alpha", color=value_field,
                        hover_name="Country", color_continuous_scale="OrRd",
                        title="Recruiting studies by country")
    os.makedirs(os.path.dirname(out_html) or ".", exist_ok=True)
    fig.write_html(out_html)
    return out_html


def save_map_png(crowded_df: pd.DataFrame, out_png: str, value_field: str = "RecruitingCount"):
    """Save choropleth as PNG using kaleido."""
    if crowded_df.empty:
        raise ValueError("Empty crowdedness data")
    df = crowded_df.copy()
    df["iso_alpha"] = df["Country"].apply(lambda c: _country_to_iso3(c) or "")
    df = df[df["iso_alpha"] != ""]
    fig = px.choropleth(df, locations="iso_alpha", color=value_field,
                        hover_name="Country", color_continuous_scale="OrRd",
                        title="Recruiting studies by country")
    os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
    fig.write_image(out_png)
    return out_png


__all__ = ["plot_trend", "plot_country_choropleth"]
__all__.extend(["save_trend_png", "save_map_png"])
