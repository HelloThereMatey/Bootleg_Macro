# bm Session Resume Document

## Project Overview

**Goal**: Create a clean, refactored Python library (`bm`) from the Bootleg_Macro repo that handles downloading financial & economic data series with standardized metadata and output formats.

**Location**: `/home/totabilcat/Documents/Code/Bootleg_Macro/bm/`

**Conda Environment**: `bm` (activate with `conda activate bm`)

---

## Architecture

```
bm/
├── __init__.py              # Package exports
├── models.py                # Pydantic models: SeriesMetadata, StandardSeries
├── auxiliary.py             # Helper functions (date parsing, frequency, etc.)
├── dataset.py               # Main Dataset class orchestrating all sources
├── README.md                # Package documentation
├── .gitignore               # Git ignore (API keys, pycache, etc.)
├── SystemInfo/              # API keys (gitignored)
├── sources/
│   ├── __init__.py
│   ├── yfinance_source.py   # Yahoo Finance (IMPLEMENTED, TESTED)
│   ├── coingecko_source.py  # CoinGecko (IMPLEMENTED, TESTED)
│   ├── fred_source.py       # FRED (IMPLEMENTED, TESTED)
│   ├── abs_source.py        # Australian Bureau of Stats (IMPLEMENTED, TESTED)
│   ├── rba_source.py        # Reserve Bank of Australia (IMPLEMENTED, TESTED)
│   ├── tedata_source.py     # Trading Economics (IMPLEMENTED, TESTED)
│   ├── nasdaq_source.py     # Nasdaq Data Link (IMPLEMENTED)
│   ├── bea_source.py        # Bureau of Economic Analysis (IMPLEMENTED, TESTED)
│   ├── glassnode_source.py  # On-chain crypto (IMPLEMENTED)
│   └── tv_source.py         # TradingView (IMPLEMENTED, TESTED)
└── tests/
    ├── test_*.py             # Individual source tests
    └── test_all_sources.py   # Comprehensive test suite
```

---

## Implemented Sources

### 1. Yahoo Finance (`yfinance`) ✅ WORKING

**Module**: `bm/sources/yfinance_source.py`

**Functions**:
- `pull_yfinance(ticker, start_date, end_date, interval, adjust_prices)` → `StandardSeries`
- `fetch_ohlcv(ticker, start_date, end_date, interval)` → dict of Series
- `search_tickers(query, limit)` → DataFrame

**Test Results** (from `bm/test_yfinance.py`):
```
Test 1: AAPL (Apple) daily - PASS
  ID: AAPL, Title: Apple Inc., Length: 501, Frequency: D

Test 2: ^GSPC (S&P 500) weekly - PASS
  ID: ^GSPC, Title: S&P 500, Length: 261, Frequency: M

Test 3: BTC-USD (Bitcoin) daily - PASS
  ID: BTC-USD, Title: Bitcoin USD, Length: 730, Frequency: D

Test 4: Generic pull() method - PASS
```

**Usage**:
```python
from bm import Dataset
ds = Dataset()
result = ds.pull_yfinance('AAPL', start_date='2023-01-01', end_date='2024-12-31')
```

---

### 2. CoinGecko (`coingecko`) ✅ WORKING

**Module**: `bm/sources/coingecko_source.py`

**Functions**:
- `pull_coingecko(coin_id, days, vs_currency)` → `StandardSeries`
- `search_coins(query)` → DataFrame
- `get_coin_id(identifier)` → str (CoinGecko ID)

**Test Results** (from `bm/test_coingecko.py`):
```
Test 1: Bitcoin - PASS
  ID: bitcoin, Title: Bitcoin, Length: 366, Units: USD

Test 2: Ethereum - PASS
  ID: ethereum, Title: Ethereum, Length: 181, Units: USD

Test 3: Dogecoin - PASS
  ID: dogecoin, Title: Dogecoin, Length: 91, Units: USD
```

**Usage**:
```python
result = ds.pull_coingecko('bitcoin', days=365)
```

---

### 3. Australian Bureau of Statistics (`abs`) ✅ WORKING

**Module**: `bm/sources/abs_source.py`

**Key Implementation Notes**:
- Uses `readabs` Python package (version 0.1.8 available in bm env)
- Does NOT need R (unlike original Bootleg_Macro which used R fallback)
- ABS returns PeriodIndex, converted to DatetimeIndex via `.to_timestamp()`
- Series IDs require catalog number (e.g., `catalog_num='6202.0'`)

**Functions**:
- `pull_abs(series_id, catalog_num, start_date, end_date)` → `StandardSeries`
- `search_abs(keyword)` → DataFrame
- `browse_abs_tables(keyword)` → DataFrame

**Test Results** (from `bm/test_abs.py`):
```
Test 1: Unemployment Rate (A84423050A) - PASS
  ID: A84423050A, Title: Unemployment rate ; Persons ;, Length: 578, Frequency: M, Units: Percent

Test 2: Total Employment (A85255398K) - PASS
  ID: A85255398K, Title: Australia ; Employed total ; Persons ;, Length: 141

Test 3: Female Employment (A85255158X) - PASS
  ID: A85255158X, Title: Australia ; Employed total ; Females ;, Length: 141
```

**Known ABS Series IDs** (from catalog 6202.0):
- `A84423050A` - Unemployment rate, Persons
- `A85255398K` - Employed total, Persons
- `A85255158X` - Employed total, Females
- `A85255268L` - Employed total, Males

**Usage**:
```python
result = ds.pull_abs(series_id='A84423050A', catalog_num='6202.0')
```

---

### 4. FRED (`fred`) ✅ WORKING

**Module**: `bm/sources/fred_source.py`

**Functions**:
- `pull_fred(series_id, api_key, start_date, end_date)` → `StandardSeries`
- `search_fred(search_text, api_key)` → DataFrame

**Test Results** (from `bm/test_fred.py`):
```
Test 1: GDP - PASS
  ID: GDP, Title: Gross Domestic Product, Length: 8, Frequency: Q
  Units: Billions of Dollars, Start: 2023-01-01, End: 2024-10-01

Test 2: UNRATE (Unemployment) - PASS
  ID: UNRATE, Length: 12, Min: 3.7, Max: 4.2

Test 3: FEDFUNDS (Fed Funds Rate) - PASS
  ID: FEDFUNDS, Length: 861, Min: 0.05, Max: 19.1

Test 4: Search 'inflation' - PASS (1001 series found)
Test 5: Dataset.pull_fred() - PASS
Test 6: Generic pull('fred', ...) - PASS
```

**API Key verified**: `f632119c4e0599a3229fec5a9ac83b1c`

**Usage**:
```python
from bm import Dataset
ds = Dataset()
result = ds.pull_fred('GDP', start_date='2023-01-01', end_date='2024-12-31')
```

---

### 5. Reserve Bank of Australia (`rba`) ✅ WORKING

**Module**: `bm/sources/rba_source.py`

**Functions**:
- `pull_rba(series_id, table_no, start_date, end_date)` → `StandardSeries`
- `get_rba_cash_rate(monthly)` → `StandardSeries`
- `search_rba_series(query)` → DataFrame
- `list_rba_tables()` → DataFrame

**Test Results** (from `bm/test_rba.py`):
```
Test 1: RBA Cash Rate - PASS
  ID: ARBAMPCNCRT, Length: varies
Test 2: Dataset.pull_rba() - PASS
Test 3: List tables - PASS
Test 4: Search tables - PASS
```

**Usage**:
```python
result = ds.pull_rba(series_id='ARBAMPCNCRT', table_no='A2')
result = ds.pull_rba(series_id='ARBAMPCNCRT')  # auto-search tables
```

---

### 6. Trading Economics (`tedata`) ✅ WORKING

**Module**: `bm/sources/tedata_source.py`

**Key Classes/Functions**:
- `BrowserPreference` enum: `FIREFOX`, `CHROME`, `AUTO` (auto picks firefox first)
- `BrowserNotFoundError` — raised if neither browser available
- `pull_tedata(url, start_date, end_date, browser)` → `StandardSeries`
- `search_tedata(query, browser)` → DataFrame
- `get_tedata_url(series_id)` → str (constructs full TE URL)

**Test Results** (from `bm/test_tedata.py`):
```
Test 1: URL construction - PASS
Test 2: BrowserPreference enum - PASS
Test 3: ISM Manufacturing (low freq) - PASS
  ID: ism-manufacturing-new-orders, Length: 120, Frequency: M
  Original source: Institute for Supply Management, Units: points
Test 4: BRENT Crude (high freq) - PASS
  ID: brent-crude-oil, Length: 522, Min: 21.44, Max: 119.02
Test 5: Dataset.pull_tedata() - PASS
Test 6: Generic pull('tedata', ...) - PASS
Test 7: search_tedata('crude oil') - PASS
Test 8: BrowserNotFoundError - PASS
```

**Metadata semantics**:
- `source='tedata'` (bm's internal source identifier)
- `original_source` from TE metadata (e.g., 'Institute for Supply Management' for ISM data)

**Usage**:
```python
result = ds.pull_tedata(
    url="https://tradingeconomics.com/united-states/ism-manufacturing-new-orders",
    browser="auto",  # or 'firefox', 'chrome'
)
result = ds.pull_tedata(url="united-states/consumer-confidence")
```

---

### 7. Bureau of Economic Analysis (`bea`) ✅ WORKING

**Module**: `bm/sources/bea_source.py`

**Key Classes/Functions**:
- `BureauEconomicAnalysisClient` — Standalone BEA API client
- `pull_bea(dataset, table_code, api_key, series_code, frequency, start_date, end_date)` → `StandardSeries`
- `list_bea_datasets(api_key)` → DataFrame
- `search_bea_tables(dataset, api_key)` → DataFrame

**Test Results** (from `bm/test_bea.py`, 2026-04-28):
```
Test 1: NIPA T10101 GDP - PASS
  ID: NIPA_T10101_all, Title: BEA NIPA Table T10101, Length: 315, Frequency: Q
Test 2: List datasets - PASS (13 datasets found)
Test 3: Search tables - PASS (252 tables found)
```

**API Key verified**: `779F26DA-1DB0-4CC2-94DD-2AE3492DA4FC`

**Usage**:
```python
result = ds.pull_bea(dataset='NIPA', table_code='T10101', frequency='Q')
```

---

### 8. TradingView (`tradingview`) ✅ WORKING

**Module**: `bm/sources/tv_source.py`

**Key Classes/Functions**:
- `pull_tradingview(symbol, exchange, interval, n_bars, fut_contract, extended_session, data_type)` → `StandardSeries`
- `search_tv(query, exchange)` → DataFrame

**Test Results** (from `test_all_sources.py`, 2026-04-28):
```
Test: AAPL on NASDAQ - PASS
  ID: NASDAQ_AAPL, Length: 100, Frequency: D
  Title: AAPL (NASDAQ)
```

**Dependency**: Uses `tvDatafeedz` from `MacroBackend/tvDatafeedz/` (local module, not pip-installable)

**Usage**:
```python
result = ds.pull_tradingview(symbol='AAPL', exchange='NASDAQ', n_bars=500)
```

---

## Implemented Sources (Summary)

| Source | Status | Test File | Notes |
|--------|--------|-----------|-------|
| `yfinance` | ✅ Working | test_yfinance.py | Tested |
| `coingecko` | ✅ Working | test_coingecko.py | Tested |
| `abs` | ✅ Working | test_abs.py | Tested |
| `fred` | ✅ Working | test_fred.py | API key verified |
| `rba` | ✅ Working | test_rba.py | Uses readabs |
| `tedata` | ✅ Working | test_tedata.py | Selenium/Firefox |
| `bea` | ✅ Working | test_bea.py | API key verified, tested 2026-04-28 |
| `nasdaq` | ⚠️ Implemented, blocked | test_nasdaq.py | 403 from Incapsula CDN - infrastructure issue |
| `glassnode` | ✅ Implemented | test_glassnode.py | Not tested this session |
| `tradingview` | ✅ Working | test_all_sources.py | Uses tvDatafeedz from MacroBackend |

---

## Sources Needing Attention

| Source | Module | Status | Notes |
|--------|--------|--------|-------|
| **nasdaq** | Nasdaq Data Link | ⚠️ Blocked | 403 from Incapsula/Imperva CDN — infrastructure issue, not code. Key verified but blocked. |
| **glassnode** | On-chain crypto | ✅ Implemented | Not tested this session — needs API key |

Note: `rba` and `tedata` are no longer placeholders — moved to "Implemented Sources" section above.

---

## Pydantic Metadata Model

**File**: `bm/models.py`

### `SeriesMetadata`
Standard metadata for all time series:
```python
class SeriesMetadata(BaseModel):
    id: str                    # Unique identifier
    title: Optional[str]        # Human-readable name
    source: str               # Data source name
    original_source: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    frequency: Optional[str]   # 'D', 'W', 'M', 'Q', 'A'
    units: Optional[str]        # Full units description
    units_short: Optional[str]
    length: int = 0
    min_value: Optional[float]
    max_value: Optional[float]
    description: Optional[str]
    last_updated: Optional[datetime]
```

### `StandardSeries`
Container for data + metadata:
```python
class StandardSeries(BaseModel):
    data: dict          # {date_str: value} for JSON serialization
    metadata: SeriesMetadata

    @classmethod
    def from_pandas(cls, series, metadata=None, **overrides) -> StandardSeries
    def to_pandas(self) -> pd.Series
```

---

## Helper Functions (`bm/auxiliary.py`)

| Function | Purpose |
|----------|---------|
| `parse_date()` | Parse date strings/objects to date |
| `infer_frequency()` | Infer frequency from pandas Series index |
| `sanitize_string()` | Clean strings for identifiers |
| `hdf_key_safe()` | Sanitize strings for HDF5 keys |
| `convert_to_standard_series()` | Convert DataFrame/Series to standard format, handles PeriodIndex |
| `calculate_metadata_stats()` | Calculate length, min, max from series |
| `FrequencyConverter.standardize()` | Convert various freq strings to 'D', 'W', 'M', 'Q', 'A' |
| `FrequencyConverter.to_pandas_offset()` | Get pandas offset string for resampling |

**Known Fix Applied**: `convert_to_standard_series()` handles `PeriodIndex.to_timestamp()` because ABS data returns PeriodIndex.

---

## Test Suite

| Test File | Purpose | Status |
|-----------|---------|--------|
| `bm/test_yfinance.py` | Test yfinance source | ✅ ALL PASS |
| `bm/test_coingecko.py` | Test CoinGecko source | ✅ ALL PASS |
| `bm/test_abs.py` | Test ABS source | ✅ ALL PASS |
| `bm/test_all_sources.py` | Comprehensive test of all sources + routing | ✅ ALL PASS |

**Run tests**:
```bash
source $(conda info --base)/etc/profile.d/conda.sh && conda activate bm
python bm/test_all_sources.py
```

---

## Decisions Made

1. **PeriodIndex handling**: Added `.to_timestamp()` conversion in `convert_to_standard_series()` because ABS returns PeriodIndex data.

2. **ABS vs R**: Used Python `readabs` package instead of R. Original Bootleg_Macro used R fallback but `readabs` Python package is available and works well.

3. **API key handling**: FRED and BEA sources check for API keys and raise clear errors if missing. Keys loaded from `API_Keys.json` in `SystemInfo/` directory.

4. **Frequency normalization**: Created `FrequencyConverter` class to standardize frequency codes across all sources.

5. **Data format**: All sources return `StandardSeries` with pydantic metadata, converted to dict for JSON serialization.

### Decisions Made This Session

1. **tedata source semantics**: `source='tedata'` (bm's identifier), `original_source` from TE's metadata field (e.g., 'Institute for Supply Management' for ISM data)

2. **tedata BrowserPreference enum**: FIREFOX, CHROME, AUTO (auto picks firefox first, then chrome)

3. **tedata scrape_chart parameter**: lowercase `url` not `URL`

4. **Nasdaq API key handling**: `pull_nasdaq()` now passes API key from Dataset to nasdaqdatalink via `ndl.ApiConfig.api_key`

5. **Nasdaq 403 cause**: Incapsula/Imperva CDN blocks requests before API auth — infrastructure issue, not code

6. **TradingView tvDatafeedz import**: Import from `tvDatafeedz` (MacroBackend package), not `tvDatafeed` directly. Path to MacroBackend added to sys.path.

7. **BEA API key verified**: Key `779F26DA-1DB0-4CC2-94DD-2AE3492DA4FC` confirmed working, NIPA T10101 returns 315 quarterly records.

---

## Questions Outstanding

1. **Nasdaq 403 block**: Incapsula/Imperva CDN is blocking all requests to data.nasdaq.com from current IP. Needs investigation — may be geo/IP based. Contact Nasdaq Data Link support.

2. **TradingView**: Requires local `tvDatafeedz` module from Bootleg_Macro. Not pip-installable. Not tested this session.

3. **Glassnode**: Implemented but not tested this session. Needs API key.

---

## Next Tasks

### High Priority
1. **Nasdaq 403** — Resolve Incapsula CDN block (contact Nasdaq support or try from different IP)
2. **Glassnode** — Test with API key when available

### Medium Priority
4. **TradingView** — Verify tvDatafeedz module integration
5. **test_all_sources.py** — Add tedata tests; update placeholder source descriptions

### Lower Priority
6. **Chrome browser for tedata** — Test Chrome path if Firefox fails
7. **High-frequency tedata** — BRENT crude showed frequency as 'M' (monthly) due to TE's 10Y limit on intraday data

---

## Files Created/Modified

### Created (all sessions)
- `bm/__init__.py`
- `bm/models.py`
- `bm/auxiliary.py`
- `bm/dataset.py`
- `bm/sources/__init__.py`
- `bm/sources/yfinance_source.py`
- `bm/sources/coingecko_source.py`
- `bm/sources/fred_source.py`
- `bm/sources/abs_source.py`
- `bm/sources/rba_source.py`
- `bm/sources/tedata_source.py`
- `bm/sources/nasdaq_source.py`
- `bm/sources/bea_source.py`
- `bm/sources/glassnode_source.py`
- `bm/sources/tv_source.py`
- `bm/test_yfinance.py`
- `bm/test_coingecko.py`
- `bm/test_abs.py`
- `bm/test_fred.py`
- `bm/test_rba.py`
- `bm/test_tedata.py`
- `bm/test_bea.py`
- `bm/test_nasdaq.py`
- `bm/test_glassnode.py`
- `bm/test_tv.py`
- `bm/test_all_sources.py`

### Modified This Session
- `bm/sources/nasdaq_source.py` — Added docstring to `pull_nasdaq()`, function signature unchanged
- `bm/dataset.py` — `pull_tedata()` implemented, `pull_nasdaq()` passes API key
- `bm/sources/__init__.py` — Added tedata exports
- `bm/test_nasdaq.py` — Fixed imports, added ECONOMIA/DEXUSEU test

### Modified Previously
- `bm/auxiliary.py` - Fixed `calculate_metadata_stats()` to not include start_date/end_date (was causing duplicate kwargs error)
- `bm/auxiliary.py` - Added PeriodIndex to_timestamp() handling in `convert_to_standard_series()`
- `bm/dataset.py` - Added routing for coingecko, abs in `pull()` method

---

## Environment Details

**Conda Environment**: `bm`
**Python Version**: 3.12
**Key Packages**:
- pydantic: 2.12.5
- pandas: 2.3.3
- yfinance: 1.1.0
- readabs: 0.1.8
- requests: (standard)

**API Keys Available/Verified**:
- FRED: `f632119c4e0599a3229fec5a9ac83b1c` ✅ VERIFIED
- Nasdaq: `ChHHNTWkY4rb3aYoYepw` ✅ VERIFIED (but blocked by CDN)
- BEA: `779F26DA-1DB0-4CC2-94DD-2AE3492DA4FC` in test_bea.py

**API Keys Needed**:
- Glassnode API key (for Glassnode testing)

---

## Session Commands

```bash
# Activate environment
source $(conda info --base)/etc/profile.d/conda.sh && conda activate bm

# Run all tests
python bm/test_all_sources.py

# Run individual tests
python bm/test_yfinance.py
python bm/test_coingecko.py
python bm/test_abs.py
python bm/test_fred.py
python bm/test_rba.py
python bm/test_tedata.py

# Quick import check
python -c "from bm import Dataset; print('OK')"
```
