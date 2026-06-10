"""
Australian Bureau of Statistics (ABS) data source for bm.

Uses the readabs Python package to pull ABS time series data.
No API key required.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from bootleg_datafeed.auxiliary import convert_to_standard_series, calculate_metadata_stats, FrequencyConverter
from bootleg_datafeed.models import SeriesMetadata, StandardSeries


def pull_abs(
    series_id: str,
    catalog_num: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    extend: bool = False,
) -> StandardSeries:
    """Pull time series data from the Australian Bureau of Statistics.

    Args:
        series_id: ABS series ID (e.g., 'A84423050A' for unemployment rate)
        catalog_num: ABS catalog number (e.g., '6202.0' for Labour Force).
                    If omitted, looked up automatically via the series master
                    index.
        start_date: Start date filter (YYYY-MM-DD), optional
        end_date: End date filter (YYYY-MM-DD), optional
        extend: If True, use extend_history to splice cross-frequency siblings
                for a longer history. If False (default), use standard
                readabs.read_abs_series().

    Returns:
        StandardSeries with data and metadata

    Raises:
        ValueError: If series not found
    """
    import readabs

    if not catalog_num:
        from .extend_history import find_cat_for_series as _find_cat
        catalog_num = _find_cat(series_id)

    if extend:
        from .extend_history import extend_series as _extend_series

        data_series, meta_df = _extend_series(
            series_id,
            cat=catalog_num,
        )
        if data_series is None or data_series.empty:
            raise ValueError(f"No data found for ABS series: {series_id}")
        series = data_series.copy()
    else:
        # Pull the series via standard readabs
        data_df, meta_df = readabs.read_abs_series(
            cat=catalog_num,
            series_id=series_id,
        )
        if data_df is None or data_df.empty:
            raise ValueError(f"No data found for ABS series: {series_id}")
        # Extract the series from the DataFrame
        series = data_df.iloc[:, 0]
        series.name = series_id

    # Convert to standard series
    series = convert_to_standard_series(series)

    # Apply date filters if specified
    if start_date:
        series = series[series.index >= pd.to_datetime(start_date)]
    if end_date:
        series = series[series.index <= pd.to_datetime(end_date)]

    # Extract metadata from meta_df
    if isinstance(meta_df, pd.DataFrame) and not meta_df.empty:
        meta_row = meta_df.iloc[0]
        title = _extract_meta(meta_row, 'Data Item Description') or series_id
        units = _extract_meta(meta_row, 'Unit')
        frequency = _map_abs_frequency(_extract_meta(meta_row, 'Freq.'))
        description = None  # ABS metadata doesn't typically have a description field
    else:
        title = series_id
        units = None
        frequency = 'M'  # Default to monthly
        description = None

    metadata = SeriesMetadata(
        id=series_id,
        title=title,
        source='abs',
        original_source='Australian Bureau of Statistics',
        start_date=series.index.min().date() if len(series) > 0 else None,
        end_date=series.index.max().date() if len(series) > 0 else None,
        frequency=frequency,
        units=units,
        units_short=units,
        description=description,
        **calculate_metadata_stats(series),
    )

    return StandardSeries.from_pandas(series, metadata)


def search_abs(keyword: str, limit: int = 20) -> pd.DataFrame:
    """Search ABS series by keyword using local master index.

    Args:
        keyword: Search term
        limit: Maximum number of results

    Returns:
        DataFrame with matching series (Series ID, Data Item Description, Unit, Freq., Catalogue number)
    """
    # Check user data dir first, then fall back to MacroBackend location
    from bootleg_datafeed._user_path import get_user_path
    user_path = Path(get_user_path())
    candidates = [
        user_path / "ABS_backend" / "abs_master_index.h5",
        user_path / "ABS_backend" / "abs_master_index-f.h5",
        user_path / "cache" / "abs_master_index.h5",
        user_path / "cache" / "abs_master_index-f.h5",
    ]

    # Old MacroBackend location as fallback
    bm_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    project_dir = os.path.dirname(bm_dir)
    candidates += [
        os.path.join(project_dir, 'MacroBackend', 'ABS_backend', 'abs_master_index.h5'),
        os.path.join(project_dir, 'MacroBackend', 'ABS_backend', 'abs_master_index-f.h5'),
    ]

    for idx_path in candidates:
        if os.path.exists(idx_path):
            try:
                df = pd.read_hdf(idx_path, key='data')
                mask = df['Data Item Description'].str.contains(keyword, case=False, na=False)
                results = df[mask].head(limit)
                return results[['Series ID', 'Data Item Description', 'Unit', 'Freq.', 'Catalogue number']]
            except Exception:
                continue

    return pd.DataFrame()


def browse_abs_tables(keyword: str = "") -> pd.DataFrame:
    """Browse ABS table catalog.

    Args:
        keyword: Filter tables by keyword (optional)

    Returns:
        DataFrame with table information
    """
    import readabs

    try:
        if keyword:
            results = readabs.print_abs_catalogue(keyword)
        else:
            results = readabs.print_abs_catalogue()
        # Results might be a string or DataFrame depending on usage
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def _extract_meta(meta_row: pd.Series, key: str) -> Optional[str]:
    """Safely extract a value from metadata row."""
    if key in meta_row.index:
        val = meta_row[key]
        if val and not pd.isna(val):
            return str(val).strip()
    return None


def _map_abs_frequency(freq_str: Optional[str]) -> str:
    """Map ABS frequency string to standard frequency code.

    Args:
        freq_str: ABS frequency string (e.g., 'Monthly', 'Quarterly', 'Annual')

    Returns:
        Standard frequency code
    """
    if not freq_str:
        return 'M'  # Default to monthly

    freq_lower = freq_str.lower().strip()

    mapping = {
        'daily': 'D',
        'weekly': 'W',
        'monthly': 'M',
        'quarterly': 'Q',
        'annual': 'A',
        'yearly': 'A',
        'half-yearly': 'Q',  # Map to quarterly as closest
        'biannual': 'Q',
    }

    return mapping.get(freq_lower, 'M')
