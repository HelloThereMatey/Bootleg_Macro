"""
Nasdaq Data Link source for bm.

Uses the nasdaqdatalink package (Nasdaq-Data-Link).
"""

from typing import Optional

import nasdaqdatalink as ndl
import pandas as pd

from ..auxiliary import FrequencyConverter, convert_to_standard_series, calculate_metadata_stats
from ..models import SeriesMetadata, StandardSeries


def pull_nasdaq(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None,
) -> StandardSeries:
    """Pull data from Nasdaq Data Link.

    Args:
        symbol: Nasdaq Data Link symbol (e.g., 'WIKI/AAPL', 'ECONOMIA/DEXUSEU')
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        api_key: Nasdaq Data Link API key

    Returns:
        StandardSeries with data and metadata
    """
    if api_key:
        ndl.ApiConfig.api_key = api_key

    # Fetch data
    data = ndl.get(symbol, start_date=start_date, end_date=end_date)

    # Handle DataFrame vs Series
    if isinstance(data, pd.DataFrame):
        if len(data.columns) == 1:
            series = data.iloc[:, 0]
        else:
            # Multiple columns - use first
            series = data.iloc[:, 0]
    else:
        series = data

    series = convert_to_standard_series(series)
    series.name = symbol.replace('/', '_')

    # Build metadata
    metadata = SeriesMetadata(
        id=symbol.replace('/', '_'),
        title=symbol,
        source='nasdaq',
        original_source='Nasdaq Data Link',
        start_date=series.index.min().date() if len(series) > 0 else None,
        end_date=series.index.max().date() if len(series) > 0 else None,
        frequency=FrequencyConverter.standardize(pd.infer_freq(series.index)) if pd.infer_freq(series.index) else None,
        **calculate_metadata_stats(series),
    )

    return StandardSeries.from_pandas(series, metadata)


def search_nasdaq(
    query: str,
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Search Nasdaq Data Link for datasets matching query.

    Args:
        query: Search query string
        api_key: Nasdaq Data Link API key

    Returns:
        DataFrame with search results
    """
    if api_key:
        ndl.ApiConfig.api_key = api_key

    try:
        results = ndl.search(query)
        return pd.DataFrame(results)
    except Exception:
        return pd.DataFrame()


def get_nasdaq_metadata(
    symbol: str,
    api_key: Optional[str] = None,
) -> dict:
    """Get metadata for a Nasdaq dataset without fetching data.

    Args:
        symbol: Nasdaq Data Link symbol
        api_key: Nasdaq Data Link API key

    Returns:
        Dict with dataset metadata
    """
    if api_key:
        ndl.ApiConfig.api_key = api_key

    try:
        meta = ndl.get_metadata(symbol)
        return meta
    except Exception:
        return {}