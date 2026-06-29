"""
bootleg_macro.watchlist_gui — PyQt6 desktop application for interactive watchlist building.

Depends on bootleg_macro.toolz.
"""

from bootleg_macro.watchlist_gui.gui import WatchlistBuilderWindow, launch

__version__ = "0.1.0"

__all__ = [
    "WatchlistBuilderWindow",
    "launch",
]
