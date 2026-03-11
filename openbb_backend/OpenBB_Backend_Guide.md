# Bootleg Macro — OpenBB Pro Custom Backend Guide

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  OpenBB Pro (pro.openbb.co)                         │
│  ┌───────────────────────────────────────────────┐  │
│  │ TradingView Advanced Charts                   │  │
│  │ Dashboard widgets (tables, charts, metrics)   │  │
│  │ Natural language → widget queries             │  │
│  └──────────────┬────────────────────────────────┘  │
│                 │ HTTPS to your localhost/server     │
└─────────────────┼───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│  Your Custom Backend (FastAPI)                      │
│  ┌───────────────────────────────────────────────┐  │
│  │ /widgets.json         → widget definitions    │  │
│  │ /fred_series          → FRED data             │  │
│  │ /bea_series           → BEA NIPA data         │  │
│  │ /pull_series          → any source via code    │  │
│  │ /watchlist_view       → watchlist contents     │  │
│  │ /backtest_sma         → VectorBT results      │  │
│  └───────────────────────────────────────────────┘  │
│  MacroBackend (Pull_Data, watchlist, PriceImporter) │
│  VectorBT backtesting engine                        │
│  HDF5 / xlsx cache layer                            │
└─────────────────────────────────────────────────────┘
```

Your existing `MacroBackend` package runs entirely in the FastAPI process. OpenBB Pro calls your localhost endpoints and renders the results in TradingView Advanced Charts and dashboard widgets.

## Prerequisites

- `bm` conda environment with all Bootleg_Macro dependencies
- FastAPI + uvicorn:
  ```bash
  conda activate bm
  pip install fastapi uvicorn
  ```
- (Optional) VectorBT for backtesting:
  ```bash
  pip install vectorbt
  ```
- Valid API keys in `MacroBackend/SystemInfo/API_Keys.json` (FRED, BEA, etc.)
- OpenBB Pro account at [pro.openbb.co](https://pro.openbb.co)

## Quick Start

```bash
conda activate bm
cd ~/Documents/Code/Bootleg_Macro/openbb_backend
chmod +x run.sh
./run.sh
```

This starts the backend on `http://localhost:5050` with hot-reload enabled.

## Connecting to OpenBB Pro

1. Open [pro.openbb.co](https://pro.openbb.co) and log in
2. Go to **Data Connectors** → **Add Custom Backend**
3. Enter URL: `http://localhost:5050`
4. Your widgets appear automatically in the widget picker

## Available Widgets

| Widget | Endpoint | Type | Description |
|--------|----------|------|-------------|
| **FRED Series** | `/fred_series` | chart | Any FRED series by ID (GDP, UNRATE, CPIAUCSL, etc.) |
| **BEA NIPA Series** | `/bea_series` | chart | Series from BEA NIPA tables (GDP components, price indexes) |
| **Multi-Source Series** | `/pull_series` | chart | Any source: fred, yfinance, bea, abs, glassnode, coingecko, tv, etc. |
| **Watchlist Viewer** | `/watchlist_view` | table | View contents + metadata of any saved watchlist |
| **SMA Backtest** | `/backtest_sma` | table | SMA crossover backtest via VectorBT with equity curve + stats |

## Widget Parameters

### FRED Series
- `series_id` (text): FRED series ID, e.g. `GDP`, `UNRATE`, `CPIAUCSL`, `M2SL`
- `start_date` (date): Start date for data

### BEA NIPA Series
- `table_code` (text): BEA NIPA table code, e.g. `T10101` (GDP), `T20100` (Income)
- `series_code` (text): Series code within the table, e.g. `A191RL` (Real GDP % change)
- `frequency` (text): `Q` (quarterly), `M` (monthly), or `A` (annual)

### Multi-Source Series
- `source` (text): One of: `fred`, `yfinance`, `bea`, `tv`, `coingecko`, `glassnode`, `abs_series`, `nasdaq`, etc.
- `data_code` (text): Ticker/series ID for that source
- `start_date` (date): Start date

### Watchlist Viewer
- `watchlist_name` (text): Name of a saved watchlist folder in `User_Data/Watchlists/`

### SMA Backtest
- `symbol` (text): Ticker symbol (pulled via yfinance), e.g. `SPY`, `AAPL`, `BTC-USD`
- `fast` (number): Fast SMA window (default: 10)
- `slow` (number): Slow SMA window (default: 50)
- `start_date` (date): Backtest start date

## How It Works

### OpenBB Pro Protocol

OpenBB Pro custom backends are simple:

1. **`GET /widgets.json`** — Returns a JSON array of widget definitions. Each widget specifies a `name`, `endpoint`, `type` (chart/table), and user-configurable `params`.
2. **Data endpoints** — Each widget's `endpoint` is a GET route that returns JSON records (list of dicts with `date` + value columns).

That's the entire protocol. No SDK, no auth layer (localhost only).

### Data Flow

```
User adjusts widget params in OpenBB Pro
    → OpenBB Pro calls GET /fred_series?series_id=GDP&start_date=2010-01-01
    → FastAPI handler creates Pull_Data.dataset(), calls get_data()
    → Pull_Data fetches from FRED API (or cache)
    → Handler converts pd.Series → list of {"date": "...", "GDP": ...} dicts
    → JSON response rendered as TradingView chart in OpenBB Pro
```

### Caching

- BEA tables are cached in `User_Data/BEA/bea_tables/bea_table_cache.h5s` (HDF5)
- FRED/yfinance data is fetched live per request (add your own cache layer if needed)
- Watchlists are read from `User_Data/Watchlists/{name}/{name}.xlsx`

## Adding New Widgets

To add a new widget:

1. Add a widget definition dict to the list in `get_widgets()`:
   ```python
   {
       "name": "My Widget",
       "description": "Does something cool",
       "category": "economy",
       "type": "chart",  # or "table"
       "endpoint": "my_endpoint",
       "gridData": {"w": 40, "h": 15},
       "params": [
           {"paramName": "param1", "label": "Label", "type": "text", "value": "default"},
       ],
   }
   ```

2. Add a matching endpoint:
   ```python
   @app.get("/my_endpoint")
   async def my_endpoint(param1: str = "default"):
       # Fetch data using MacroBackend
       ds = Pull_Data.dataset()
       ds.get_data(source="fred", data_code=param1, start_date="2000-01-01")
       return JSONResponse(_series_to_records(ds.data, value_col=param1))
   ```

3. Restart uvicorn (auto if `--reload` is on) and refresh OpenBB Pro.

## Adding VectorBT Strategies

The `/backtest_sma` endpoint is a minimal example. To add more strategies:

```python
@app.get("/backtest_rsi")
async def backtest_rsi(symbol: str = "SPY", rsi_window: int = 14,
                       oversold: int = 30, overbought: int = 70,
                       start_date: str = "2015-01-01"):
    import vectorbt as vbt
    ds = Pull_Data.dataset()
    ds.get_data(source="yfinance", data_code=symbol, start_date=start_date)
    close = ds.data.dropna()

    rsi = vbt.RSI.run(close, window=rsi_window)
    entries = rsi.rsi_crossed_below(oversold)
    exits = rsi.rsi_crossed_above(overbought)

    pf = vbt.Portfolio.from_signals(close, entries, exits, init_cash=10000)
    stats = {k: str(v) for k, v in pf.stats().to_dict().items()}
    eq_records = _series_to_records(pf.value(), value_col="equity")

    return JSONResponse({"stats": stats, "equity_curve": eq_records})
```

Then add a matching widget definition in `get_widgets()`.

## Remote Access (Optional)

To access from other machines on your Tailscale network:

```bash
# Listen on all interfaces
uvicorn main:app --host 0.0.0.0 --port 5050 --reload
```

Then connect OpenBB Pro to `http://<your-tailscale-ip>:5050`.

For public access, use a Cloudflare Tunnel:
```bash
cloudflared tunnel --url http://localhost:5050
```

## Troubleshooting

- **CORS errors**: The backend allows origins for `pro.openbb.co`, `excel.openbb.co`, and `localhost:1420`. Add more in the `allow_origins` list if needed.
- **API key errors**: Ensure `MacroBackend/SystemInfo/API_Keys.json` has valid keys for the sources you're using.
- **Import errors**: Make sure you're running from the `bm` conda environment with all dependencies.
- **BEA table errors**: First-time BEA pulls are slow (downloads full table). Subsequent calls use cached HDF5.

## Reference

- [OpenBB Backends for OpenBB](https://github.com/OpenBB-finance/backends-for-openbb) — Protocol specification and examples
- [OpenBB Pro](https://pro.openbb.co) — The frontend
- [FastAPI docs](https://fastapi.tiangolo.com/) — Backend framework
- [VectorBT docs](https://vectorbt.dev/) — Backtesting engine
- [TradingView Lightweight Charts](https://github.com/nicehash/tradingview-lightweight-charts) — Charting library (used internally by OpenBB Pro)
