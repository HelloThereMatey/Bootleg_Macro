"""
Yahoo Finance data source for bm.

Uses the yfinance package to pull price/volume data for equities, indices, crypto, etc.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Union

import pandas as pd
import yfinance as yf

from ..auxiliary import FrequencyConverter, convert_to_standard_series, calculate_metadata_stats
from ..models import SeriesMetadata, StandardSeries


def pull_yfinance(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = "1d",
    adjust_prices: bool = True,
) -> StandardSeries:
    """Pull time series data from Yahoo Finance.

    Args:
        ticker: Ticker symbol (e.g., 'AAPL', '^GSPC', 'BTC-USD')
        start_date: Start date as string (YYYY-MM-DD), default 5 years ago
        end_date: End date as string (YYYY-MM-DD), default today
        interval: Data interval ('1d', '1wk', '1mo', '1h', '5m', etc.)
        adjust_prices: Whether to adjust for splits/dividends

    Returns:
        StandardSeries with data and metadata

    Raises:
        ValueError: If no data returned for ticker
    """
    # Set defaults
    if end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
    if start_date is None:
        # Default to 5 years ago
        start = pd.Timestamp.today() - pd.DateOffset(years=5)
        start_date = start.strftime('%Y-%m-%d')

    # Create ticker object
    ticker_obj = yf.Ticker(ticker)

    # Fetch data
    if interval == "1d":
        # yfinance is faster for daily data
        data = ticker_obj.history(
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=False,  # Keep close unadjusted
        )
    else:
        data = ticker_obj.history(
            start=start_date,
            end=end_date,
            interval=interval,
        )

    if data.empty:
        raise ValueError(f"No data returned for ticker: {ticker}")

    # Convert DataFrame to Series (use Close price by default)
    if 'Close' in data.columns:
        series = data['Close']
        if 'Volume' in data.columns:
            series.name = f"{ticker}_close"
        else:
            series.name = ticker
    else:
        series = data.iloc[:, 0]
        series.name = ticker

    # Ensure proper formatting
    series = convert_to_standard_series(series)

    # Build metadata from yfinance info
    info = _fetch_ticker_info(ticker_obj)

    metadata = SeriesMetadata(
        id=ticker,
        title=info.get('longName') or info.get('shortName') or ticker,
        source='yfinance',
        original_source='Yahoo Finance',
        start_date=series.index.min().date() if len(series) > 0 else None,
        end_date=series.index.max().date() if len(series) > 0 else None,
        frequency=FrequencyConverter.standardize(interval),
        units=info.get('currency', 'USD'),
        units_short=info.get('currency', 'USD'),
        description=info.get('longBusinessSummary') or info.get('description'),
        **calculate_metadata_stats(series),
    )

    return StandardSeries.from_pandas(series, metadata)


def fetch_ohlcv(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = "1d",
) -> dict[str, pd.Series]:
    """Fetch OHLCV (Open, High, Low, Close, Volume) data.

    Args:
        ticker: Ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval

    Returns:
        Dictionary mapping column name to Series
    """
    if end_date is None:
        end_date = datetime.today().strftime('%Y-%m-%d')
    if start_date is None:
        start = pd.Timestamp.today() - pd.DateOffset(years=5)
        start_date = start.strftime('%Y-%m-%d')

    ticker_obj = yf.Ticker(ticker)
    data = ticker_obj.history(
        start=start_date,
        end=end_date,
        interval=interval,
    )

    if data.empty:
        raise ValueError(f"No data returned for ticker: {ticker}")

    result = {}
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in data.columns:
            result[col.lower()] = convert_to_standard_series(data[col], name=f"{ticker}_{col.lower()}")

    return result


def search_tickers(query: str, limit: int = 10) -> pd.DataFrame:
    """Search for ticker symbols.

    Args:
        query: Search query
        limit: Maximum results

    Returns:
        DataFrame with matching tickers
    """
    ticker = yf.Ticker(query)
    if hasattr(ticker, 'info') and ticker.info:
        return pd.DataFrame([ticker.info])
    return pd.DataFrame()


def _fetch_ticker_info(ticker_obj) -> dict:
    """Safely fetch ticker info, handling rate limits."""
    try:
        return ticker_obj.info or {}
    except Exception:
        return {}
