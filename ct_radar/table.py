import os
from typing import Optional
import pandas as pd
from .metrics import load_input


DT_CSS = "https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css"
DT_JS = "https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"
JQ_JS = "https://code.jquery.com/jquery-3.6.0.min.js"


def _make_nct_links(df: pd.DataFrame) -> pd.DataFrame:
    if "NCTId" in df.columns:
        df = df.copy()
        df["NCTId_link"] = df["NCTId"].apply(lambda v: f"<a href='https://clinicaltrials.gov/study/{v}' target='_blank'>{v}</a>" if v else "")
        # move NCTId_link to first column
        cols = list(df.columns)
        cols.insert(0, cols.pop(cols.index("NCTId_link")))
        return df[cols]
    return df


def generate_studies_table(input_path: str, out_html: str, max_rows: Optional[int] = 1000) -> str:
    """Generate an interactive HTML table (DataTables) from CSV(s).

    - `input_path`: file or directory containing CSV files (same as metrics.load_input)
    - `out_html`: output path for the HTML file
    """
    df = load_input(input_path)
    if df.empty:
        raise ValueError("No study data found at input path")

    # shorten long text fields for display
    display_df = df.copy()
    for c in display_df.columns:
        if display_df[c].dtype == object:
            display_df[c] = display_df[c].astype(str).str.replace('\n', ' ').str.slice(0, 500)

    display_df = _make_nct_links(display_df)
    if max_rows is not None and len(display_df) > max_rows:
        display_df = display_df.head(max_rows)

    table_html = display_df.to_html(classes="display", index=False, escape=False)

    html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Clinical Trial Radar — Studies Table</title>
<link rel="stylesheet" href="{DT_CSS}">
<style> body {{ font-family: Arial, sans-serif; margin: 20px; }} </style>
</head>
<body>
<h2>Studies table</h2>
{table_html}
<script src="{JQ_JS}"></script>
<script src="{DT_JS}"></script>
<script>
$(document).ready(function(){{
    $('table.display').DataTable({{
        pageLength: 25,
        lengthMenu: [ [25, 50, 100, -1], [25, 50, 100, 'All'] ]
    }});
}});
</script>
</body>
</html>
"""
    os.makedirs(os.path.dirname(out_html) or '.', exist_ok=True)
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(html)
    return out_html


__all__ = ["generate_studies_table"]
