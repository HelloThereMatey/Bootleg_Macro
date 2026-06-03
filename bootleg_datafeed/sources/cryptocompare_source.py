"""
CryptoCompare data source for bm.

Pulls cryptocurrency price data from CryptoCompare API.
Free tier provides up to ~2001 days of daily data per call.
No API key required for basic endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
import requests

from ..auxiliary import FrequencyConverter, convert_to_standard_series, calculate_metadata_stats
from ..models import SeriesMetadata, StandardSeries


BASE_URL = "https://min-api.cryptocompare.com/data/v2"


def pull_cryptocompare(
    fsym: str,
    tsym: str = "USD",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 2000,
) -> StandardSeries:
    """Pull cryptocurrency price history from CryptoCompare.

    Args:
        fsym: From symbol (e.g., 'BTC', 'ETH')
        tsym: To symbol (default: 'USD')
        start_date: Optional start date (YYYY-MM-DD) — fetches max available if None
        end_date: Optional end date (YYYY-MM-DD) — defaults to today
        limit: Max number of daily bars per API call (default: 2000, max: 2000)

    Returns:
        StandardSeries with price data and metadata

    Raises:
        ValueError: If symbol not found or API error
    """
    url = f"{BASE_URL}/histoday"

    params = {
        "fsym": fsym.upper(),
        "tsym": tsym.upper(),
        "limit": min(limit, 2000),  # CryptoCompare max is 2000
    }

    # Optional date range
    if end_date:
        params["toTs"] = int(pd.Timestamp(end_date).timestamp())

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise ValueError(f"CryptoCompare API error: {response.status_code} - {response.text}")

    data = response.json()
    if data.get("Response") == "Error":
        raise ValueError(f"CryptoCompare error: {data.get('Message', 'Unknown error')}")

    bars = data.get("Data", {}).get("Data", [])
    if not bars:
        raise ValueError(f"No data returned for {fsym}/{tsym}")

    # Parse bars
    dates = [datetime.fromtimestamp(bar["time"]) for bar in bars]
    close = [bar["close"] for bar in bars]

    series = pd.Series(close, index=pd.DatetimeIndex(dates), name=f"{fsym}_{tsym}")
    series = convert_to_standard_series(series)

    # Filter by start_date if specified
    if start_date:
        series = series[series.index >= pd.to_datetime(start_date)]
    if end_date:
        series = series[series.index <= pd.to_datetime(end_date)]

    metadata = SeriesMetadata(
        id=f"{fsym.upper()}{tsym.upper()}",
        title=_format_title(fsym),
        source="cryptocompare",
        original_source="CryptoCompare",
        start_date=series.index.min().date() if len(series) > 0 else None,
        end_date=series.index.max().date() if len(series) > 0 else None,
        frequency=FrequencyConverter.standardize("D"),
        units=tsym.upper(),
        units_short=tsym.upper(),
        description=f"CryptoCompare {fsym}/{tsym} daily",
        **calculate_metadata_stats(series),
    )

    return StandardSeries.from_pandas(series, metadata)


def fetch_ohlcv_cryptocompare(
    fsym: str,
    tsym: str = "USD",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch OHLCV data from CryptoCompare.

    Args:
        fsym: From symbol (e.g., 'BTC', 'ETH')
        tsym: To symbol (default: 'USD')
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)

    Returns:
        DataFrame with columns: time, open, high, low, close, volumefrom, volumeto
    """
    url = f"{BASE_URL}/histoday"

    params = {
        "fsym": fsym.upper(),
        "tsym": tsym.upper(),
        "limit": 2000,
    }

    if end_date:
        params["toTs"] = int(pd.Timestamp(end_date).timestamp())

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return pd.DataFrame()

    data = response.json()
    if data.get("Response") == "Error":
        return pd.DataFrame()

    bars = data.get("Data", {}).get("Data", [])
    if not bars:
        return pd.DataFrame()

    df = pd.DataFrame(bars)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df


def search_cryptocompare(query: str) -> pd.DataFrame:
    """Search for coins/symbols on CryptoCompare.

    Uses CryptoCompare's all exchanges list to find matching symbols.

    Args:
        query: Search query (symbol or name)

    Returns:
        DataFrame with matching symbols
    """
    # CryptoCompare doesn't have a direct search endpoint for symbols,
    # so we use a common top coins list as a fallback search
    url = "https://min-api.cryptocompare.com/data/pricemultifull"
    params = {
        "fsyms": "BTC,ETH,XRP,BNB,SOL,ADA,DOGE,DOT,AVAX,LINK,MATIC,UNI,LTC,ATOM,FIL",
        "tsyms": "USD",
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return pd.DataFrame()

    data = response.json()
    raw = data.get("RAW", {})

    # Build a searchable list of top coins
    top_coins = []
    for sym, info in raw.items():
        top_coins.append({
            "symbol": sym,
            "name": _format_title(sym),
            "price": info.get("USD", {}).get("PRICE"),
        })

    df = pd.DataFrame(top_coins)
    if df.empty:
        return pd.DataFrame()

    # Filter by query (case-insensitive)
    mask = (
        df["symbol"].str.contains(query, case=False, na=False) |
        df["name"].str.contains(query, case=False, na=False)
    )
    return df[mask][["symbol", "name", "price"]]


def get_cryptocompare_pairs(fsym: str) -> pd.DataFrame:
    """Get available trading pairs for a symbol.

    Args:
        fsym: From symbol (e.g., 'BTC')

    Returns:
        DataFrame with available quote currencies
    """
    url = f"https://min-api.cryptocompare.com/data/generateAvg"
    params = {"fsym": fsym.upper(), "tsym": "USD"}
    # This doesn't return pairs, so we just return USD as default
    return pd.DataFrame([{"tsym": "USD", "price_source": "CryptoCompare"}])


def _format_title(sym: str) -> str:
    """Format a symbol into a display title."""
    special = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "XRP": "XRP",
        "BNB": "Binance Coin",
        "SOL": "Solana",
        "ADA": "Cardano",
        "DOGE": "Dogecoin",
        "DOT": "Polkadot",
        "AVAX": "Avalanche",
        "LINK": "Chainlink",
        "MATIC": "Polygon",
        "UNI": "Uniswap",
        "LTC": "Litecoin",
        "ATOM": "Cosmos",
        "FIL": "Filecoin",
        "TRX": "TRON",
        "XLM": "Stellar",
        "ALGO": "Algorand",
        "VET": "VeChain",
        "ICP": "Internet Computer",
        "NEAR": "Near Protocol",
        "FTM": "Fantom",
        "AAVE": "Aave",
        "GRT": "The Graph",
        "SAND": "The Sandbox",
        "MANA": "Decentraland",
        "AXS": "Axie Infinity",
        "THETA": "Theta",
        "EOS": "EOS",
        "XTZ": "Tezos",
    }
    return special.get(sym.upper(), sym.upper())