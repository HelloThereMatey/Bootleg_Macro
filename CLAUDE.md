# CLAUDE.md

## Repo specific instructions

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

```bash
# Install core datafeed
pip install -e ./bootleg_datafeed

# Install everything (including toolz, indexes)
pip install -e ./bootleg_macro

# Install with GUI support
pip install -e "./bootleg_macro[gui]"
```

## Architecture

The repo ships **two pip-installable packages**:

```
Bootleg_Macro/
├── bootleg_datafeed/     # Core package — data acquisition
│   ├── dataset.py         # Dataset class for pulling time series
│   ├── models.py          # SeriesMetadata, StandardSeries
│   ├── sources/           # 11+ data source implementations
│   │   ├── fred_source.py
│   │   ├── bea_source.py
│   │   ├── yfinance_source.py
│   │   ├── tv_source.py   # TradingView
│   │   ├── abs_source.py  # Australia (plus extend_history/)
│   │   ├── rba_source.py  # Australia RBA
│   │   ├── coingecko_source.py
│   │   ├── cryptocompare_source.py
│   │   ├── glassnode_source.py
│   │   ├── nasdaq_source.py
│   │   └── tedata_source.py
│   ├── search.py          # WatchlistSearch for finding series
│   ├── auxiliary.py       # Utilities, frequency conversion
│   └── _user_path.py      # User data directory management
│
└── bootleg_macro/         # Meta-package — everything else
    ├── toolz/             # Analysis, charting, watchlists
    │   ├── watchlist.py   # Watchlist class
    │   ├── charting.py    # Plotly charting
    │   ├── stats.py       # Correlation, stationarity
    │   ├── fitting.py     # Distribution/trend fitting
    │   ├── data_processing.py  # Seasonal adjustment
    │   └── utilities.py   # Helpers
    ├── indexes/           # Custom indexes
    │   ├── nlq_clean.py  # Net Liquidity (NLQ)
    │   ├── gm2_data_handler.py  # Global M2
    │   └── UpdateM2Infos/  # M2 config files
    └── watchlist_gui/     # PyQt6 desktop GUI (optional)
        ├── gui/
        │   ├── watchlist_builder.py  # Main window
        │   ├── widgets.py            # UI components
        │   ├── _models.py            # Qt models
        │   └── _logging.py           # Logging setup
        └── tests/
```

## Installation

```bash
# Core only
pip install -e ./bootleg_datafeed

# Everything (default: datafeed + toolz + indexes)
pip install -e ./bootleg_macro

# With GUI (adds PyQt6)
pip install -e "./bootleg_macro[gui]"
pip install -e "./bootleg_macro[all]"   # same as [gui]
```

## Common Usage Patterns

### Pull data from any source

```python
from bootleg_datafeed import Dataset

ds = Dataset()

# FRED (requires API key)
ds.pull_fred("GDP", start_date="2020-01-01")

# Yahoo Finance (no key)
ds.pull_yfinance("SPY")

# TradingView (no key)
ds.pull_tradingview("BTCUSD", exchange="INDEX")

# BEA (requires API key)
ds.pull_bea(dataset="NIPA", table_code="T10101")

# ABS Australia (no key)
ds.pull_abs("A2304350A")
```

### Search for series

```python
from bootleg_datafeed import WatchlistSearch

ws = WatchlistSearch()
results = ws.search("fred", "GDP")
all_results = ws.search_all("inflation")
```

### Chart and analyze

```python
from bootleg_macro import charting

fig = charting.plot_series(ds.data["GDP"], title="US GDP")
charting.show(fig)
```

### Build watchlists

```python
from bootleg_macro import Watchlist

wl = Watchlist(name="my_study")
wl.add_series(metadata, series)  # Add from search results
wl.get_watchlist_data(start_date="2020-01-01")
wl.save_watchlist("my_study.xlsx")
```

### Launch GUI (requires [gui] extra)

```python
from bootleg_macro import launch
window = launch()
```

### Custom indexes

```python
from bootleg_macro import NetLiquidity, Global_M2

# Net Liquidity
nlq = NetLiquidity(start_date="2010-01-01")
results = nlq.calculate_all()

# Global M2
gm2 = Global_M2()
gm2.download_data(n_bars=500, countries=['United States', 'Japan'])
gm2.create_all_aggregates()
```

## Data Sources

| Source | API Key | Notes |
|--------|---------|-------|
| `fred` | Yes | US macro data |
| `bea` | Yes | US national accounts (cached table pulls) |
| `yfinance` | No | Price data |
| `tv` (TradingView) | No | Price data, 5000-bar limit |
| `coingecko` | No | Crypto prices, 365-day limit |
| `cryptocompare` | No | Crypto prices, 2000-bar limit |
| `nasdaq` | Yes | Formerly Quandl (free key) |
| `glassnode` | Yes | On-chain crypto metrics |
| `abs` (Australia) | No | Australian Bureau of Statistics |
| `rba` (Australia) | No | Reserve Bank of Australia |
| `tedata` | No | Selenium scraping |

## API Keys

Stored in `~/Documents/Bootleg_Macro/system/API_Keys.json` (managed via `bootleg_datafeed._user_path`):

```json
{
    "fred": "your_fred_key",
    "bea": "your_bea_key",
    "nasdaq": "your_nasdaq_key",
    "glassnode": "your_glassnode_key"
}
```

## Key Patterns

- **Adding a new data source**: Implement in `bootleg_datafeed/sources/`, add to `SOURCES` in `dataset.py`
- **Import paths**: Use `from bootleg_macro import ...` for convenience, or `from bootleg_datafeed import ...` for core
- **Optional GUI**: Use `try/except ImportError` around GUI imports or check `_gui_available` flag

## License

MIT
