# Plan: Search Module for `bm`

## Context

The `bm` package (at `Bootleg_Macro/bm/`) has a completed Watchlist Module. The next task is a **Search Module** that enables finding series across all sources interactively when building watchlists — usable in jupyter, CLI, scripts, and later a GUI.

**Reference**: `MacroBackend/search_symbol_gui.py` (lines 31-57, 574-709) and `MacroBackend/Utilities.py::Search_DF_np` (lines 760+)

---

## Architecture

```
bm/
    search.py                  # NEW: WatchlistSearch class + _multi_term_filter
    search_indexes/            # NEW: Local index files (created on demand)
        .gitkeep               # NEW: Placeholder
    __init__.py                # MODIFY: Export WatchlistSearch

    sources/                   # NO CHANGES — existing search_* functions used as-is
    tests/
        test_search.py         # NEW: Unit + integration tests
```

---

## Class: `WatchlistSearch`

```python
class WatchlistSearch:
    def __init__(self, api_keys_path: Optional[str] = None):
        self._dataset = Dataset(api_keys_path=api_keys_path)

    def search(self, source: str, query: str, **kwargs) -> pd.DataFrame:
        """Search a single source. Returns DataFrame with id/title/source columns."""

    def search_all(self, query: str, sources: Optional[list[str]] = None, **kwargs) -> pd.DataFrame:
        """Search multiple sources and concatenate results."""
```

**Result format**: DataFrame with columns `['id', 'title', 'source', 'meta']`
- `id`: Series/ticker/coin identifier
- `title`: Human-readable name
- `source`: Source name (`fred`, `yfinance`, etc.)
- `meta`: dict of extra columns from original search result

**Multi-term filtering**: Query `"GDP, monthly"` → AND-match across all result columns (case-insensitive regex). Applied post-normalization uniformly across all sources.

---

## Source Handler Map

| Source | Handler | Key Required? | Function Used |
|--------|---------|---------------|---------------|
| `fred` | `_search_fred` | Yes | `search_fred(query, api_key)` — single call, limit=50, order_by=search_rank |
| `yfinance` | `_search_yfinance` | No | `search_tickers(query, limit=20)` |
| `coingecko` | `_search_coingecko` | No | `search_coins(query)` |
| `tv` / `tradingview` | `_search_tv` | No | `search_tv(query, exchange='')` |
| `abs` | `_search_abs` | No | `search_abs(query)` via local `abs_master_index.h5` |
| `rba` | `_search_rba` | No | `search_rba_tables(query)` (or `search_rba_series` via `search_type` kwarg) |
| `bea` | `_search_bea` | Yes | `search_bea_tables(dataset='NIPA', api_key=api_key)` |
| `nasdaq` | `_search_nasdaq` | Yes | `search_nasdaq(query, api_key)` |
| `glassnode` | `_search_glassnode` | Yes | `search_glassnode_metrics(query, api_key)` |
| `tedata` | `_search_tedata` | No | `search_tedata(query, browser='auto')` |

**API key handling**: Keys loaded from `Dataset` via `self._dataset.get_api_key(source)`. Can be overridden per-call via `search(source, query, api_key=...)`.

---

## Normalization

Each source returns different column names. The `_normalize(raw, source)` method maps them to canonical columns:

| Source | ID column | Title column |
|---------|-----------|--------------|
| fred | `series_id` | `title` |
| yfinance | `symbol` | `longName` / `shortName` |
| coingecko | `id` | `name` |
| tv | `symbol` | `description` |
| abs | `Series ID` | `Data Item Description` |
| bea | `TableName` | `TableName` (name=id for tables) |
| nasdaq | `symbol` | `name` |
| glassnode | `path` | `name` or `path` |
| rba | `TableNo` | `Description` |
| tedata | `url` | `metric` |

If source column missing, falls back to first available column.

---

## Multi-Term Filter

```python
def _multi_term_filter(df: pd.DataFrame, query: str) -> pd.DataFrame:
    """AND-match comma-separated terms as case-insensitive regex across all columns."""
    terms = [t.strip() for t in re.split(r'[,;]', query) if t.strip()]
    if not terms:
        return df

    def _row_matches(row, patterns):
        row_str = ' '.join(str(v) for v in row.values() if pd.notna(v))
        return all(re.search(re.escape(p), row_str, re.IGNORECASE) for p in patterns)

    mask = df.apply(lambda row: _row_matches(row, terms), axis=1)
    return df[mask]
```

Pattern from `MacroBackend/Utilities.py::Search_DF_np` — supports comma-split terms, `*` wildcard treated as `.*`.

---

## Files to Modify/Create

| File | Action |
|------|--------|
| `bm/search.py` | **CREATE** — `WatchlistSearch` class, `_multi_term_filter`, handlers |
| `bm/search_indexes/.gitkeep` | **CREATE** — placeholder so directory is tracked |
| `bm/__init__.py` | **MODIFY** — add `WatchlistSearch` export |
| `bm/tests/test_search.py` | **CREATE** — unit + mock tests |

---

## Verification

1. `python -c "from bm import WatchlistSearch; ws = WatchlistSearch(); print('OK')"`
2. `ws.search('fred', 'GDP')` → returns DataFrame with `id`, `title`, `source` columns
3. `ws.search_all('unemployment')` → returns concatenated results from multiple sources
4. Multi-term: `ws.search('fred', 'GDP, monthly')` → filters to rows matching both terms
5. `pytest bm/tests/test_search.py` → all tests pass

---

## Open Questions (for next session)

1. **Index files**: Should `bm/search_indexes/` store any local index files, or just use API-based search? Answer: yes some sources have no search functionality in the API and we will need to use local data of available metrics stored in h5 format. Load dataframe from file and search the df. JUst like it is done in `MacroBackend/search_symbol_gui.py` for ABS. See ABSMasterINdex file. Use this for ABS source. 
2. **RBA series search**: Should `search_type` default to `'tables'` or should we provide a way to search both? ANswer:  Keep it at tables fro now and maybe series addedd later.
3. **tedata browser**: Should search fail gracefully if no browser is available? Answer: Yes.
4. **CoinGecko CSV fallback**: Should we support the legacy `AllCG.csv` for offline use? Yes, but make it optional via `index_file` kwarg in case user has an updated CSV or prefers API. APi as default.
5. **yfinance search**: bm's `search_tickers` is a simple Ticker.info lookup — is this sufficient vs the Node.js bridge `search_yf_tickers`? If yfinance python package has search functionality we can use that, otherwise we stick to using the node yahoo_finance2 package for search.

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `bm/watchlist.py` | Class pattern (Option B plain Python object) |
| `bm/dataset.py` | Dataset's API key loading and SOURCES list |
| `bm/sources/__init__.py` | Lists all `search_*` functions exported |
| `MacroBackend/search_symbol_gui.py:31-57` | Sources dict mapping |
| `MacroBackend/search_symbol_gui.py:574-709` | `run_search_df` logic |
| `MacroBackend/Utilities.py:760+` | `Search_DF_np` multi-term search pattern |