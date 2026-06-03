# bootleg-datafeed

Core data acquisition module for the **bm** (Bootleg Macro) ecosystem. Pulls financial and economic time series from 11+ data sources into a unified `pandas`-based interface.

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

### API Keys

Most sources require API keys stored in `bootleg_datafeed/SystemInfo/API_Keys.json`:

```json
{
    "fred": "your_fred_api_key",
    "bea": "your_bea_api_key",
    "nasdaq": "your_nasdaq_data_link_key",
    "glassnode": "your_glassnode_api_key"
}
```

Sources that **don't** need API keys: Yahoo Finance, TradingView, CoinGecko, CryptoCompare, ABS, RBA, Trading Economics.

## Usage

### Dataset — pull data from any source

```python
from bootleg_datafeed import Dataset

ds = Dataset()

# FRED (US macro)
fred_data = ds.pull_fred("GDP", api_key="...")
fred_data = ds.pull_fred("CPIAUCSL", api_key="...")

# Yahoo Finance
yf_data = ds.pull_yfinance("SPY", interval="1d")

# BEA (Bureau of Economic Analysis)
bea_data = ds.pull_bea("NIPA|T10101|A191RX", api_key="...")

# Australian Bureau of Statistics
abs_data = ds.pull_abs("A2304350A")

# Reserve Bank of Australia
rba_data = ds.pull_rba("GCPIAG")

# CoinGecko (crypto)
cg_data = ds.pull_coingecko("bitcoin")

# CryptoCompare
cc_data = ds.pull_cryptocompare("BTC", "USD")

# Nasdaq Data Link
ndl_data = ds.pull_nasdaq("CHRIS/CME_CL1", api_key="...")

# Glassnode (on-chain crypto)
gn_data = ds.pull_glassnode("addresses/active_count", api_key="...", asset="BTC")

# TradingView
tv_data = ds.pull_tv("NASDAQ:SPY")

# Trading Economics
te_data = ds.pull_tedata("us gdp")
```

### Search — find series across sources

```python
from bootleg_datafeed import WatchlistSearch

searcher = WatchlistSearch()

# Search all sources
results = searcher.search("GDP", source="all")

# Search a specific source
fred_results = searcher.search("inflation", source="fred")
yf_results = searcher.search("Apple", source="yfinance")
```

### Models

```python
from bootleg_datafeed.models import SeriesMetadata, StandardSeries

# SeriesMetadata holds id, title, source
meta = SeriesMetadata(id="GDP", title="Gross Domestic Product", source="fred")

# StandardSeries wraps data + metadata
series = StandardSeries(data=pd.Series(...), metadata=meta)
```

## Sources

| Source | Module | API Key | Search |
|--------|--------|---------|--------|
| FRED | `fred_source` | Yes | Yes |
| BEA | `bea_source` | Yes | Yes |
| Yahoo Finance | `yfinance_source` | No | Yes |
| TradingView | `tv_source` | No | Yes |
| CoinGecko | `coingecko_source` | No | Yes |
| CryptoCompare | `cryptocompare_source` | No | Yes |
| Nasdaq Data Link | `nasdaq_source` | Yes | Yes |
| Glassnode | `glassnode_source` | Yes | Yes |
| ABS (Australia) | `abs_source` | No | Yes |
| RBA (Australia) | `rba_source` | No | Yes |
| Trading Economics | `tedata_source` | No | Yes |

## License

MIT
