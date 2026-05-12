# bm Usage Guide

**bm** (Bootleg Macro Data Library) is a Python toolkit for acquiring financial and economic time series data from 10+ sources, with standardized metadata and multiple output formats. It runs in conda environment `bm`.

```bash
conda activate bm
cd /home/totabilcat/Documents/Code/Bootleg_Macro
```

---

## Table of Contents

1. [Dataset — Pulling Data](#1-dataset--pulling-data)
2. [Search — Finding Series](#2-search--finding-series)
3. [Watchlists — Managing Series](#3-watchlists--managing-series)
4. [Charting — Plotting Series](#4-charting--plotting-series)
5. [GUI — Watchlist Builder](#5-gui--watchlist-builder)
6. [API Keys](#6-api-keys)
7. [Output Format — StandardSeries](#7-output-format--standardseries)
8. [Multi-Param Sources](#8-multi-param-sources)
9. [Logging](#9-logging)
9. [Logging](#9-logging)

---

## 1. Dataset — Pulling Data

The `Dataset` class is the main entry point for downloading time series. Each `pull_*` method returns a `StandardSeries` object.

```python
from bm import Dataset

ds = Dataset()
```

### Yahoo Finance (stocks, ETFs, crypto — no API key)

```python
# Apple stock daily
result = ds.pull_yfinance('AAPL', start_date='2023-01-01', end_date='2024-12-31')

# S&P 500 weekly
result = ds.pull_yfinance('^GSPC', interval='1wk')

# Bitcoin
result = ds.pull_yfinance('BTC-USD', start_date='2020-01-01')

# Interval options: '1d', '1wk', '1mo', '5m', '15m', '30m', '90m', '1h', '4h'
```

### FRED — US Federal Reserve Economic Data (API key required)

```python
result = ds.pull_fred('GDP', start_date='2020-01-01', end_date='2024-12-31')      # Quarterly GDP
result = ds.pull_fred('UNRATE')          # Unemployment rate
result = ds.pull_fred('FEDFUNDS')        # Fed funds rate
result = ds.pull_fred('M2SL')           # M2 Money Supply
result = ds.pull_fred('DFF')            # Effective Federal Funds Rate
```

### CoinGecko — Crypto prices (no API key)

```python
result = ds.pull_coingecko('bitcoin', days=365)
result = ds.pull_coingecko('ethereum', days=90, vs_currency='usd')
# days: 1–365 (free tier). vs_currency: 'usd', 'eur', 'gbp', etc.
```

### Bureau of Economic Analysis — US National Accounts (API key required)

```python
# GDP (NIPA Table T10101)
result = ds.pull_bea(dataset='NIPA', table_code='T10101', frequency='Q')

# Personal Consumption Expenditures
result = ds.pull_bea(dataset='NIPA', table_code='T10101', series_code='A191RX')

# Dataset options: 'NIPA', 'NIUnderlyingDetail', 'FixedAssets', 'InputOutput'
# frequency: 'A' (annual), 'Q' (quarterly), 'M' (monthly)
```

### TradingView — Chart data via local tvDatafeedz (no API key)

```python
result = ds.pull_tradingview(symbol='AAPL', exchange='NASDAQ', interval='1D', n_bars=5000)
result = ds.pull_tradingview(symbol='ES1!', exchange='CME', interval='1H')  # E-mini S&P futures
result = ds.pull_tradingview(symbol='BTCUSD', exchange='BITSTAMP', interval='4H')
# n_bars: max 5000. interval: '1D', '1H', '4H', '1W', '1M', etc.
```

### Trading Economics — Macroeconomic indicators via Selenium scraping (no API key)

```python
result = ds.pull_tedata(url='united-states/consumer-confidence')
result = ds.pull_tedata(url='united-states/ism-manufacturing-new-orders')
result = ds.pull_tedata(url='australia/unemployment-rate')
result = ds.pull_tedata(url='brent-crude-oil', browser='firefox')
# browser: 'auto' (default, tries Firefox first), 'firefox', 'chrome'
```

### Australian Bureau of Statistics (no API key)

```python
# Labour Force Survey (catalog 6202.0)
result = ds.pull_abs(series_id='A84423050A', catalog_num='6202.0')  # Unemployment rate
result = ds.pull_abs(series_id='A85255398K', catalog_num='6202.0')  # Total employment

# Find series IDs via search_abs()
```

### Reserve Bank of Australia (no API key)

```python
result = ds.pull_rba(series_id='ARBAMPCNCRT', table_no='A2')  # Cash rate
result = ds.pull_rba(series_id='ARIAUCYCRT', table_no='A2')  # Indicator rates
```

### Nasdaq Data Link (API key required — currently blocked by CDN)

```python
result = ds.pull_nasdaq('WIKI/AAPL', start_date='2020-01-01')
result = ds.pull_nasdaq('ECONOMIA/DEXUSEU')  # USD/EUR exchange rate
```

### Glassnode — On-chain crypto metrics (API key required)

```python
result = ds.pull_glassnode(metric='/market/price_usd_close', asset='BTC', interval='24h')
result = ds.pull_glassnode(metric='/market/market_cap_usd', asset='ETH', interval='24h')
result = ds.pull_glassnode(metric='/exchange/flow_in_exchange', asset='BTC', interval='24h')
# interval: '10m', '1h', '24h', '1w'. asset: 'BTC', 'ETH', 'SOL', etc.
```

### CryptoCompare — Alternative crypto data (no API key)

```python
result = ds.pull_cryptocompare('BTC', tsym='USD', start_date='2020-01-01', limit=2000)
result = ds.pull_cryptocompare('ETH', tsym='USD', limit=2000)
# limit: max 2000 daily bars per call
```

### Generic `pull()` Dispatcher

```python
# Route by source name string instead of calling a specific method
result = ds.pull('yfinance', 'AAPL', start_date='2023-01-01')
result = ds.pull('fred', 'GDP')
result = ds.pull('coingecko', 'bitcoin', days=90)
```

---

## 2. Search — Finding Series

Use `WatchlistSearch` to search across all sources before adding series to a watchlist. This is the recommended way to discover valid series IDs.

```python
from bm import WatchlistSearch

ws = WatchlistSearch()
```

### Search a Single Source

```python
# FRED — returns series id and title
results = ws.search('fred', 'inflation')          # DataFrame: id, title, source, meta
results = ws.search('fred', 'GDP, quarterly')     # Multi-term: match both words

# Yahoo Finance — search ticker symbols
results = ws.search('yfinance', 'apple')         # Returns symbol, longName

# CoinGecko — search coin names/IDs
results = ws.search('coingecko', 'bitcoin')

# TradingView
results = ws.search('tv', 'aapl', exchange='NASDAQ')

# ABS (Australian Bureau of Statistics)
results = ws.search('abs', 'unemployment')

# RBA (Reserve Bank of Australia)
results = ws.search('rba', 'cash rate')          # search_type='tables' (default)
results = ws.search('rba', 'inflation', search_type='series')

# BEA (Bureau of Economic Analysis)
results = ws.search('bea', 'GDP')                # requires API key

# Glassnode
results = ws.search('glassnode', 'price')        # requires API key

# Trading Economics
results = ws.search('tedata', 'consumer confidence')
```

### Search All Sources at Once

```python
# Searches all 11 sources and concatenates results
all_results = ws.search_all('inflation')
all_results = ws.search_all('GDP, quarterly')

# Filter results by source
fred_only = all_results[all_results['source'] == 'fred']
```

### Multi-Term and Wildcard Search

```python
# Comma-separated terms = AND-match (case-insensitive regex)
results = ws.search('fred', 'M2, weekly')

# Asterisk = wildcard (converted to .* in regex)
results = ws.search('fred', 'M2*')               # matches M2SL, M2NSL, etc.
```

### Result Format

All search methods return a `pandas.DataFrame` with columns:

| Column | Description |
|--------|-------------|
| `id` | Series identifier (ticker, code, URL path) |
| `title` | Human-readable name |
| `source` | Source name ('fred', 'yfinance', etc.) |
| `meta` | Full original result row as a dict |

---

## 3. Watchlists — Managing Series

A `Watchlist` holds multiple series, fetches their data, and persists to Excel or CSV.

```python
from bm import Watchlist, WatchlistSearch, SeriesMetadata, StandardSeries

wl = Watchlist(name='my_study')
```

### Build from Search Results

```python
ws = WatchlistSearch()
results = ws.search_all('inflation')

for _, row in results.iterrows():
    meta = SeriesMetadata(
        id=row['id'],
        title=row['title'],
        source=row['source'],
    )
    ss = StandardSeries(data={}, metadata=meta)
    wl.append_series(ss)
```

### Fetch Data for All Series

```python
# Fetch all series data from their respective sources
errors = wl.get_watchlist_data(start_date='2020-01-01', end_date='2024-12-31')

if errors:
    print("Failed series:")
    for series_id, exc in errors.items():
        print(f"  {series_id}: {exc}")
```

### Save and Load

```python
# Save as Excel (.xlsx + .h5s HDF5 sidecar for data)
wl.save_watchlist('my_study.xlsx')

# Save as CSV (watchlist index only — no series data)
wl.save_watchlist_csv('my_study.csv')

# Load from Excel
wl2 = Watchlist()
wl2.load_watchlist('my_study.xlsx')

# Load from CSV
wl2 = Watchlist()
wl2.load_watchlist_csv('my_study.csv')
# Then call wl2.get_watchlist_data() to fetch series data
```

### Manipulate Series

```python
# Drop a series
wl.drop_series('UNRATE')

# Remove duplicates
wl.deduplicate()

# View watchlist
print(wl.watchlist)          # DataFrame: id, source, title
print(wl.metadata)           # DataFrame: metadata rows indexed by property name

# Access series data directly
gdp_series = wl.datasets['GDP']
```

---

## 4. Charting — Plotting Series

Charting uses Plotly. The `Watchlist.plot_watchlist()` method is the simplest way to plot a loaded watchlist.

### Plot a Watchlist

```python
# Load a watchlist with data already fetched
wl = Watchlist()
wl.load_watchlist('my_study.xlsx')

# Simple plot — all series on left axis
fig = wl.plot_watchlist()

# Dual axis — specify series ids for each side
fig = wl.plot_watchlist(
    left=['GDP', 'UNRATE'],       # left axis
    right=['M2SL'],              # right axis
    plot_title='US Macro Overview',
    primary_yaxis_title='Billions USD',
    secondary_yaxis_title='YoY %',
)

# Save as high-resolution PNG
path = wl.save_chart('my_study.png', left=['GDP'], right=['UNRATE'], scale=3)
print(f"Saved to {path}")

# Or save as interactive HTML
from bm import charting
fig = wl.plot_watchlist(left=['GDP'])
charting.save_html(fig, 'my_study.html')
```

### Standalone Plotting Functions

```python
from bm import charting
import pandas as pd

# Single series
series = wl.datasets['GDP']
fig = charting.plot_series(
    series,
    title='US Gross Domestic Product',
    yaxis_title='Billions USD',
)
charting.save_png(fig, 'gdp.png', scale=3)

# Multiple series, dual axis
primary = {'GDP': gdp_series, 'UNRATE': unr_series}
secondary = {'M2SL': m2_series}
fig = charting.plot_multi(
    primary,
    secondary_series=secondary,
    title='Macro Dashboard',
    primary_yaxis_title='USD / Percent',
    secondary_yaxis_title='Billions USD',
)
```

### Display in Jupyter

```python
from bm import charting
fig = wl.plot_watchlist(left=['GDP'])
charting.show(fig)      # renders interactive Plotly chart
# or just: fig.show()
```

---

## 5. GUI — Watchlist Builder

A PyQt6 desktop application for interactive watchlist building. Launch it from the command line or a Python script.

### Launching the GUI

From the command line:
```bash
conda activate bm
python -m bm.gui.watchlist_builder
```

Or from a Python script:
```python
from bm.gui import WatchlistBuilderWindow
from PyQt6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = WatchlistBuilderWindow()
window.show()
sys.exit(app.exec())
```

Or via the shortcut:
```python
from bm.gui import launch
window = launch()
```

### GUI Features

**Search Panel (top)**
- Type a query and select a source from the dropdown (or "All Sources")
- Press Enter or click "Search" to run
- Results appear in the table below with id/title/source columns
- Search runs in a background thread (`SearchWorker` via `QThreadPool`) — the UI stays responsive

**Adding Series**
- Double-click any row in the results table to add it to the watchlist panel (bottom table)
- **No "New Watchlist" needed** — a default watchlist (`name="untitled"`) is created automatically on first double-click
- Added series appear in the watchlist panel with their id/source/title
- Duplicates (same id+source) are silently ignored

**Watchlist Panel (bottom)**
- "Remove Selected" — select rows in the watchlist panel and click to remove
- "Clear All" — remove all selected series
- "Load Watchlist" — open an existing `.xlsx` or `.csv` file
- "Save Watchlist" — save current selection to `.xlsx` (with data) or `.csv` (index only)
- Watchlist name is derived from the save filename (e.g., `my_study.xlsx` → name = `my_study`)

**File Menu**
- `File → New Watchlist` — start fresh (name = `untitled`)
- `File → Open Watchlist…` — load `.xlsx` or `.csv`
- `File → Save Watchlist…` — save to a location of your choosing
- `File → Quit` — exit the application
- Shortcuts: Ctrl+N (new), Ctrl+O (open), Ctrl+S (save)

**Default Save Location**
Watchlists are saved to `~/Documents/Bootleg_Macro/Watchlists/` (created automatically if it doesn't exist).

### Loading a Watchlist via Code

```python
window = WatchlistBuilderWindow()
window.load_watchlist('/path/to/my_watchlist.xlsx')

# Or pre-load into the window:
from bm import Watchlist
wl = Watchlist()
wl.load_watchlist('/path/to/my_watchlist.xlsx')
window = WatchlistBuilderWindow(watchlist=wl)
```

---

## 9. Logging

The `bm` package uses Python's standard `logging` module. The GUI has its own dedicated logger (`bm.gui`) that writes to stderr with timestamps.

### GUI Logging

All GUI actions are logged at `INFO` level and appear in the terminal where the GUI was launched:

```text
[14:36:22] INFO  bm.gui.__init__  Initialising WatchlistBuilderWindow
[14:36:22] INFO  bm.gui._ensure_watchlist  Created new default watchlist (name='untitled')
[14:36:22] INFO  bm.gui._on_search_clicked  Search button clicked — source=fred query='GDP'
[14:36:22] INFO  bm.gui._on_search_triggered  Search triggered — source=fred query='GDP'
[14:36:22] INFO  bm.gui.run  SearchWorker starting — source=fred query='GDP'
[14:36:22] INFO  bm.gui.run  SearchWorker done — 50 result(s) in 0.34s
[14:36:22] INFO  bm.gui._on_series_double_clicked  Adding GDP (fred) → watchlist 'untitled'
```

### Logger Hierarchy

| Logger name | Module | What's logged |
|------------|--------|---------------|
| `bm.gui` | `bm/gui/_logging.py` | GUI actions: search, double-click, save/load, errors |

### Using the Logger in Code

```python
from bm.gui._logging import log
log.info("Something happened: %s", value)
log.warning("Check this: %s", warning_msg)
log.error("Something broke: %s", exc_info=True)
```

The logger is pre-configured — no setup needed. It uses a `StreamHandler` at `INFO` level with format `[time] LEVEL name.funcName  message`.

### Adding Logging to a New Module

```python
import logging
log = logging.getLogger("bm.module_name")
log.setLevel(logging.INFO)
```

---

## 9. Logging

The `bm` package uses Python's standard `logging` module. The GUI has its own dedicated logger (`bm.gui`) that writes to stderr with timestamps.

### GUI Logging

All GUI actions are logged at `INFO` level and appear in the terminal where the GUI was launched:

```text
[14:36:22] INFO  bm.gui.__init__  Initialising WatchlistBuilderWindow
[14:36:22] INFO  bm.gui._ensure_watchlist  Created new default watchlist (name='untitled')
[14:36:22] INFO  bm.gui._on_search_clicked  Search button clicked — source=fred query='GDP'
[14:36:22] INFO  bm.gui._on_search_triggered  Search triggered — source=fred query='GDP'
[14:36:22] INFO  bm.gui.run  SearchWorker starting — source=fred query='GDP'
[14:36:22] INFO  bm.gui.run  SearchWorker done — 50 result(s) in 0.34s
[14:36:22] INFO  bm.gui._on_series_double_clicked  Adding GDP (fred) → watchlist 'untitled'
```

### Logger Hierarchy

| Logger name | Module | What's logged |
|------------|--------|---------------|
| `bm.gui` | `bm/gui/_logging.py` | GUI actions: search, double-click, save/load, errors |

### Using the Logger in Code

```python
from bm.gui._logging import log
log.info("Something happened: %s", value)
log.warning("Check this: %s", warning_msg)
log.error("Something broke: %s", exc_info=True)
```

The logger is pre-configured — no setup needed. It uses a `StreamHandler` at `INFO` level with format `[time] LEVEL name.funcName  message`.

### Adding Logging to a New Module

```python
import logging
log = logging.getLogger("bm.module_name")
log.setLevel(logging.INFO)
```

---

## 6. API Keys

API keys are stored in `bm/SystemInfo/API_Keys.json`. Copy the template and fill in your keys:

```bash
cp bm/SystemInfo/API_Keys.json.example bm/SystemInfo/API_Keys.json
```

```json
{
  "fred": "your_fred_api_key",
  "bea": "your_bea_api_key",
  "nasdaq": "your_nasdaq_api_key",
  "glassnode": "your_glassnode_api_key"
}
```

**Getting API keys:**
- **FRED**: https://fred.stlouisfed.org/docs/api/api_key.html (free)
- **BEA**: https://apps.bea.gov/developers/ (free registration)
- **Nasdaq Data Link**: https://data.nasdaq.com/ (free tier available)
- **Glassnode**: https://glassnode.com/pricing (subscription required)

Sources **not requiring API keys**: yfinance, coingecko, abs, rba, tedata, tradingview, cryptocompare.

---

## 7. Output Format — StandardSeries

All `Dataset.pull_*` methods return a `StandardSeries` object containing:

```python
result = ds.pull_yfinance('AAPL')

# The data as a dict {date_string: value}
print(result.data)          # {'2024-01-02': 185.59, '2024-01-03': 186.21, ...}

# Convert to pandas Series
series = result.to_pandas()
print(series.head())

# Metadata
print(result.metadata.id)           # 'AAPL'
print(result.metadata.title)        # 'Apple Inc.'
print(result.metadata.source)      # 'yfinance'
print(result.metadata.frequency)   # 'D'
print(result.metadata.units)      # 'USD'
print(result.metadata.length)     # 501
print(result.metadata.start_date) # datetime.date(2024, 1, 2)
print(result.metadata.end_date)   # datetime.date(2024, 12, 31)
print(result.metadata.last_updated) # datetime.datetime
```

**StandardSeries from scratch:**

```python
from bm import SeriesMetadata, StandardSeries

meta = SeriesMetadata(
    id='AAPL',
    title='Apple Inc.',
    source='yfinance',
    frequency='D',
    units='USD',
)
ss = StandardSeries(data={'2024-01-02': 185.59}, metadata=meta)

# Convert back to pandas
series = ss.to_pandas()
```

---

## 8. Multi-Param Sources

Some sources require multiple parameters beyond just the series ID. The watchlist stores these as delimited strings in the `id` column, parsed at fetch time.

| Source | ID Format | Example |
|--------|-----------|---------|
| **TradingView** | `symbol, exchange` | `AAPL, NASDAQ` |
| **BEA** | `dataset, table_code` | `NIPA, T10101` |
| **ABS** | `series_id, catalog_num` | `A84423050A, 6202.0` |
| **Glassnode** | `metric, asset, interval` | `/market/price_usd_close, BTC, 24h` |
| **CryptoCompare** | `fsym, tsym` | `BTC, USD` |

The `_parse_id()` function in `bm/watchlist.py` handles splitting these at load time.

**Example — constructing a multi-param watchlist entry programmatically:**

```python
from bm import Watchlist, Dataset, SeriesMetadata, StandardSeries

wl = Watchlist()

# TradingView — need symbol AND exchange
meta_tv = SeriesMetadata(
    id='AAPL, NASDAQ',            # comma-delimited in id column
    title='Apple on NASDAQ',
    source='tv',
)
wl.append_series(StandardSeries(data={}, metadata=meta_tv))

# Glassnode — metric, asset, interval
meta_gn = SeriesMetadata(
    id='/market/price_usd_close, BTC, 24h',   # comma-delimited
    title='BTC Price USD Close',
    source='glassnode',
)
wl.append_series(StandardSeries(data={}, metadata=meta_gn))

# Fetch data for all series
errors = wl.get_watchlist_data()

# Save
wl.save_watchlist('multi_param_study.xlsx')
```
