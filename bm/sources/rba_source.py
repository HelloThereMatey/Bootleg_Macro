"""
Reserve Bank of Australia (RBA) source for bm.

Uses the readabs package for accessing RBA data.
"""

from typing import Optional

import numpy as np
import pandas as pd
import readabs as ra

from ..auxiliary import FrequencyConverter, convert_to_standard_series, calculate_metadata_stats
from ..models import SeriesMetadata, StandardSeries


def pull_rba(
    series_id: str,
    table_no: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> StandardSeries:
    """Pull data from Reserve Bank of Australia.

    Args:
        series_id: RBA series ID (e.g., 'ARBAMPCNCRT' for cash rate)
        table_no: Optional table number (e.g., 'A2', 'C1'). If None, will search for the series.
        start_date: Start date (YYYY-MM-DD) - filters after fetch
        end_date: End date (YYYY-MM-DD) - filters after fetch

    Returns:
        StandardSeries with data and metadata
    """
    if table_no:
        data, meta = ra.read_rba_table(table_no)
    else:
        # Search for the series across tables
        data, meta = _find_rba_series(series_id)

    if series_id not in data.columns:
        raise ValueError(f"Series '{series_id}' not found in RBA data. Available columns: {list(data.columns)}")

    series = data[series_id].dropna()

    # Try to convert to numeric if stored as strings
    if series.dtype == 'object':
        # Try to parse numeric values (handle "17.00 to 17.50" style ranges by taking first value)
        def _parse_rba_value(val):
            if pd.isna(val):
                return np.nan
            s = str(val).strip()
            if s in ('nan', '', 'N/A', '-'):
                return np.nan
            # Handle ranges like "17.00 to 17.50" - take the first number
            if ' to ' in s:
                s = s.split(' to ')[0].strip()
            try:
                return float(s)
            except ValueError:
                return np.nan
        series = series.apply(_parse_rba_value)

    # Get metadata from meta DataFrame
    meta_row = meta[meta['Series ID'] == series_id] if 'Series ID' in meta.columns else None
    if meta_row is not None and len(meta_row) > 0:
        title = meta_row.iloc[0].get('Title', series_id)
        description = meta_row.iloc[0].get('Description', '')
        units = meta_row.iloc[0].get('Units', '')
    else:
        title = series_id
        description = ''
        units = ''

    # Handle PeriodIndex
    if isinstance(series.index, pd.PeriodIndex):
        series = series.to_timestamp()

    series = convert_to_standard_series(series)
    series.name = series_id

    # Filter by date range
    if start_date:
        start = pd.Timestamp(start_date)
        series = series[series.index >= start]
    if end_date:
        end = pd.Timestamp(end_date)
        series = series[series.index <= end]

    # Infer frequency
    freq = pd.infer_freq(series.index)
    std_freq = FrequencyConverter.standardize(freq) if freq else None

    metadata = SeriesMetadata(
        id=series_id,
        title=title,
        source='rba',
        original_source='Reserve Bank of Australia',
        start_date=series.index.min().date() if len(series) > 0 else None,
        end_date=series.index.max().date() if len(series) > 0 else None,
        frequency=std_freq,
        units=units,
        units_short=units,
        description=description,
        **calculate_metadata_stats(series),
    )

    return StandardSeries.from_pandas(series, metadata)


def _find_rba_series(series_id: str, max_tables: int = 50) -> tuple:
    """Find a series across RBA tables.

    Args:
        series_id: Series ID to search for
        max_tables: Maximum number of tables to search

    Returns:
        Tuple of (data, metadata)
    """
    catalogue = ra.rba_catalogue(cache_only=True)
    if catalogue.empty:
        catalogue = ra.rba_catalogue(cache_only=False)

    # Get table list (first max_tables tables)
    table_nums = catalogue.index.tolist()[:max_tables]

    for table_no in table_nums:
        try:
            data, meta = ra.read_rba_table(table_no)
            if series_id in data.columns:
                return data, meta
        except Exception:
            continue

    raise ValueError(f"Series '{series_id}' not found in first {max_tables} RBA tables. "
                      f"Please specify table_no explicitly.")


def list_rba_tables() -> pd.DataFrame:
    """List all available RBA tables.

    Returns:
        DataFrame with table numbers and descriptions
    """
    catalogue = ra.rba_catalogue(cache_only=True)
    if catalogue.empty:
        catalogue = ra.rba_catalogue(cache_only=False)
    return catalogue.reset_index().rename(columns={'index': 'TableNo'})


def search_rba_tables(query: str) -> pd.DataFrame:
    """Search RBA tables by keyword.

    Args:
        query: Search query string

    Returns:
        DataFrame with matching tables
    """
    catalogue = list_rba_tables()
    mask = catalogue['Description'].str.contains(query, case=False, na=False)
    return catalogue[mask]


def search_rba_series(query: str, table_no: Optional[str] = None) -> pd.DataFrame:
    """Search RBA series by keyword.

    Args:
        query: Search query string
        table_no: Optional table to search within

    Returns:
        DataFrame with matching series (Series ID, Title, Table)
    """
    if table_no:
        _, meta = ra.read_rba_table(table_no)
        if 'Title' in meta.columns:
            mask = meta['Title'].str.contains(query, case=False, na=False)
            return meta[mask][['Series ID', 'Title', 'Table']].drop_duplicates()
        return pd.DataFrame()

    # Search across multiple tables
    catalogue = ra.rba_catalogue(cache_only=True)
    if catalogue.empty:
        catalogue = ra.rba_catalogue(cache_only=False)

    results = []
    table_nums = catalogue.index.tolist()[:20]  # Limit search to first 20 tables

    for table in table_nums:
        try:
            _, meta = ra.read_rba_table(table)
            if 'Title' in meta.columns:
                matches = meta[meta['Title'].str.contains(query, case=False, na=False)]
                if not matches.empty:
                    for _, row in matches.iterrows():
                        results.append({
                            'Series ID': row.get('Series ID', ''),
                            'Title': row.get('Title', ''),
                            'Table': table,
                            'Units': row.get('Units', ''),
                        })
        except Exception:
            continue

    if results:
        return pd.DataFrame(results).drop_duplicates()
    return pd.DataFrame()


def get_rba_cash_rate(monthly: bool = True) -> StandardSeries:
    """Get RBA Official Cash Rate.

    Args:
        monthly: If True, return monthly data; if False, return daily

    Returns:
        StandardSeries with cash rate data
    """
    series = ra.read_rba_ocr(monthly=monthly)

    if isinstance(series.index, pd.PeriodIndex):
        series = series.to_timestamp()

    series = convert_to_standard_series(series)
    series.name = 'CashRate'

    std_freq = 'M' if monthly else 'D'

    metadata = SeriesMetadata(
        id='ARBAMPCNCRT',
        title='RBA Official Cash Rate',
        source='rba',
        original_source='Reserve Bank of Australia',
        start_date=series.index.min().date() if len(series) > 0 else None,
        end_date=series.index.max().date() if len(series) > 0 else None,
        frequency=std_freq,
        units='Percent',
        units_short='%',
        description='RBA Official Cash Rate target',
        **calculate_metadata_stats(series),
    )

    return StandardSeries.from_pandas(series, metadata)
