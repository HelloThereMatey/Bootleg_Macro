"""
Auxiliary helper functions for bm data sources.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional, Union

import pandas as pd


def parse_date(date_str: Union[str, date, datetime]) -> date:
    """Parse a date string or date object to date.

    Args:
        date_str: Date as string (YYYY-MM-DD), date, or datetime

    Returns:
        date object
    """
    if isinstance(date_str, datetime):
        return date_str.date()
    if isinstance(date_str, date):
        return date_str
    if isinstance(date_str, str):
        return pd.to_datetime(date_str).date()
    raise ValueError(f"Cannot parse date: {date_str}")


def infer_frequency(series: pd.Series) -> Optional[str]:
    """Infer the frequency code from a pandas Series index.

    Args:
        series: pandas Series with DatetimeIndex

    Returns:
        Frequency string (e.g., 'D', 'W', 'M', 'Q', 'A') or None
    """
    if not isinstance(series.index, pd.DatetimeIndex):
        return None

    freq = pd.infer_freq(series.index)
    if freq is None:
        return None

    # Normalize to single letter codes
    freq_upper = freq.upper()

    if freq_upper.startswith('D') or freq_upper == 'B':
        return 'D'
    elif freq_upper.startswith('W'):
        return 'W'
    elif any(f in freq_upper for f in ['M', 'ME', 'MS', 'BM', 'BMS']):
        return 'M'
    elif any(f in freq_upper for f in ['Q', 'QE', 'QS', 'BQ', 'BQS']):
        return 'Q'
    elif any(f in freq_upper for f in ['Y', 'YE', 'YS', 'A', 'AE', 'AS']):
        return 'A'

    # Handle compound frequencies like 'Q-DEC'
    match = re.match(r'([A-Z])[-]?', freq_upper)
    if match:
        code = match.group(1)
        if code == 'D':
            return 'D'
        elif code == 'W':
            return 'W'
        elif code in ('M', 'ME', 'MS'):
            return 'M'
        elif code in ('Q', 'QE', 'QS'):
            return 'Q'
        elif code in ('Y', 'A'):
            return 'A'

    return None


def sanitize_string(value: str) -> str:
    """Clean a string for safe use in identifiers.

    Args:
        value: String to clean

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    # Replace non-alphanumeric with underscore, collapse multiple underscores
    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '_', value)
    cleaned = re.sub(r'_+', '_', cleaned)
    return cleaned.strip('_')


def hdf_key_safe(key: str) -> str:
    """Sanitize a string to be a valid HDF5 store key.

    Args:
        key: Raw key string

    Returns:
        Key safe for use in pd.HDFStore
    """
    cleaned = re.sub(r'[^a-zA-Z0-9_/]', '_', str(key))
    cleaned = re.sub(r'_+', '_', cleaned)
    if cleaned and not (cleaned[0].isalpha() or cleaned[0] == '_'):
        cleaned = '_' + cleaned
    return cleaned


def convert_to_standard_series(
    data: Union[pd.Series, pd.DataFrame],
    name: Optional[str] = None
) -> pd.Series:
    """Convert DataFrame to Series or ensure Series is properly formatted.

    Args:
        data: pandas Series or DataFrame
        name: Name to assign if not present

    Returns:
        Properly formatted pandas Series
    """
    if isinstance(data, pd.DataFrame):
        if len(data.columns) == 1:
            data = data.iloc[:, 0]
        else:
            raise ValueError("DataFrame with multiple columns cannot be converted to StandardSeries")
    elif not isinstance(data, pd.Series):
        raise ValueError("Input must be pandas Series or DataFrame")

    series = data.copy()

    # Ensure index is DatetimeIndex
    if hasattr(series.index, 'to_timestamp'):
        # Handle PeriodIndex by converting to timestamps
        series.index = series.index.to_timestamp()
    elif not isinstance(series.index, pd.DatetimeIndex):
        series.index = pd.to_datetime(series.index)

    # Deduplicate index
    series = series[~series.index.duplicated(keep='first')]

    # Sort by date
    series = series.sort_index()

    # Assign name if missing
    if series.name is None:
        series.name = name or 'value'

    return series


def calculate_metadata_stats(series: pd.Series) -> dict:
    """Calculate statistical metadata from a series.

    Args:
        series: pandas Series with DatetimeIndex

    Returns:
        Dictionary of calculated statistics (length, min_value, max_value)
    """
    if not isinstance(series, pd.Series):
        return {}

    vals = series.dropna()

    stats = {
        'length': int(len(vals)),
        'min_value': float(vals.min()) if len(vals) > 0 else None,
        'max_value': float(vals.max()) if len(vals) > 0 else None,
    }

    return stats


class FrequencyConverter:
    """Helper to convert between different frequency representations."""

    # Map common frequency strings to standardized codes
    TO_STANDARD = {
        'd': 'D', 'daily': 'D', 'b': 'D', 'business': 'D',
        'w': 'W', 'weekly': 'W',
        'm': 'M', 'monthly': 'M', 'me': 'M', 'ms': 'M', 'bm': 'M', 'bms': 'M',
        'q': 'Q', 'quarterly': 'Q', 'qe': 'Q', 'qs': 'Q', 'bq': 'Q', 'bqs': 'Q',
        'a': 'A', 'annual': 'A', 'y': 'A', 'yearly': 'A',
        'ye': 'A', 'ys': 'A', 'ae': 'A', 'as': 'A',
    }

    # Pandas offset aliases for resampling
    PANDAS_OFFSETS = {
        'D': 'D', 'W': 'W-SUN', 'M': 'ME', 'Q': 'QE', 'A': 'YE',
    }

    @classmethod
    def standardize(cls, freq: str) -> str:
        """Convert various frequency representations to standard code.

        Args:
            freq: Frequency string (e.g., 'daily', '1D', 'Q', 'quarterly')

        Returns:
            Standardized frequency code: 'D', 'W', 'M', 'Q', or 'A'
        """
        if freq is None:
            return 'M'  # Default to monthly

        freq_clean = str(freq).strip().lower()

        # Handle numeric prefixes like '1D', '1d', '1W'
        match = re.match(r'^(\d+)([a-zA-Z]+)$', freq_clean)
        if match:
            freq_clean = match.group(2)

        return cls.TO_STANDARD.get(freq_clean, 'M')

    @classmethod
    def to_pandas_offset(cls, freq: str) -> str:
        """Get pandas offset string for resampling.

        Args:
            freq: Standard frequency code

        Returns:
            Pandas offset alias
        """
        return cls.PANDAS_OFFSETS.get(cls.standardize(freq), 'D')
