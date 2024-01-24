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
from MacroBackend.Glassnode import GlassNode_API
import datetime
import pandas as pd
import pandas_datareader as pdr
import quandl

class get_data_failure(Exception):
    pass

# if len(SeriesInfo) > 0:
#     if Source != 'load':    
#         SeriesInfo['Source'] = Source            
# else:
#     print("Using default Series info for series: ", TheSeries['Legend_Name'], )
#     SeriesInfo['units'] = 'US Dollars'; SeriesInfo['units_short'] = 'USD'
#     SeriesInfo['title'] = TheSeries['Legend_Name']; SeriesInfo['id'] = TheSeries['Name']
#     SeriesInfo['Source'] = Source
# if Source != 'load':    
#     SeriesInfo['Source'] = Source       

# ######### Applies to all data loaded #####################
# TheData.index.rename('date',inplace=True)
# SeriesInfo.index.rename('Property',inplace=True); #SeriesInfo = pd.Series(SeriesInfo,name="Value")
# TheData2 = TheData.copy()

# if type(TheData2) == pd.Series:
#     pass
# else:
#     if len(TheData2.columns) > 1:
#         TheData2.name = TheSeries["Name"]
#         pass
#     else:
#         TheData2 = pd.Series(TheData2[TheData2.columns[0]],name=TheSeries['Name'])
# print('Data pull function, data series name: ',TheSeries['Name'],'Datatype:  ',type(TheData2))    
# TheData2 = TheData2[StartDate:EndDate]
# TheSeries['Data'] = TheData2
# TheSeries['SeriesInfo'] = SeriesInfo     ###Gotta make series info for the non-FRED series.   
# SeriesDict[series] = TheSeries
      


class dataset(object):
    def __init__(self, source: str, data_code: str, start_date: str, exchange_code: str = None, 
                 end_date: str = datetime.date.today().strftime('%Y-%m-%d'), data_freq: str = "1d", dtype: str = "close"):
        
        self.supported_sources = ['fred', 'yfinance', 'tv', 'coingecko', 'yahoo',
                                'iex-tops', 'iex-last', 'bankofcanada', 'stooq', 'iex-book',
                                'enigma', 'famafrench', 'oecd', 'eurostat', 'nasdaq',
                                'quandl', 'tiingo', 'yahoo-actions', 'yahoo-dividends', 'av-forex',
                                'av-forex-daily', 'av-daily', 'av-daily-adjusted', 'av-weekly', 'av-weekly-adjusted',
                                'av-monthly', 'av-monthly-adjusted', 'av-intraday', 'econdb', 'naver', 'glassnode']
        self.added_sources = ['fred', 'yfinance', 'tv', 'coingecko', 'quandl', 'glassnode']
        
        self.pd_dataReader = list(set(self.supported_sources) - set(self.added_sources))
        self.keySources = ['fred', 'bea', 'glassnode', 'quandl']
        
        self.keyz = Utilities.api_keys(JSONpath = parent + fdel + 'MacroBackend' + fdel + 'SystemInfo')
        self.api_keys = dict(self.keyz.keys)
        self.data = None
        self.data_freq = data_freq
        self.source = source
        if self.source not in self.supported_sources:
            print('The data source: ', source, 'is not supported. You must choose from the following sources: \n', self.supported_sources)
            print("Your specified source is not supported, get the fuck out of town you cunt.") 
            quit()
        
        self.check_key()
        self.data_code = data_code
        self.exchange_code = exchange_code
        self.start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') 
        self.SeriesInfo = pd.Series([],dtype=str)
        self.dataName = data_code
        self.d_type = dtype 

        self.pull_data()

    def check_key(self):
        print("Checking API keys: ", self.api_keys)
        if self.source in self.keySources and self.source not in self.api_keys.keys():
            print("No API key found for your source: ", self.source, "do you have the key at hand ready to paste into terminal?")
            if input("y/n?") == 'y':
                self.keyz.add_key(self.source)
            else:
                print("You need an API key too get data from ", self.source)    
            quit()
        else:
            return    
        
    def pull_data(self):
        if ',' in self.data_code:    #Ths is for tickers that are formulated for tvdataFeed format: ticker,exchange.
            split = self.data_code.split(',', maxsplit=1)
            self.data_code = split[0]
            self.exchange_code = split[1]
        
        if self.source == 'fred':
            SeriesInfo, TheData = PriceImporter.PullFredSeries(self.data_code, self.api_keys['fred'],
                        start = self.start_date.strftime('%Y-%m-%d'), end = self.end_date.strftime('%Y-%m-%d'))
            self.dataName = SeriesInfo['id']

            self.SeriesInfo = SeriesInfo
            self.data = TheData

        elif self.source == 'yfinance':
            try:
                TheData, ticker = PriceImporter.pullyfseries(self.data_code, start = self.start_date.strftime('%Y-%m-%d'),
                                                   interval = self.data_freq)
                if len(TheData) < 1:
                    raise get_data_failure('Could not get data for the data-code from the source specified.')
                self.filterData(TheData)
            
            except Exception as e:
                print("Could not score data for asset: "+ticker," from yfinance. Error: ", e, "Trying other scraper packages...") 
                print("Trying yahoo_fin web scraper.....")   
                TheData = PriceImporter.Yahoo_Fin_PullData(self.data_code, self.start_date.strftime('%Y-%m-%d'), 
                                                           end_date = self.end_date.strftime('%Y-%m-%d'))   
                self.filterData(TheData)

        elif self.source == 'tv': 
            TheData, info = PriceImporter.DataFromTVGen(self.data_code, self.exchange_code, start_date = self.start_date, 
                                                        end_date = self.end_date, BarTimeFrame='D')
            print(TheData)
            dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(TheData.index).date)
            TheData.rename({'symbol':'Symbol','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'}, axis=1, inplace=True)
            if 'Symbol' in TheData.columns:
                TheData.drop('Symbol',axis=1,inplace=True)

            self.SeriesInfo = info
            TheData.set_index(dtIndex,inplace=True)
            print('Data pulled from TV for ticker: ', self.data_code)    
            self.data = TheData[self.start_date:self.end_date]      
        
        elif self.source == 'coingecko':
            CoinID = PriceImporter.getCoinID(self.data_code, InputTablePath=parent+fdel+'MacroBackend'+fdel+'AllCG.xlsx')
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
            splitted = self.data_code.split(',')
            
            params = {'a':splitted[1].strip(),'i':splitted[2].strip(),'f':'json','api_key': self.api_keys['glassnode']} 
            data = GlassNode_API.GetMetric()
        elif self.source in self.pd_dataReader:
            print("Attempting to pull data from source: ", self.source, ', for ticker; ', self.data_code, 'using pandas datareader.')
            data = pdr.DataReader(self.data_code, self.source, start = self.start_date, end = self.end_date)
            print(data)

        else:
            if self.source in self.supported_sources:
                print("Your specified source will be supported but the coding has not been done yet, sorry sucker..") 
                quit()
            else:
                print("Your specified source is not supported, get the fuck out of town you cunt.") 
                quit()

    def filterData(self, TheData: pd.DataFrame):
        columns_to_keep = ['Open', 'High', 'Low', 'Close', 'Volume']
        columns_to_keep = list(set(TheData.columns) & set(columns_to_keep))

        if self.d_type == 'OHLCV':
            try: 
                self.data = TheData[columns_to_keep]
            except:
                columns_to_keep = ['open', 'high', 'low', 'close', 'volume']
                columns_to_keep = list(set(TheData.columns) & set(columns_to_keep))
                self.data = TheData[columns_to_keep]

        elif self.d_type == 'close':    
            try: 
                self.data = pd.Series(TheData['Close'], name = self.dataName)     
            except:
                self.data = pd.Series(TheData['close'], name = self.dataName)    
        else:
            self.data = TheData            

if __name__ == "__main__":
    
    me_data = dataset(source = 'quandl', data_code = 'AAPL', exchange_code='WIKI',start_date = '2015-01-01')
    print(me_data.data, me_data.dataName)
    #print(me_data.data.iloc[len(me_data.data)-1])




                    
