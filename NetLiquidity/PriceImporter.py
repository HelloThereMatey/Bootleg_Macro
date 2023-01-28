import numpy as np
from numpy import NaN, ceil, floor
import pandas as pd
import requests
import io
from datetime import timedelta
import datetime
import pandas_datareader.data as web
import yfinance as yf
import yahoo_fin.stock_info as si
from tvDatafeedz import TvDatafeed, Interval #This package 'tvDatafeed' is not available through pip, ive included in the project folder. 
import os
from sys import platform

wd = os.path.dirname(os.path.realpath(__file__))
if platform == "linux" or platform == "linux2":
    FDel = '/' # linux
elif platform == "darwin":
    FDel = '/' # OS X
elif platform == "win32":
    FDel = '\\' #Windows...

def CoinGeckoPriceHistory(CoinID,TimeLength):
    #Call CoinGecko API:
    print("Pinging coin gecko API, requesting data for asset: "+CoinID)
    url = r'https://api.coingecko.com/api/v3/coins/'+CoinID+r'/market_chart?vs_currency=usd&days='+str(TimeLength)+r'&interval=daily' 
    r = requests.get(url)           #Requests calls the coin gecko API. I'll have to figure out how to add trading view too. 
    df = pd.read_csv(io.StringIO(r.text))
    print("Coin gecko API response: \n",r)
    df = pd.DataFrame.from_dict(r.json())

    DateToday = datetime.date.today(); #DateToday = DateInstant.strftime("%d.%m.%y")
    length = len(df)
    #print('CG_Raw data: ',df)
    elementA1 = df.loc[0].at["prices"]     #Figure out the time string in the json response. 
    elementA2 = df.loc[length-1].at["prices"]     #Turns out to be time elapsed in ms since start of price tracking!!
    startTime = elementA1[0]      
    endTime = elementA2[0]       
    numDays = int(floor((endTime-startTime)/(1000*60*60*24))+1); print('Number of days in data: ',numDays,'Data length ',len(df))

    PricesDict = {'Date':[],'Days ago':[],'Price (USD)':[],'Market Cap (USD)':[],'Volume (USD)':[]}
    for i in range(len(df)):         #This converts the json response array from API into Pandas dataframe..
        PricesDict['Price (USD)'].append(df.loc[i].at["prices"][1])
        PricesDict['Market Cap (USD)'].append(df.loc[i].at["market_caps"][1])
        PricesDict['Volume (USD)'].append(df.loc[i].at["total_volumes"][1])
        TimeInPast = numDays - floor((df.loc[i].at["prices"][0]-startTime)/(1000*60*60*24))
        PricesDict['Days ago'].append(TimeInPast)
        DateTime = DateToday-timedelta(days=TimeInPast)
        Date = DateTime.strftime("%d.%m.%y")
        PricesDict['Date'].append(Date)
    #print(len(PricesDict['Date']), len(PricesDict['Days ago']), len(PricesDict['Market Cap (USD)']), len(PricesDict['Price (USD)'])\
        #, len(PricesDict['Volume (USD)']))
    PriceMatrix1 = pd.DataFrame(PricesDict);# PriceMatrix1.drop_duplicates(subset='Date',keep='first',inplace=True)
    dtIndex = pd.DatetimeIndex(PriceMatrix1['Date'],dayfirst=True,yearfirst=False)
    PriceMatrix1.set_index(dtIndex,inplace = True); PriceMatrix1.drop(['Date'],axis=1,inplace=True)
    PriceMatrix1 = PriceMatrix1[:-1]
    return PriceMatrix1

###### You Can pull the pirce history for a single coin using syntax as shown below with the function above:     
# PriceData = CoinGeckoPriceHistory('bitcoin',721)
# print(PriceData)

def GetFullListofCoinsCG():
    url = 'https://api.coingecko.com/api/v3/coins/list'
    r = requests.get(url)   #Requests calls the coin gecko API. I'll have to figure out how to add trading view too. 
    df = pd.read_csv(io.StringIO(r.text))
    df = pd.DataFrame.from_dict(r.json())
    return df

#### You can pull the full list of coins tracked by coin gecko and save it to an excel file using the function above, e.g:

# CG_CoinList = GetFullListofCoinsCG()
# CG_CoinList.to_excel('......Path to save file at.......')

def getCoinID(Coin:str,InputTablePath = None):   #This will get the ticker and coin gecko coin ID for a given coin,
    if InputTablePath is not None:                    #'Coin'here is basically a search string. Beware coin gecko can match others with same ticker. 
        df = pd.read_excel(InputTablePath)        #Best to put in the name of a coin rather than search using ticker. 
    else:
        df = GetFullListofCoinsCG()

    CoinSearch1 = df[df['name'] == Coin ]     ###This is syntax for searching through a dataframe to pull out the row where this condition is True. 
    CoinSearch2 = df[df['name'] == Coin.upper() ]
    CoinSearch3 = df[df['name'] == Coin.lower() ]
    CoinSearch4 = df[df['symbol'] == Coin ]
    CoinSearch5 = df[df['symbol'] == Coin.upper() ]  #This is a crude way to search, there'd definitely be a better way. 
    CoinSearch6 = df[df['symbol'] == Coin.lower() ]
    CoinSearch7 = df[df['id'] == Coin ]
    CoinSearch8 = df[df['id'] == Coin.upper() ]
    CoinSearch9 = df[df['id'] == Coin.lower()]

    CoinRows = [CoinSearch1,CoinSearch2,CoinSearch3,CoinSearch4,CoinSearch5,CoinSearch6,CoinSearch7,CoinSearch8,CoinSearch9]
    for i in CoinRows:
        if len(i) > 0: 
            CoinRow = i.to_dict('list')
    try:         
        Symbol = str(CoinRow['symbol'][0]).upper()    
        CoinID = str(CoinRow['id'][0])
        return (Symbol,CoinID)
    except:
        print('Coin name not found in dataframe from Coin Gecko.')  
        return ('Failed_Search', 'Failed_Search')

# def getNASDAQData(Ticker):
#     mydata = nasdaqdatalink.get(Ticker)        
#     print(mydata, type(mydata),type(mydata.index))

def DataReaderAllSources(ticker,DataStart,DataEnd=datetime.date.today()):    ### Try all sources using pandas datareader, slow, use when api not pre-specified.
    ### DataStart is str in YYYY-MM-DD format. Default dataEnd date is today. 
    expected_source = ["yahoo","iex","iex-tops","iex-last","iex-last","bankofcanada","stooq","iex-book","enigma","fred","famafrench","oecd",\
        "eurostat","nasdaq","quandl","moex","tiingo","yahoo-actions","yahoo-dividends","av-forex","av-forex-daily","av-daily","av-daily-adjusted",\
            "av-weekly","av-weekly-adjusted","av-monthly","av-monthly-adjusted","av-intraday","econdb","naver"]
    for source in expected_source:
        try:
            AssetData = pd.DataFrame(web.DataReader(ticker,source,start=DataStart,end=DataEnd))
        except:
            print('Could not get data for '+ticker+' from '+source+' using DataReader.')  
        else:
            print('Successfully pulled data for '+ticker+' from '+source+' using DataReader.') 
            break 
    return AssetData  

def GetIndiciiSame(data1,data2):   # Takes only pandas dataframe or series and gets them same length with same datetime index, padding nans.
    print('Running index resampler...',type(data1.index),type(data2.index))
    data1 = pd.DataFrame(data1); data2 = pd.DataFrame(data2)
    data1.set_index(pd.DatetimeIndex(data1.index),inplace=True)
    data2.set_index(pd.DatetimeIndex(data2.index),inplace=True)
    freq1 = data1.index.inferred_freq
    freq2 = data2.index.inferred_freq
    print('Series inferred frequencies, data1: ',freq1,', data2: ',freq2)
    #print(type(data1.index),type(data2.index),data1.index,data2.index)
    d1_start = data1.index[0]; d2_start = data2.index[0]
    d1_end = data1.index[len(data1)-1]; d2_end = data2.index[len(data2)-1]
    if len(data1) < len(data2):
        index = data2.index.to_list()
    else:
        index = data1.index.to_list()   
    if d1_start < d2_start:
        start_date = d1_start
    else:
        start_date = d2_start
    if d1_end < d2_end:
        end_date = d2_end
    else:
        end_date = d1_end
    index.insert(0,start_date); index.append(end_date)
    index = pd.DatetimeIndex(index)
    data1 = data1.reindex(index=index,method="ffill")
    data2 = data2.reindex(index=index,method="ffill")
    data1 = data1.resample('D').mean()
    data2 = data2.resample('D').mean()
    data1 = data1.squeeze(axis='columns'); data2 = data2.squeeze(axis='columns')
    data1.fillna(method='ffill',inplace=True)
    data2.fillna(method='ffill',inplace=True)
    data1.fillna(method='bfill',inplace=True)
    data2.fillna(method='bfill',inplace=True)
    print('Indexing function, datatypes: ',type(data1),type(data2)) 
    return data1, data2

def ReSampleToRefIndex(data,index,freq:str):   #This function will resample and reindex a series or dataframe to a given reference index. 
    #freq is the frequency of the reference index as str, e.g 'D' for daily, 'W' for weekly, 'M' monthly.
    if str(type(data)) ==  "<class 'pandas.core.series.Series'>":
        data =  pd.DataFrame(data); datType = 'series'
        pass
        #print('Data is series')
    elif str(type(data)) == "<class 'pandas.core.frame.DataFrame'>":
        data =  pd.DataFrame(data); datType = 'df'
        pass
        #print('This data is a dataframe.')
    else:
        print('We need input data to be a series or dataframe. Convert to that before using this ReSampleToRefIndex function.')
        return (data)
    if str(type(index)) ==  "<class 'pandas.core.indexes.datetimes.DatetimeIndex'>":
        pass
    else:
        print('This function needs a datetime index as a reference index. This index will not do, pulling out.')
        return (data) 
    index = pd.DatetimeIndex(index); index = index.drop_duplicates()
    data.reset_index(inplace=True); data.drop_duplicates(subset=data.columns[0],inplace=True)
    data.set_index(pd.DatetimeIndex(data.iloc[:,0]),inplace=True)
    data.drop(data.columns[0],axis=1,inplace=True)
    data = data.reindex(index=index)
    data = data.resample(freq).mean()
    data.fillna(method='ffill',inplace=True)
    data.fillna(method='bfill',inplace=True)
    if datType == 'series':
        data = pd.Series(data.squeeze())
    #print('Data after reindexing function, ',data.head(54))    
    return data

def pullyfseries(ticker,start:str="2020-01-01",interval="1d"):
    asset = yf.ticker.Ticker(ticker=ticker)
    PriceData = asset.history(period="1d",start=start,interval=interval)
    PriceData = pd.DataFrame(PriceData)
    if (interval == "1d"):
        ind = pd.DatetimeIndex(PriceData.index)
        PriceData.set_index(ind.date,inplace=True)
    return PriceData, ticker 

def Yahoo_Fin_PullData(Ticker, start_date = None, end_date = None): #Pull daily data for an asset using yahoo_fin web scraper
    data = si.get_data(Ticker,start_date = start_date, end_date = end_date) #Start date end date in YYYY-MM-DD str format. 
    data = data.resample('D').mean()
    data.fillna(method='pad',inplace=True)
    data.rename({"open":"Open","high":"High","low":"Low","close":"Close","adjclose":"AdjClose","volume":"Volume","ticker":"Ticker"},\
        axis=1,inplace=True)
    return data

##PriceAPI choices: "coingecko", "yfinance" or any from the pandas datareader:
#expected_source = ["yahoo","iex","iex-tops","iex-last","iex-last","bankofcanada","stooq","iex-book","enigma","fred","famafrench","oecd",\
        #"eurostat","nasdaq","quandl","moex","tiingo","yahoo-actions","yahoo-dividends","av-forex","av-forex-daily","av-daily","av-daily-adjusted",\
            #"av-weekly","av-weekly-adjusted","av-monthly","av-monthly-adjusted","av-intraday","econdb","naver"]
## Also tv for tradingview and alpha for alpha vantage. Still being developed.          

def PullDailyAssetData(ticker:str,PriceAPI:str,startDate:str,endDate:str=None):  ## This is my main data pulling function. 
    StartDate = datetime.datetime.strptime(startDate,"%Y-%m-%d").date()
    if endDate is not None:
        EndDate = datetime.datetime.strptime(endDate,"%Y-%m-%d").date()
    else:
        EndDate = datetime.date.today()
    TimeLength=(EndDate-StartDate).days
    print('Looking for data for ticker:',ticker,'using',PriceAPI,'for date range: ',StartDate,' to ',EndDate)
    AssetData = []

    if PriceAPI == 'coingecko':
        CoinID = getCoinID(ticker,InputTablePath=wd+FDel+'AllCG.xlsx')
        AssetData = CoinGeckoPriceHistory(CoinID[1],TimeLength=TimeLength) 
        AssetData.rename({"Price (USD)":"Close"},axis=1,inplace=True)
    elif PriceAPI == 'yfinance':
        try:
            asset = pullyfseries(ticker=ticker,start=StartDate,interval="1d")
            AssetData = asset[0]; AssetName = asset[1]
            if len(AssetData) < 1:
                print('No data for ',ticker,' scored using yfinance package, now trying yahoo_fin package....')
                AssetData = Yahoo_Fin_PullData(ticker, start_date = StartDate, end_date = EndDate)
            else:
                print("Data pulled from yfinance for: "+str(AssetName))    
        except:
            print("Could not score data for asset: "+ticker," from yfinance. Trying other APIs.") 
            print("Trying yahoo_fin web scraper.....")   
            AssetData = Yahoo_Fin_PullData(ticker, start_date = StartDate, end_date = EndDate)
        if len(AssetData) < 1: 
            AssetData = Yahoo_Fin_PullData(ticker, start_date = StartDate, end_date = EndDate) 
        if len(AssetData) < 1:     
            AssetData = DataReaderAllSources(ticker,DataStart=StartDate,end_date = EndDate) 
    elif  PriceAPI == 'tv': 
        split = ticker.split(',')
        ticker = (split[0],split[1]); print(ticker,type(ticker))
        if isinstance(ticker,tuple):
            symbol = ticker[0]; exchange = ticker[1]
            AssetData = DataFromTVDaily(symbol,exchange,start_date=StartDate,end_date=EndDate)
            AssetData.rename({'symbol':'Symbol','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'},axis=1,inplace=True)
            AssetData.drop('Symbol',axis=1,inplace=True)
            print('Data pulled from TV for: ',ticker,"\n")
        else:
            print('You should provide "ticker" as a tuple with (ticker,exchange) when using data from TV. Otherwise exchange will be "NSE" by default.')
            AssetData = DataFromTVDaily(ticker,start_date=StartDate,end_date=EndDate)    
            AssetData.rename({'symbol':'Symbol','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'},axis=1,inplace=True)
            AssetData.drop('Symbol',axis=1,inplace=True)
            print('Data pulled from TV for: ',ticker,"\n")
    else:
        try:        
            AssetData = pd.DataFrame(web.DataReader(ticker,PriceAPI,start=StartDate)) 
        except:
            print('Could not score data from '+str(PriceAPI)+', trying DataReader, all sources....')
            AssetData = DataReaderAllSources(ticker,DataStart=StartDate)
            print("Asset data pulled for "+str(ticker)+": ")   
    if len(AssetData) < 1: 
        print("Could not score data for asset: ",ticker," from any of the usual sources. Pulling out")  
    else:           
        return AssetData     

def YoYCalcFromDaily(series:pd.Series): 
    series = series.resample('D').mean()
    series.fillna(method='ffill',inplace=True) #This'l make it daily data even if weekly data is input. 
    YoYCalc = [np.nan for i in range(365)]
    for i in range(365,len(series),1):
        YoYCalc.append(((series[i]-series[i-365])/series[i-365])*100)
    YoYSeries = pd.Series(YoYCalc,index=series.index,name='YoY % change')    
    return YoYSeries   

def YoY4Monthly(series:pd.Series): #Input monthly data and get out monthly series.
    series = series.resample('M').mean()
    series.fillna(method='ffill',inplace=True) #This'l make it daily data even if weekly data is input. 
    YoYCalc = [np.nan for i in range(12)]
    for i in range(12,len(series),1):
        YoYCalc.append(((series[i]-series[i-12])/series[i-12])*100)
    YoYSeries = pd.Series(YoYCalc,index=series.index,name='YoY % change')    
    return YoYSeries        

def FREDSearch(search_text:str,apiKey:str,searchType:str="series_id"):
    myFredAPI_key = apiKey; fileType = "&file_type=json"
    if searchType == "series_id":
        searchType = "&search_type=series_id"
    search = "https://api.stlouisfed.org/fred/series/search?search_text="+search_text+searchType  
    r = requests.get(search+"&api_key="+myFredAPI_key+fileType)
    print(r.json())
    df = pd.json_normalize(r.json())
    df2 = pd.DataFrame.from_dict(df['seriess'][0])
    print(df2)
    return df2    

def DataFromTVDaily(symbol,exchange,start_date=datetime.date(2020,1,1),end_date=datetime.date.today()): 
    numBars = (end_date-start_date).days; print('Number of days of data for ',symbol,': ',numBars)
    tv = TvDatafeed()
    data = tv.get_hist(symbol,exchange,n_bars=numBars)
    return data

"""WORLD BANK API DATA STUFF. """
# print(wb.series.info(id="FM.LBL.BMNY.ZG"))
# print(wb.series.get(id="FM.LBL.BMNY.ZG")["value"])
# data = wb.data.DataFrame(series="FM.LBL.BMNY.ZG",economy='USA',time="all")
# print(data)
# # for query in QueryList:
# #     print(query)
# # Countries = wb.economy.list("all")
# # CountriesDF = wb.economy.DataFrame("all")
# SelectCountries = ["United Arab Emirates", "Argentina","Australia","Brazil","Canada","Chile","Japan","Hong Kong SAR, China","European Union",\
# "United Kingdom","India","Korea, Rep.","Mexico","Russian Federation","United States"]

""" OECD data pull in SDMX format """
#url = "https://stats.oecd.org/SDMX-JSON/data/MEI_FIN/MANM.AUS+CAN+CHL+COL+CZE+DNK+HUN+ISL+ISR+JPN+KOR+LVA+MEX+NZL+NOR+POL+SWE+CHE+TUR+GBR+USA+EA19+OECD+NMEC+BRA+CHN+IND+IDN+RUS+ZAF.M/all?startTime=1990&endTime=2022-12"
#https://stats.oecd.org/SDMX-JSON/data/MEI_FIN/MANM.AUS+CAN+CHL+COL+CZE+DNK+HUN+ISL+ISR+JPN+KOR+LVA+MEX+NZL+NOR+POL+SWE+CHE+TUR+GBR+USA+EA19+OECD+NMEC+BRA+CHN+IND+IDN+RUS+ZAF.M/all?startTime=2020-07&endTime=2022-11

# ecb = sdmx.Request('ecb')
# flow_msg = ecb.dataflow()
# print(flow_msg)
# dataflows = sdmx.to_pandas(flow_msg.dataflow)
# print(dataflows.head)
# StartDate = "2020-01-01"; EndDate = datetime.date.today()
# StartDate = datetime.datetime(2020,1,1)
# print(StartDate,EndDate)
# data = Yahoo_Fin_PullData("^GSPC", start_date = StartDate, end_date = EndDate)
# print(data)

