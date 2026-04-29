"""
TradingView source for bm.

Uses local tvDatafeedz module from MacroBackend for accessing TradingView chart data.
"""

import os
import sys
from typing import Optional

import pandas as pd

# Add MacroBackend to path for tvDatafeedz
_BOOTLEG_MACRO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TVDATAFEEDZ_PATH = os.path.join(_BOOTLEG_MACRO_ROOT, 'MacroBackend')
if _TVDATAFEEDZ_PATH not in sys.path:
    sys.path.insert(0, _TVDATAFEEDZ_PATH)

from tvDatafeedz import TvDatafeed, Interval

from ..auxiliary import convert_to_standard_series, calculate_metadata_stats
from ..models import SeriesMetadata, StandardSeries


# Mapping from interval string to Interval enum
INTERVAL_MAP = {
    '1': Interval.in_1_minute,
    '3': Interval.in_3_minute,
    '5': Interval.in_5_minute,
    '15': Interval.in_15_minute,
    '30': Interval.in_30_minute,
    '45': Interval.in_45_minute,
    '1H': Interval.in_1_hour,
    '2H': Interval.in_2_hour,
    '3H': Interval.in_3_hour,
    '4H': Interval.in_4_hour,
    '1D': Interval.in_daily,
    '1W': Interval.in_weekly,
    '1M': Interval.in_monthly,
}

# Frequency mapping for standard metadata
FREQ_MAP = {
    '1': 'D',   # 1 minute -> treated as daily for storage
    '3': 'D',
    '5': 'D',
    '15': 'D',
    '30': 'D',
    '45': 'D',
    '1H': 'D',   # hourly -> daily
    '2H': 'D',
    '3H': 'D',
    '4H': 'D',
    '1D': 'D',
    '1W': 'W',
    '1M': 'M',
}


def pull_tv(
    symbol: str,
    exchange: str = "NSE",
    interval: str = "1D",
    n_bars: int = 5000,
    fut_contract: Optional[int] = None,
    extended_session: bool = False,
    data_type: str = "close",
) -> StandardSeries:
    """Pull data from TradingView.

    Args:
        symbol: Symbol name (e.g., 'RELIANCE', 'AAPL')
        exchange: Exchange name (default: 'NSE')
        interval: Chart interval (default: '1D')
        n_bars: Number of bars to download, max 5000 (default: 5000)
        fut_contract: None for cash, 1 for front contract, 2 for next contract
        extended_session: Use extended session (default: False)
        data_type: Type of data to return ('close', 'open', 'high', 'low', 'volume')

    Returns:
        StandardSeries with data and metadata
    """
    tv = TvDatafeed()
    interval_enum = INTERVAL_MAP.get(interval, Interval.in_daily)

    data = tv.get_hist(
        symbol=symbol,
        exchange=exchange,
        interval=interval_enum,
        n_bars=n_bars,
        fut_contract=fut_contract,
        extended_session=extended_session,
    )

    if data.empty:
        raise ValueError(f"No data returned from TradingView for {exchange}:{symbol}")

    # Format symbol name
    symbol_name = f"{exchange}:{symbol}" if ":" not in symbol else symbol

    if data_type in ('close', 'open', 'high', 'low', 'volume'):
        series = data[data_type]
        series.name = f"{symbol_name}_{data_type}"
    else:
        series = data['close']
        series.name = f"{symbol_name}_close"

    series = convert_to_standard_series(series)

    std_freq = FREQ_MAP.get(interval, 'D')

    metadata = SeriesMetadata(
        id=symbol_name.replace(':', '_'),
        title=f"{symbol} ({exchange})",
        source='tradingview',
        original_source=f'TradingView {exchange}',
        start_date=series.index.min().date() if len(series) > 0 else None,
        end_date=series.index.max().date() if len(series) > 0 else None,
        frequency=std_freq,
        description=f"Symbol: {symbol_name}, Interval: {interval}, Type: {data_type}",
        **calculate_metadata_stats(series),
    )

    return StandardSeries.from_pandas(series, metadata)


def search_tv(
    query: str,
    exchange: str = "",
) -> pd.DataFrame:
    """Search for symbols on TradingView.

    Args:
        query: Search query string
        exchange: Optional exchange filter

    Returns:
        DataFrame with matching symbols
    """
    tv = TvDatafeed()
    results = tv.search_symbol(query, exchange)
    if results:
        return pd.DataFrame(results)
    return pd.DataFrame()