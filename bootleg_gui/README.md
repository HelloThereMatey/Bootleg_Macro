# bootleg-gui

PyQt6 desktop GUI for interactive watchlist building. Provides a visual interface for searching data sources and constructing watchlists.

Built on top of `bootleg-toolz` (which depends on `bootleg-datafeed`).

## Installation

```bash
pip install bootleg-gui
```

Or install from source in editable mode:

```bash
cd bootleg_gui
pip install -e .
```

### Dependencies

- `bootleg-toolz >= 0.1`
- `PyQt6 >= 6.0`

---

## Quick start

### Launch the GUI

```python
from bootleg_gui import launch

# Start the application (blocking, opens window)
window = launch()
```

### From the command line

```bash
python -c "from bootleg_gui import launch; launch()"
```

Or run the window module directly:

```bash
python -m bootleg_gui.gui.watchlist_builder
```

---

## Workflow

1. **Select a source** from the dropdown (or "All Sources" to search everything)
2. **Type a search query** — comma-separated terms use AND logic, `*` for wildcard
3. **Press Enter** or click **Search** — runs in a background thread, UI stays responsive
4. **Double-click** a search result to add it to the watchlist
5. **Save** your watchlist as `.xlsx` (with `.h5s` HDF5 sidecar) or `.csv`

### Search tips

- `CPI, monthly` — both terms must match (AND logic)
- `GD*` — wildcard matches "GDP", "GNP", etc.
- `unemployment, sa` — seasonally adjusted series

### Sources queried

FRED, Yahoo Finance, BEA, TradingView, CoinGecko, CryptoCompare, Nasdaq Data Link, Glassnode, ABS (Australia), RBA (Australia), Trading Economics.

---

## API

### Window instance

```python
from bootleg_gui import WatchlistBuilderWindow

# Create and configure before showing
window = WatchlistBuilderWindow(watchlists_path="/path/to/watchlists")

# Load an existing watchlist
window.load_watchlist("/path/to/watchlist.xlsx")

# Set a watchlist directly
from bootleg_toolz import Watchlist
wl = Watchlist(name="my_list")
# ... populate wl ...
window.set_watchlist(wl)

# Get the current watchlist
current = window.get_watchlist()

window.show()
```

### Alternative launchers

```python
# From gui submodule
from bootleg_gui.gui import launch

window = launch()

# Or as a classmethod — returns window after exec finishes
window = WatchlistBuilderWindow.run()
```

### Default watchlists path

Watchlists default to `{user_path}/Watchlists/` (where `user_path` is configured via `bootleg_datafeed._user_path`, defaulting to `~/Documents/Bootleg_Macro`). Override by passing `watchlists_path` to the constructor.

---

## Features

### Search
- Type a query and select a data source from the dropdown
- Search runs in a background thread (`QThreadPool` + `QRunnable`) — UI stays responsive
- Results appear in a sortable table with source-specific metadata
- Results auto-filter through the `WatchlistSearch` module (`_multi_term_filter`)

### Watchlist building
- Double-click a search result to add it to your watchlist
- Select rows and use "Remove Selected" to delete them
- "Clear All" removes all selections
- Deduplication built in — same id+source can't be added twice

### File operations
- **Save** — persists your watchlist to `.xlsx` (3 sheets: watchlist, all_metadata, full_metadata) with `.h5s` HDF5 sidecar for series data
- **Open** — loads an existing watchlist from `.xlsx` or `.csv`
- **New** — starts a fresh watchlist

### Keyboard shortcuts
| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New watchlist |
| `Ctrl+O` | Open watchlist |
| `Ctrl+S` | Save watchlist |
| `Ctrl+Q` | Quit |

---

## Architecture

### Package structure

```
bootleg_gui/
├── __init__.py           # Exports WatchlistBuilderWindow, version
└── gui/
    ├── __init__.py       # Exports WatchlistBuilderWindow, launch()
    ├── watchlist_builder.py  # Main window (WatchlistBuilderWindow)
    ├── widgets.py            # Reusable Qt widgets
    ├── _models.py            # Qt model classes + background worker
    └── _logging.py           # Logger setup
```

### Internal modules

| Module | Contents |
|--------|----------|
| `gui.watchlist_builder` | `WatchlistBuilderWindow` — main QMainWindow with menu bar, search bar, results table, watchlist panel, status bar. Handles all signal wiring and file dialogs. |
| `gui.widgets` | `SearchBar` (query input + source selector + button), `ResultsTable` (QTableView with double-click emit), `WatchlistPanel` (selected series table + action buttons), `SourceSelector` (QComboBox with "All Sources" default). |
| `gui._models` | `PandasModel` (QAbstractTableModel wrapping any DataFrame), `WatchlistSelectionModel` (QAbstractTableModel for selected series with add/remove/clear/update), `SearchWorker` (QRunnable running WatchlistSearch in a background thread). |
| `gui._logging` | Pre-configured logger (`log`) at INFO level, writing to stderr with timestamps. Import via `from bootleg_gui.gui._logging import log`. |

### Data flow

```
User types query → SearchBar emits search_triggered(source, query)
    → WatchlistBuilderWindow creates SearchWorker
        → Worker calls WatchlistSearch.search() in background thread
            → emits finished(DataFrame) or error(str)
                → PandasModel updated → ResultsTable refreshed

User double-clicks row → ResultsTable emits series_double_clicked(dict)
    → Window builds StandardSeries with metadata
        → Watchlist.append_series() + WatchlistSelectionModel.add_series()

User saves → Window builds new Watchlist from selection model
    → Watchlist.save_watchlist() → .xlsx + .h5s
```

## License

MIT
