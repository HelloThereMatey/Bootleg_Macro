import os
import sys
import datetime

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Ensure repo root is importable when run from examples/
wd = os.path.dirname(__file__)
repo_root = os.path.dirname(wd)
if repo_root not in sys.path:
    sys.path.append(repo_root)

from MacroBackend import Pull_Data


def _pick_two_series(table_df: pd.DataFrame, table_meta: pd.Series) -> tuple[tuple[str, str], tuple[str, str]]:
    """
    Pick two BEA series from a pulled table.
    Returns ((left_series_code, left_title), (right_series_code, right_title)).
    Prefers GDP + Personal Consumption if available; otherwise first two columns.
    """
    line_to_code = {}
    if isinstance(table_meta, pd.Series):
        for line_desc, code in table_meta.items():
            if str(line_desc) in table_df.columns:
                line_to_code[str(line_desc)] = str(code)

    preferred_left = None
    preferred_right = None

    for line_desc, series_code in line_to_code.items():
        l = line_desc.lower()
        if preferred_left is None and "gross domestic product" in l:
            preferred_left = (series_code, line_desc)
        elif preferred_right is None and "personal consumption" in l:
            preferred_right = (series_code, line_desc)

    if preferred_left is not None and preferred_right is not None:
        return preferred_left, preferred_right

    # Fallback: first two columns from table
    cols = [str(c) for c in table_df.columns]
    if len(cols) < 2:
        raise RuntimeError("BEA table returned fewer than 2 series columns.")

    left_col, right_col = cols[0], cols[1]
    left_code = str(line_to_code.get(left_col, left_col))
    right_code = str(line_to_code.get(right_col, right_col))
    return (left_code, left_col), (right_code, right_col)


def main():
    dataset_name = "NIPA"
    table_code = "T10101"
    frequency = "Q"
    start_date = "2000-01-01"
    end_date = datetime.date.today().strftime("%Y-%m-%d")

    # 1) Pull full table once (download or cache)
    cache_loader = Pull_Data.dataset()
    table_df, table_meta = cache_loader._load_bea_table(dataset_name, table_code, frequency)

    # 2) Choose two series from the downloaded table
    (left_code, left_title), (right_code, right_title) = _pick_two_series(table_df, table_meta)
    print(f"Chosen left series:  {left_code} ({left_title})")
    print(f"Chosen right series: {right_code} ({right_title})")

    # 3) Pull each series via the public dataset.get_data(...) path
    left = Pull_Data.dataset()
    left.get_data(
        source="bea",
        data_code=f"{dataset_name}|{table_code}|{left_code}",
        start_date=start_date,
        end_date=end_date,
        data_freq=frequency,
        dtype="close",
    )

    right = Pull_Data.dataset()
    right.get_data(
        source="bea",
        data_code=f"{dataset_name}|{table_code}|{right_code}",
        start_date=start_date,
        end_date=end_date,
        data_freq=frequency,
        dtype="close",
    )

    left_ser = pd.Series(left.data).dropna()
    right_ser = pd.Series(right.data).dropna()

    # Align to common index for cleaner plotting
    common_index = left_ser.index.intersection(right_ser.index)
    left_ser = left_ser.reindex(common_index)
    right_ser = right_ser.reindex(common_index)

    # 4) Plotly dual-axis chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=left_ser.index, y=left_ser.values, mode="lines", name=left_title),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=right_ser.index, y=right_ser.values, mode="lines", name=right_title),
        secondary_y=True,
    )

    fig.update_layout(
        title=f"BEA {dataset_name} {table_code}: Two Series (Dual Axis)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.06, x=0.0),
    )
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text=left_title, secondary_y=False)
    fig.update_yaxes(title_text=right_title, secondary_y=True)

    fig.show()


if __name__ == "__main__":
    main()
