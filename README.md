# Bootleg Macro

Sources for economic and financial data, as well as convenience and analysis tools such as watchlists, charting, and custom index construction. 

The repo ships **two** pip-installable packages:

| Package | pip name | What it gives you |
|---------|----------|-------------------|
| **Core** | `bootleg-datafeed` | Unified interface for pulling time series from 11+ data sources (FRED, BEA, Yahoo Finance, TradingView, CoinGecko, ABS, RBA, …). API-key management, search, metadata. |
| **Meta-package** | `bootleg-macro` | Everything else: Plotly charting, watchlist management, statistics & trend fitting, a desktop GUI (optional), plus custom indexes — Net Liquidity (NLQ) and Global M2 aggregates. |

---

## Architecture

```
bootleg-datafeed              ← core data acquisition (standalone package)
        │
        └── bootleg-macro     ← meta-package, bundles everything on top
                ├── toolz/          (analysis, charting, watchlists)
                ├── indexes/        (NLQ, Global M2)
                └── watchlist_gui/  (desktop GUI — optional [gui] extra)
```

Installing `bootleg-macro` pulls in `bootleg-datafeed` and ships `toolz` + `indexes` by default. Add `[gui]` (or `[all]`) to also get the PyQt6-based desktop watchlist builder.

---

## Installation

### Prerequisites

- Python ≥ 3.11
- [git](https://github.com/git-guides/install-git)
- Optional — some TradingView search features need Node.js and the `@mathieuc/tradingview` npm package installed globally:
  ```bash
  npm install -g @mathieuc/tradingview
  ```

### From source (development)

```bash
# Core only (if you just want data acquisition)
pip install -e ./bootleg_datafeed

# Everything — the meta-package
pip install -e ./bootleg_macro

# Or everything including the desktop GUI
pip install -e "./bootleg_macro[gui]"
pip install -e "./bootleg_macro[all]"   # same as [gui]
```

### What gets installed

| pip command | Pulls in |
|-------------|----------|
| `pip install -e ./bootleg_datafeed` | Just the core datafeed |
| `pip install -e ./bootleg_macro` | datafeed + toolz + indexes |
| `pip install -e "./bootleg_macro[gui]"` | Above + desktop GUI (PyQt6) |
| `pip install -e "./bootleg_macro[all]"` | Same as `[gui]` |

---

## Quick Start

### Pull data from any source

```python
# You can import from the meta-package …
from bootleg_macro import Dataset

# … or from the core directly — both work
from bootleg_datafeed import Dataset

ds = Dataset()

# FRED (free API key required)
df = ds.pull_fred("GDP")

# Yahoo Finance — no key needed
df = ds.pull_yfinance("SPY")

# TradingView — no key needed
df = ds.pull_tradingview("BTCUSD", exchange="INDEX")

# BEA, ABS, CoinGecko, Glassnode, and more
```

### Chart and analyse

```python
from bootleg_macro import charting

fig = charting.plot_series(ds.data["GDP"], title="US GDP")
charting.show(fig)
```

### Build watchlists with the GUI

```python
from bootleg_macro import launch
window = launch()
```

(Requires `pip install bootleg-macro[gui]` — raises a clear error otherwise.)

### Calculate Net Liquidity

```python
from bootleg_macro import NetLiquidity

nlq = NetLiquidity(start_date="2010-01-01")
results = nlq.calculate_all()
nlq.summary()
```

---

## Package READMEs

Detailed documentation lives in each sub-package's own README:

- **[bootleg-datafeed](bootleg_datafeed/README.md)** — full API reference for all 11+ data sources, `Dataset`, `WatchlistSearch`, models, API key management, and configuration.
- **[bootleg-macro.toolz](bootleg_macro/toolz/README.md)** — charting API, `Watchlist` class, `Pair_stats`, distribution/trend fitting, seasonal adjustment.
- **[bootleg-macro.watchlist_gui](bootleg_macro/watchlist_gui/README.md)** — window reference, keyboard shortcuts, search tips, architecture and data flow.
- **[bootleg-macro.indexes](bootleg_macro/indexes/README.md)** — `NetLiquidity`, `Global_M2` index classes, outlier detection, and aggregate index construction.

All of the above are also accessible through the `bootleg-macro` meta-package.

---

## API Documentation (auto-generated)

Full HTML API reference is generated from docstrings with [pdoc](https://pdoc.dev):

```bash
conda activate bm
python build_docs.py          # writes ./docs/
```

Then open `docs/index.html` in a browser, or serve locally:

```bash
python -m http.server --directory docs 8000
```

The `docs/` directory is gitignored (regenerable); `build_docs.py` is the source of truth. It documents every importable submodule of both packages — run it in the `bm` environment, which has pdoc + all optional dependencies installed.

---

## Data Sources

Available through `bootleg-datafeed`'s `Dataset`:

| Source | API Key | Notes |
|--------|---------|-------|
| FRED | Yes | US macro data |
| BEA | Yes | US national accounts (full table caching) |
| Yahoo Finance | No | Price data via `yfinance` |
| TradingView | No | Price data, 5000-bar limit |
| CoinGecko | No | Crypto prices |
| CryptoCompare | No | Crypto prices |
| Nasdaq Data Link | No | Formerly Quandl (free key) |
| Glassnode | Yes | On-chain crypto metrics |
| ABS (Australia) | No | Australian Bureau of Statistics |
| RBA (Australia) | No | Reserve Bank of Australia |
| Trading Economics | No | Selenium scraping |

---

## License

MIT
