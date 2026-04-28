"""
FRED (Federal Reserve Economic Data) source for bm.

Uses the FRED API to pull US macroeconomic data.
Requires API key.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

import pandas as pd
import requests

from ..auxiliary import FrequencyConverter, convert_to_standard_series, calculate_metadata_stats
from ..models import SeriesMetadata, StandardSeries


FRED_BASE_URL = "https://api.stlouisfed.org/fred"


def pull_fred(
    series_id: str,
    api_key: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> StandardSeries:
    """Pull time series data from FRED.

    Args:
        series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'FEDFUNDS')
        api_key: FRED API key
        start_date: Start date (YYYY-MM-DD), default '1776-07-04'
        end_date: End date (YYYY-MM-DD), default today

    Returns:
        StandardSeries with data and metadata

    Raises:
        ValueError: If API key invalid or series not found
    """
    if not api_key or len(api_key) < 5:
        raise ValueError("Valid FRED API key is required")

    # Set defaults
    if end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = '1776-07-04'  # FRED's practical earliest

    # Validate date range
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        if start_dt > end_dt:
            raise ValueError("start_date must be before end_date")
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e}")

    filetype = "json"

    # First, get series info
    info_url = f"{FRED_BASE_URL}/series"
    info_params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": filetype,
    }

    info_response = requests.get(info_url, params=info_params)
    if info_response.status_code != 200:
        raise ValueError(f"FRED API error: {info_response.status_code} - {info_response.text}")

    info_data = info_response.json()
    if 'seriess' not in info_data or not info_data['seriess']:
        raise ValueError(f"Series not found: {series_id}")

    series_info = info_data['seriess'][0]

    # Now get the actual data
    data_url = f"{FRED_BASE_URL}/series/observations"
    data_params = {
        "series_id": series_id,
        "api_key": api_key,
        "observation_start": start_date,
        "observation_end": end_date,
        "file_type": filetype,
    }

    data_response = requests.get(data_url, params=data_params)
    if data_response.status_code != 200:
        raise ValueError(f"FRED API error: {data_response.status_code} - {data_response.text}")

    data_json = data_response.json()
    if 'observations' not in data_json or not data_json['observations']:
        raise ValueError(f"No observations found for series: {series_id}")

    # Parse observations
    observations = data_json['observations']
    dates = []
    values = []

    for obs in observations:
        date_str = obs['date']
        value = obs['value']

        # Skip missing values
        if value in ['.', '/', '', None]:
            continue

        try:
            dates.append(pd.to_datetime(date_str))
            values.append(float(value))
        except (ValueError, TypeError):
            continue

    if not dates:
        raise ValueError(f"No valid observations for series: {series_id}")

    series = pd.Series(values, index=pd.DatetimeIndex(dates), name=series_id)
    series = convert_to_standard_series(series)

    # Extract metadata from series_info
    title = series_info.get('title', series_id)
    units = series_info.get('units', '')
    units_short = series_info.get('units_short', units)
    frequency = _map_fred_frequency(series_info.get('frequency', ''))
    description = series_info.get('notes', '')

    # Calculate date range from data (not request params)
    actual_start = series.index.min().date() if len(series) > 0 else None
    actual_end = series.index.max().date() if len(series) > 0 else None

    metadata = SeriesMetadata(
        id=series_id,
        title=title,
        source='fred',
        original_source='FRED (Federal Reserve Economic Data)',
        start_date=actual_start,
        end_date=actual_end,
        frequency=frequency,
        units=units,
        units_short=units_short,
        description=description,
        **calculate_metadata_stats(series),
    )

    return StandardSeries.from_pandas(series, metadata)


def search_fred(search_text: str, api_key: str) -> pd.DataFrame:
    """Search FRED series by keyword.

    Args:
        search_text: Search term
        api_key: FRED API key

    Returns:
        DataFrame with matching series
    """
    if not api_key or len(api_key) < 5:
        raise ValueError("Valid FRED API key is required")

    results = []
    for search_type in ['series_id', 'full_text']:
        url = f"{FRED_BASE_URL}/series/search"
        params = {
            "search_text": search_text,
            "search_type": search_type,
            "api_key": api_key,
            "file_type": "json",
        }

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'seriess' in data:
                results.extend(data['seriess'])

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    # Limit to useful columns
    cols = [c for c in ['series_id', 'title', 'units', 'frequency', 'last_updated'] if c in df.columns]
    return df[cols]


def _map_fred_frequency(fred_freq: str) -> str:
    """Map FRED frequency string to standard frequency code.

    Args:
        fred_freq: FRED frequency string (e.g., 'Monthly', 'Quarterly')

    Returns:
        Standard frequency code
    """
    freq_lower = fred_freq.lower().strip()

    mapping = {
        'daily': 'D',
        'weekly': 'W',
        'monthly': 'M',
        'quarterly': 'Q',
        'annual': 'A',
        'semiannual': 'A',
    }

    return mapping.get(freq_lower, 'M')
