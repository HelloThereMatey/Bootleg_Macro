# bm - Bootleg Macro Data Library

Python toolkit for acquisition of financial and economic time series data with standardized metadata and output formats. Obtain data for stocks, macroeconomic indicators, cryptocurrencies and much more from 10+ sources. GUI (PyQt6) for finding data and building watchlists. Plot with Plotly (planned) backtest trading strategies and create custom indexes.

## Features

- [x] **Data Sources** — Download from 10+ sources with unified API (FRED, BEA, Yahoo Finance, CoinGecko, Glassnode, TradingView, Trading Economics, Nasdaq, ABS, RBA)
- [x] **Watchlists** — Create, save, and manage multi-series watchlists (Excel `.xlsx` + HDF5 `.h5s` sidecar)
- [x] **Search** — Unified cross-source search to find series before adding them to a watchlist
- [x] **Charting** — Plot watchlist series with Plotly (dual-axis, recession bars, transforms)
- [x] **GUI — Watchlist Builder** — PyQt6 desktop app for interactive watchlist creation
- [ ] **Custom Indexes** — Build aggregated indexes from multiple series (e.g., liquidity indexes, custom benchmarks)
- [ ] **Line Fitting** — Trendlines, linear regression, and curve fitting on series
- [ ] **Correlation Analysis** — Rolling correlations between any two series
- [ ] **Backtesting** — Backtest trading strategies on watchlist series

---

## Installation

```bash
# Requires conda environment 'bm'
conda activate bm

# Or create the environment
cd Bootleg_Macro/setup
chmod +x setup.sh
./setup.sh
```

## Quick Start

```python
from bm import Dataset

ds = Dataset()

# Yahoo Finance - stock/crypto prices
result = ds.pull_yfinance('AAPL', start_date='2024-01-01')

# FRED - US macroeconomic data
result = ds.pull_fred('GDP', start_date='2023-01-01')

# CoinGecko - cryptocurrency prices
result = ds.pull_coingecko('bitcoin', days=90)

# BEA - US National Accounts
result = ds.pull_bea(dataset='NIPA', table_code='T10101')

# TradingView - chart data
result = ds.pull_tradingview(symbol='AAPL', exchange='NASDAQ')

# Trading Economics - macroeconomic indicators
result = ds.pull_tedata(url='united-states/consumer-confidence')

# Australian Bureau of Statistics
result = ds.pull_abs(series_id='A84423050A', catalog_num='6202.0')

# Reserve Bank of Australia
result = ds.pull_rba(series_id='ARBAMPCNCRT', table_no='A2')
```

## Data Sources

| Source | API Key Required | Description |
|--------|-----------------|-------------|
| `yfinance` | No | Yahoo Finance - stocks, ETFs, crypto |
| `coingecko` | No | CoinGecko - cryptocurrency prices |
| `fred` | Yes | FRED - US Federal Reserve economic data |
| `bea` | Yes | Bureau of Economic Analysis - US national accounts |
| `nasdaq` | Yes | Nasdaq Data Link - financial data |
| `glassnode` | Yes | Glassnode - on-chain crypto metrics |
| `abs` | No | Australian Bureau of Statistics |
| `rba` | No | Reserve Bank of Australia |
| `tedata` | No | Trading Economics - macroeconomic indicators |
| `tradingview` | No | TradingView - chart data (uses local tvDatafeedz) |

## API Keys

API keys are stored in `SystemInfo/API_Keys.json`. Copy the template and add your keys:

```bash
cp SystemInfo/API_Keys.json.example SystemInfo/API_Keys.json
```

Supported key names:
- `fred` - FRED API key
- `bea` - Bureau of Economic Analysis API key
- `nasdaq` - Nasdaq Data Link API key
- `glassnode` - Glassnode API key

## Architecture

```
bm/
├── __init__.py              # Package exports
├── models.py                # Pydantic models (SeriesMetadata, StandardSeries)
├── auxiliary.py             # Helper functions (date parsing, frequency detection)
├── dataset.py               # Main Dataset class
├── watchlist.py             # Watchlist class for multi-series management
├── search.py                # Unified search across all sources
├── charting.py             # Plotly charting utilities
├── watchlist_builder.py     # (planned) PyQt6 GUI for watchlist building
├── gui/                     # (planned) GUI widgets
│   ├── _models.py
│   ├── widgets.py
│   └── watchlist_builder.py
├── sources/
│   ├── __init__.py
│   ├── yfinance_source.py
│   ├── coingecko_source.py
│   ├── fred_source.py
│   ├── abs_source.py
│   ├── rba_source.py
│   ├── tedata_source.py
│   ├── nasdaq_source.py
│   ├── bea_source.py
│   ├── glassnode_source.py
│   └── tv_source.py
├── local_cache/              # Local index/cache files
└── tests/                    # Test suite
```

## Watchlist Usage

```python
from bm import Watchlist, WatchlistSearch

# Build a watchlist by searching
ws = WatchlistSearch()
results = ws.search_all('inflation')
results = ws.search('fred', 'GDP')

# Create and populate a watchlist
wl = Watchlist(name='my_study')
for _, row in results.iterrows():
    meta = SeriesMetadata(id=row['id'], title=row['title'], source=row['source'])
    wl.append_series(StandardSeries(data={}, metadata=meta))

# Save watchlist
wl.save_watchlist('path/to/my_study.xlsx')   # .xlsx + .h5s sidecar
wl.save_watchlist_csv('path/to/my_study.csv')  # index only

# Load watchlist
wl2 = Watchlist()
wl2.load_watchlist('path/to/my_study.xlsx')

# Fetch all data for the watchlist
wl2.get_watchlist_data(start_date='2020-01-01', end_date='2024-12-31')

# Plot
wl2.plot_watchlist(left=['GDP'], right=['UNRATE'])
```

## Search Usage

```python
from bm import WatchlistSearch

ws = WatchlistSearch()

# Search single source
results = ws.search('fred', 'GDP')       # DataFrame: id, title, source, meta
results = ws.search('coingecko', 'bitcoin')

# Search all sources
all_results = ws.search_all('inflation')  # concatenated across sources

# Multi-term search (comma-separated, case-insensitive)
results = ws.search('fred', 'GDP, quarterly')

# Wildcard support
results = ws.search('fred', 'M2*')
```

## Output Format

All sources return `StandardSeries` objects:

```python
result = ds.pull_yfinance('AAPL')

# Access data
result.data          # dict {date_str: value}

# Access metadata
result.metadata.id          # 'AAPL'
result.metadata.title       # 'Apple Inc.'
result.metadata.source      # 'yfinance'
result.metadata.frequency   # 'D', 'W', 'M', 'Q', 'A'
result.metadata.start_date  # datetime.date
result.metadata.length     # int
result.metadata.units      # str

# Convert to pandas
series = result.to_pandas()
```

## Running Tests

```bash
# Run all sources test
python -m bm.tests.test_all_sources

# Run individual tests
python -m bm.tests.test_yfinance
python -m bm.tests.test_fred
python -m bm.tests.test_bea
# etc.
```

## Development

### Adding a New Source

1. Create `sources/newsource_source.py` with `pull_newsource()` function
2. Add `pull_newsource()` method to `Dataset` class in `dataset.py`
3. Add routing in `Dataset.pull()` method
4. Add tests in `tests/`
5. Update this README

### Key Files
- `dataset.py` - Main Dataset class with `pull_*` methods
- `models.py` - Pydantic models for metadata standardization
- `watchlist.py` - Watchlist class for multi-series management
- `search.py` - Unified search across all sources
- `sources/` - Individual source implementations
