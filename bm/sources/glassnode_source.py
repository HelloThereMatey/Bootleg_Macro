"""
Glassnode source for bm.

On-chain crypto data from Glassnode API.
Uses direct HTTP requests (no extra package needed).
"""

import json
from typing import Optional

import pandas as pd
import requests

from ..auxiliary import FrequencyConverter, convert_to_standard_series, calculate_metadata_stats
from ..models import SeriesMetadata, StandardSeries

GLASSNODE_BASE_URL = "https://api.glassnode.com/v1/metrics"
GLASSNODE_METADATA_URL = "https://api.glassnode.com/v1/metadata/metrics"


def _map_interval_to_frequency(interval: str) -> str:
    """Map Glassnode interval to standard frequency code."""
    mapping = {
        '10m': 'D',   # 10 minutes -> treated as daily (intraday)
        '1h': 'D',
        '24h': 'D',
        '1w': 'W',
        '1month': 'M',
    }
    return mapping.get(interval, 'D')


def pull_glassnode(
    metric: str,
    asset: str = "BTC",
    interval: str = "24h",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None,
) -> StandardSeries:
    """Pull on-chain data from Glassnode.

    Args:
        metric: Glassnode metric path (e.g., '/market/price_usd_close')
        asset: Crypto asset ticker (default: 'BTC')
        interval: Time resolution (default: '24h')
        start_date: Start date (YYYY-MM-DD) - filters after fetch
        end_date: End date (YYYY-MM-DD) - filters after fetch
        api_key: Glassnode API key

    Returns:
        StandardSeries with data and metadata
    """
    if not api_key:
        raise ValueError("Glassnode API key required")

    url = f"{GLASSNODE_BASE_URL}{metric}"

    params = {
        'a': asset,
        'i': interval,
        'f': 'json',
        'api_key': api_key,
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise ValueError(f"Glassnode API error: {response.status_code} - {response.text}")

    data = json.loads(response.text)
    df = pd.DataFrame(data)

    # Parse timestamp
    df['timestamp'] = pd.to_datetime(df['t'], unit='s')
    df = df.set_index('timestamp').drop('t', axis=1)

    # Handle 'v' column (single value) or unpack dict values
    if 'v' in df.columns and isinstance(df['v'].iloc[0], dict):
        # Unpack nested dict values
        df = pd.json_normalize(df['v'])
        df.index = df.index  # Preserve timestamp index
    else:
        df = df['v']

    # Handle Series vs DataFrame
    if isinstance(df, pd.DataFrame):
        if len(df.columns) == 1:
            series = df.iloc[:, 0]
        else:
            series = df.iloc[:, 0]  # Use first column
    else:
        series = df

    series = convert_to_standard_series(series)

    # Extract metric name from path
    metric_name = metric.split('/')[-1] if metric else 'unknown'

    metadata = SeriesMetadata(
        id=f"{asset}_{metric_name}",
        title=f"{asset} {metric_name}",
        source='glassnode',
        original_source='Glassnode',
        start_date=series.index.min().date() if len(series) > 0 else None,
        end_date=series.index.max().date() if len(series) > 0 else None,
        frequency=_map_interval_to_frequency(interval),
        description=f"Asset: {asset}, Interval: {interval}, Metric: {metric}",
        **calculate_metadata_stats(series),
    )

    return StandardSeries.from_pandas(series, metadata)


def list_glassnode_metrics(api_key: str) -> pd.DataFrame:
    """List all available Glassnode metrics.

    Args:
        api_key: Glassnode API key

    Returns:
        DataFrame with available metrics and paths
    """
    response = requests.get(
        GLASSNODE_METADATA_URL,
        params={'a': 'BTC', 'api_key': api_key}
    )
    if response.status_code != 200:
        return pd.DataFrame()

    return pd.DataFrame(json.loads(response.text))


def search_glassnode_metrics(query: str, api_key: str) -> pd.DataFrame:
    """Search Glassnode metrics by keyword in path.

    Args:
        query: Search query string
        api_key: Glassnode API key

    Returns:
        DataFrame with matching metrics
    """
    all_metrics = list_glassnode_metrics(api_key)
    if all_metrics.empty:
        return all_metrics

    mask = all_metrics['path'].str.contains(query, case=False)
    return all_metrics[mask]
