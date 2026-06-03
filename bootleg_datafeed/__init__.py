"""
bootleg_datafeed — Core data acquisition module.

Provides a unified interface for pulling financial/economic time series
from 11+ sources, with standardized metadata and search.
"""

from .models import SeriesMetadata, StandardSeries
from .dataset import Dataset, SOURCES, KEY_SOURCES
from .auxiliary import (
    parse_date,
    infer_frequency,
    sanitize_string,
    hdf_key_safe,
    convert_to_standard_series,
    calculate_metadata_stats,
    FrequencyConverter,
    drop_duplicate_columns,
    close_open_stores,
    strip_timezone_from_df,
)
from .search import WatchlistSearch

__version__ = "0.1.0"

__all__ = [
    # Models
    "SeriesMetadata",
    "StandardSeries",
    # Dataset
    "Dataset",
    "SOURCES",
    "KEY_SOURCES",
    # Auxiliary
    "parse_date",
    "infer_frequency",
    "sanitize_string",
    "hdf_key_safe",
    "convert_to_standard_series",
    "calculate_metadata_stats",
    "FrequencyConverter",
    "drop_duplicate_columns",
    "close_open_stores",
    "strip_timezone_from_df",
    # Search
    "WatchlistSearch",
]
