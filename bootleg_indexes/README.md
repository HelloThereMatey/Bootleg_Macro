# bootleg-indexes

Custom index construction from multiple time series.

Build aggregated indexes from `bootleg-datafeed` time series: Net Liquidity (NLQ) and Global M2 money supply indexes.

## Modules

### `nlq_clean` — Net Liquidity (NLQ) Index

Calculates the Net Liquidity metric originally formulated by Darius Dale and 42Macro:

```
Net Liquidity = Fed Balance Sheet - Treasury General Account (TGA) - Reverse Repo Facility (RRP)
```

Two classes:

- **`NLQDataFetcher`** — Fetches core data components:
  - FRED series via `bootleg_datafeed.Dataset` (WALCL, RESPPNTNWW, RRPONTSYD, WTREGEN)
  - Daily TGA balances via the US Treasury API (`api.fiscaldata.treasury.gov`) — more timely than FRED's weekly TGA data
  - Caches downloaded data to `{user_path}/NLQ_Data/` as Excel files

- **`NetLiquidity`** — Calculates three variants of NLQ:
  - **Weekly** — raw FRED data, no resampling (WALCL - WTREGEN - RRPONTSYD)
  - **Daily (Treasury TGA)** — all components resampled to daily, using Treasury API TGA data (most accurate)
  - Supports a QE-only mode (RESPPNTNWW instead of WALCL) for isolating QE-driven liquidity

#### Quick start

```python
from bootleg_indexes.nlq_clean import NetLiquidity

nlq = NetLiquidity(start_date="2010-01-01")
results = nlq.calculate_all()
nlq.summary()

# Access series
results['nlq_weekly']        # pd.Series
results['nlq_daily_treasury'] # pd.Series
results['fed_balance_sheet_daily']
```

### `gm2_data_handler` — Global M2 Index

Downloads M2 money supply data and FX rates for multiple countries via TradingView (through `bootleg_datafeed`), converts M2 to USD, and constructs aggregate Global M2 indexes.

Classes and functions:

- **`Global_M2`** — Main handler class:
  - Loads country configuration from Excel files (M2 symbols, FX symbols, exchanges, currency codes)
  - Downloads M2 close data and FX rates via `Dataset.pull_tradingview()` with 3x retry
  - Converts M2 to USD using appropriate FX inversion logic
  - Builds aggregate indexes (Top50, Top33, Long28, Long27, Top8) or custom groups
  - Provides forward-filled aggregate variants for handling missing recent data
  - Saves/loads data to/from HDF5 or Excel
  - Outlier detection and correction (IQR, z-score, percentage change, magnitude)

- **`identify_outliers()`** — Standalone outlier detection utility supporting multiple methods.

#### Quick start

```python
from bootleg_indexes.gm2_data_handler import Global_M2

gm2 = Global_M2()

# Download data for specific countries
gm2.download_data(n_bars=500, countries=['United States', 'Japan', 'China'])

# Build a custom aggregate
agg_raw, agg_ffill = gm2.create_aggregate(
    ['United States', 'Japan', 'China'],
    name="Top3"
)

# Or load predefined aggregates
gm2.load_aggregate_definitions()
gm2.create_all_aggregates()

# Save results
gm2.save_to_hdf5()
gm2.save_aggregates(format='xlsx')
```

#### Config files

Country configuration is stored in Excel files under `UpdateM2Infos/`:
| File | Contents |
|------|----------|
| `M2Info_Top50.xlsx` | Top 50 countries by economic weight |
| `M2Info_Top33.xlsx` | Top 33 countries |
| `M2Info_Long28.xlsx` | Long-only subset |
| `M2Info_Long27.xlsx` | Long-only subset (alt) |
| `M2Info_Top8.xlsx` | Top 8 countries |

Each file uses the country name as the index with columns for `M2_Symbol`, `M2_exchange`, `FX_Symbol`, `FX_Exchange`, and `M2_currency_code`. Config files are resolved automatically — the handler searches the package directory first, then falls back to the repo root's `Liquidity/Global_M2/` location.

## Source: TradingView data

Both modules use TradingView as the primary data source (via `bootleg_datafeed.dataset`), which requires a network connection. No API keys are needed for the TradingView source.

## Dependencies

- `bootleg-datafeed >= 0.1` (TradingView source, FRED API)
- `pandas >= 2.0`
- `numpy >= 1.0`
- `requests` (Treasury API for daily TGA)

## License

MIT
