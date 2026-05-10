# bm GUI Watchlist Builder — Implementation Plan

## Context

The `bm` package (under active development in `/home/totabilcat/Documents/Code/Bootleg_Macro/bm/`) provides clean Python APIs for financial data acquisition from 10+ sources. The dataset, watchlist, and search modules are complete. The next step is a **PyQt6 GUI** for interactive watchlist creation — search data series across sources, add them to a watchlist, and save as Excel or CSV.

## Goal

Build `bm/gui/` — a clean, layout-based PyQt6 GUI module that:
1. Searches all bm sources via `WatchlistSearch`
2. Displays results in a table view
3. Double-click rows to add series to a watchlist
4. Views/manages selected series
5. Saves/loads watchlists via `Watchlist.save_watchlist()` / `Watchlist.load_watchlist()`

## File Structure

```
bm/gui/
├── __init__.py           # Exports: WatchlistBuilderWindow, PandasModel
├── _models.py            # PandasModel, WatchlistSelectionModel, SearchWorker
├── widgets.py            # SearchBar, ResultsTable, WatchlistPanel, SourceSelector
├── watchlist_builder.py  # WatchlistBuilderWindow (main window)
└── qt_utils.py           # Layout helpers (optional)
```

## Core Classes

### `bm/gui/_models.py`

**`PandasModel`** — Qt table model wrapping a DataFrame (same pattern as reference GUI):
```python
class PandasModel(QtCore.QAbstractTableModel):
    def update_data(self, new_data: pd.DataFrame) -> None: ...
    def get_row(self, row_idx: int) -> dict: ...
    def get_dataframe(self) -> pd.DataFrame: ...
```

**`WatchlistSelectionModel`** — manages the user's selected series list:
```python
class WatchlistSelectionModel(QtCore.QAbstractTableModel):
    def add_series(self, series_row: dict) -> None: ...  # dict: id, source, title
    def remove_rows(self, row_indices: list[int]) -> None: ...
    def clear(self) -> None: ...
    def to_watchlist(self) -> Watchlist: ...
```

**`SearchWorker`** — `QRunnable` that runs search in a background thread, emits `finished(pd.DataFrame)` or `error(str)` signals.

### `bm/gui/widgets.py`

**`SearchBar`** — query input + source selector + search button:
```python
search_triggered = QtCore.pyqtSignal(str, str)  # (query, source_or_"all")
def set_searching(self, is_searching: bool) -> None: ...
```

**`ResultsTable`** — table view for search results:
```python
series_double_clicked = QtCore.pyqtSignal(dict)  # row dict with id/title/source
def set_results(self, df: pd.DataFrame) -> None: ...
```

**`WatchlistPanel`** — selected series table + action buttons:
```python
def get_selection_model(self) -> WatchlistSelectionModel: ...
def set_watchlist(self, watchlist: Watchlist) -> None: ...
```

**`SourceSelector`** — `QComboBox` dropdown with "All Sources" + all bm sources.

### `bm/gui/watchlist_builder.py`

**`WatchlistBuilderWindow`** — main window assembling all widgets:
```python
def __init__(
    self,
    watchlist: Optional[Watchlist] = None,
    watchlists_path: Optional[str] = None,
    parent: Optional[QtWidgets.QWidget] = None,
) -> None: ...

def load_watchlist(self, filepath: str) -> None: ...
def get_watchlist(self) -> Watchlist: ...
def set_watchlist(self, watchlist: Watchlist) -> None: ...
```

## UI Layout (no absolute positioning)

```
┌─────────────────────────────────────────────────────────┐
│  MenuBar: File | Help                                   │
├─────────────────────────────────────────────────────────┤
│  SearchBar: [query QLineEdit] [SourceSelector] [Search]│
├─────────────────────────────────────────────────────────┤
│  ResultsTable (QTableView, stretch=True)               │
├─────────────────────────────────────────────────────────┤
│  WatchlistPanel:                                       │
│  ┌──────────────────────────────┬────────────┐        │
│  │ WatchlistSelectionTable       │ Remove btn │        │
│  │ (id, source, title)           │ Clear btn  │        │
│  ├───────────────────────────────┴────────────┤        │
│  │ [Load Watchlist] [Save Watchlist]          │        │
│  └────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

## Key Design Decisions

1. **Thread-based async search**: `SearchWorker` (`QRunnable`) runs `WatchlistSearch.search()` in background, emits `finished`/`error` signals. Qt auto-queues to main thread.
2. **Multi-param ID handling (TradingView)**: Row dict from `series_double_clicked` contains `exchange` field. `WatchlistSelectionModel.add_series()` reconstructs comma-formatted ID (`"AAPL, NASDAQ"`) for TV.
3. **Watchlist integration**: Uses existing `Watchlist.append_series()`, `save_watchlist()`, `load_watchlist()` — no new persistence code needed.
4. **Default watchlists path**: `Path.home() / "Documents" / "Bootleg_Macro" / "Watchlists"` (created automatically).
5. **Double-click row capture**: `ResultsTable.mouseDoubleClickEvent` override emits full row dict, not just index.

## Implementation Sequence

1. `bm/gui/__init__.py` — empty init
2. `bm/gui/_models.py` — `PandasModel`, `WatchlistSelectionModel`, `SearchWorker`
3. `bm/gui/widgets.py` — `SearchBar`, `ResultsTable`, `WatchlistPanel`, `SourceSelector`
4. `bm/gui/watchlist_builder.py` — `WatchlistBuilderWindow`
5. Update `bm/gui/__init__.py` exports
6. Update `bm/__init__.py` to re-export from `bm.gui`

## Reuse Reference

| Pattern | Location |
|---------|----------|
| `PandasModel` pattern | `MacroBackend/search_symbol_gui.py:122-155` |
| `Watchlist` persistence | `bm/watchlist.py` — `save_watchlist()`, `load_watchlist()`, `append_series()` |
| `WatchlistSearch` interface | `bm/search.py` — `search()`, `search_all()` |
| `SOURCES` list | `bm/dataset.py` — `SOURCES = ['fred', 'yfinance', ...]` |
| Helper functions | `bm/auxiliary.py` — `drop_duplicate_columns`, `close_open_stores`, `strip_timezone_from_df` |

## Verification

```bash
conda activate bm
cd /home/totabilcat/Documents/Code/Bootleg_Macro

# Run existing tests
python -m pytest bm/tests/test_watchlist.py bm/tests/test_search.py -v

# Launch the GUI (after implementation)
python -c "from bm.gui import WatchlistBuilderWindow; from PyQt6.QtWidgets import QApplication; import sys; app=QApplication(sys.argv); w=WatchlistBuilderWindow(); w.show(); sys.exec()"
```
