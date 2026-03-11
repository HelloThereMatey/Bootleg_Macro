import os
import sys
import datetime

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fuzzywuzzy import fuzz, process

# Ensure repo root is importable when run from examples/
wd = os.path.dirname(__file__)
repo_root = os.path.dirname(wd)
if repo_root not in sys.path:
    sys.path.append(repo_root)

from MacroBackend import Pull_Data


def _fuzzy_match_column(search_str: str, columns: list[str], score_cutoff: int = 40) -> str | None:
    """Find the best fuzzy match for a search string among column names.

    Args:
        search_str: Query string to match against column names.
        columns: List of column name candidates.
        score_cutoff: Minimum fuzzywuzzy score (0-100) to accept a match.

    Returns:
        Best matching column name, or None if no match exceeds the cutoff.
    """
    result = process.extractOne(search_str, columns, scorer=fuzz.token_set_ratio, score_cutoff=score_cutoff)
    if result is None:
        return None
    match, score, *_ = result
    print(f"  Fuzzy match: '{search_str}' → '{match}' (score {score})")
    return match


def _pick_two_series(table_df: pd.DataFrame, table_meta: pd.Series,
                     left_series: str = None, right_series: str = None
                     ) -> tuple[tuple[str, str], tuple[str, str]]:
    """Pick two BEA series from a pulled table.

    When *left_series* / *right_series* are supplied they are matched against
    the table's column names.  An exact match is tried first; on failure a
    fuzzy search (fuzzywuzzy token_set_ratio) selects the best candidate.

    When either parameter is None the original heuristic is used: prefer
    "Gross domestic product" (left) and "Personal consumption" (right),
    falling back to the first two columns.

    Args:
        table_df: Full BEA table DataFrame (columns = series line descriptions).
        table_meta: Series mapping line descriptions to BEA series codes.
        left_series: Column name or search string for the left-axis series.
        right_series: Column name or search string for the right-axis series.

    Returns:
        ((left_series_code, left_title), (right_series_code, right_title))
    """
    # Build line_desc → series_code lookup
    line_to_code: dict[str, str] = {}
    if isinstance(table_meta, pd.Series):
        for line_desc, code in table_meta.items():
            if str(line_desc) in table_df.columns:
                line_to_code[str(line_desc)] = str(code)

    columns = [str(c) for c in table_df.columns]

    def _resolve(search: str | None, fallback_keyword: str | None) -> tuple[str, str] | None:
        """Resolve a search string to (series_code, column_name)."""
        if search is not None:
            # 1) exact match
            if search in columns:
                col = search
            else:
                # 2) fuzzy match
                col = _fuzzy_match_column(search, columns)
            if col is not None:
                code = line_to_code.get(col, col)
                return (code, col)
            print(f"  Warning: no match found for '{search}'")
            return None

        # No search string → keyword heuristic
        if fallback_keyword:
            for line_desc, series_code in line_to_code.items():
                if fallback_keyword in line_desc.lower():
                    return (series_code, line_desc)
        return None

    left_result = _resolve(left_series, "gross domestic product")
    right_result = _resolve(right_series, "personal consumption")

    if left_result is not None and right_result is not None:
        return left_result, right_result

    # Fallback: first two columns
    if len(columns) < 2:
        raise RuntimeError("BEA table returned fewer than 2 series columns.")

    if left_result is None:
        left_col = columns[0]
        left_result = (line_to_code.get(left_col, left_col), left_col)
    if right_result is None:
        right_col = columns[1] if columns[1] != left_result[1] else columns[0]
        right_result = (line_to_code.get(right_col, right_col), right_col)

    return left_result, right_result


    
if __name__ == "__main__":
    
    dataset_name = "NIPA"
    table_code = "T10103"
    frequency = "M"
    start_date = "1900-01-01"
    end_date = datetime.date.today().strftime("%Y-%m-%d")

    # 1) Pull full table once (download or cache)
    cache_loader = Pull_Data.dataset()
    table_df, table_meta = cache_loader._load_bea_table(dataset_name, table_code, frequency)

    # 2) Choose two series from the downloaded table
    #    Pass left_series / right_series as search strings (fuzzy matched) or exact column names.
    #    Set to None to fall back to the GDP / PCE heuristic.

    (left_code, left_title), (right_code, right_title) = _pick_two_series(
        table_df, table_meta,
        left_series="gross domestic product",   # fuzzy search example
        right_series="personal consumption",    # fuzzy search example
    )
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
