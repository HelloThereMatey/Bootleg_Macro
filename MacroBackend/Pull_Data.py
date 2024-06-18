###### Required modules/packages #####################################
import os
fdel = os.path.sep
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
parent = os.path.dirname(wd)
print(wd,parent)
import sys
sys.path.append(parent)

## This is one of my custom scripts holding functions for pulling price data from APIs. Your IDE might not find it before running script. 
from MacroBackend import PriceImporter, Utilities
from MacroBackend.ABS_backend import abs_series_by_r
from MacroBackend.Glassnode import GlassNode_API
import datetime
import pandas as pd
import numpy as np
import pandas_datareader as pdr
import quandl
from yahoofinancials import YahooFinancials as yf
import json

def yf_get_data(ticker: str, start_date: str, end_date: str, data_freq: str = "daily"):
    yfobj = yf(ticker)
    data = yfobj.get_historical_price_data(start_date, end_date, data_freq)
    data = pd.DataFrame(data[ticker]["prices"]).set_index("formatted_date", drop=True).drop("date", axis=1)
    # if dtype == "close":
    #     return pd.Series(data['prices']['close'], name = ticker)
    # elif dtype == "OHLCV":
    #     return pd.DataFrame(data['prices'])[['open', 'high', 'low', 'close', 'volume']]
    # else:
    return data

####### CLASSES ######################################################
class get_data_failure(Exception):
    pass
      
class dataset(object):
    def __init__(self):
        
        self.supported_sources = ['fred', 'yfinance', 'yfinance2', 'tv', 'coingecko', 'yahoo',
                                'iex-tops', 'iex-last', 'bankofcanada', 'stooq', 'iex-book',
                                'enigma', 'famafrench', 'oecd', 'eurostat', 'nasdaq',
                                'quandl', 'tiingo', 'yahoo-actions', 'yahoo-dividends', 'av-forex',
                                'av-forex-daily', 'av-daily', 'av-daily-adjusted', 'av-weekly', 'av-weekly-adjusted',
                                'av-monthly', 'av-monthly-adjusted', 'av-intraday', 'econdb', 'naver', 'glassnode',
                                'abs']
        self.added_sources = ['fred', 'yfinance', 'yfinance2', 'tv', 'coingecko', 'quandl', 'glassnode', 'abs']
        
        self.pd_dataReader = list(set(self.supported_sources) - set(self.added_sources))
        self.keySources = ['fred', 'bea', 'glassnode', 'quandl']
        
        self.keyz = Utilities.api_keys(JSONpath = parent + fdel + 'MacroBackend' + fdel + 'SystemInfo')
        self.api_keys = dict(self.keyz.keys)
        self.data = None

    def get_data(self, source: str, data_code: str, start_date: str, exchange_code: str = None, 
                 end_date: str = datetime.date.today().strftime('%Y-%m-%d'), data_freq: str = "1d", dtype: str = "close",
                 capitalize_column_names: bool = False):
        
        self.data_freq = data_freq
        self.source = source.lower()
        self.check_key()
        if self.source not in self.supported_sources:
            print('The data source: ', source, 'is not supported. You must choose from the following sources: \n', self.supported_sources)
            print("Your specified source is not supported, get the fuck out of town you cunt.") 
            quit()

        self.data_code = data_code
        self.exchange_code = exchange_code
        self.start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') 
        self.SeriesInfo = pd.Series([],dtype=str)
        self.dataName = data_code
        self.d_type = dtype 

        print("Looking for data from source: ", self.source, "data code: ", self.data_code)
        self.pull_data()

        if capitalize_column_names and dtype != "close":
            self.data.columns = self.data.columns.str.capitalize()

    def check_key(self):
        # print("Checking API keys: ", self.api_keys)
        if self.source in self.keySources and self.source not in self.api_keys.keys():
            print("No API key found for your source: ", self.source, "do you have the key at hand ready to paste into terminal?")
            if input("y/n?") == 'y':
                self.keyz.add_key(self.source)
            else:
                print("You need an API key to get data from ", self.source)    
            quit()
        else:
            return    
        
    def pull_data(self):

        if self.source == 'fred':
            SeriesInfo, TheData = PriceImporter.PullFredSeries(self.data_code, self.api_keys['fred'],
                        start = self.start_date.strftime('%Y-%m-%d'), end = self.end_date.strftime('%Y-%m-%d'))
            self.dataName = SeriesInfo['id']

            self.SeriesInfo = SeriesInfo
            self.data = TheData

        elif self.source == 'yfinance':
            try:
                print("Trying yfinance package to get historical data for ", self.data_code)  
                TheData, ticker = PriceImporter.pullyfseries(self.data_code, start = self.start_date.strftime('%Y-%m-%d'),
                                                   interval = self.data_freq)
                if len(TheData) < 1:
                    raise get_data_failure('Could not get data for the data-code from the source specified.')
                self.filterData(TheData)
            
            except Exception as e:
                print("Could not score data for asset: "+ticker," from yfinance. Error: ", e, "Trying other scraper packages...") 
                print("Trying yahoo financials.....")   
                # TheData = PriceImporter.Yahoo_Fin_PullData(self.data_code, self.start_date.strftime('%Y-%m-%d'), 
                #                                            end_date = self.end_date.strftime('%Y-%m-%d'))   
                TheData = yf_get_data(self.data_code, self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d'))
                self.filterData(TheData)

        elif self.source == 'yfinance2':
            print("Trying yahoo financials package to get historical data..")  
            TheData = yf_get_data(self.data_code, self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d'))
            self.filterData(TheData)

        elif self.source == 'tv': 
            split = self.data_code.split(',', maxsplit=1)   #Data codes for tv are input in the format: DATA_CODE,EXCHANGE_CODE
            self.data_code = split[0]; self.exchange_code = split[1]

            TheData, info = PriceImporter.DataFromTVGen(self.data_code, self.exchange_code, start_date = self.start_date, 
                                                        end_date = self.end_date, BarTimeFrame='D')
            dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(TheData.index).date)
            TheData.rename({'symbol':'Symbol','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}, axis=1, inplace=True)
            if 'Symbol' in TheData.columns:
                TheData.drop('Symbol',axis=1,inplace=True)

            self.SeriesInfo = info
            TheData.set_index(dtIndex,inplace=True)
            print('Data pulled from TV for ticker: ', self.data_code)    
            self.data = TheData[self.start_date:self.end_date]      
        
        elif self.source == 'coingecko':
            CoinID = PriceImporter.getCoinID(self.data_code, InputTablePath=parent+fdel+'MacroBackend'+fdel+'AllCG.csv')
            numDays = (self.end_date - self.start_date).days
            TheData = PriceImporter.CoinGeckoPriceHistory(CoinID[1],TimeLength = numDays) 
            TheData.rename({"Price (USD)":"Close"},axis=1,inplace=True) 
            TheData = pd.Series(TheData['Close'], name = self.dataName) 
            self.data = TheData

        elif self.source == 'quandl':
            if quandl.ApiConfig.api_key == self.api_keys['quandl']:
                print('quandl key already set: ', quandl.ApiConfig.api_key)    
            else:    
                quandl.ApiConfig.api_key = self.api_keys['quandl']
                print('quandl API key set just now: ', quandl.ApiConfig.api_key) 
            print(self.start_date, self.end_date)
            self.data = quandl.get(self.exchange_code+'/'+self.data_code, start_date = self.start_date, end_date = self.end_date)

        elif self.source == 'glassnode':
            # For GlassNode we need the data_code. specification to be in thee format METRIC,ASSET,TIME_RESOLUTION
            # TIME_RESOLUTION parameter is optional, default = '24h'            
            splitted = self.data_code.split(',')
            if len(splitted) < 2:
                print("You need to specify the metric, asset in the data_code parameter at minimum for Glassnode. \
                      Can also add time resolution as third parameter after another comma.")
                quit()
            elif len(splitted) == 2:
                splitted.append('24h')
            else:
                pass
            
            # params = {'a':splitted[1].strip(),'i':splitted[2].strip(),'f':'json','api_key': self.api_keys['glassnode']} 
            gnpull = glassnode_data()
            gnpull.chosen_met(splitted[0].strip())
            gnpull.get_data(asset = splitted[1].strip(), resolution = splitted[2].strip(), format = 'json')
            self.data = gnpull.data
            self.SeriesInfo = gnpull.seriesInfo; self.dataName = gnpull.seriesInfo["metric_short"]

        elif self.source in self.pd_dataReader:
            print("Attempting to pull data from source: ", self.source, ', for ticker; ', self.data_code, 'using pandas datareader.')
            data = pdr.DataReader(self.data_code, self.source, start = self.start_date, end = self.end_date)
            print(data)

        elif self.source.lower() == 'abs'.lower():  

            series, SeriesInfo = abs_series_by_r.get_abs_series_r(series_id = self.data_code)
            # abs_path = parent+fdel+"User_Data"+fdel+"ABS"+fdel+"LastPull"
            # data_index = r_to_pd_df(ABS.read_abs_series(self.data_code, path = abs_path))
            # table_name = data_index.iloc[0].at['table_no']
            # data = pd.read_excel(abs_path+fdel+table_name+'.xlsx', sheet_name="Data1", index_col=0)
            # data.columns = data.columns.str.replace(";", "").str.strip()
            # data.to_excel(parent+fdel+"User_Data"+fdel+"ABS"+fdel+"Full_Sheets"+fdel+table_name+".xlsx")
            # column = data.columns[data.isin([self.data_code]).any()]
            # series = data[column]
            # self.SeriesInfo = series.iloc[0:9]
            # series = series.iloc[9:].squeeze()
            # index = pd.to_datetime(series.index).date
            # self.data = pd.Series(series.to_list(), index = pd.DatetimeIndex(index))
            self.data = series
            self.SeriesInfo = SeriesInfo
            self.dataName = series.name

        else:
            if self.source in self.supported_sources:
                print("Your specified source will be supported but the coding has not been done yet, sorry sucker..") 
                quit()
            else:
                print("Your specified source is not supported, get the fuck out of town you cunt.") 
                quit()

    def filterData(self, TheData: pd.DataFrame):
        TheData.columns = TheData.columns.str.capitalize()
        columns_to_keep = ['Open', 'High', 'Low', 'Close', 'Volume']
        columns_to_keep = list(set(TheData.columns) & set(columns_to_keep))

        if self.d_type == 'OHLCV':
            self.data = TheData[columns_to_keep]

        elif self.d_type == 'close':    
            self.data = pd.Series(TheData['Close'], name = self.dataName)       
        else:
            self.data = TheData        

class glassnode_data(object):   ## One can use this class to get data from Glassnode without using dataset class. 

    def __init__(self):
        self.metric_df = pd.read_csv(wd+fdel+"Glassnode"+fdel+"Saved_Data"+fdel+"GN_MetricsList.csv", index_col=0)
        self.metric_list = pd.Series([str(path).split("/")[-1] for path in self.metric_df["path"]])
        self.keys = Utilities.api_keys().keys

    def chosen_met(self, metric):
        self.metric = metric
        metIndex = (self.metric_list == metric).idxmax()
        self.metric_path = self.metric_df['path'].iloc[metIndex]
        ass_json = json.loads(str(self.metric_df['assets'].iloc[metIndex]).strip().replace("'", '"'))
        self.met_assets = [asset["symbol"] for asset in ass_json]
        self.met_currs = [curr for curr in self.metric_df['currencies'].iloc[metIndex]]
        self.met_resolutions = [res for res in self.metric_df['resolutions'].iloc[metIndex]]
        self.met_formats = [form for form in self.metric_df['formats'].iloc[metIndex]]
        dom_json = json.loads(str(self.metric_df['paramsDomain'].iloc[metIndex]).strip().replace("'", '"'))
        self.met_domain = [dom for dom in dom_json.values()]

    def get_data(self, asset: str = "BTC", tier: int = 1, resolution: str = '24h', format: str = 'csv', paramsDomain: str = "a"):
        params = {'a': asset,'i': resolution,'f': format,'api_key': self.keys['glassnode']} 
        self.data = GlassNode_API.GetMetric(path = self.metric_path, APIKey = self.keys['glassnode'], params = params)
        self.seriesInfo = {"Source": "glassnode", "metric_short": self.metric, "metric_full": self.metric_path, "asset": asset,
                           "tier": tier, "resolution": resolution, "format": format, "paramsDomain": paramsDomain}
               

if __name__ == "__main__":
    
    # me_data = dataset(source = 'yfinance', data_code = 'BTC-USD',start_date="2011-01-01", dtype="OHLCV")
    # print(me_data.data, me_data.SeriesInfo, me_data.dataName)
    # me_data = dataset(source = 'abs', data_code = 'A3605929A',start_date="2011-01-01")
    # print(me_data.data, me_data.SeriesInfo, me_data.dataName)

    #DXY = PriceImporter.ReSampleToRefIndex(DXY,Findex,'D') 
    #print(me_data.data.iloc[len(me_data.data)-1])
    # keyz = Utilities.api_keys()
    # res = PriceImporter.FREDSearch("Gross",apiKey=keyz.keys['fred'])
    # print(res)
    # data = PriceImporter.tv_data("SPY", "NSE", search=True)
    # print(data.seriesInfo)
   
    
    # print(full_results1['symbol'][0], full_results1['exchange'][0])
    # data = yf('AAPL')
    # print(data.get_financial_data('annual'))
    #.get_historical_price_data('2020-01-01', '2020-01-10', 'daily')
    #print(data)
    # tvd = PriceImporter.tv_data("BTCUSD", 'INDEX')#, username="NoobTrade181", password="4Frst6^YuiT!")
    # #tvd.all_data_for_timeframe(timeframe = "4H")
    # datas = tvd.tv.exp_ws("BTCUSD", exchange = 'INDEX', interval=PriceImporter.TimeInterval("4H"),n_bars=5000)
    # print(datas)
     
    # gn = glassnode_data()
    # gn.chosen_met("price_usd_ohlc")
    # print(gn.met_assets, gn.met_resolutions, gn.met_formats, gn.met_currs, gn.met_domain)
    # gn.get_data("price_usd_ohlc", asset = "BTC", resolution = '24h', format = 'json', paramsDomain = "a")
    # print(gn.data)

    me_data = dataset(source = 'glassnode', data_code = 'price_usd_ohlc,BTC,24h',start_date="2011-01-01", dtype="OHLCV")
    print(me_data.data, me_data.SeriesInfo, me_data.dataName)


    



                    
