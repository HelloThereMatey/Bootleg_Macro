"""
Custom backend for OpenBB Pro — serves data from MacroBackend.
Run:  uvicorn openbb_backend.main:app --host localhost --port 5050
Then add http://localhost:5050 as a custom backend in OpenBB Pro.
"""
import sys, os

# Ensure MacroBackend is importable
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
sys.path.insert(0, project_root)

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
from typing import Optional
from MacroBackend import Pull_Data, Utilities
from MacroBackend.BEA_Data import bea_data_mate

app = FastAPI(title="Bootleg Macro Backend for OpenBB Pro")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pro.openbb.co", "https://excel.openbb.co", "http://localhost:1420"],
    allow_methods=["*"],
    allow_headers=["*"],
)

keys = Utilities.api_keys().keys

# ──────────────────────────────────────────────
# Widget registry
# ──────────────────────────────────────────────

@app.get("/widgets.json")
async def get_widgets():
    return [
        {
            "name": "FRED Series",
            "description": "Pull any FRED series by ID",
            "category": "economy",
            "type": "chart",
            "endpoint": "fred_series",
            "gridData": {"w": 40, "h": 15},
            "params": [
                {"paramName": "series_id", "label": "FRED Series ID",
                 "type": "text", "value": "GDP", "description": "e.g. GDP, UNRATE, CPIAUCSL"},
                {"paramName": "start_date", "label": "Start Date",
                 "type": "date", "value": "2000-01-01"},
            ],
        },
        {
            "name": "BEA NIPA Series",
            "description": "Pull a series from a BEA NIPA table",
            "category": "economy",
            "type": "chart",
            "endpoint": "bea_series",
            "gridData": {"w": 40, "h": 15},
            "params": [
                {"paramName": "table_code", "label": "Table Code",
                 "type": "text", "value": "T10101"},
                {"paramName": "series_code", "label": "Series Code",
                 "type": "text", "value": "A191RL"},
                {"paramName": "frequency", "label": "Frequency",
                 "type": "text", "value": "Q"},
            ],
        },
        {
            "name": "Watchlist Viewer",
            "description": "View all series in a saved watchlist",
            "category": "portfolio",
            "type": "table",
            "endpoint": "watchlist_view",
            "gridData": {"w": 60, "h": 20},
            "params": [
                {"paramName": "watchlist_name", "label": "Watchlist Name",
                 "type": "text", "value": ""},
            ],
        },
        {
            "name": "Multi-Source Series",
            "description": "Pull data from any supported source (fred, yfinance, bea, abs, etc.)",
            "category": "economy",
            "type": "chart",
            "endpoint": "pull_series",
            "gridData": {"w": 40, "h": 15},
            "params": [
                {"paramName": "source", "label": "Source",
                 "type": "text", "value": "fred"},
                {"paramName": "data_code", "label": "Symbol / Code",
                 "type": "text", "value": "GDP"},
                {"paramName": "start_date", "label": "Start Date",
                 "type": "date", "value": "2000-01-01"},
            ],
        },
        {
            "name": "Backtest (SMA Crossover)",
            "description": "Run a simple SMA crossover backtest via VectorBT",
            "category": "portfolio",
            "type": "table",
            "endpoint": "backtest_sma",
            "gridData": {"w": 60, "h": 20},
            "params": [
                {"paramName": "symbol", "label": "Symbol",
                 "type": "text", "value": "SPY"},
                {"paramName": "fast", "label": "Fast SMA",
                 "type": "number", "value": "10"},
                {"paramName": "slow", "label": "Slow SMA",
                 "type": "number", "value": "50"},
                {"paramName": "start_date", "label": "Start Date",
                 "type": "date", "value": "2015-01-01"},
            ],
        },
    ]

# ──────────────────────────────────────────────
# Data endpoints
# ──────────────────────────────────────────────

def _series_to_records(series: pd.Series, value_col: str = "value") -> list[dict]:
    """Convert a pandas Series with datetime index to OpenBB-compatible records."""
    df = series.dropna().reset_index()
    df.columns = ["date", value_col]
    df["date"] = df["date"].astype(str)
    return df.to_dict(orient="records")


@app.get("/fred_series")
async def fred_series(series_id: str = "GDP", start_date: str = "2000-01-01"):
    ds = Pull_Data.dataset()
    ds.get_data(source="fred", data_code=series_id, start_date=start_date)
    return JSONResponse(_series_to_records(ds.data, value_col=series_id))


@app.get("/bea_series")
async def bea_series(table_code: str = "T10101", series_code: str = "A191RL",
                     frequency: str = "Q"):
    data_code = f"NIPA|{table_code}|{series_code}"
    ds = Pull_Data.dataset()
    ds.get_data(source="bea", data_code=data_code, start_date="1900-01-01", data_freq=frequency)
    return JSONResponse(_series_to_records(ds.data, value_col=series_code))


@app.get("/pull_series")
async def pull_series(source: str = "fred", data_code: str = "GDP",
                      start_date: str = "2000-01-01"):
    ds = Pull_Data.dataset()
    ds.get_data(source=source, data_code=data_code, start_date=start_date)
    return JSONResponse(_series_to_records(ds.data, value_col=data_code))


@app.get("/watchlist_view")
async def watchlist_view(watchlist_name: str = ""):
    from MacroBackend.watchlist import Watchlist
    wl = Watchlist(watchlist_name=watchlist_name)
    wl_dir = os.path.join(project_root, "User_Data", "Watchlists")
    wl_xlsx = os.path.join(wl_dir, watchlist_name, watchlist_name + ".xlsx")

    if not os.path.exists(wl_xlsx):
        return JSONResponse({"error": f"Watchlist '{watchlist_name}' not found at {wl_xlsx}"}, status_code=404)

    wl.load_watchlist(filepath=wl_xlsx)
    watchlist_df = wl["watchlist"]
    meta_df = wl["metadata"]

    rows = []
    for idx, row in watchlist_df.iterrows():
        entry = {"id": str(row.get("id", idx)), "source": str(row.get("source", ""))}
        if str(idx) in meta_df.columns:
            col = meta_df[str(idx)]
            entry["title"] = str(col.get("title", ""))
            entry["frequency"] = str(col.get("frequency", ""))
            entry["units"] = str(col.get("units", ""))
            entry["start_date"] = str(col.get("start_date", ""))
            entry["end_date"] = str(col.get("end_date", ""))
        rows.append(entry)

    return JSONResponse(rows)


@app.get("/backtest_sma")
async def backtest_sma(symbol: str = "SPY", fast: int = 10, slow: int = 50,
                       start_date: str = "2015-01-01"):
    try:
        import vectorbt as vbt
    except ImportError:
        return JSONResponse({"error": "vectorbt not installed. Run: pip install vectorbt"}, status_code=500)

    # Pull price data via yfinance through Pull_Data
    ds = Pull_Data.dataset()
    ds.get_data(source="yfinance", data_code=symbol, start_date=start_date)
    close = ds.data.dropna()
    if close.empty:
        return JSONResponse({"error": f"No price data returned for {symbol}"}, status_code=404)

    fast_ma = vbt.MA.run(close, window=fast)
    slow_ma = vbt.MA.run(close, window=slow)
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)

    pf = vbt.Portfolio.from_signals(close, entries, exits, init_cash=10000)
    stats = pf.stats().to_dict()
    # Serialize stats (some values are Timestamp/Timedelta)
    clean_stats = {k: str(v) for k, v in stats.items()}

    # Equity curve
    equity = pf.value()
    eq_records = _series_to_records(equity, value_col="equity")

    return JSONResponse({"stats": clean_stats, "equity_curve": eq_records})
