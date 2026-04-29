# bm - Bootleg Macro Data Library

A clean, refactored Python library for downloading financial and economic time series data with standardized metadata and output formats.

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
├── __init__.py          # Package exports (Dataset, StandardSeries, SOURCES)
├── models.py            # Pydantic models (SeriesMetadata, StandardSeries)
├── auxiliary.py         # Helper functions (date parsing, frequency detection)
├── dataset.py           # Main Dataset class
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
└── tests/               # Test suite
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

## Development

This package is being developed as a standalone library extracted from the Bootleg_Macro project.

### Key Files
- `dataset.py` - Main Dataset class with `pull_*` methods
- `models.py` - Pydantic models for metadata standardization
- `auxiliary.py` - Helper functions for date/frequency handling
- `sources/` - Individual source implementations

### Adding a New Source

1. Create `sources/newsource_source.py` with `pull_newsource()` function
2. Add `pull_newsource()` method to `Dataset` class in `dataset.py`
3. Add routing in `Dataset.pull()` method
4. Add tests in `tests/`
5. Update this README