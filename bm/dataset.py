"""
Main dataset class for bm.

Orchestrates data pulling from all supported sources and returns
standardized time series with metadata.
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Optional, Union

import pandas as pd

from .models import SeriesMetadata, StandardSeries
from .auxiliary import parse_date


# Supported sources
SOURCES = [
    'yfinance',
    'fred',
    'bea',
    'coingecko',
    'nasdaq',
    'glassnode',
    'abs',
    'rba',
    'tradingview',
    'tedata',
]

# Sources requiring API keys
KEY_SOURCES = ['fred', 'bea', 'nasdaq', 'glassnode']


class Dataset:
    """Main dataset class for pulling and managing time series data."""

    def __init__(
        self,
        api_keys_path: Optional[str] = None,
    ):
        """Initialize Dataset.

        Args:
            api_keys_path: Path to directory containing API_Keys.json.
                          Defaults to looking in bm/SystemInfo/
        """
        self._api_keys: dict[str, str] = {}
        self._api_keys_path = api_keys_path or self._default_keys_path()
        self.last_result: Optional[StandardSeries] = None
        self._load_api_keys()

    def _default_keys_path(self) -> str:
        """Get default path for API keys."""
        # Look for API_Keys.json in bm/SystemInfo/ or parent/SystemInfo/
        bm_dir = os.path.dirname(__file__)
        candidates = [
            os.path.join(bm_dir, 'SystemInfo'),
            os.path.join(os.path.dirname(bm_dir), 'SystemInfo'),
        ]
        for path in candidates:
            if os.path.isdir(path):
                return path
        return candidates[0]

    def _load_api_keys(self) -> None:
        """Load API keys from JSON file."""
        import json

        key_file = os.path.join(self._api_keys_path, 'API_Keys.json')
        if os.path.isfile(key_file):
            try:
                with open(key_file, 'r') as f:
                    self._api_keys = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load API keys: {e}")

    def get_api_key(self, source: str) -> Optional[str]:
        """Get API key for a source.

        Args:
            source: Source name

        Returns:
            API key string or None
        """
        return self._api_keys.get(source)

    # -------------------------------------------------------------------------
    # yfinance source
    # -------------------------------------------------------------------------

    def pull_yfinance(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d",
    ) -> StandardSeries:
        """Pull data from Yahoo Finance.

        Args:
            ticker: Ticker symbol (e.g., 'AAPL', '^GSPC', 'BTC-USD')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval ('1d', '1wk', '1mo', etc.)

        Returns:
            StandardSeries with data and metadata
        """
        from .sources.yfinance_source import pull_yfinance as _pull_yfinance

        result = _pull_yfinance(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )
        self.last_result = result
        return result

    # -------------------------------------------------------------------------
    # FRED source
    # -------------------------------------------------------------------------

    def pull_fred(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> StandardSeries:
        """Pull data from FRED (Federal Reserve Economic Data).

        Args:
            series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'FEDFUNDS')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            StandardSeries with data and metadata

        Raises:
            ValueError: If API key is missing or series not found
        """
        api_key = self.get_api_key('fred')
        if not api_key:
            raise ValueError(
                "FRED API key required. "
                "Add 'fred' key to your API_Keys.json or pass api_key directly."
            )

        from .sources.fred_source import pull_fred as _pull_fred

        result = _pull_fred(
            series_id=series_id,
            api_key=api_key,
            start_date=start_date,
            end_date=end_date,
        )
        self.last_result = result
        return result

    # -------------------------------------------------------------------------
    # BEA source (placeholder)
    # -------------------------------------------------------------------------

    def pull_bea(
        self,
        dataset: str,
        table_code: str,
        series_code: Optional[str] = None,
        frequency: str = "Q",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> StandardSeries:
        """Pull data from Bureau of Economic Analysis.

        Args:
            dataset: BEA dataset name (e.g., 'NIPA', 'NIUnderlyingDetail', 'FixedAssets')
            table_code: Table code (e.g., 'T10101' for GDP)
            series_code: Series code within table
            frequency: Data frequency ('A', 'Q', 'M')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            StandardSeries with data and metadata
        """
        api_key = self.get_api_key('bea')
        if not api_key:
            raise ValueError(
                "BEA API key required. "
                "Add 'bea' key to your API_Keys.json or pass api_key directly."
            )

        from .sources.bea_source import pull_bea as _pull_bea

        result = _pull_bea(
            dataset=dataset,
            table_code=table_code,
            series_code=series_code,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            api_key=api_key,
        )
        self.last_result = result
        return result

    # -------------------------------------------------------------------------
    # Coingecko source
    # -------------------------------------------------------------------------

    def pull_coingecko(
        self,
        coin_id: str,
        days: int = 365,
        vs_currency: str = "usd",
    ) -> StandardSeries:
        """Pull cryptocurrency price data from CoinGecko.

        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
            days: Number of days of history (max 365 for free tier)
            vs_currency: Quote currency (default: 'usd')

        Returns:
            StandardSeries with data and metadata
        """
        from .sources.coingecko_source import pull_coingecko as _pull_coingecko

        result = _pull_coingecko(coin_id=coin_id, days=days, vs_currency=vs_currency)
        self.last_result = result
        return result

    # -------------------------------------------------------------------------
    # ABS source
    # -------------------------------------------------------------------------

    def pull_abs(
        self,
        series_id: str,
        catalog_num: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> StandardSeries:
        """Pull data from Australian Bureau of Statistics (ABS).

        Args:
            series_id: ABS series ID (e.g., 'A84423050A')
            catalog_num: ABS catalog number (e.g., '6202.0' for Labour Force)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            StandardSeries with data and metadata
        """
        from .sources.abs_source import pull_abs as _pull_abs

        result = _pull_abs(
            series_id=series_id,
            catalog_num=catalog_num,
            start_date=start_date,
            end_date=end_date,
        )
        self.last_result = result
        return result

    # -------------------------------------------------------------------------
    # RBA source
    # -------------------------------------------------------------------------

    def pull_rba(
        self,
        series_id: str,
        table_no: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> StandardSeries:
        """Pull data from Reserve Bank of Australia (RBA).

        Args:
            series_id: RBA series ID (e.g., 'ARBAMPCNCRT' for cash rate)
            table_no: Optional table number (e.g., 'A2', 'C1')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            StandardSeries with data and metadata
        """
        from .sources.rba_source import pull_rba as _pull_rba

        result = _pull_rba(
            series_id=series_id,
            table_no=table_no,
            start_date=start_date,
            end_date=end_date,
        )
        self.last_result = result
        return result

    # -------------------------------------------------------------------------
    # TradingView source (placeholder)
    # -------------------------------------------------------------------------

    def pull_tradingview(
        self,
        symbol: str,
        exchange: str = "NASDAQ",
        interval: str = "1D",
        n_bars: int = 5000,
        fut_contract: Optional[int] = None,
        extended_session: bool = False,
        data_type: str = "close",
    ) -> StandardSeries:
        """Pull data from TradingView.

        Args:
            symbol: TradingView symbol (e.g., 'AAPL', 'ES1!')
            exchange: Exchange code (e.g., 'NASDAQ', 'NSE', 'CME')
            interval: Chart interval (default: '1D')
            n_bars: Number of bars to download, max 5000 (default: 5000)
            fut_contract: None for cash, 1 for front contract, 2 for next contract
            extended_session: Use extended session (default: False)
            data_type: Type of data ('close', 'open', 'high', 'low', 'volume')

        Returns:
            StandardSeries with data and metadata
        """
        from .sources.tv_source import pull_tv as _pull_tv

        result = _pull_tv(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            n_bars=n_bars,
            fut_contract=fut_contract,
            extended_session=extended_session,
            data_type=data_type,
        )
        self.last_result = result
        return result

    # -------------------------------------------------------------------------
    # Nasdaq source (placeholder)
    # -------------------------------------------------------------------------

    def pull_nasdaq(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> StandardSeries:
        """Pull data from Nasdaq Data Link.

        Args:
            symbol: Nasdaq Data Link symbol (e.g., 'WIKI/AAPL', 'ECONOMIA/DEXUSEU')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            StandardSeries with data and metadata
        """
        from .sources.nasdaq_source import pull_nasdaq as _pull_nasdaq

        api_key = self.get_api_key('nasdaq')
        result = _pull_nasdaq(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            api_key=api_key,
        )
        self.last_result = result
        return result

    # -------------------------------------------------------------------------
    # Glassnode source

    def pull_glassnode(
        self,
        metric: str,
        asset: str = "BTC",
        interval: str = "24h",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> StandardSeries:
        """Pull on-chain data from Glassnode.

        Args:
            metric: Glassnode metric path (e.g., '/market/price_usd_close')
            asset: Crypto asset ticker (default: 'BTC')
            interval: Time resolution (default: '24h')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            StandardSeries with data and metadata
        """
        api_key = self.get_api_key('glassnode')
        if not api_key:
            raise ValueError(
                "Glassnode API key required. "
                "Add 'glassnode' key to your API_Keys.json."
            )

        from .sources.glassnode_source import pull_glassnode as _pull_glassnode

        result = _pull_glassnode(
            metric=metric,
            asset=asset,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            api_key=api_key,
        )
        self.last_result = result
        return result

    # -------------------------------------------------------------------------
    # Trading Economics source (tedata)
    # -------------------------------------------------------------------------

    def pull_tedata(
        self,
        url: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        browser: str = "auto",
    ) -> StandardSeries:
        """Pull data from Trading Economics via Selenium scraping.

        Args:
            url: Trading Economics chart URL (full URL or path portion)
            start_date: Optional start date filter (YYYY-MM-DD)
            end_date: Optional end date filter (YYYY-MM-DD)
            browser: Browser preference ('firefox', 'chrome', or 'auto') — default 'auto'

        Returns:
            StandardSeries with data and metadata
        """
        from .sources.tedata_source import pull_tedata as _pull_tedata

        result = _pull_tedata(
            url=url,
            start_date=start_date,
            end_date=end_date,
            browser=browser,
        )
        self.last_result = result
        return result

    # -------------------------------------------------------------------------
    # Generic pull method
    # -------------------------------------------------------------------------

    def pull(
        self,
        source: str,
        *args,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> StandardSeries:
        """Generic pull method routing to appropriate source.

        Args:
            source: Source name ('yfinance', 'fred', etc.)
            *args: Source-specific positional arguments
            start_date: Optional start date
            end_date: Optional end date
            **kwargs: Source-specific keyword arguments

        Returns:
            StandardSeries with data and metadata
        """
        source = source.lower()

        if source == 'yfinance':
            return self.pull_yfinance(*args, start_date=start_date, end_date=end_date, **kwargs)
        elif source == 'fred':
            return self.pull_fred(*args, start_date=start_date, end_date=end_date, **kwargs)
        elif source == 'bea':
            return self.pull_bea(*args, start_date=start_date, end_date=end_date, **kwargs)
        elif source == 'coingecko':
            return self.pull_coingecko(*args, **kwargs)
        elif source in ('abs', 'abs_series'):
            return self.pull_abs(*args, **kwargs)
        elif source in ('rba', 'rba_series'):
            return self.pull_rba(*args, **kwargs)
        elif source in ('tv', 'tradingview'):
            return self.pull_tradingview(*args, **kwargs)
        elif source == 'nasdaq':
            return self.pull_nasdaq(*args, start_date=start_date, end_date=end_date, **kwargs)
        elif source == 'glassnode':
            return self.pull_glassnode(*args, start_date=start_date, end_date=end_date, **kwargs)
        elif source in ('te', 'tedata', 'trading_economics'):
            return self.pull_tedata(*args, **kwargs)
        else:
            raise ValueError(f"Unknown or unimplemented source: {source}")
