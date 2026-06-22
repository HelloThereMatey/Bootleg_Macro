# bootleg-datafeed

Core data acquisition module for the **bm** (Bootleg Macro) ecosystem. Pulls financial and economic time series from 11+ sources into a unified `pandas`-based interface with standardized metadata. Includes an `extend_history` module for the ABS source that splices cross-frequency siblings to extend series history. Includes an `extend_history` module for the ABS source that splices cross-frequency siblings to extend series history.

## Installation

```bash
pip install bootleg-datafeed
```

Or install from source in editable mode:

```bash
cd bootleg_datafeed
pip install -e .
```

### Dependencies

- `pandas >= 2.0`
- `requests >= 2.0`
- `pydantic >= 2.0`
- `yfinance >= 0.1`
- `numpy >= 1.0`
- `readabs >= 0.1`
- `nasdaq-data-link >= 0.1`
- `openpyxl >= 3.0`

### Optional

Some sources require Node.js for search functionality:

```bash
cd bootleg_datafeed/sources
npm install
```

## Configuration

### User data directory

The default user data path is `~/Documents/Bootleg_Macro`. Override it by:

```python
from bootleg_datafeed import set_user_path, get_user_path

set_user_path("/path/to/data")
print(get_user_path())  # /path/to/data
```

Or via the `BM_USER_PATH` environment variable — set before starting Python:

```bash
export BM_USER_PATH=/path/to/data
```

### API Keys

Most sources require API keys stored in `{user_path}/system/API_Keys.json`:

```json
{
    "fred": "your_fred_api_key",
    "bea": "your_bea_api_key",
    "nasdaq": "your_nasdaq_data_link_key",
    "glassnode": "your_glassnode_api_key"
}
```

On first import, the `Dataset` class will prompt interactively for missing keys and save them. In non-interactive contexts (scripts, notebooks), an empty file is created and you must populate it manually.

Sources that **don't** need API keys: Yahoo Finance, TradingView, CoinGecko, CryptoCompare, ABS, RBA, Trading Economics.

## Usage

### Dataset — pull data from any source

```python
from bootleg_datafeed import Dataset

ds = Dataset()

# FRED (US macro) — requires 'fred' key in API_Keys.json
fred_data = ds.pull_fred("GDP")
fred_data = ds.pull_fred("CPIAUCSL")
fred_data = ds.pull_fred("UNRATE", start_date="2020-01-01")

# Yahoo Finance — no API key needed
yf_data = ds.pull_yfinance("SPY", interval="1d")
yf_data = ds.pull_yfinance("AAPL", start_date="2020-01-01", end_date="2024-12-31")

# BEA (Bureau of Economic Analysis) — requires 'bea' key
bea_data = ds.pull_bea(dataset="NIPA", table_code="T10101")

# ABS (Australian Bureau of Statistics) — no API key
abs_data = ds.pull_abs("A2304350A")
abs_data = ds.pull_abs("A84423050A", catalog_num="6202.0", extend=True)

# RBA (Reserve Bank of Australia) — no API key
rba_data = ds.pull_rba("GCPIAG", table_no="G2")

# CoinGecko (crypto) — no API key
cg_data = ds.pull_coingecko("bitcoin", days=365)

# CryptoCompare — no API key
cc_data = ds.pull_cryptocompare("BTC", "USD", limit=2000)

# Nasdaq Data Link — requires 'nasdaq' key
ndl_data = ds.pull_nasdaq("CHRIS/CME_CL1")

# Glassnode (on-chain crypto) — requires 'glassnode' key
gn_data = ds.pull_glassnode("/market/price_usd_close", asset="BTC")

# TradingView — no API key
tv_data = ds.pull_tradingview("SPY", exchange="NASDAQ", interval="1D")

# Trading Economics — no API key, uses Selenium scraping
te_data = ds.pull_tedata("united-states/gdp", timeout=30)

# Generic pull method — routes to the right source automatically
data = ds.pull("fred", "GDP")
data = ds.pull("tv", "BTCUSD", exchange="INDEX", interval="1D")
```

All `pull_*` methods return a `StandardSeries` object with `.to_pandas()` for the raw series and `.metadata` for metadata.

### Search — find series across sources

```python
from bootleg_datafeed import WatchlistSearch

searcher = WatchlistSearch()

# Search all sources at once
results = searcher.search_all("GDP")

# Search a specific source
results = searcher.search("fred", "unemployment")
results = searcher.search("coingecko", "bitcoin")
results = searcher.search("abs", "labour force")

# Results are DataFrames with columns: id, title, source, meta
# The meta column contains source-specific details as a dict
```

Multi-term search (comma-separated terms use AND logic, `*` for wildcard):

```python
# Both terms must match
results = searcher.search("fred", "GDP, monthly")

# Wildcard prefix
results = searcher.search("fred", "CP*")
```

### Models

```python
from bootleg_datafeed.models import SeriesMetadata, StandardSeries
import pandas as pd

# SeriesMetadata holds id, title, source, frequency, and computed stats
meta = SeriesMetadata(
    id="GDP",
    title="Gross Domestic Product",
    source="fred",
    frequency="Q",
    units="Billions of Dollars",
)

# StandardSeries wraps data + metadata
data = pd.Series([1.0, 2.0, 3.0], index=pd.date_range("2020-01-01", periods=3, freq="QE"))
series = StandardSeries(data=data, metadata=meta)

# Access data and metadata
pandas_series = series.to_pandas()
print(series.metadata.title)
```

### Auxiliary utilities

```python
from bootleg_datafeed.auxiliary import (
    parse_date,         # Parse flexible date formats
    infer_frequency,    # Infer frequency code from DatetimeIndex
    sanitize_string,    # Clean strings for HDF5 keys
    hdf_key_safe,       # Sanitize a key for HDF5 store
    convert_to_standard_series,  # Normalize a raw Series
    calculate_metadata_stats,    # Compute min/max/length stats
    FrequencyConverter, # Resample between frequencies
    drop_duplicate_columns,      # Remove duplicate DataFrame columns
    close_open_stores,           # Close any open HDF5 stores
    strip_timezone_from_df,      # Strip tz from DatetimeIndex columns
)
```

### API key management

```python
ds = Dataset()

# Programmatically set (and persist) a key
ds.set_api_key("fred", "my_fred_key")

# Retrieve a key
key = ds.get_api_key("fred")
```

## Sources

| Source | Module | API Key | Notes |
|--------|--------|---------|-------|
| FRED | `fred_source` | Yes | US macro data |
| BEA | `bea_source` | Yes | US national accounts |
| Yahoo Finance | `yfinance_source` | No | Price data |
| TradingView | `tv_source` | No | Price data, 5000 bar limit |
| CoinGecko | `coingecko_source` | No | Crypto prices, 365 day limit |
| CryptoCompare | `cryptocompare_source` | No | Crypto prices, 2000 bar limit |
| Nasdaq Data Link | `nasdaq_source` | Yes | Formerly Quandl |
| Glassnode | `glassnode_source` | Yes | On-chain crypto metrics |
| ABS (Australia) | `abs_source` | No | Australian Bureau of Statistics |
| RBA (Australia) | `rba_source` | No | Reserve Bank of Australia |
| Trading Economics | `tedata_source` | No | Selenium scraping |

## License

MIT
