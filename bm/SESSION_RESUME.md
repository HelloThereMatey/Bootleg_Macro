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
├── sources/
│   ├── __init__.py
│   ├── yfinance_source.py   # Yahoo Finance (IMPLEMENTED, TESTED)
│   ├── coingecko_source.py  # CoinGecko (IMPLEMENTED, TESTED)
│   ├── fred_source.py       # FRED (IMPLEMENTED, needs API key to test)
│   └── abs_source.py        # Australian Bureau of Stats (IMPLEMENTED, TESTED)
└── test_*.py                # Test scripts
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

### 4. FRED (`fred`) ⚠️ IMPLEMENTED, NEEDS API KEY TO TEST

**Module**: `bm/sources/fred_source.py`

**Functions**:
- `pull_fred(series_id, api_key, start_date, end_date)` → `StandardSeries`
- `search_fred(search_text, api_key)` → DataFrame

**Status**: Code is implemented and placeholder correctly raises error when API key missing. To fully test, need FRED API key.

**Placeholder Behavior** (confirmed from test):
```
ds.pull_fred('GDP') → ValueError: "FRED API key required. Add 'fred' key to your API_Keys.json"
```

---

## Placeholder Sources (Not Yet Implemented)

These sources have placeholder methods in `dataset.py` that raise `NotImplementedError`:

| Source | Module | Status | Notes |
|--------|--------|--------|-------|
| **bea** | Bureau of Economic Analysis | Placeholder | Needs API key |
| **nasdaq** | Nasdaq Data Link | Placeholder | Needs API key |
| **glassnode** | On-chain crypto | Placeholder | Needs API key |
| **rba** | Reserve Bank Australia | Placeholder | Could use readabs Python package |
| **tradingview** | TradingView | Placeholder | Needs local `tvDatafeedz` module |
| **tedata** | Trading Economics | Placeholder | Needs `tedata` package |

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

---

## Questions Outstanding

1. **RBA implementation**: Original Bootleg_Macro used R `readrba` package. `readabs` Python package may have RBA support (has `rba_catalogue`, `rba_meta_data`, `read_rba_table`, `read_rba_ocr` functions). Could implement without R.

2. **TradingView**: Requires local `tvDatafeedz` module from Bootleg_Macro. Not pip-installable. Should we integrate it or use an alternative?

3. **BEA**: Complex table-based API. Original has extensive caching logic. Should we implement fully or just as placeholder?

4. **NAS/Glassnode/Nasdaq**: Need API keys. Should we implement test stubs that can be verified with keys?

---

## Next Tasks (Priority Order)

### High Priority
1. **Verify FRED with real API key** - Implement `bm/test_fred.py` once API key is available
2. **Implement RBA source** - Try using `readabs` Python package's RBA functions first (no R needed)

### Medium Priority
3. **Implement BEA source** - Complex, table-based with caching
4. **Implement Nasdaq source** - nasdaqdatalink Python package available
5. **Implement Glassnode source** - Need API key, complex API

### Lower Priority
6. **TradingView** - Requires tvDatafeedz integration
7. **Trading Economics (tedata)** - Need to investigate package availability

---

## Files Created/Modified

### Created
- `bm/__init__.py`
- `bm/models.py`
- `bm/auxiliary.py`
- `bm/dataset.py`
- `bm/sources/__init__.py`
- `bm/sources/yfinance_source.py`
- `bm/sources/coingecko_source.py`
- `bm/sources/fred_source.py`
- `bm/sources/abs_source.py`
- `bm/test_yfinance.py`
- `bm/test_coingecko.py`
- `bm/test_abs.py`
- `bm/test_all_sources.py`

### Modified (Bug Fixes)
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

**API Keys Needed**:
- FRED API key (for full FRED testing)
- BEA API key (for BEA implementation)
- Nasdaq API key (for Nasdaq implementation)
- Glassnode API key (for Glassnode implementation)

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

# Quick import check
python -c "from bm import Dataset; print('OK')"
```
