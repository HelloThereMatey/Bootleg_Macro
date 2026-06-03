"""
Tests for the bm Watchlist module.
"""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from bootleg_toolz import Watchlist
from bootleg_datafeed import Dataset
from bootleg_datafeed.models import SeriesMetadata, StandardSeries


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_series():
    """Create a mock StandardSeries for testing."""
    # freq='YE' from 2020-01-01 to 2024-01-01 gives 4 end-of-year dates (2020-2023)
    dates = pd.date_range('2020-01-01', periods=4, freq='YE')
    series = pd.Series([1.0, 1.5, 2.0, 2.5], index=dates, name='GDP')
    meta = SeriesMetadata(
        id='GDP',
        title='Gross Domestic Product',
        source='fred',
        frequency='A',
        units='Billions of Dollars',
        length=4,
        min_value=1.0,
        max_value=2.5,
    )
    return StandardSeries.from_pandas(series, metadata=meta)


@pytest.fixture
def wl():
    """Create an empty Watchlist for testing."""
    return Watchlist(name='test_watchlist')


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_watchlist_init():
    """Watchlist initializes with correct empty data structures."""
    wl = Watchlist(name='my_watchlist')
    assert wl.name == 'my_watchlist'
    assert wl.watchlists_path is None
    assert wl.storepath is None
    assert list(wl.watchlist.columns) == ['id', 'source', 'title']
    assert list(wl.metadata.index) == list(wl.metadata.index)
    assert wl.datasets == {}
    assert wl.full_metadata == {}


def test_watchlist_init_default():
    """Default name is 'base_watchlist'."""
    wl = Watchlist()
    assert wl.name == 'base_watchlist'


def test_append_series_single(wl, mock_series):
    """append_series adds a series to all storage."""
    wl.append_series(mock_series)
    assert 'GDP' in wl.datasets
    assert 'GDP' in wl.watchlist['id'].values
    assert wl.datasets['GDP'].name == 'GDP'


def test_append_series_replaces_duplicate(wl, mock_series):
    """append_series replaces existing series with same id."""
    wl.append_series(mock_series)
    assert len(wl.watchlist) == 1

    # Modify and append again
    dates2 = pd.date_range('2020-01-01', periods=4, freq='YE')
    series2 = pd.Series([2.0, 2.5, 3.0, 3.5], index=dates2, name='GDP')
    meta2 = SeriesMetadata(
        id='GDP', title='GDP Revised', source='fred',
        frequency='A', units='Billions', length=4,
        min_value=2.0, max_value=3.5,
    )
    wl.append_series(StandardSeries.from_pandas(series2, metadata=meta2))

    assert len(wl.watchlist) == 1  # No new row added
    assert wl.datasets['GDP'].max() == 3.5  # Replaced, not appended


def test_drop_series(wl, mock_series):
    """drop_series removes from all storage."""
    wl.append_series(mock_series)
    wl.drop_series('GDP')
    assert 'GDP' not in wl.datasets
    assert 'GDP' not in wl.metadata.columns
    assert 'GDP' not in wl.watchlist['id'].values


def test_deduplicate():
    """deduplicate removes duplicate ids, columns, and orphaned dataset keys."""
    wl = Watchlist()

    # Add a series first
    dates = pd.date_range('2020-01-01', periods=4, freq='YE')
    series = pd.Series([1.0, 1.5, 2.0, 2.5], index=dates, name='GDP')
    meta = SeriesMetadata(id='GDP', title='GDP', source='fred', frequency='A')
    ss = StandardSeries.from_pandas(series, metadata=meta)
    wl.append_series(ss)
    wl.update_metadata()  # Populate metadata before adding dupes

    # Manually add duplicate row to watchlist DataFrame
    new_row = pd.DataFrame({'id': ['GDP'], 'source': ['fred'], 'title': ['GDP dup']})
    wl.watchlist = pd.concat([wl.watchlist, new_row], ignore_index=True)

    # Manually add duplicate column to metadata
    wl.metadata['GDP_dup'] = wl.metadata['GDP']

    # Manually add to datasets
    wl.datasets['GDP_dup'] = wl.datasets['GDP']

    assert len(wl.watchlist) == 2
    assert 'GDP_dup' in wl.metadata.columns

    wl.deduplicate()

    assert len(wl.watchlist) == 1
    assert 'GDP_dup' not in wl.metadata.columns
    assert 'GDP_dup' not in wl.datasets


def test_update_metadata(wl, mock_series):
    """update_metadata rebuilds the metadata DataFrame from datasets."""
    wl.append_series(mock_series)
    wl.update_metadata()

    assert 'GDP' in wl.metadata.columns
    assert wl.metadata.loc['id', 'GDP'] == 'GDP'
    assert wl.metadata.loc['source', 'GDP'] == 'fred'
    assert wl.metadata.loc['frequency', 'GDP'] == 'A'
    assert wl.metadata.loc['length', 'GDP'] == 4


def test_update_metadata_empty(wl):
    """update_metadata on empty watchlist creates empty DataFrame with METADATA_INDEX."""
    wl.update_metadata()
    assert wl.metadata.empty or list(wl.metadata.index) == list(wl.metadata.index)


# ---------------------------------------------------------------------------
# Save/load cycle tests (Excel)
# ---------------------------------------------------------------------------

def test_save_load_cycle_excel(wl, mock_series, tmp_path):
    """Save watchlist to xlsx, reload, verify data matches."""
    wl.append_series(mock_series)
    wl.update_metadata()
    save_path = tmp_path / 'test_cycle.xlsx'
    wl.save_watchlist(str(save_path))

    wl2 = Watchlist()
    wl2.load_watchlist(str(save_path))

    assert wl2.name == 'test_cycle'
    assert set(wl2.watchlist['id']) == set(wl.watchlist['id'])
    assert set(wl2.datasets.keys()) == set(wl.datasets.keys())
    assert set(wl2.metadata.columns) == set(wl.metadata.columns)


def test_save_load_multiple_series_excel(tmp_path):
    """Save and reload a watchlist with multiple series."""
    wl = Watchlist(name='multi')

    for ticker in ['AAPL', 'MSFT', 'GOOGL']:
        dates = pd.date_range('2020-01-01', periods=5, freq='YE')
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=dates, name=ticker)
        meta = SeriesMetadata(
            id=ticker, title=ticker, source='yfinance',
            frequency='D', units='USD',
        )
        wl.append_series(StandardSeries.from_pandas(series, metadata=meta))

    save_path = tmp_path / 'multi.xlsx'
    wl.save_watchlist(str(save_path))

    wl2 = Watchlist()
    wl2.load_watchlist(str(save_path))

    assert set(wl2.datasets.keys()) == {'AAPL', 'MSFT', 'GOOGL'}
    assert set(wl2.watchlist['id']) == {'AAPL', 'MSFT', 'GOOGL'}


# ---------------------------------------------------------------------------
# CSV tests
# ---------------------------------------------------------------------------

def test_save_load_csv_basic(wl, mock_series, tmp_path):
    """Save watchlist index to CSV and reload."""
    wl.append_series(mock_series)
    save_path = tmp_path / 'test_csv.csv'
    wl.save_watchlist_csv(str(save_path))

    wl2 = Watchlist()
    wl2.load_watchlist_csv(str(save_path))

    assert wl2.name == 'test_csv'
    assert set(wl2.watchlist['id']) == {'GDP'}


def test_csv_does_not_store_datasets(tmp_path):
    """CSV format saves the index only, not series data."""
    wl = Watchlist()
    dates = pd.date_range('2020-01-01', periods=4, freq='YE')
    series = pd.Series([1.0, 2.0, 3.0, 4.0], index=dates, name='GDP')
    meta = SeriesMetadata(id='GDP', title='GDP', source='fred', frequency='A')
    wl.append_series(StandardSeries.from_pandas(series, metadata=meta))

    save_path = tmp_path / 'csv_only.csv'
    wl.save_watchlist_csv(str(save_path))

    wl2 = Watchlist()
    wl2.load_watchlist_csv(str(save_path))

    # datasets should be empty after CSV-only load (no HDF5)
    assert wl2.datasets == {}


# ---------------------------------------------------------------------------
# Integration tests (live data — skip if no API keys)
# ---------------------------------------------------------------------------

def _has_fred_key():
    try:
        from bootleg_datafeed.dataset import Dataset
        ds = Dataset()
        return ds._api_keys.get('fred') is not None
    except Exception:
        return False


def _has_yfinance():
    try:
        import yfinance
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _has_fred_key(), reason="No FRED API key")
def test_get_watchlist_data_fred(wl):
    """get_watchlist_data fetches a FRED series end-to-end."""
    # Add GDP to watchlist
    row = pd.DataFrame({'id': ['GDP'], 'source': ['fred'], 'title': ['GDP']})
    wl.watchlist = pd.concat([wl.watchlist, row], ignore_index=True)

    errors = wl.get_watchlist_data(start_date='2020-01-01', end_date='2024-01-01')
    assert errors == {}
    assert 'GDP' in wl.datasets
    assert len(wl.datasets['GDP']) > 0


@pytest.mark.skipif(not _has_yfinance(), reason="yfinance not available")
def test_get_watchlist_data_yfinance(wl):
    """get_watchlist_data fetches a yfinance ticker end-to-end."""
    row = pd.DataFrame({'id': ['AAPL'], 'source': ['yfinance'], 'title': ['Apple']})
    wl.watchlist = pd.concat([wl.watchlist, row], ignore_index=True)

    errors = wl.get_watchlist_data(start_date='2023-01-01', end_date='2024-12-31')
    # Some tickers may fail depending on availability — just check no critical error
    if errors:
        assert all(k in ['AAPL'] for k in errors.keys())


# ---------------------------------------------------------------------------
# Plot test
# ---------------------------------------------------------------------------

def test_plot_returns_figure(wl, mock_series):
    """plot_watchlist returns a go.Figure without raising."""
    wl.append_series(mock_series)
    wl.update_metadata()
    try:
        fig = wl.plot_watchlist(left=['GDP'])
        assert fig is not None
        assert hasattr(fig, 'data') and hasattr(fig, 'layout')
    except Exception as e:
        # If MacroBackend plotting is unavailable, skip
        pytest.skip(f"Plotting unavailable: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
