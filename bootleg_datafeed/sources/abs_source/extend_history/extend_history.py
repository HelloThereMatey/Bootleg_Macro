"""Extend the history of ABS time series by splicing lower-frequency siblings.

This module provides a self-contained way to take a higher-frequency ABS series
(e.g. monthly) and extend its history backwards by concatenating the data from
a lower-frequency sibling (e.g. quarterly).  The sibling is discovered
automatically from a packaged master index by matching on the exact data item
description.

Usage
-----
    >>> from readabs.extend_history import extend_series

    >>> data, meta = extend_series("A130392586J")
    >>> type(data).__name__
    'Series'
    >>> len(data)
    246

    >>> data_dict, meta = extend_catalogue("6401.0")
    >>> len(data_dict)
    ...
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from functools import cache
from importlib import resources
from typing import Any

import pandas as pd
from pandas import DataFrame, Series

import readabs as ra
from readabs.read_abs_cat import read_abs_cat

# Frequency hierarchy — lower number = lower frequency
_FREQ_RANK: dict[str, int] = {"Y": 0, "Q": 1, "M": 2, "W": 3, "D": 4}
# Module-level cache for historical downloads per (cat, history) pair
# Value is a tuple of (data_dict, metadata_or_None)
_historical_cache: dict[tuple[str, str], tuple[dict[str, DataFrame], DataFrame | None]] = {}


def _log(verbose: bool, msg: str, *args: Any) -> None:
    """Print a diagnostic message when *verbose* is ``True``."""
    if verbose:
        print(f"[extend] {msg % args}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extend_series(
    series_id: str,
    cat: str | None = None,
    **kwargs: Any,
) -> tuple[Series, DataFrame]:
    """Return a single ABS series with history extended by a sibling.

    When the series has a sibling at a different frequency (e.g. monthly ↔
    quarterly) the two are spliced together to produce a single continuous
    series covering the full date range.  Works in both directions:
    passing a monthly series extends backwards with quarterly data; passing
    a quarterly series extends forwards with monthly data.

    Parameters
    ----------
    series_id : str
        The ABS series identifier to extend (e.g. ``"A130392586J"``).

    cat : str, optional
        The ABS catalogue number.  If omitted, it is looked up from the
        packaged master index automatically.

    **kwargs
        Passed through to :func:`readabs.read_abs_series` and the underlying
        :func:`readabs.read_abs_cat` call for historical downloads.  See the
        documentation of those functions for supported parameters.

    Returns
    -------
    tuple[pd.Series, DataFrame]
        ``(data, metadata)`` where *data* is a :class:`pd.Series` indexed by
        date and *metadata* is a :class:`DataFrame` containing the series
        metadata.

    Raises
    ------
    ValueError
        If *series_id* is not found in the master index, or if it cannot be
        fetched from either the current catalogue or any historical release.

    """
    idx = load_master_index()
    series_id = series_id.strip()
    verbose = kwargs.get("verbose", False)

    # Resolve catalogue number if not provided
    if not cat:
        cat = find_cat_for_series(series_id, master_index=idx)
        _log(verbose, "Resolved catalogue: %s", cat)

    # --- 1. Try to get base data from the current catalogue ---
    base_data: DataFrame | None = None
    base_meta: DataFrame | None = None
    cat_kwargs = _inject_table_filter(series_id, idx, kwargs)
    try:
        base_data, base_meta = ra.read_abs_series(cat, series_id, **cat_kwargs)
        _log(
            verbose,
            "Got base series: %d obs (%s to %s)",
            len(base_data),
            base_data.index[0],
            base_data.index[-1],
        )
    except ValueError:
        _log(verbose, "Series %s not in current catalogue %s", series_id, cat)

    # --- 2. Find a sibling (any frequency) ---
    sibling = _find_sibling(series_id, master_index=idx)
    if sibling is None:
        _log(verbose, "No sibling found — returning base data")
        if base_data is not None:
            assert base_meta is not None  # read_abs_series always returns meta
            return base_data[series_id], base_meta
        raise ValueError(f"Series '{series_id}' not found in catalogue {cat} and no sibling available.")

    # --- 3. Determine roles: higher-freq (current) vs lower-freq (historical) ---
    higher_id, lower_id, higher_data, higher_meta = _resolve_higher_freq_series(
        series_id,
        sibling,
        base_data,
        base_meta,
        cat,
        idx=idx,
        **kwargs,
    )

    # --- 4. Determine historical release for lower-frequency data ---
    higher_start = _series_start_from_idx(higher_id, idx)
    lower_end = _series_end_from_idx(lower_id, idx)
    history = _find_historical_release(higher_start, lower_end)
    if not history:
        _log(verbose, "Could not determine historical release — returning base data")
        return higher_data[higher_id], higher_meta
    _log(
        verbose,
        "Historical release: %s (higher-freq starts %s, lower-freq ends %s)",
        history,
        higher_start,
        lower_end,
    )

    # --- 5. Fetch historical catalogue data ---
    hist_dict, hist_meta = _fetch_historical_data(cat, history, **kwargs)
    _log(verbose, "Historical catalogue: %d tables fetched", len(hist_dict))

    # --- 6. Find lower-frequency column in historical tables ---
    lower_col = _find_sibling_column(hist_dict, lower_id)
    if lower_col is None:
        _log(verbose, "Lower-freq series not found in historical tables — returning higher-freq data")
        return higher_data[higher_id], higher_meta
    _log(
        verbose,
        "Lower-freq column found: %d non-NaN obs (%s to %s)",
        lower_col.notna().sum(),
        lower_col.index[0],
        lower_col.index[-1],
    )

    # --- 7. Concatenate: lower (older) + higher (newer) ---
    extended = _concat_frequencies(lower_col, higher_data[higher_id], series_id, verbose=verbose)
    _log(
        verbose,
        "Extended result: %d non-NaN obs (%s to %s)",
        extended.notna().sum(),
        extended.index[0],
        extended.index[-1],
    )

    # --- 8. Build metadata for the requested series_id ---
    _log(verbose, "Building result metadata")
    result_meta = _build_result_meta(series_id, higher_id, lower_id, higher_meta, hist_meta)
    return extended, result_meta


def _build_result_meta(
    series_id: str,
    higher_id: str,
    lower_id: str,
    higher_meta: DataFrame | None,
    hist_meta: DataFrame | None,
) -> DataFrame:
    """Build metadata for *series_id*, preferring current-catalogue metadata."""
    if series_id == higher_id and higher_meta is not None:
        return higher_meta
    if series_id == lower_id and hist_meta is not None:
        try:
            return hist_meta.set_index("Series ID").loc[[series_id]]
        except (KeyError, AttributeError):
            pass
    return higher_meta if higher_meta is not None else DataFrame()


def _resolve_higher_freq_series(
    series_id: str,
    sibling: pd.Series,
    base_data: DataFrame | None,
    base_meta: DataFrame | None,
    cat: str,
    *,
    idx: DataFrame,
    **kwargs: Any,
) -> tuple[str, str, DataFrame, DataFrame]:
    """Compare frequencies of *series_id* and *sibling*, then fetch the higher-freq series.

    Returns ``(higher_id, lower_id, higher_data, higher_meta)``.
    The higher-frequency series is always fetched from the current catalogue.
    """
    # ignore too-many-args: bundled helper to avoid complexity in extend_series
    series_freq = _series_freq_from_idx(series_id, idx)

    sibling_id = str(sibling["Series ID"])
    sibling_freq = str(sibling.get("frequency", "")).strip().upper()[0] if sibling.get("frequency") else ""

    series_rank = _FREQ_RANK.get(series_freq, 99)
    sibling_rank = _FREQ_RANK.get(sibling_freq, 99)
    verbose = kwargs.get("verbose", False)

    higher_id: str
    lower_id: str
    if sibling_rank > series_rank:
        higher_id, lower_id = sibling_id, series_id
        _log(
            verbose,
            "Series is lower-freq (%s); sibling %s is higher-freq (%s)",
            series_freq,
            sibling_id,
            sibling_freq,
        )
    else:
        higher_id, lower_id = series_id, sibling_id

    if higher_id == series_id and base_data is not None:
        assert base_meta is not None
        return higher_id, lower_id, base_data, base_meta

    _log(verbose, "Fetching higher-freq series %s from current catalogue", higher_id)
    higher_kwargs = _inject_table_filter(higher_id, idx, kwargs)
    higher_data, higher_meta = ra.read_abs_series(cat, higher_id, **higher_kwargs)
    _log(
        verbose,
        "Got higher-freq series: %d obs (%s to %s)",
        len(higher_data),
        higher_data.index[0],
        higher_data.index[-1],
    )
    return higher_id, lower_id, higher_data, higher_meta


# ---------------------------------------------------------------------------
# Sibling discovery & historical release calculation


def extend_catalogue(cat: str, **kwargs: Any) -> tuple[dict[str, DataFrame], DataFrame]:
    """Return a full ABS catalogue with every series extended where possible.

    Parameters
    ----------
    cat : str
        The ABS catalogue number (e.g. ``"6401.0"``).

    **kwargs
        Passed through to :func:`readabs.read_abs_cat` and historical downloads.

    Returns
    -------
    tuple[dict[str, DataFrame], DataFrame]
        ``(data_dict, metadata)`` in the same format as :func:`readabs.read_abs_cat`.

    """
    idx = load_master_index()
    verbose = kwargs.get("verbose", False)
    data_dict, meta = read_abs_cat(cat, **kwargs)
    _log(verbose, "Catalogue %s: %d tables loaded", cat, len(data_dict))

    for table_name in list(data_dict.keys()):
        tbl = data_dict[table_name]
        for col in tbl.columns:
            sid = str(col)
            # Check this series has a sibling of a different frequency
            sibling = _find_sibling(sid, master_index=idx)
            if sibling is None:
                continue

            sibling_id = str(sibling["Series ID"])
            _log(verbose, "Extending %s in %s via sibling %s", sid, table_name, sibling_id)

            sid_start = _series_start_from_idx(sid, idx)
            sibling_end = _series_end_from_idx(sibling_id, idx)
            # For extend_catalogue the sid is always from the current catalogue
            # (higher-freq), so use sid_start as higher_start
            history = _find_historical_release(sid_start, sibling_end)
            if not history:
                _log(verbose, "  no historical release found — skipping")
                continue
            _log(verbose, "  historical release: %s", history)

            hist_dict, _hist_meta = _fetch_historical_data(cat, history, **kwargs)
            sibling_col = _find_sibling_column(hist_dict, sibling_id)
            if sibling_col is None:
                _log(verbose, "  sibling not found in historical tables — skipping")
                continue
            _log(verbose, "  sibling column: %d non-NaN obs", sibling_col.notna().sum())

            extended = _concat_frequencies(sibling_col, tbl[col], sid, verbose=verbose)
            data_dict[table_name] = data_dict[table_name].assign(**{sid: extended})
            _log(verbose, "  extended: %d non-NaN obs", extended.notna().sum())

    return data_dict, meta


def find_cat_for_series(
    series_id: str,
    *,
    master_index: DataFrame | None = None,
    verbose: bool = False,
) -> str:
    """Return the ABS catalogue number that contains *series_id*.

    Parameters
    ----------
    series_id : str
        The ABS series identifier to look up (e.g. ``"A84423050A"``).

    master_index : DataFrame, optional
        A pre-loaded master index.  If omitted, the shipped index is loaded
        (and cached) automatically.

    verbose : bool
        Print diagnostic messages when ``True``.

    Returns
    -------
    str
        The catalogue number (e.g. ``"6202.0"``).

    Raises
    ------
    ValueError
        If *series_id* is not found in the master index.

    """
    if not series_id or not series_id.strip():
        raise ValueError("series_id must be a non-empty string.")

    idx = master_index if master_index is not None else load_master_index()
    series_id = series_id.strip()
    row = _lookup_series_by_id(idx, series_id)

    raw = str(row["catalogue_number"]) if isinstance(row, pd.Series) else str(row["catalogue_number"].iloc[0])
    cat = _normalise_cat(raw)

    if verbose:
        print(f"Found series '{series_id}' in catalogue {cat}.")
    return cat


# ---------------------------------------------------------------------------
# Master index
# ---------------------------------------------------------------------------


@cache
def load_master_index() -> DataFrame:
    """Load the ABS series master index from the package data directory.

    The returned DataFrame has columns ``Series ID``, ``catalogue_number``,
    ``description``, ``frequency``, ``series_start``, ``series_end``,
    ``table``, ``unit``, indexed by ``Series ID``.  The result is cached so
    repeated calls return instantly after the first load.

    Returns
    -------
    DataFrame
        Master index with one row per unique series ID.

    """
    csv_path = str(resources.files("bootleg_datafeed.sources.abs_source.extend_history.data").joinpath("abs_series_map.csv.gz"))
    idx: DataFrame = pd.read_csv(csv_path, compression="gzip", dtype=str)
    idx.index = pd.Index(idx["Series ID"])
    idx.index.name = "Series ID"
    return idx


# ---------------------------------------------------------------------------
# Sibling discovery & historical release calculation
# ---------------------------------------------------------------------------


def _find_sibling(
    series_id: str,
    *,
    master_index: DataFrame | None = None,
    direction: str = "any",
) -> pd.Series | None:
    """Find a sibling for *series_id* by matching on description.

    Matches on exact ``description`` in the master index, excludes
    *series_id* itself, and returns the sibling with the closest
    frequency in the requested direction.

    Parameters
    ----------
    series_id : str
        The ABS series identifier.

    master_index : DataFrame, optional
        Pre-loaded master index.

    direction : str
        ``"lower"`` — siblings with strictly lower frequency only.
        ``"higher"`` — siblings with strictly higher frequency only.
        ``"any"`` (default) — closest sibling regardless of direction.

    Returns
    -------
    pd.Series or None
        The sibling row, or ``None`` if no matching sibling exists.

    """
    idx = master_index if master_index is not None else load_master_index()
    row = _lookup_series_by_id(idx, series_id)

    desc = _get_field(row, "description")
    if not desc:
        return None

    freq = _get_field(row, "frequency")
    series_freq = freq.strip().upper()[0] if freq else ""

    # All rows with the same description
    mask = idx["description"] == desc
    candidates = idx[mask].copy()
    # Remove self
    candidates = candidates[candidates["Series ID"] != series_id]

    if candidates.empty:
        return None

    # Assign frequency rank
    candidates["_freq_rank"] = candidates["frequency"].str.strip().str[0].map(_FREQ_RANK).fillna(99).astype(int)
    target_rank = _FREQ_RANK.get(series_freq, 99)

    if direction == "lower":
        candidates = candidates[candidates["_freq_rank"] < target_rank]
        if candidates.empty:
            return None
        candidates = candidates.sort_values("_freq_rank", ascending=False)
    elif direction == "higher":
        candidates = candidates[candidates["_freq_rank"] > target_rank]
        if candidates.empty:
            return None
        candidates = candidates.sort_values("_freq_rank", ascending=True)
    else:  # "any"
        # Exclude same-frequency siblings (no extension possible)
        candidates = candidates[candidates["_freq_rank"] != target_rank]
        if candidates.empty:
            return None
        # Closest rank difference (lowest abs diff)
        candidates["_rank_diff"] = (candidates["_freq_rank"] - target_rank).abs()
        candidates = candidates.sort_values("_rank_diff")

    return candidates.iloc[0]


def _find_lower_freq_sibling(
    series_id: str,
    *,
    master_index: DataFrame | None = None,
) -> pd.Series | None:
    """Find the next-lower-frequency sibling for *series_id*.

    Thin wrapper around :func:`_find_sibling` for backward compatibility.
    """
    return _find_sibling(series_id, master_index=master_index, direction="lower")


def _find_historical_release(higher_start: str, lower_end: str) -> str | None:
    """Determine the historical release period at a frequency transition.

    Given the start date of a higher-frequency series (e.g. monthly) and
    the end date of its lower-frequency sibling (e.g. quarterly),
    identifies which historical release (e.g. ``"jun-2022"``) to download.

    The logic finds the latest quarter-end that is *before* the higher-frequency
    series started and *not before* the lower-frequency data ends.

    Returns
    -------
    str or None
        A release period string (e.g. ``"jun-2022"``) or ``None``.

    """
    try:
        m_start = pd.Timestamp(higher_start)
        q_end = pd.Timestamp(lower_end)
    except (ValueError, TypeError):
        return None

    quarter_months = [3, 6, 9, 12]
    # Try current year, then previous year
    for year_offset in (0, -1):
        yr = m_start.year + year_offset
        # Avoid searching negative years
        if yr < 1970:  # noqa: PLR2004
            break
        for qm in reversed(quarter_months):
            release_ts = pd.Timestamp(year=yr, month=qm, day=1)
            if release_ts >= q_end.replace(day=1):
                # Don't go earlier than the lower-freq data extends
                continue
            if yr == m_start.year and qm >= m_start.month:
                # Must be strictly before the higher-freq series started
                continue
            return release_ts.strftime("%b-%Y").lower()

    return None


# ---------------------------------------------------------------------------
# Historical data fetching
# ---------------------------------------------------------------------------


def _fetch_historical_data(
    cat: str,
    history: str,
    **kwargs: Any,
) -> tuple[dict[str, DataFrame], DataFrame | None]:
    """Download the full catalogue as it stood at a historical release.

    Results are cached in the module-level ``_historical_cache`` dict keyed
    by ``(cat, history)`` so repeated calls for the same history return
    instantly.

    Returns
    -------
    tuple[dict[str, DataFrame], DataFrame | None]
        ``(data_dict, metadata)`` — the catalogue data and its metadata.
        Metadata is the second element (may be ``None`` if not available).

    """
    key = (cat, history)
    if key in _historical_cache:
        return _historical_cache[key]

    # Force Excel-only, suppress errors — historical releases won't have ZIPs
    # and some files won't exist in older releases
    hist_kwargs: dict[str, Any] = {
        "get_zip": False,
        "get_excel": True,
        "ignore_errors": True,
        "history": history,
    }
    # Only forward kwargs that are meaningful for read_abs_cat
    for k in ("verbose", "cache_only"):
        if k in kwargs:
            hist_kwargs[k] = kwargs[k]

    with redirect_stdout(io.StringIO()):
        hist_dict, hist_meta = read_abs_cat(cat, **hist_kwargs)

    _historical_cache[key] = (hist_dict, hist_meta)
    return hist_dict, hist_meta


# ---------------------------------------------------------------------------
# Concat helpers
# ---------------------------------------------------------------------------


def _concat_frequencies(
    lower: pd.Series,
    higher: pd.Series,
    name: str,
    *,
    verbose: bool = False,
) -> pd.Series:
    """Concatenate a lower-frequency series under a higher-frequency series.

    The result covers the full span of both inputs, with the higher-frequency
    data taking precedence where periods overlap.

    Before concatenating, the lower-frequency series is **rebased** so that
    its last valid value matches the first valid value of the higher-frequency
    series.  This handles level shifts caused by ABS index reference period
    changes (e.g. quarterly on old base 114.6 → monthly on new base 82.63).

    The higher-frequency series is also truncated to start at its first
    non-NaN value, preventing pre-data NaN rows from wiping out valid
    lower-frequency data at the same DatetimeIndex points.

    Parameters
    ----------
    lower : pd.Series
        Older, lower-frequency data (e.g. quarterly).
    higher : pd.Series
        Newer, higher-frequency data (e.g. monthly).
    name : str
        Name for the resulting series.
    verbose : bool
        Print diagnostic messages.

    Returns
    -------
    pd.Series
        A single series covering the combined date range.

    """
    # --- truncate higher-freq series to its valid range ---
    valid_start = higher.first_valid_index()
    if valid_start is not None and isinstance(valid_start, (pd.Period, pd.Timestamp)):
        loc = higher.index.get_loc(valid_start)
        pre_count = loc if isinstance(loc, int) else 0
        if pre_count > 0:
            _log(verbose, "  truncating higher-freq: dropping %d pre-data NaN rows", pre_count)
            higher = higher.loc[valid_start:]

    # --- rebase lower-freq series to higher-freq level ---
    higher_first = float(higher.iloc[0])
    lower_last_idx = lower.last_valid_index()
    if lower_last_idx is not None:
        lower_last = float(lower.loc[lower_last_idx])
        ratio = higher_first / lower_last
        _log(
            verbose,
            "  rebasing lower-freq: scale factor %.6f (higher_first=%.4f / lower_last=%.4f)",
            ratio,
            higher_first,
            lower_last,
        )
        lower = lower * ratio
    else:
        _log(verbose, "  no valid lower-freq values — skipping rebase")

    # Convert to DatetimeIndex so mixed frequencies (Q / M) are sortable
    lower_dti = pd.DatetimeIndex(lower.index.map(lambda p: p.start_time))
    higher_dti = pd.DatetimeIndex(higher.index.map(lambda p: p.start_time))

    combined = pd.concat(
        [
            pd.Series(lower.values, index=lower_dti),
            pd.Series(higher.values, index=higher_dti),
        ]
    )
    # Remove duplicate index entries — keep the last (higher-freq) value
    combined = combined[~combined.index.duplicated(keep="last")]
    combined = combined.sort_index()
    combined.name = name
    return combined


def _find_sibling_column(
    data_dict: dict[str, DataFrame],
    sibling_id: str,
) -> pd.Series | None:
    """Search all tables in *data_dict* for a column matching *sibling_id*.

    Returns the column as a Series, or ``None`` if the sibling is not found
    in any table.
    """
    for tbl in data_dict.values():
        if sibling_id in tbl.columns:
            return tbl[sibling_id]
    return None


# ---------------------------------------------------------------------------
# Master-index helpers
# ---------------------------------------------------------------------------


def _inject_table_filter(series_id: str, idx: DataFrame, kwargs: dict) -> dict:
    """Return *kwargs* with ``single_excel_only`` set from the master index.

    If *kwargs* already contains ``single_excel_only`` or ``selected_excel``
    the original dict is returned unchanged.  If the series cannot be found
    in the master index (or has no table entry) the original dict is also
    returned.  Otherwise a shallow copy with ``single_excel_only`` added is
    returned so callers never mutate the caller's kwargs.
    """
    if kwargs.get("single_excel_only") or kwargs.get("selected_excel"):
        return kwargs
    try:
        row = _lookup_series_by_id(idx, series_id)
    except ValueError:
        return kwargs
    table = _get_field(row, "table")
    # ABS table identifiers are alphanumeric without spaces.
    # ~14 % of master-index rows have descriptions here (e.g.
    # ``"Industry summary table"``) rather than actual table numbers.
    if not table or " " in table:
        return kwargs
    result = dict(kwargs)
    result["single_excel_only"] = table
    return result


def _lookup_series_by_id(idx: DataFrame, series_id: str) -> DataFrame | pd.Series:
    """Look up a row in the master index by series ID (index or column).

    Returns a Series for a single match, or a DataFrame when there are
    duplicate index entries.
    """
    if idx.index.name == "Series ID":
        try:
            result = idx.loc[series_id]
        except KeyError as e:
            raise ValueError(f"Series ID '{series_id}' not found in the ABS master index.") from e
        return result
    # Fallback: column-based lookup
    mask = idx["Series ID"].astype(str).str.strip() == series_id.strip()
    if not mask.any():
        raise ValueError(f"Series ID '{series_id}' not found in the ABS master index.")
    return idx[mask].iloc[0]


def _get_field(row: DataFrame | pd.Series, field: str) -> str:
    """Extract a scalar string field from a DataFrame row or Series."""
    if isinstance(row, pd.Series):
        val = row.get(field)
        return str(val) if pd.notna(val) else ""
    if field in row.columns:
        val = row[field].iloc[0] if len(row) else None
        return str(val) if pd.notna(val) else ""
    return ""


def _normalise_cat(raw: str) -> str:
    """Normalise a catalogue number to the format ``read_abs_cat`` expects.

    The index stores numbers like ``"6202"``, ``"6401.0"``, or
    ``"5232.0.55.001"``.  This ensures the form without a trailing ``.0``
    (``"6202"``) is expanded to ``"6202.0"`` but leaves multi-part numbers
    (``"5232.0.55.001"``) alone.
    """
    raw = raw.strip()
    _min_dots = 2
    if raw.endswith(".0") or raw.count(".") >= _min_dots:
        return raw
    if "." not in raw:
        return raw + ".0"
    return raw


def _series_freq_from_idx(series_id: str, idx: DataFrame) -> str:
    """Get the frequency character (M, Q, Y, …) for a series from the index."""
    row = _lookup_series_by_id(idx, series_id)
    freq = _get_field(row, "frequency")
    return freq.strip().upper()[0] if freq else ""


def _series_start_from_idx(series_id: str, idx: DataFrame) -> str:
    """Get the series_start date string from the master index."""
    row = _lookup_series_by_id(idx, series_id)
    return _get_field(row, "series_start")


def _series_end_from_idx(series_id: str, idx: DataFrame) -> str:
    """Get the series_end date string from the master index."""
    row = _lookup_series_by_id(idx, series_id)
    return _get_field(row, "series_end")
