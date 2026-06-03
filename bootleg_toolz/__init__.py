"""
bootleg_toolz — Watchlist management, charting, and data utilities.

Built on top of bootleg_datafeed. Provides multi-series watchlist
management, Plotly charting, and data transformation utilities.
"""

from .watchlist import Watchlist
from . import charting
from . import data_processing

__version__ = "0.1.0"

__all__ = [
    "Watchlist",
    "charting",
    "data_processing",
]
