# bm GUI Watchlist Builder — Implementation Plan (COMPLETED)

## Context

The `bm` package provides clean Python APIs for financial data acquisition from 10+ sources. The dataset, watchlist, and search modules are complete. **The GUI watchlist builder is now built and functional.**

## Status: COMPLETED 2026-05-12

### What was built

`bm/gui/` — a clean, layout-based PyQt6 GUI module that:

1. **Searches all bm sources** via `WatchlistSearch` (single source or "All Sources")
2. **Displays results** in a table view (id/title/source columns)
3. **Double-click rows** to add series to a watchlist (auto-creates if none loaded)
4. **Views/manages selected series** (remove, clear)
5. **Saves/loads** watchlists via `Watchlist.save_watchlist()` / `Watchlist.load_watchlist()`
6. **Logs all actions** to stderr with timestamps for debugging

### File Structure

```
bm/gui/
├── __init__.py           # Lazy imports to avoid circular-import warning
├── _logging.py           # Logger setup: StreamHandler, INFO level, timestamps
├── _models.py            # PandasModel, WatchlistSelectionModel, SearchWorker
├── widgets.py            # SearchBar, ResultsTable, WatchlistPanel, SourceSelector
└── watchlist_builder.py  # WatchlistBuilderWindow (main window)
```

### Bugs Fixed During Testing

- **PyQt6 `dataChanged.emit()`**: Requires `topLeft` + `bottomRight` QModelIndex args (unlike PyQt5)
- **"All Sources" routing**: SourceSelector returned `"All Sources"` but SearchWorker checked for `"all"`
- **FRED search column name**: FRED API returns `id` not `series_id`
- **Double-click not firing**: `ResultsTable._model` stayed `None` because `setModel()` wasn't tracked — override added
- **Load watchlist crash**: `update_metadata()` crashed on non-numeric series — wrapped in try/except

### Launch

```bash
conda activate bm
python -m bm.gui.watchlist_builder
```
