"""
bm GUI module — watchlist builder widget.

Use `from bm.gui import launch` or `from bm.gui import WatchlistBuilderWindow`.
"""

from bm.gui._models import PandasModel, WatchlistSelectionModel, SearchWorker
from bm.gui.widgets import SearchBar, ResultsTable, WatchlistPanel, SourceSelector


def __getattr__(name):
    """Lazy-import WatchlistBuilderWindow/launch to avoid
    circular-import warning when running as __main__."""
    if name in ("WatchlistBuilderWindow", "launch"):
        from bm.gui.watchlist_builder import WatchlistBuilderWindow, launch
        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "PandasModel",
    "WatchlistSelectionModel",
    "SearchWorker",
    "SearchBar",
    "ResultsTable",
    "WatchlistPanel",
    "SourceSelector",
    "WatchlistBuilderWindow",
    "launch",
]
