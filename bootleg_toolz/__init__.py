"""
bootleg_toolz — Watchlist management, charting, statistics, and data utilities.

Built on top of bootleg_datafeed. Provides multi-series watchlist
management, Plotly charting, pairwise correlation / trend fitting /
distribution analysis (ported from MacroBackend), and data utilities.

Submodules:
    charting        — Plotly-based time series charting
    watchlist       — Watchlist class (multi-series management, persistence)
    stats           — Pair_stats, rolling correlation, stationarity tests
    fitting         — Distribution fitting, trend fitting, seasonal adjustment
    data_processing — STL / X-13 seasonal adjustment utilities
    utilities       — Low-level helpers (tick generation, date lookup, dialogs)
"""

from .watchlist import Watchlist
from . import charting
from . import data_processing
from . import utilities
from . import stats
from . import fitting

__version__ = "0.1.0"

__all__ = [
    "Watchlist",
    "charting",
    "data_processing",
    "utilities",
    "stats",
    "fitting",
]
