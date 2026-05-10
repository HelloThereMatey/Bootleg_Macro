"""
Search module for bm.

Provides a unified WatchlistSearch class for finding series across all sources
before building watchlists. Normalizes results to id/title/source columns.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import pandas as pd

from bm.dataset import Dataset, SOURCES


# Canonical result columns
RESULT_COLUMNS = ['id', 'title', 'source']
META_COLUMN = 'meta'


class WatchlistSearch:
    """
    Unified search interface across all bm data sources.

    Wraps each source's existing search_* function from bm.sources,
    normalizes results to id/title/source, and supports multi-term
    comma-split regex filtering.

    Example:
        ws = WatchlistSearch()
        results = ws.search('fred', 'GDP growth')
        results = ws.search('coingecko', 'bitcoin, eth')
        all_results = ws.search_all('inflation')
    """

    def __init__(self, api_keys_path: Optional[str] = None):
        """Initialize WatchlistSearch.

        Args:
            api_keys_path: Optional path to directory containing API_Keys.json.
                          Defaults to bm/SystemInfo/.
        """
        self._dataset = Dataset(api_keys_path=api_keys_path)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def search(self, source: str, query: str, **kwargs) -> pd.DataFrame:
        """Search a single source for query.

        Args:
            source: Source name ('fred', 'yfinance', 'coingecko', etc.)
            query: Search query string
            **kwargs: Source-specific options (api_key, exchange, search_type, etc.)

        Returns:
            DataFrame with columns: id, title, source, meta
        """
        source = source.lower()
        if source not in SOURCES:
            raise ValueError(f"Unknown source: {source}. Available: {SOURCES}")

        handler = self._HANDLERS.get(source)
        if handler is None:
            raise NotImplementedError(f"Search not implemented for source: {source}")

        raw = handler(self, query, **kwargs)
        return self._normalize(raw, source, query)

    def search_all(
        self,
        query: str,
        sources: Optional[list[str]] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Search multiple sources and concatenate results.

        Args:
            query: Search query string
            sources: List of sources to search. If None, searches all sources.
            **kwargs: Source-specific options passed to each search call.

        Returns:
            DataFrame with columns: id, title, source, meta
        """
        targets = sources or SOURCES
        results = []
        for src in targets:
            handler = self._HANDLERS.get(src)
            if handler is None:
                continue
            try:
                raw = handler(self, query, **kwargs)
                r = self._normalize(raw, src, query)
                if not r.empty:
                    results.append(r)
            except Exception:
                continue
        if not results:
            return pd.DataFrame(columns=RESULT_COLUMNS + [META_COLUMN])
        return pd.concat(results, ignore_index=True)

    # -------------------------------------------------------------------------
    # Source-specific search handlers
    # -------------------------------------------------------------------------

    def _search_fred(self, query: str, **kwargs) -> pd.DataFrame:
        from bm.sources.fred_source import search_fred
        api_key = kwargs.pop('api_key', None) or self._dataset.get_api_key('fred')
        return search_fred(query, api_key=api_key)

    def _search_yfinance(self, query: str, **kwargs) -> pd.DataFrame:
        from bm.sources.yfinance_source import search_tickers
        limit = kwargs.pop('limit', 20)
        return search_tickers(query, limit=limit)

    def _search_coingecko(self, query: str, **kwargs) -> pd.DataFrame:
        from bm.sources.coingecko_source import search_coins
        return search_coins(query)

    def _search_tv(self, query: str, **kwargs) -> pd.DataFrame:
        from bm.sources.tv_source import search_tv
        exchange = kwargs.pop('exchange', '')
        return search_tv(query, exchange=exchange)

    def _search_abs(self, query: str, **kwargs) -> pd.DataFrame:
        from bm.sources.abs_source import search_abs
        return search_abs(query)

    def _search_rba(self, query: str, **kwargs) -> pd.DataFrame:
        from bm.sources.rba_source import search_rba_tables, search_rba_series
        search_type = kwargs.pop('search_type', 'tables')
        if search_type == 'series':
            return search_rba_series(query)
        return search_rba_tables(query)

    def _search_bea(self, query: str, **kwargs) -> pd.DataFrame:
        from bm.sources.bea_source import search_bea_tables
        api_key = kwargs.pop('api_key', None) or self._dataset.get_api_key('bea')
        dataset = kwargs.pop('dataset', 'NIPA')
        return search_bea_tables(dataset=dataset, api_key=api_key)

    def _search_nasdaq(self, query: str, **kwargs) -> pd.DataFrame:
        from bm.sources.nasdaq_source import search_nasdaq
        api_key = kwargs.pop('api_key', None) or self._dataset.get_api_key('nasdaq')
        return search_nasdaq(query, api_key=api_key)

    def _search_glassnode(self, query: str, **kwargs) -> pd.DataFrame:
        from bm.sources.glassnode_source import search_glassnode_metrics
        api_key = kwargs.pop('api_key', None) or self._dataset.get_api_key('glassnode')
        return search_glassnode_metrics(query, api_key=api_key)

    def _search_tedata(self, query: str, **kwargs) -> pd.DataFrame:
        from bm.sources.tedata_source import search_tedata
        browser = kwargs.pop('browser', 'auto')
        return search_tedata(query, browser=browser)

    def _search_cryptocompare(self, query: str, **kwargs) -> pd.DataFrame:
        from bm.sources.cryptocompare_source import search_cryptocompare
        return search_cryptocompare(query)

    # Handler dispatch table
    _HANDLERS = {
        'fred': _search_fred,
        'yfinance': _search_yfinance,
        'coingecko': _search_coingecko,
        'tradingview': _search_tv,
        'tv': _search_tv,
        'abs': _search_abs,
        'rba': _search_rba,
        'bea': _search_bea,
        'nasdaq': _search_nasdaq,
        'glassnode': _search_glassnode,
        'tedata': _search_tedata,
        'cryptocompare': _search_cryptocompare,
    }

    # -------------------------------------------------------------------------
    # Normalization
    # -------------------------------------------------------------------------

    def _normalize(self, raw: pd.DataFrame, source: str, query: str) -> pd.DataFrame:
        """Map raw search results to canonical columns (id, title, source, meta)."""
        if raw.empty:
            return pd.DataFrame(columns=RESULT_COLUMNS + [META_COLUMN])

        cols = raw.columns.tolist()

        # Source-specific column detection
        if source == 'fred':
            id_col = next((c for c in ['id', 'series_id'] if c in cols), None)
            title_col = next((c for c in ['title', 'name'] if c in cols), None)

        elif source == 'yfinance':
            id_col = next((c for c in ['symbol', 'ticker'] if c in cols), None)
            title_col = next((c for c in ['longName', 'shortName', 'name'] if c in cols), None)

        elif source == 'coingecko':
            id_col = 'id' if 'id' in cols else None
            title_col = next((c for c in ['name', 'title', 'symbol'] if c in cols), None)

        elif source in ('tv', 'tradingview'):
            id_col = next((c for c in ['symbol', 'ticker'] if c in cols), None)
            title_col = next((c for c in ['description', 'symbol', 'name'] if c in cols), None)

        elif source == 'abs':
            id_col = next((c for c in ['Series ID', 'series_id'] if c in cols), None)
            title_col = next((c for c in ['Data Item Description', 'title'] if c in cols), None)

        elif source == 'bea':
            id_col = next((c for c in ['TableName', 'TableCode', 'table_name'] if c in cols), None)
            title_col = id_col

        elif source == 'nasdaq':
            id_col = next((c for c in ['symbol', 'ticker'] if c in cols), None)
            title_col = next((c for c in ['name', 'title', 'description'] if c in cols), None)

        elif source == 'glassnode':
            id_col = 'path' if 'path' in cols else None
            title_col = next((c for c in ['name', 'title', 'path'] if c in cols), None)

        elif source == 'rba':
            id_col = next((c for c in ['TableNo', 'Table', 'Series ID', 'table_no'] if c in cols), None)
            title_col = next((c for c in ['Description', 'Title', 'title'] if c in cols), None)

        elif source == 'tedata':
            id_col = 'url' if 'url' in cols else None
            title_col = next((c for c in ['metric', 'title', 'country'] if c in cols), None)

        elif source == 'cryptocompare':
            id_col = next((c for c in ['symbol', 'id'] if c in cols), None)
            title_col = next((c for c in ['name', 'title', 'symbol'] if c in cols), None)

        else:
            id_col = cols[0] if cols else None
            title_col = cols[1] if len(cols) > 1 else None

        # Build normalized DataFrame
        records = []
        for _, row in raw.iterrows():
            meta_dict = row.to_dict()
            record = {
                'id': str(row[id_col]) if id_col and id_col in row else '',
                'title': str(row[title_col]) if title_col and title_col in row else '',
                'source': source,
                META_COLUMN: meta_dict,
            }
            records.append(record)

        result = pd.DataFrame(records, columns=RESULT_COLUMNS + [META_COLUMN])

        # Apply multi-term filter if query contains commas
        if re.search(r'[,;]', query):
            result = _multi_term_filter(result, query)

        return result

    # -------------------------------------------------------------------------
    # Index management (for future expansion)
    # -------------------------------------------------------------------------

    @staticmethod
    def search_indexes_dir() -> Path:
        """Return the bm/local_cache/ directory path."""
        bm_dir = Path(__file__).parent
        idx_dir = bm_dir / 'local_cache'
        idx_dir.mkdir(exist_ok=True)
        return idx_dir


def _multi_term_filter(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """
    Apply AND-style multi-term regex filter across all result columns.

    Comma-separated terms: "GDP, monthly" -> match rows containing both
    "GDP" AND "monthly" (case-insensitive) in any cell.

    Also supports * as wildcard (converted to .* before matching).

    Args:
        df: DataFrame to filter
        query: Comma-separated search string

    Returns:
        Filtered DataFrame
    """
    if df.empty or not query:
        return df

    terms = [t.strip() for t in re.split(r'[,;]', query) if t.strip()]
    if not terms:
        return df

    # Convert * to .* for wildcard support
    terms = [t.replace('*', '.*') for t in terms]

    def _row_matches(row, patterns):
        vals = list(row.values)
        row_str = ' '.join(str(v) for v in vals if pd.notna(v))
        return all(re.search(p, row_str, re.IGNORECASE) for p in patterns)

    mask = df.apply(lambda row: _row_matches(row, terms), axis=1)
    return df[mask].copy()