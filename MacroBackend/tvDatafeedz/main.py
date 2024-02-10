import datetime
import enum
import json
import logging
import random
import re
import string
import pandas as pd
from websocket import create_connection
import requests
import json
import os

wd = os.path.dirname(os.path.realpath(__file__))
fdel = os.path.sep

logger = logging.getLogger(__name__)

custom_headers = {
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "Upgrade",
    "Host": "data.tradingview.com",
    "Origin": "https://www.tradingview.com",
    "Pragma": "no-cache",
    "Sec-Gpc": "1",
    "Sec-Websocket-Extensions": "permessage-deflate; client_max_window_bits",
    "Sec-Websocket-Key": "fRH1UmdBfnogHJRc5GmnAw==",
    "Sec-Websocket-Version": "13",
    "Upgrade": "websocket",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

class Interval(enum.Enum):
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
    __sign_in_url = 'https://www.tradingview.com/accounts/signin/'
    __search_url = 'https://symbol-search.tradingview.com/symbol_search/?text={}&hl=1&exchange={}&lang=en&type=&domain=production'
    __ws_headers = json.dumps({"Origin": "https://data.tradingview.com"})
    __signin_headers = {'Referer': 'https://www.tradingview.com'}
    __ws_timeout = 30

    def __init__(
        self,
        username: str = None,
        password: str = None,
    ) -> None:
        """Create TvDatafeed object

        Args:
            username (str, optional): tradingview username. Defaults to None.
            password (str, optional): tradingview password. Defaults to None.
        """

        self.ws_debug = False
        self.token = self.__auth(username, password)

        if self.token is None:
            self.token = "unauthorized_user_token"
            logger.warning(
                "you are using nologin method, data you access may be limited"
            )

        self.ws = None
        self.session = self.__generate_session()
        self.chart_session = self.__generate_chart_session()

    def __auth(self, username, password):

        if (username is None or password is None):
            token = None

        else:
            data = {"username": username,
                    "password": password,
                    "remember": "on"}
            print(data) 
            try:
                response = requests.post(
                    url=self.__sign_in_url, data=data, headers=self.__signin_headers)
                print(response.text)
                token = response.json()['user']['auth_token']
                print("User auth token: ", token)
            except Exception as e:
                logger.error('error while signin', e)
                token = None

        return token

    "wss://data.tradingview.com/socket.io/websocket?from=chart%2FPUfaTXYt%2F&date=2024_02_02-15_12&type=chart"
    def __create_connection(self):
        logging.debug("creating websocket connection")
        self.ws = create_connection(
            "wss://data.tradingview.com/socket.io/websocket", headers=self.__ws_headers, timeout=self.__ws_timeout
        )
    
    def create_custom_ws_connection(self, custom_headers: str, end_date: str = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M")):
        #If putting in a custom end_date, must be YYYY_YY_DD-HH_MM format as str. 
        logging.debug("creating websocket connection")
        #chart%2FPUfaTXYt%2F
        self.ws = create_connection(
            "wss://data.tradingview.com/socket.io/websocket?&date="+end_date+"&type=chart", 
            headers=custom_headers, timeout=self.__ws_timeout)
        print(self.ws.getheaders(), self.ws.status, self.ws.handshake_response.status)

    @staticmethod
    def __filter_raw_message(text):
        try:
            found = re.search('"m":"(.+?)",', text).group(1)
            found2 = re.search('"p":(.+?"}"])}', text).group(1)

            return found, found2
        except AttributeError:
            logger.error("error in filter_raw_message")

    @staticmethod
    def __generate_session():
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters)
                                for i in range(stringLength))
        return "qs_" + random_string

    @staticmethod
    def __generate_chart_session():
        stringLength = 12
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters)
                                for i in range(stringLength))
        return "cs_" + random_string

    @staticmethod
    def __prepend_header(st):
        return "~m~" + str(len(st)) + "~m~" + st

    @staticmethod
    def __construct_message(func, param_list):
        return json.dumps({"m": func, "p": param_list}, separators=(",", ":"))

    def __create_message(self, func, paramList):
        return self.__prepend_header(self.__construct_message(func, paramList))

    def __send_message(self, func, args):
        m = self.__create_message(func, args)
        if self.ws_debug:
            print(m)   
        self.ws.send(m)

    def receive_ohlcv_data(self, symbol: str = "TICKER"):
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
        return self.__create_df(raw_data, symbol)    

    @staticmethod
    def __create_df(raw_data, symbol):
        try:
            out = re.search('"s":\[(.+?)\}\]', raw_data).group(1)
            x = out.split(',{"')
            data = list()
            volume_data = True

            for xi in x:
                xi = re.split("\[|:|,|\]", xi)
                ts = datetime.datetime.fromtimestamp(float(xi[4]))

                row = [ts]

                for i in range(5, 10):

                    # skip converting volume data if does not exists
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
                data, columns=["datetime", "open",
                               "high", "low", "close", "volume"]
            ).set_index("datetime")
            data.insert(0, "symbol", value=symbol)
            return data
        except AttributeError:
            logger.error("no data, please check the exchange and symbol")

    @staticmethod
    def __format_symbol(symbol, exchange, contract: int = None):

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
        """get historical data

        Args:
            symbol (str): symbol name
            exchange (str, optional): exchange, not required if symbol is in format EXCHANGE:SYMBOL. Defaults to None.
            interval (str, optional): chart interval. Defaults to 'D'.
            n_bars (int, optional): no of bars to download, max 5000. Defaults to 10.
            fut_contract (int, optional): None for cash, 1 for continuous current contract in front, 2 for continuous next contract in front . Defaults to None.
            extended_session (bool, optional): regular session if False, extended session if True, Defaults to False.

        Returns:
            pd.Dataframe: dataframe with sohlcv as columns
        """
        symbol = self.__format_symbol(
            symbol=symbol, exchange=exchange, contract=fut_contract
        )

        interval = interval.value

        self.__create_connection()

        self.__send_message("set_auth_token", [self.token])
        self.__send_message("chart_create_session", [self.chart_session, ""])
        self.__send_message("quote_create_session", [self.session])
        self.__send_message(
            "quote_set_fields",
            [
                self.session,
                "ch",
                "chp",
                "current_session",
                "description",
                "local_description",
                "language",
                "exchange",
                "fractional",
                "is_tradable",
                "lp",
                "lp_time",
                "minmov",
                "minmove2",
                "original_name",
                "pricescale",
                "pro_name",
                "short_name",
                "type",
                "update_mode",
                "volume",
                "currency_code",
                "rchp",
                "rtc",
            ],
        )

        self.__send_message(
            "quote_add_symbols", [self.session, symbol,
                                  {"flags": ["force_permission"]}]
        )
        self.__send_message("quote_fast_symbols", [self.session, symbol])

        self.__send_message(
            "resolve_symbol",
            [
                self.chart_session,
                "symbol_1",
                '={"symbol":"'
                + symbol
                + '","adjustment":"splits","session":'
                + ('"regular"' if not extended_session else '"extended"')
                + "}",
            ],
        )
        self.__send_message(
            "create_series",
            [self.chart_session, "s1", "s1", "symbol_1", interval, n_bars],
        )
        self.__send_message("switch_timezone", [
                            self.chart_session, "exchange"])

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

        return self.__create_df(raw_data, symbol)

    def search_symbol(self, text: str, exchange: str = ''):
        url = self.__search_url.format(text, exchange)

        symbols_list = []
        try:
            resp = requests.get(url)

            symbols_list = json.loads(resp.text.replace(
                '</em>', '').replace('<em>', ''))
        except Exception as e:
            logger.error(e)

        return symbols_list
    
    ## This is my custom function here...
    def exp_ws(self, symbol: str, exchange: str = "NSE",interval: Interval = Interval.in_daily,
        n_bars: int = 10, fut_contract: int = None, extended_session: bool = False, time_zone: str = 'Australia/Sydney',
        collection_method: int = 0) -> pd.DataFrame:
        
        symbol = self.__format_symbol(symbol=symbol, exchange=exchange, contract=fut_contract)
        interval = interval.value
        print("Symbol:Exchange: ", symbol, "\n time interval: ", interval, '\n number of bars requested: ',n_bars)

        self.create_custom_ws_connection(custom_headers=json.dumps(custom_headers), end_date = "2022_01_01-00_00")

        self.__send_message("set_auth_token", [self.token])
        self.__send_message("chart_create_session", [self.chart_session, ""])
        self.__send_message("quote_create_session", [self.session])

        self.set_fields = [self.session,"ch","chp","current_session","description","local_description","language","exchange","fractional","is_tradable",
                    "lp","lp_time","minmov","minmove2","original_name","pricescale","pro_name","short_name","type","update_mode","volume",
                    "currency_code","rchp","rtc"]
        self.__send_message("quote_set_fields", self.set_fields)

        self.__send_message("quote_add_symbols", [self.session, symbol,{"flags": ["force_permission"]}])
        self.__send_message("quote_fast_symbols", [self.session, symbol])
        self.__send_message("resolve_symbol",
                [self.chart_session,"symbol_1",
                    '={"symbol":"'+ symbol
                    + '","adjustment":"splits","session":'
                    + ('"regular"' if not extended_session else '"extended"')+ "}",],)
        
        self.__send_message("switch_timezone", [self.chart_session, time_zone])

        if collection_method == 0:  ##Use create_series function to get the data. 
            self.__send_message("create_series", [self.chart_session, "sds_1","s1", "symbol_1", interval, n_bars,""])
            logger.debug(f"getting data for {symbol}...")
            full_data = self.receive_ohlcv_data(symbol)

        elif collection_method == 1:  #Get the data through repeated calls of "request_more_data" function. 
            self.__send_message("create_series", [self.chart_session, "sds_1","s1", "symbol_1", interval, 300,""])
            logger.debug(f"getting data for {symbol}...")
            full_data = self.receive_ohlcv_data(symbol); bars = 300
            print(full_data)

            while bars <= n_bars:
                print("Bars already collected: ", bars)
                self.__send_message("request_more_data", [self.chart_session, "sds_1", 300])
                new_data = self.receive_ohlcv_data(symbol)
                print(new_data)
                full_data = pd.concat([full_data, new_data], axis = 0)
                bars += 300 
        else:
            print("No other data collections are implemented yet, pther than 0 or 1.")      
            return None  

        return full_data
    
    def multi_attempt_pull(self, symbol: str, exchange: str = "NSE",interval: Interval = Interval.in_daily,
        n_bars: int = 10, fut_contract: int = None, extended_session: bool = False, time_zone: str = 'Australia/Sydney',
        collection_method: int = 0, attempts: int = 5):
        print(symbol, exchange, collection_method)
        data = None; tries = 0
        while tries <= attempts:
            try:
                data = self.exp_ws(symbol, exchange = exchange, interval = interval, n_bars = n_bars, fut_contract = fut_contract, 
                                   collection_method = collection_method, extended_session = extended_session, time_zone = time_zone)
            except Exception as ahshit:
                print(ahshit)
                tries += 1
            if data is not None:
                break      
        return data

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    tv = TvDatafeed()
    attempts = 0; data = None

    while attempts <= 5:
        try:
            data = tv.multi_attempt_pull("BTCUSD", exchange= "INDEX",interval=Interval.in_4_hour, n_bars=6770)
        except Exception as cunt:
            print(cunt)    
            attempts += 1   
        if data is not None:
            break     
    print(data)
    
    # print(tv.get_hist("NIFTY", "NSE", fut_contract=1))
    # print(
    #     tv.get_hist(
    #         "EICHERMOT",
    #         "NSE",
    #         interval=Interval.in_1_hour,
    #         n_bars=500,
    #         extended_session=False,
    #     )
    # )
    

"wss://data.tradingview.com/socket.io/websocket?from=chart%2FPUfaTXYt%2F&date=2024_02_02-15_12&type=chart"