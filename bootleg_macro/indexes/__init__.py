"""
bootleg_indexes — Custom index construction from multiple series.

Build aggregated indexes (liquidity indexes, Global M2, etc.)
from bootleg_datafeed time series.

Modules:
    nlq_clean         — Net Liquidity (NLQ) from FRED + Treasury API data
                        (bootleg_datafeed.Dataset)
    gm2_data_handler  — Global M2 index from TradingView country data
                        (bootleg_datafeed.Dataset)
"""

__version__ = "0.1.0"
