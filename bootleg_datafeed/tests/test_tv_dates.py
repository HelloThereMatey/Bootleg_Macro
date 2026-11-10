"""Regression tests for TradingView bar-date alignment.

tvDatafeed stamps daily bars with the session *open* rendered in the machine's
local timezone. On a UTC+11 host the 09:30 New York open becomes 01:30 the next
morning, so every US bar was labelled one calendar day late — a Friday close
appeared as a Saturday bar and a Monday session as Tuesday. Values were right;
every date was wrong.
"""
from __future__ import annotations

import pandas as pd
import pytest

from bootleg_datafeed.sources.tv_source import _align_daily_bars


def _frame(*stamps, values=None):
    idx = pd.DatetimeIndex(pd.to_datetime(list(stamps)))
    vals = values or list(range(1, len(stamps) + 1))
    return pd.Series(vals, index=idx, dtype="float64")


def test_new_york_open_maps_back_to_same_session():
    # 01:30 local (UTC+11) is the 09:30 New York open of the *previous* day.
    s = _frame("2026-11-10 01:30:00", "2026-11-07 01:30:00")
    out = _align_daily_bars(s, "AMEX", "1D")
    assert [str(d.date()) for d in out.index] == ["2026-11-06", "2026-11-09"]


def test_us_dst_boundary_is_honoured():
    # October stamps come through at 00:30 (AEDT, UTC+11); November at 01:30
    # (AEST, UTC+10). Both must land on their true session date.
    s = _frame("2026-10-31 00:30:00", "2026-11-03 01:30:00")
    out = _align_daily_bars(s, "SP", "1D")
    assert [str(d.date()) for d in out.index] == ["2026-10-30", "2026-11-02"]


def test_weekend_labelled_bars_map_onto_weekdays():
    # The mislabelling showed up as Saturday bars (2026-10-31, 2026-11-07).
    # Real sessions are the preceding Friday, so those labels must disappear.
    s = _frame("2026-10-31 00:30:00", "2026-11-07 01:30:00")
    out = _align_daily_bars(s, "AMEX", "1D")
    assert [str(d.date()) for d in out.index] == ["2026-10-30", "2026-11-06"]
    assert not [d for d in out.index if d.weekday() >= 5]


def test_crypto_labels_are_untouched():
    # Bitcoin bars are stamped at 00:00 UTC -> 11:00 local, which is already
    # the correct UTC day; shifting them would corrupt the series.
    s = _frame("2026-11-08 11:00:00", "2026-11-09 11:00:00")
    out = _align_daily_bars(s, "INDEX", "1D")
    assert [str(d.date()) for d in out.index] == ["2026-11-08", "2026-11-09"]


def test_intraday_intervals_are_left_alone():
    s = _frame("2026-11-10 01:30:00")
    out = _align_daily_bars(s, "AMEX", "5")
    assert [str(d.date()) for d in out.index] == ["2026-11-10"]


def test_duplicate_session_dates_collapse_to_last():
    s = _frame("2026-11-10 01:30:00", "2026-11-10 02:30:00", values=[1.0, 2.0])
    out = _align_daily_bars(s, "AMEX", "1D")
    assert len(out) == 1
    assert float(out.iloc[0]) == 2.0


@pytest.mark.parametrize("exchange", ["AMEX", "NASDAQ", "NYSE", "SP"])
def test_known_us_exchanges_are_mapped(exchange):
    s = _frame("2026-11-10 01:30:00")
    out = _align_daily_bars(s, exchange, "1D")
    assert str(out.index[0].date()) == "2026-11-09"
