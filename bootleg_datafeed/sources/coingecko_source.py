"""
CoinGecko data source for bm.

Pulls cryptocurrency price data from CoinGecko API.
No API key required.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd
import requests

from ..auxiliary import FrequencyConverter, convert_to_standard_series, calculate_metadata_stats
from ..models import SeriesMetadata, StandardSeries


BASE_URL = "https://api.coingecko.com/api/v3"


def pull_coingecko(
    coin_id: str,
    days: int = 365,
    vs_currency: str = "usd",
) -> StandardSeries:
    """Pull cryptocurrency price history from CoinGecko.

    Args:
        coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum', 'dogecoin')
        days: Number of days of history (max 365 for free tier)
        vs_currency: Quote currency (default: 'usd')

    Returns:
        StandardSeries with price data and metadata

    Raises:
        ValueError: If coin_id not found or API error
    """
    url = f"{BASE_URL}/coins/{coin_id}/market_chart"

    params = {
        "vs_currency": vs_currency,
        "days": days,
        "interval": "daily",
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise ValueError(f"CoinGecko API error: {response.status_code} - {response.text}")

    data = response.json()

    if "prices" not in data or not data["prices"]:
        raise ValueError(f"No price data returned for coin: {coin_id}")

    # Parse price data
    prices = data["prices"]
    dates = [datetime.fromtimestamp(p[0] / 1000) for p in prices]
    values = [p[1] for p in prices]

    series = pd.Series(values, index=pd.DatetimeIndex(dates), name=f"{coin_id}_price")
    series = convert_to_standard_series(series)

    # Build metadata
    metadata = SeriesMetadata(
        id=coin_id,
        title=_format_title(coin_id),
        source="coingecko",
        original_source="CoinGecko",
        start_date=series.index.min().date() if len(series) > 0 else None,
        end_date=series.index.max().date() if len(series) > 0 else None,
        frequency=FrequencyConverter.standardize("D"),
        units=vs_currency.upper(),
        units_short=vs_currency.upper(),
        **calculate_metadata_stats(series),
    )

    return StandardSeries.from_pandas(series, metadata)


def search_coins(query: str) -> pd.DataFrame:
    """Search for coins on CoinGecko.

    Args:
        query: Search query (coin name or symbol)

    Returns:
        DataFrame with matching coins
    """
    url = f"{BASE_URL}/search"
    params = {"query": query}

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise ValueError(f"CoinGecko search error: {response.status_code}")

    data = response.json()
    coins = data.get("coins", [])

    if not coins:
        return pd.DataFrame()

    df = pd.DataFrame(coins)
    # Limit columns to useful ones
    cols = [c for c in ["id", "name", "symbol", "market_cap_rank"] if c in df.columns]
    return df[cols]


def get_coin_id(identifier: str) -> str:
    """Resolve a coin name/symbol/id to a CoinGecko coin ID.

    Args:
        identifier: Coin name, symbol (e.g., 'BTC'), or coin ID

    Returns:
        CoinGecko coin ID

    Raises:
        ValueError: If coin not found
    """
    # Try direct lookup first
    url = f"{BASE_URL}/coins/list"
    response = requests.get(url)
    if response.status_code == 200:
        all_coins = pd.DataFrame(response.json())
        # Search by id, symbol, or name (case insensitive)
        mask = (
            (all_coins["id"] == identifier.lower()) |
            (all_coins["symbol"] == identifier.lower()) |
            (all_coins["name"].str.lower() == identifier.lower())
        )
        matches = all_coins[mask]
        if not matches.empty:
            return matches.iloc[0]["id"]

    # Fall back to search
    search_results = search_coins(identifier)
    if not search_results.empty:
        return search_results.iloc[0]["id"]

    raise ValueError(f"Coin not found: {identifier}")


def _format_title(coin_id: str) -> str:
    """Format a coin ID into a display title."""
    # Convert kebab-case or snake_case to Title Case
    title = coin_id.replace("-", " ").replace("_", " ").title()

    # Special cases
    special = {
        "btc": "Bitcoin",
        "eth": "Ethereum",
        "usdt": "Tether",
        "usdc": "USD Coin",
        "bnb": "Binance Coin",
        "xrp": "XRP",
        "ada": "Cardano",
        "doge": "Dogecoin",
        "sol": "Solana",
        "dot": "Polkadot",
        "matic": "Polygon",
        "ltc": "Litecoin",
        "shib": "Shiba Inu",
        "avax": "Avalanche",
        "link": "Chainlink",
    }

    return special.get(coin_id.lower(), title)
