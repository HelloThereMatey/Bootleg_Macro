"""Extend the history of ABS time series by splicing cross-frequency siblings.

This module provides a self-contained way to take an ABS series at any
frequency (e.g. monthly or quarterly) and extend its history by
concatenating data from a sibling series at a different frequency.

Usage
-----
    >>> from readabs.extend_history import extend_series

    >>> data, meta = extend_series("A130392586J")
    >>> len(data)
    246

    >>> data_dict, meta = extend_catalogue("6401.0")
    >>> len(data_dict)
    ...
"""

from .extend_history import (
    extend_catalogue,
    extend_series,
    find_cat_for_series,
)

__all__ = [
    "extend_catalogue",
    "extend_series",
    "find_cat_for_series",
]
