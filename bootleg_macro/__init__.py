"""
bootleg_macro — Financial & economic data analysis toolkit.

Meta-package that bundles bootleg-toolz (analysis, charting, watchlists),
bootleg-gui (desktop GUI — optional), and bootleg-indexes (custom liquidity
and Global M2 indexes) on top of the core bootleg-datafeed module.

Usage:
    pip install bootleg-macro        # default: datafeed + toolz + indexes
    pip install bootleg-macro[gui]   # + desktop GUI (PyQt6)
    pip install bootleg-macro[all]   # same as [gui]
"""

# ---------------------------------------------------------------------------
# bootleg_datafeed — core (always installed)
# ---------------------------------------------------------------------------
from bootleg_datafeed import (
    Dataset,
    WatchlistSearch,
    set_user_path,
    get_user_path,
    SOURCES,
    KEY_SOURCES,
)
from bootleg_datafeed.models import SeriesMetadata, StandardSeries

# ---------------------------------------------------------------------------
# bootleg_macro.toolz — analysis & charting (always installed)
# ---------------------------------------------------------------------------
from bootleg_macro.toolz import Watchlist, charting, stats, fitting, utilities, data_processing

# ---------------------------------------------------------------------------
# bootleg_macro.indexes — custom indexes (always installed)
# ---------------------------------------------------------------------------
from bootleg_macro.indexes.nlq_clean import NetLiquidity
from bootleg_macro.indexes.gm2_data_handler import Global_M2

# ---------------------------------------------------------------------------
# bootleg_macro.watchlist_gui — desktop GUI (optional, requires [gui] extra)
# ---------------------------------------------------------------------------
try:
    from bootleg_macro.watchlist_gui import WatchlistBuilderWindow, launch

    _gui_available = True
except ImportError:
    WatchlistBuilderWindow = None  # type: ignore[assignment]

    def launch() -> None:  # type: ignore[misc]
        raise ImportError(
            "GUI is not installed. "
            "Install it with: pip install bootleg-macro[gui]"
        )

    _gui_available = False

__version__ = "0.1.0"

__all__ = [
    # datafeed
    "Dataset",
    "WatchlistSearch",
    "set_user_path",
    "get_user_path",
    "SOURCES",
    "KEY_SOURCES",
    "SeriesMetadata",
    "StandardSeries",
    # toolz
    "Watchlist",
    "charting",
    "stats",
    "fitting",
    "utilities",
    "data_processing",
    # indexes
    "NetLiquidity",
    "Global_M2",
    # gui
    "WatchlistBuilderWindow",
    "launch",
    "_gui_available",
]
