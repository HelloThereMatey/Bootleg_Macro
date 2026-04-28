"""
TradingView source for bm.

Uses local tvDatafeedz module for accessing TradingView chart data.
Based on tvDatafeedz/main.py from the original Bootleg_Macro implementation.
"""

import datetime
import enum
import json
import logging
import random
import re
import string
from typing import Optional, Union

import pandas as pd
import requests
from websocket import create_connection

from ..auxiliary import FrequencyConverter, convert_to_standard_series, calculate_metadata_stats
from ..models import SeriesMetadata, StandardSeries


logger = logging.getLogger(__name__)

_WS_HEADERS = json.dumps({"Origin": "https://data.tradingview.com"})


class Interval(enum.Enum):
    """TradingView chart intervals."""
    in_1_minute = "1"
    in_3_minute = "3"
    in_5_minute = "5"
    in_15_minute = "15"
    in_30_minute = "30"
    in_45_minute = "45"
    in_1_hour = "1H"
    in_2_hour = "2H"
    in_3_hour = "3H"
    in_4_hour = "4H"
    in_daily = "1D"
    in_weekly = "1W"
    in_monthly = "1M"


class TvDatafeed:
    """TradingView data fetcher using websocket connection."""

    __sign_in_url = 'https://www.tradingview.com/accounts/signin/'
    __search_url = 'https://symbol-search.tradingview.com/symbol_search/?text={}&hl=1&exchange={}&lang=en&type=&domain=production'
    __ws_timeout = 30

    def __init__(
        self,
        username: str = None,
        password: str = None,
    ) -> None:
        """Create TvDatafeed object.

        Args:
            username (str, optional): TradingView username. Defaults to None.
            password (str, optional): TradingView password. Defaults to None.
        """
        self.ws_debug = False
        self.token = self._auth(username, password)

        if self.token is None:
            self.token = "unauthorized_user_token"
            logger.warning(
                "you are using nologin method, data you access may be limited"
            )

        self.ws = None
        self.session = self._generate_session()
        self.chart_session = self._generate_chart_session()

    def _auth(self, username, password):
        if username is None or password is None:
            return None

        data = {"username": username, "password": password, "remember": "on"}
        try:
            response = requests.post(
                url=self.__sign_in_url, data=data, headers={"Referer": "https://www.tradingview.com"}
            )
            token = response.json()['user']['auth_token']
        except Exception as e:
            logger.error('error while signin', e)
            token = None

        return token

    def _create_connection(self):
        logging.debug("creating websocket connection")
        self.ws = create_connection(
            "wss://data.tradingview.com/socket.io/websocket", headers=_WS_HEADERS, timeout=self.__ws_timeout
        )

    @staticmethod
    def _filter_raw_message(text):
        try:
            found = re.search(r'"m":"(.+?)",', text).group(1)
            found2 = re.search(r'"p":(.+?"}"])}', text).group(1)
            return found, found2
        except AttributeError:
            logger.error("error in filter_raw_message")

    @staticmethod
    def _generate_session():
        random_string = "".join(random.choice(string.ascii_lowercase) for i in range(12))
        return "qs_" + random_string

    @staticmethod
    def _generate_chart_session():
        random_string = "".join(random.choice(string.ascii_lowercase) for i in range(12))
        return "cs_" + random_string

    @staticmethod
    def _prepend_header(st):
        return "~m~" + str(len(st)) + "~m~" + st

    @staticmethod
    def _construct_message(func, param_list):
        return json.dumps({"m": func, "p": param_list}, separators=(",", ":"))

    def _create_message(self, func, paramList):
        return self._prepend_header(self._construct_message(func, paramList))

    def _send_message(self, func, args):
        m = self._create_message(func, args)
        if self.ws_debug:
            print(m)
        self.ws.send(m)

    def _receive_data(self, symbol: str = "TICKER"):
        raw_data = ""
        while True:
            try:
                result = self.ws.recv()
                raw_data = raw_data + result + "\n"
            except Exception as e:
                logger.error(e)
                break
            if "series_completed" in result:
                break
        return self._create_df(raw_data, symbol)

    @staticmethod
    def _create_df(raw_data, symbol):
        try:
            out = re.search(r'"s":\[(.+?)\}]', raw_data).group(1)
            x = out.split(',{"')
            data = list()
            volume_data = True

            for xi in x:
                xi = re.split(r"\[|:|,|\]", xi)
                ts = datetime.datetime.fromtimestamp(float(xi[4]))

                row = [ts]

                for i in range(5, 10):
                    if not volume_data and i == 9:
                        row.append(0.0)
                        continue
                    try:
                        row.append(float(xi[i]))
                    except ValueError:
                        volume_data = False
                        row.append(0.0)
                        logger.debug('no volume data')

                data.append(row)

            data = pd.DataFrame(
                data, columns=["datetime", "open", "high", "low", "close", "volume"]
            ).set_index("datetime")
            data.insert(0, "symbol", value=symbol)
            return data
        except AttributeError:
            logger.error("no data, please check the exchange and symbol")
            return pd.DataFrame()

    @staticmethod
    def _format_symbol(symbol, exchange, contract: int = None):
        if ":" in symbol:
            pass
        elif contract is None:
            symbol = f"{exchange}:{symbol}"
        elif isinstance(contract, int):
            symbol = f"{exchange}:{symbol}{contract}!"
        else:
            raise ValueError("not a valid contract")
        return symbol

    def get_hist(
        self,
        symbol: str,
        exchange: str = "NSE",
        interval: Interval = Interval.in_daily,
        n_bars: int = 10,
        fut_contract: int = None,
        extended_session: bool = False,
    ) -> pd.DataFrame:
        """Get historical OHLCV data.

        Args:
            symbol: Symbol name
            exchange: Exchange name (default: 'NSE')
            interval: Chart interval (default: daily)
            n_bars: Number of bars to download, max 5000 (default: 10)
            fut_contract: None for cash, 1 for front contract, 2 for next contract
            extended_session: Use extended session (default: False)

        Returns:
            DataFrame with OHLCV columns
        """
        symbol = self._format_symbol(symbol=symbol, exchange=exchange, contract=fut_contract)
        interval_value = interval.value

        self._create_connection()

        self._send_message("set_auth_token", [self.token])
        self._send_message("chart_create_session", [self.chart_session, ""])
        self._send_message("quote_create_session", [self.session])
        self._send_message(
            "quote_set_fields",
            [
                self.session, "ch", "chp", "current_session", "description",
                "local_description", "language", "exchange", "fractional",
                "is_tradable", "lp", "lp_time", "minmov", "minmove2",
                "original_name", "pricescale", "pro_name", "short_name",
                "type", "update_mode", "volume", "currency_code", "rchp", "rtc",
            ],
        )
        self._send_message("quote_add_symbols", [self.session, symbol, {"flags": ["force_permission"]}])
        self._send_message("quote_fast_symbols", [self.session, symbol])
        self._send_message(
            "resolve_symbol",
            [
                self.chart_session, "symbol_1",
                '={"symbol":"' + symbol + '","adjustment":"splits","session":'
                + ('"regular"' if not extended_session else '"extended"') + "}",
            ],
        )
        self._send_message("create_series", [self.chart_session, "s1", "s1", "symbol_1", interval_value, n_bars])
        self._send_message("switch_timezone", [self.chart_session, "exchange"])

        raw_data = ""
        logger.debug(f"getting data for {symbol}...")

        while True:
            try:
                result = self.ws.recv()
                raw_data = raw_data + result + "\n"
            except Exception as e:
                logger.error(e)
                break
            if "series_completed" in result:
                break

        return self._create_df(raw_data, symbol)

    def search_symbol(self, text: str, exchange: str = ''):
        """Search for symbols on TradingView.

        Args:
            text: Search query
            exchange: Exchange filter (default: '')

        Returns:
            List of matching symbols
        """
        url = self.__search_url.format(text, exchange)
        try:
            resp = requests.get(url)
            symbols_list = json.loads(resp.text.replace('</em>', '').replace('<em>', ''))
        except Exception as e:
            logger.error(e)
            symbols_list = []
        return symbols_list


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
    data_type: str = "OHLCV",  # 'OHLCV', 'close', 'open', 'high', 'low', 'volume'
) -> StandardSeries:
    """Pull data from TradingView.

    Args:
        symbol: Symbol name (e.g., 'RELIANCE', 'AAPL')
        exchange: Exchange name (default: 'NSE')
        interval: Chart interval (default: '1D')
        n_bars: Number of bars to download, max 5000 (default: 5000)
        fut_contract: None for cash, 1 for front contract, 2 for next contract
        extended_session: Use extended session (default: False)
        data_type: Type of data to return ('OHLCV' returns all, or 'close', 'open', 'high', 'low', 'volume')

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

    if data_type == 'OHLCV':
        # Return close price series for simplicity
        series = data['close']
        series.name = f"{symbol_name}_close"
    elif data_type in ('close', 'open', 'high', 'low', 'volume'):
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
