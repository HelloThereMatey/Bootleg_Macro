# CLAUDE.md

## Repo specific instructions

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
cd Bootleg_Macro/setup
chmod +x setup.sh
./setup.sh          # creates conda environment "bm" with all dependencies
conda activate bm   # always activate this environment when working in the repo
```

## Common Commands

```bash
# Run charting tool (Macro_Chartist)
cd Bootleg_Macro/Macro_Chartist
python chartist.py

# Run NetLiquidity tool
cd Bootleg_Macro/Liquidity/NetLiquidity
python nlq.py

# Run Global M2 tool
cd Bootleg_Macro/Liquidity/Global_M2
python Plot_GM2.py

# Run a single test/example
cd Bootleg_Macro
python -c "from MacroBackend import Pull_Data; print(Pull_Data.dataset().added_sources)"
```

## Architecture

```
Bootleg_Macro/
├── MacroBackend/           # Core Python library — data pulling, charting, utilities
│   ├── Pull_Data.py       # Main entry point: dataset.get_data() for all sources
│   ├── PriceImporter.py   # Price/crypto data (Yahoo Finance, TradingView, CoinGecko)
│   ├── Charting.py       # Matplotlib charting utilities
│   ├── charting_plotly.py # Plotly charting (fit_trendlines, etc.)
│   ├── Utilities.py      # API key management, frequency determination, resampling
│   ├── js_funcs.py       # JavaScript-based data fetching (yfinance2)
│   ├── Glassnode/        # GlassNode on-chain crypto data
│   ├── BEA_Data/         # Bureau of Economic Analysis — cached table pulls
│   ├── ABS_backend/      # Australian Bureau of Statistics via readabs (R + Python)
│   └── SystemInfo/       # API keys (JSON), screen config
├── Liquidity/
│   ├── Global_M2/         # Aggregated global M2 money supply index
│   └── NetLiquidity/      # US Net Liquidity metric (Fed balance - RRP - TGA)
├── Macro_Chartist/        # Excel-driven multi-axis charting tool (Control.xlsx)
├── PairCorrelation/       # Rolling correlation tool
├── openbb_backend/        # OpenBB platform integration
├── User_Data/
│   ├── Watchlists/        # Excel watchlist files (.xlsx + .h5s)
│   ├── Research_notebooks/ # Example Jupyter notebooks
│   ├── BEA/bea_tables/    # BEA HDF5 cache (bea_table_cache.h5s)
│   └── SavedData/         # Local saved data files
└── examples/              # Example scripts (test_bea_*.py)
```

## Data Sources

Supported via `Pull_Data.dataset().get_data()`:

| Source | API Key Required | Notes |
|--------|-----------------|-------|
| `fred` | Yes (FRED) | US macro data |
| `bea` | Yes (BEA) | US national accounts; cached in `User_Data/BEA/bea_tables/` |
| `abs_series` | No | Australian Bureau of Stats; can use local Excel files |
| `yfinance` | No | Yahoo Finance price data |
| `yfinance2` | No | Yahoo Finance via JS package |
| `tv` | No | TradingView scraping (needs exchange_code) |
| `nasdaq` | Yes (Nasdaq Data Link) | |
| `glassnode` | Yes (Glassnode subscription) | On-chain crypto |
| `coingecko` | No | Crypto prices |
| `tedata` | No | Trading Economics scraping |
| `rba_series` | No | Reserve Bank of Australia |

BEA data codes use `Dataset|TableId|SeriesCode` format (e.g. `NIPA|T10101|A191RX`). BEA pulls fetch full tables and cache them; series extraction happens from cached data.

## Key Patterns

- **Adding a new data source**: Implement in `Pull_Data.dataset.pull_data()`, add to `added_sources`
- **Adding a new chart type**: Add to `Charting.py` or `charting_plotly.py`
- **Watchlist files**: Excel `.xlsx` control files + corresponding `.h5s` HDF stores
- **API keys**: Stored in `MacroBackend/SystemInfo/API_Keys.json`, managed via `Utilities.api_keys`
- **Jupyter notebook usage**: Append parent dir to `sys.path`, then `import MacroBackend`
