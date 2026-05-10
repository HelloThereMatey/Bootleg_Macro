"""
bm - Bootleg Macro Data Library

A clean, refactored library for obtaining financial and economic data series
with standardized metadata and output formats.
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
from .watchlist import Watchlist
from .search import WatchlistSearch
from . import charting

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
    # Watchlist
    "Watchlist",
    "WatchlistSearch",
    # Charting
    "charting",
]
