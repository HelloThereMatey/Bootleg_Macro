"""
Tests for the bm WatchlistSearch module.
"""

import pandas as pd
import pytest

from bootleg_datafeed import WatchlistSearch
from bootleg_datafeed.search import _multi_term_filter


# ---------------------------------------------------------------------------
# Unit tests for multi_term_filter
# ---------------------------------------------------------------------------

def test_multi_term_filter_single_term():
    """Single term returns all matching rows."""
    df = pd.DataFrame([
        {'id': 'A', 'title': 'GDP Monthly', 'source': 'fred'},
        {'id': 'B', 'title': 'GDP Quarterly', 'source': 'fred'},
        {'id': 'C', 'title': 'CPI Monthly', 'source': 'fred'},
    ])
    filtered = _multi_term_filter(df, "GDP")
    assert len(filtered) == 2


def test_multi_term_filter_comma_and():
    """Comma-separated terms apply AND logic."""
    df = pd.DataFrame([
        {'id': 'A', 'title': 'GDP Monthly', 'source': 'fred'},
        {'id': 'B', 'title': 'GDP Quarterly', 'source': 'fred'},
        {'id': 'C', 'title': 'CPI Monthly', 'source': 'fred'},
    ])
    filtered = _multi_term_filter(df, "GDP, monthly")
    assert len(filtered) == 1
    assert filtered.iloc[0]['id'] == 'A'


def test_multi_term_filter_no_match():
    """No matching rows returns empty DataFrame."""
    df = pd.DataFrame([
        {'id': 'A', 'title': 'GDP Monthly', 'source': 'fred'},
    ])
    filtered = _multi_term_filter(df, "notfound")
    assert len(filtered) == 0


def test_multi_term_filter_empty_df():
    """Empty DataFrame returns empty DataFrame."""
    df = pd.DataFrame(columns=['id', 'title', 'source'])
    filtered = _multi_term_filter(df, "GDP")
    assert len(filtered) == 0


def test_multi_term_filter_empty_query():
    """Empty query returns original DataFrame."""
    df = pd.DataFrame([
        {'id': 'A', 'title': 'GDP Monthly', 'source': 'fred'},
    ])
    filtered = _multi_term_filter(df, "")
    assert len(filtered) == 1


def test_multi_term_filter_wildcard():
    """Wildcard * is converted to .* regex."""
    df = pd.DataFrame([
        {'id': 'A', 'title': 'GDP Monthly', 'source': 'fred'},
        {'id': 'B', 'title': 'GDPQ Quarterly', 'source': 'fred'},
        {'id': 'C', 'title': 'CPI Monthly', 'source': 'fred'},
    ])
    filtered = _multi_term_filter(df, "GD*")
    assert len(filtered) == 2


def test_multi_term_filter_semicolon():
    """Semicolon also acts as separator."""
    df = pd.DataFrame([
        {'id': 'A', 'title': 'GDP Monthly', 'source': 'fred'},
        {'id': 'B', 'title': 'GDP Quarterly', 'source': 'fred'},
        {'id': 'C', 'title': 'CPI Monthly', 'source': 'fred'},
    ])
    filtered = _multi_term_filter(df, "GDP; monthly")
    assert len(filtered) == 1
    assert filtered.iloc[0]['id'] == 'A'


# ---------------------------------------------------------------------------
# Unit tests for WatchlistSearch class
# ---------------------------------------------------------------------------

def test_watchlist_search_init():
    """WatchlistSearch initializes with empty dataset."""
    ws = WatchlistSearch()
    assert ws._dataset is not None


def test_search_unknown_source():
    """Unknown source raises ValueError."""
    ws = WatchlistSearch()
    with pytest.raises(ValueError, match="Unknown source"):
        ws.search('unknown_source', 'test')


def test_search_fred_normalizes_columns():
    """FRED search returns normalized columns (id, title, source, meta)."""
    ws = WatchlistSearch()
    result = ws.search('fred', 'GDP')
    assert list(result.columns) == ['id', 'title', 'source', 'meta']
    assert result['source'].iloc[0] == 'fred'


def test_search_all_combines_sources():
    """search_all returns concatenated results from multiple sources."""
    ws = WatchlistSearch()
    result = ws.search_all('bitcoin', sources=['coingecko'])
    assert len(result) > 0
    assert set(result['source'].unique()) <= {'coingecko'}


# ---------------------------------------------------------------------------
# Tests with mocked handlers (unit tests for normalization)
# ---------------------------------------------------------------------------

def test_normalize_fred_id_and_title():
    """FRED normalization correctly maps id and title columns."""
    ws = WatchlistSearch()
    raw = pd.DataFrame([
        {'id': 'GDP', 'title': 'Gross Domestic Product', 'units': 'Billions'},
        {'id': 'GNP', 'title': 'Gross National Product', 'units': 'Billions'},
    ])
    result = ws._normalize(raw, 'fred', 'test query')
    assert list(result.columns) == ['id', 'title', 'source', 'meta']
    assert result.iloc[0]['id'] == 'GDP'
    assert result.iloc[0]['title'] == 'Gross Domestic Product'
    assert result.iloc[0]['source'] == 'fred'


def test_normalize_empty_df():
    """Normalize returns empty DataFrame with correct columns."""
    ws = WatchlistSearch()
    result = ws._normalize(pd.DataFrame(), 'fred', 'test')
    assert len(result) == 0
    assert list(result.columns) == ['id', 'title', 'source', 'meta']


def test_normalize_coingecko():
    """CoinGecko normalization maps id and name correctly."""
    ws = WatchlistSearch()
    raw = pd.DataFrame([
        {'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'btc', 'market_cap_rank': 1},
    ])
    result = ws._normalize(raw, 'coingecko', 'test')
    assert result.iloc[0]['id'] == 'bitcoin'
    assert result.iloc[0]['title'] == 'Bitcoin'


def test_normalize_rba():
    """RBA normalization maps Table column as id."""
    ws = WatchlistSearch()
    raw = pd.DataFrame([
        {'Table': 'A2', 'Description': 'Cash Rate', 'URL': 'http://example.com'},
    ])
    result = ws._normalize(raw, 'rba', 'test')
    assert result.iloc[0]['id'] == 'A2'
    assert result.iloc[0]['title'] == 'Cash Rate'


def test_normalize_tedata():
    """TEDATA normalization maps url as id and metric as title."""
    ws = WatchlistSearch()
    raw = pd.DataFrame([
        {'url': 'united-states/gdp', 'metric': 'GDP', 'country': 'US'},
    ])
    result = ws._normalize(raw, 'tedata', 'test')
    assert result.iloc[0]['id'] == 'united-states/gdp'
    assert result.iloc[0]['title'] == 'US - GDP'


def test_normalize_meta_preserved():
    """Original columns are preserved in meta dict."""
    ws = WatchlistSearch()
    raw = pd.DataFrame([
        {'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'btc', 'rank': 1},
    ])
    result = ws._normalize(raw, 'coingecko', 'test')
    meta = result.iloc[0]['meta']
    assert 'symbol' in meta
    assert meta['symbol'] == 'btc'
    assert 'rank' in meta
    assert meta['rank'] == 1


def test_multi_term_filter_applies_after_normalize():
    """Multi-term filter is applied post-normalization."""
    ws = WatchlistSearch()
    raw = pd.DataFrame([
        {'id': 'A', 'title': 'GDP Monthly', 'source': 'fred'},
        {'id': 'B', 'title': 'GDP Quarterly', 'source': 'fred'},
        {'id': 'C', 'title': 'CPI Monthly', 'source': 'fred'},
    ])
    # "GDP, monthly" should match A but not B or C
    result = ws._normalize(raw, 'fred', "GDP, monthly")
    assert len(result) == 1
    assert result.iloc[0]['id'] == 'A'


# ---------------------------------------------------------------------------
# Integration tests (live data — skip if no API keys)
# ---------------------------------------------------------------------------

def _has_fred_key():
    try:
        from bootleg_datafeed.dataset import Dataset
        ds = Dataset()
        return ds.get_api_key('fred') is not None
    except Exception:
        return False


def _has_bea_key():
    try:
        from bootleg_datafeed.dataset import Dataset
        ds = Dataset()
        return ds.get_api_key('bea') is not None
    except Exception:
        return False


@pytest.mark.skipif(not _has_fred_key(), reason="No FRED API key")
def test_search_fred_live():
    """Live FRED search returns real results."""
    ws = WatchlistSearch()
    result = ws.search('fred', 'unemployment')
    assert len(result) > 0
    assert result['source'].iloc[0] == 'fred'
    assert 'id' in result.columns


@pytest.mark.skipif(not _has_bea_key(), reason="No BEA API key")
def test_search_bea_live():
    """Live BEA table search returns results."""
    ws = WatchlistSearch()
    result = ws.search('bea', 'GDP')
    assert len(result) > 0


def test_search_coingecko_live():
    """Live CoinGecko search returns results (no key required)."""
    ws = WatchlistSearch()
    result = ws.search('coingecko', 'ethereum')
    assert len(result) > 0
    assert 'id' in result.columns


def test_search_abs_live():
    """Live ABS search via readabs returns results."""
    ws = WatchlistSearch()
    result = ws.search('abs', 'unemployment')
    # ABS search may return empty if readabs has rate limit
    assert 'id' in result.columns


def test_search_rba_live():
    """Live RBA table search returns results."""
    ws = WatchlistSearch()
    result = ws.search('rba', 'interest')
    assert len(result) > 0
    assert result['source'].iloc[0] == 'rba'


# Search local_cache directory
# ---------------------------------------------------------------------------

def test_search_indexes_dir():
    """search_indexes_dir returns Path and creates directory."""
    idx_dir = WatchlistSearch.search_indexes_dir()
    assert idx_dir.exists()
    assert idx_dir.is_dir()
    assert idx_dir.name == 'local_cache'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])