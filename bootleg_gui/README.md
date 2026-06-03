# bootleg-gui

PyQt6 desktop GUI for interactive watchlist building. Provides a visual interface for searching data sources and constructing watchlists.

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

## Usage

### Launch the GUI

```python
from bootleg_gui import launch

# Start the application (blocking, opens window)
window = launch()
```

### From the command line

```python
python -c "from bootleg_gui import launch; launch()"
```

### Using the window programmatically

```python
from bootleg_gui import WatchlistBuilderWindow
from bootleg_toolz import Watchlist

# Create and configure before showing
window = WatchlistBuilderWindow(watchlists_path="/path/to/watchlists")

# Load an existing watchlist
window.load_watchlist("/path/to/watchlist.xlsx")

# Set a watchlist directly
wl = Watchlist(name="my_list")
# ... populate wl ...
window.set_watchlist(wl)

# Get the current watchlist
current = window.get_watchlist()

window.show()
```

## Features

### Search
- Type a query and select a data source from the dropdown
- Search runs in a background thread — UI stays responsive
- Results appear in a sortable table

### Watchlist building
- Double-click a search result to add it to your watchlist
- Select rows and use Remove to delete them
- Clear removes all selections

### File operations
- **Save** — persists your watchlist to `.xlsx` (with `.h5s` HDF5 sidecar) or `.csv`
- **Open** — loads an existing watchlist from `.xlsx` or `.csv`
- **New** — starts a fresh watchlist
- Keyboard shortcuts: `Ctrl+N`, `Ctrl+O`, `Ctrl+S`

### Data sources queried
FRED, Yahoo Finance, BEA, TradingView, CoinGecko, CryptoCompare, Nasdaq Data Link, Glassnode, ABS, RBA, Trading Economics

## License

MIT
