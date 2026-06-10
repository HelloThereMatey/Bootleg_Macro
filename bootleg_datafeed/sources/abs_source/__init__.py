"""
ABS data source package for bm.

Provides data pulling and search for Australian Bureau of Statistics
time series, with optional history-extension via the extend_history module.
"""

from __future__ import annotations

from .abs_source import pull_abs, search_abs, browse_abs_tables

__all__ = [
    "pull_abs",
    "search_abs",
    "browse_abs_tables",
]
