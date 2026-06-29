# Package Dependency Lists
========================
Generated from pyproject.toml files — 2026-06-26

Dependency structure: bootleg-datafeed → bootleg-macro (with optional [gui] extra)

---

## 1. bootleg-datafeed
**Description**: Core data acquisition — pull financial/economic time series from 11+ sources
**Requires-python**: >=3.11
**pip install**: `pip install -e ./bootleg_datafeed`

### Dependencies
- pandas>=2.0
- requests>=2.0
- pydantic>=2.0
- yfinance>=0.1
- numpy>=1.0
- readabs>=0.1
- nasdaq-data-link>=0.1
- openpyxl>=3.0

### Optional Dependencies
- `tv`: tvDatafeedz (local module, install manually)
- `chrome`: selenium
- `all`: selenium

---

## 2. bootleg-macro
**Description**: Meta-package bundling toolz, indexes, and optional GUI on top of bootleg-datafeed
**Requires-python**: >=3.11
**pip install**: `pip install -e ./bootleg_macro`

### Included Subdirectories (always installed)
- `toolz/` — Watchlist management, Plotly charting, statistics, fitting
- `indexes/` — Custom indexes (Net Liquidity, Global M2)
- `watchlist_gui/` — PyQt6 desktop GUI (code always included, requires PyQt6 to run)

### Core Dependencies
- bootleg-datafeed>=0.1

### Optional Extras
- `[gui]`: PyQt6>=6.0
- `[all]`: same as `[gui]` (may expand in future)

### Install Variations
| Command | What you get |
|---------|--------------|
| `pip install -e ./bootleg_macro` | datafeed + toolz + indexes (no GUI runtime) |
| `pip install -e "./bootleg_macro[gui]"` | Above + PyQt6 (GUI fully functional) |
| `pip install -e "./bootleg_macro[all]"` | Same as `[gui]` |

---

## Subpackage: bootleg_macro/toolz
**Location**: `bootleg_macro/toolz/`
**Description**: Watchlist management, Plotly charting, statistics, and data utilities
**Part of**: bootleg-macro (always installed)

### Dependencies (via bootleg-datafeed)
- pandas>=2.0
- plotly>=5.0
- openpyxl>=3.0
- tables>=3.0
- statsmodels>=0.14
- scipy>=1.10
- matplotlib>=3.7

---

## Subpackage: bootleg_macro/indexes
**Location**: `bootleg_macro/indexes/`
**Description**: Custom index construction from multiple series
**Part of**: bootleg-macro (always installed)

### Dependencies (via bootleg-datafeed)
- pandas>=2.0
- numpy>=1.0
- requests (for Treasury API in NLQ)

---

## Subpackage: bootleg_macro/watchlist_gui
**Location**: `bootleg_macro/watchlist_gui/`
**Description**: PyQt6 desktop application for interactive watchlist building
**Part of**: bootleg-macro (code always installed, requires PyQt6 to run)

### Runtime Dependencies
- PyQt6>=6.0 (only installed with `[gui]` or `[all]` extra)

### Internal Dependencies
- bootleg_macro.toolz (Watchlist class)
- bootleg_datafeed (Dataset, WatchlistSearch)

---

## Import Paths

### From meta-package (recommended)
```python
from bootleg_macro import Dataset, Watchlist, charting, stats, fitting
from bootleg_macro import NetLiquidity, Global_M2
from bootleg_macro import launch  # GUI (requires [gui] extra)
```

### From core directly
```python
from bootleg_datafeed import Dataset, WatchlistSearch
from bootleg_datafeed.models import SeriesMetadata, StandardSeries
```

### From subpackages (if needed)
```python
from bootleg_macro.toolz import charting, Watchlist
from bootleg_macro.indexes.nlq_clean import NetLiquidity
from bootleg_macro.watchlist_gui import WatchlistBuilderWindow
```
