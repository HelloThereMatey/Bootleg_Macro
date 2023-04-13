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
from .tvDatafeedz import TvDatafeed, Interval #This package 'tvDatafeed' is not available through pip, ive included in the project folder. 
import os
from sys import platform
import re

wd = os.path.dirname(os.path.realpath(__file__))
dir = os.path.dirname(wd)
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
    print('Running index resampler...',type(data1.index),type(data2.index),len(data1.index),len(data2.index))
    data1 = pd.DataFrame(data1); data2 = pd.DataFrame(data2)
    data1.reset_index(inplace=True); data2.reset_index(inplace=True)
    data1.drop_duplicates(subset=data1.columns[0],inplace=True); data2.drop_duplicates(subset=data2.columns[0],inplace=True)
    data1.set_index(pd.DatetimeIndex(data1[data1.columns[0]]),inplace=True)
    data2.set_index(pd.DatetimeIndex(data2[data2.columns[0]]),inplace=True)
    data1.drop(data1.columns[0],axis=1,inplace=True); data2.drop(data2.columns[0],axis=1,inplace=True)
    freq1 = data1.index.inferred_freq; freq2 = data2.index.inferred_freq
    print('Series inferred frequencies, data1: ',freq1,', data2: ',freq2)
    #print('Resampling function, index differentials',data1.index.difference(data2.index),data2.index.difference(data1.index))
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
    index = pd.DatetimeIndex(pd.DatetimeIndex(index).date)
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
    print('Looking for data for ticker:',ticker,'using',PriceAPI,'for date range: ',StartDate,' to ',EndDate,type(StartDate),type(EndDate))
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
        if len(split) > 1:
            ticker = (split[0],split[1]); print(ticker,type(ticker))
        else:
            pass
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
        AssetData = AssetData[StartDate:EndDate]         
        return AssetData     

def YoYCalcFromDaily(series:pd.Series): 
    print('\nYoY calcuation on series: ',series.name,', data frequency: ',pd.infer_freq(series.index))
    if series.index.inferred_freq != 'D':
        print('Resampling',series.name,'to daily frequency for YoY calculation....')
        series = series.resample('D').mean()
        series.fillna(method='ffill',inplace=True) #This'l make it daily data even if weekly data is input. 
    YoYCalc = [np.nan for i in range(len(series))]
    YoYSeries = pd.Series(YoYCalc,index=series.index,name=series.name+' YoY % change')
    for i in range(365,len(series),1):
        YoYSeries.iloc[i] = (((series[i]-series[i-365])/series[i-365])*100)
    #print('After YoY calc: ',YoYSeries.tail(54),len(YoYSeries))        
    return YoYSeries   

def YoY4Monthly(series:pd.Series): #Input monthly data and get out monthly series.
    series.fillna(method='ffill',inplace=True)
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

def DataFromTVDaily(symbol,exchange='NSE',start_date=datetime.date(2020,1,1),end_date=datetime.date.today()): 
    numBars = (end_date-start_date).days; print('Number of days of data for ',symbol,': ',numBars)
    tv = TvDatafeed()
    data = tv.get_hist(symbol,exchange,n_bars=numBars)
    return data

def DataFromTVGen(symbol,exchange='NSE',start_date=datetime.date(2020,1,1),end_date=datetime.date.today(),BarTimeFrame='daily'): 
    numDays = (end_date-start_date).days; print('Number of days of data for ',symbol,': ',numDays)
    tv = TvDatafeed()
    if BarTimeFrame == 'daily':
        TimeFrame = Interval.in_daily; numBars = numDays
    elif BarTimeFrame == 'weekly':
        TimeFrame = Interval.in_weekly; numBars = ceil(numDays/7)
    elif BarTimeFrame == 'monthly':
        TimeFrame = Interval.in_monthly; numBars = ceil(numDays/30)
    elif BarTimeFrame == '4hr':
        TimeFrame = Interval.in_4_hour; numBars = numDays*6
    elif BarTimeFrame == 'hr':
        TimeFrame = Interval.in_1_hour; numBars = numDays*24
    data = tv.get_hist(symbol,exchange,interval=TimeFrame,n_bars=numBars)
    return data

###### Functions ###############################################################################################################################################

def Correlation(Series1:pd.Series, Series2:pd.Series,period='Full'): #Calculate Pearson Correlation co-efficient between two series with time frame: period. 
    if (period=='Full'):
        Cor = round(Series1.corr(other=Series2,method='pearson', min_periods=len(Series1)),3)
        try:
            print('The correlation over the entire length between the two series: '+Series1.name+' and '+Series2.name+' is: '+str(round(Cor,3))+'.')
        except:
            pass    
    else:
        Cor = Series1.rolling(period).corr(Series2) ##Using Pandas to calculate the correlation. 
        #print('Correlation sub-function, data series: ',Cor, type(Cor))
    return Cor 

def PullFredSeries(series:str,apikey:str,start="1776-07-04",filetype="&file_type=json",outputDataName:str=None,end=datetime.date.today().strftime('%Y-%m-%d')): 
    series_header = "https://api.stlouisfed.org/fred/series?series_id="      ##This pulls data series from FRED API. 
    r = requests.get(series_header+series+"&observation_start="+start+"&api_key="+apikey+filetype)
    df = pd.json_normalize(r.json())
    df2 = pd.DataFrame.from_dict(df['seriess'][0]); df2 = df2.T
    df2 = df2.squeeze()
    SeriesInfo = pd.Series(df2,name=series)
    
    series_data = "https://api.stlouisfed.org/fred/series/observations?series_id="  
    r = requests.get(series_data+series+"&observation_start="+start+"&api_key="+apikey+filetype)
    df = pd.json_normalize(r.json())
    df2 = pd.DataFrame.from_dict(df['observations'][0])
    dateIndex = pd.DatetimeIndex(df2['date'])
    df2.set_index(dateIndex,inplace=True)
    dfraw = df2
    remove = {'.':np.nan, '/':np.nan, ']':np.nan} 
    df2['value'] = df2['value'].replace(remove)
    df2.dropna(inplace=True)
    #df2 = df2[df2.index.duplicated(keep='first')]
    TheData = pd.Series(df2['value'].astype(float),name=series)
    #print('Units info for series: ',TheData.name,'Units:',SeriesInfo['units'],'#')
    units = SeriesInfo['units']
    
    if re.search('Millions',units) is not None:
        TheData /= 1000 
        #print(series+' pulled from FRED. Data divided by 1000 to make units of Billions $ from original units of ',units)
    elif re.search('Billions',units) is not None:
        #print(series+' pulled from FRED. Data divided by 1 to make units of Billions $ from original units of ',units)
        pass
    elif re.search('Thousands',units) is not None:
        TheData /= 1000000
        #print(series+' pulled from FRED. Data divided by 100000 to make units of Billions $ from original units of ',units)
    elif re.search('Trillions',units) is not None: 
        TheData *= 1000
        #print(series+' pulled from FRED. Data multiplied by 1000 to make units of Billions $ from original units of ',units)
    else: 
        print('CAUTION: Data units: ',SeriesInfo['units'],'are not standard for this calc, units may be incorrect.')
    if outputDataName is not None:
        df2.to_excel(wd+FDel+outputDataName+".xlsx")
        #dfraw.to_excel(wd+FDel+outputDataName+"_raw.xlsx")
    endDate = datetime.datetime.strptime(end,'%Y-%m-%d'); startChart = datetime.datetime.strptime(start,'%Y-%m-%d')
    TheData = TheData[startChart:endDate]    
    return SeriesInfo, TheData    

def PullTGA_Data(AccountName = 'Federal Reserve Account',start_date='2000-01-01') -> pd.DataFrame:
    urlBase = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service'
    TrGenAccBal = '/v1/accounting/dts/dts_table_1'
    fields = '?fields=record_date,account_type,close_today_bal,open_today_bal,open_month_bal'
    filters = '&filter=record_date:gte:'+start_date

    FullData = pd.DataFrame(); exceptions = 0
    for i in range(10000):
        if i > 0:
            LastSetFinDay = LastDay
        if i == 0:
            url = urlBase+TrGenAccBal+fields+filters
        elif NextDSStart >= datetime.date.today():
            break    
        else:
            filt = '&filter=record_date:gte:'+NextDSStarT
            url = urlBase+TrGenAccBal+fields+filt
        try:
            r = requests.get(url)
            if r.status_code != 200:
                print("Couldn't pull data from this date: ",NextDSStarT)
                continue
            df = pd.json_normalize(r.json())
            data = pd.json_normalize(df['data'][0])
            if len(data) < 1:
                break
            df.drop('data',axis=1,inplace=True)
            MetaData = df.T
            data.set_index('record_date',inplace=True)
            extracted = data[data['account_type'] == AccountName]
            TheData = extracted.sort_index()
            #print(TheData)
            DayOne = datetime.datetime.strptime(TheData.index[0],'%Y-%m-%d').date()
            LastDay = datetime.datetime.strptime(TheData.index[len(TheData)-1],'%Y-%m-%d').date()
            NextDSStart = LastDay + datetime.timedelta(days=1); NextDSStarT = str(NextDSStart) 
            EndDateStr = TheData.index[len(TheData)-1]; print('Will start next dataset pull at: ',NextDSStart)
            DateDiff = LastDay - DayOne
            print('\nData from: ',DayOne,type(DayOne),' to ',LastDay,type(LastDay),'. DataLength: ',len(TheData),'TimeDelta (days): ',DateDiff.days)
            FullData= pd.concat([FullData,TheData],axis=0)
            if i > 0 and LastSetFinDay == LastDay:
                break
        except Exception as e: 
            print(e)
            print('Exception, may be at end of data or those cunts changed the names in the table or sumtin, have a few more tries & then pull out.')
            exceptions += 1  
        if exceptions > 5: 
            print('Enuff of dis shit...')
            break    
            
    return FullData

def AssCorr(series1:pd.Series, series2:pd.Series,periodsList:list, SaveDatas: str = None):    #This calculates the pearson correlation coefficient for two given series. 
    if (len(series1.index.difference(series2.index))) > 0:
        series1,series2 = GetIndiciiSame(series1,series2)
    elif (len(series2.index.difference(series1.index))) > 0:
        series2,series1 = GetIndiciiSame(series2,series1)
    else:
        pass    
    if SaveDatas is not None:       #This function implements the correlation function on 
        output = pd.concat([series1,series2],axis=1)
        output.to_excel(SaveDatas+".xlsx")
    CorrDict = {}
    for period in periodsList:
        CorrDict["CC_"+str(period)+r"$_{day}$"] = Correlation(series1,series2,period=period) 
    #print('Correlation master function: ',CorrDict)    
    Correlations = pd.DataFrame(CorrDict)  
    return Correlations, Correlation(series1,series2)  

################ PullFX data if wanted #############################################################################
### This gets data for the BOJ balance sheet from trading view. Returns a series of BOJ bal. sheet in USD as well as raw data. 
def GetBOJ_USD(apiKey,Start:str,end:str=None):
    StartDate = datetime.datetime.strptime(Start,'%Y-%m-%d').date()
    if end is not None:
        EndDate = datetime.datetime.strptime(end,'%Y-%m-%d').date(); EndDateStr = end
    else:
        EndDate = datetime.date.today(); EndDateStr = EndDate.strftime('%Y-%m-%d')
    
    try:
        FXData = pd.read_excel(dir+FDel+'GlobalReserves'+FDel+'FXData'+FDel+'JPYUSD'+'.xlsx')
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(FXData['datetime']).date)
        FXData.set_index(dtIndex,inplace=True); FXData.drop('datetime',axis=1,inplace=True)
    except:
        FXData = pd.DataFrame(DataFromTVGen('JPYUSD',exchange='FX_IDC',start_date=StartDate,end_date=EndDate))
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(FXData.index).date)
        FXData.set_index(dtIndex,inplace=True)
    
    FXData = FXData[StartDate::]; FXData.fillna(method='ffill',inplace=True)
    FXData.dropna(inplace=True); FXData.index.rename('datetime',inplace=True) 
    LastDay = FXData.index[len(FXData)-1]; LastDay = LastDay.date()
    FirstDay = FXData.index[0]; FirstDay = FirstDay.date()
    if LastDay < datetime.date.today() or FirstDay > StartDate:
        print('FXData not up to date, pulling new data for JPYUSD from TV......')
        NewFXData = pd.DataFrame(DataFromTVGen('JPYUSD',exchange='FX_IDC',start_date=StartDate,end_date=EndDate))
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(NewFXData.index).date)
        NewFXData.set_index(dtIndex,inplace=True)
        NewFXData.index.rename('Date',inplace=True)
        NewFXData = NewFXData[StartDate::]
        NewFXData.fillna(method='ffill',inplace=True)
        NewFXData.dropna(inplace=True)
        FXData = NewFXData
        FXData.index.rename('datetime',inplace=True)    
        FXData.to_excel(dir+FDel+'GlobalReserves'+FDel+'FXData'+FDel+'JPYUSD'+'.xlsx')
        #print('FXData to add: ',NewFXData)

    try:
        BOJAss = pd.read_excel(dir+FDel+'GlobalReserves'+FDel+'FRED_Data'+FDel+'JPNASSETS'+'.xlsx',sheet_name='Data')
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(BOJAss['Unnamed: 0']).date)
        BOJAss.set_index(dtIndex,inplace=True); BOJAss.drop('Unnamed: 0',axis=1,inplace=True)
    except:
        DataPull = PullFredSeries("JPNASSETS",apiKey,start=Start,end=EndDateStr)
        BOJAss  = pd.DataFrame(DataPull[1]) 
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(BOJAss.index).date)
        BOJAss.set_index(dtIndex,inplace=True)

    BOJAss = pd.Series(BOJAss.squeeze(),name='BOJ Assets')
    BOJAss.fillna(method='ffill',inplace=True); BOJAss.dropna(inplace=True)
    BOJLastDay = BOJAss.index[len(BOJAss)-1]; BOJLastDay = BOJLastDay.date()
    BOJFirstDay = BOJAss.index[0]; BOJFirstDay = BOJFirstDay.date()

    if BOJLastDay < datetime.date.today() or BOJFirstDay > StartDate:
        DPStart = BOJLastDay.strftime('%Y-%m-%d')
        ############# Pull data from FRED. ###########################################
        DataPull = PullFredSeries("JPNASSETS",apiKey,start=Start,end=EndDateStr)
        NewData = pd.DataFrame(DataPull[1])
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(NewData.index).date)
        NewData.set_index(dtIndex,inplace=True)
        LastPoint = NewData.index[len(NewData)-1]; LastPoint = LastPoint.date()
        FirstPoint = NewData.index[0]; FirstPoint = FirstPoint.date()
        if LastPoint > BOJLastDay: 
            print('New data available for JPNASSETS from FRED')
            BOJAss = pd.Series(pd.concat([BOJAss,NewData],axis=0))
            BOJAss.to_excel(dir+FDel+'GlobalReserves'+FDel+'FRED_Data'+FDel+'JPNASSETS'+'.xlsx',sheet_name='Data')
    BOJAss = BOJAss[StartDate:EndDate]
    Index = FXData.index; SeriesInfo_US = {}
    BOJAss_d = pd.Series(ReSampleToRefIndex(BOJAss,Index,freq='D'),name='BOJ bal. sheet (bil. USD)')
    BOJAss_d *= 100000000. #Convert to Yen.
    BOJAss_dUS = BOJAss_d*FXData['close'] #Convert to USD.
    BOJAss_dUS /= 10**9 #Convert to bilper cats. 
    BOJAss_dUS.fillna(method='ffill',inplace=True); BOJAss_dUS.dropna(inplace=True)
    BOJAss_dUS = pd.Series(BOJAss_dUS,name='BoJ BS (bil. USD)')
    SeriesInfo_US['units'] = 'Billions of U.S dollaridoos'
    SeriesInfo_US['units_short'] = 'Billlions of USD'
    SeriesInfo_US['title'] = 'Bank of Japan: Total Assets in USD worth'
    SeriesInfo_US['id'] = 'BOJ Assets (USD)' 
    return BOJAss_dUS, SeriesInfo_US, BOJAss, FXData

############### PullFX data to convert bal sheet data to USD  #############################################################################
### This gets data for a CB balance sheet from trading view. Returns a series of CB bal. sheet in USD as well as the raw data. 
## Needs FRED apikey. Doesn't need TV account. ## Data pulled from TV using TVDataFeed so need it as a tuple like input: Exchange,Symbol 
# e.g "ECONOMICS,CNCBBS" for PBoC bal  sheet and "FX_IDC,CNYUSD" for CNYUSD. Put them in a string though. 

def GetCBAssets_USD(TV_Code,FXSymbol,Start:str,end:str=None,SerName:str=""):
    split = TV_Code.split(',')  ## Split the input string into exchange and asset symbol to get the DATA FROM tv. 
    if len(split) > 1:
        TV_Code = (split[0],split[1])
    else:
        print("Data symbol for CB bal sheet to pull from TV must be formatted as a str with 'exchange,ticker' format.")
        quit()
    split = FXSymbol.split(',')
    if len(split) > 1:
        FXSymbol = (split[0],split[1])
    else:
        print("Data symbol for FX pair data to pull from TV must be formatted as a str with 'exchange,ticker' format.")
        quit()    
    print(TV_Code,FXSymbol)

    StartDate = datetime.datetime.strptime(Start,'%Y-%m-%d').date() ## sTART AND END DATES FOR DATA. 
    print('Get CB data function, start date: ',StartDate,type(StartDate))
    StartDate
    if end is not None:
        EndDate = datetime.datetime.strptime(end,'%Y-%m-%d').date(); EndDateStr = end
    else:
        EndDate = datetime.date.today()   

    FXDataPath = dir+FDel+'GlobalReserves'+FDel+'FXData'+FDel+FXSymbol[1]+'.xlsx' ### Get FX data for currency pair.
    if os.path.isfile(FXDataPath):
        FXData = pd.read_excel(FXDataPath)
        print('FXData for '+FXSymbol[1]+', loaded from file.')
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(FXData['datetime']).date)
        FXData.set_index(dtIndex,inplace=True)
        FXData.drop('datetime',axis=1,inplace=True)
    else:  ##Get data if no file already containing the data exists in the right spot. 
        FXData = pd.DataFrame(DataFromTVGen(FXSymbol[1],exchange=FXSymbol[0],start_date=StartDate,end_date=EndDate)) 
        FXData.to_excel(FXDataPath); print('FXData for '+FXSymbol[1]+', pulled from TV.')
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(FXData.index).date)
        FXData.set_index(dtIndex,inplace=True)
    
    FXData.fillna(method='ffill',inplace=True)
    FXData.dropna(inplace=True); FXData.index.rename('datetime',inplace=True) 
    LastDay = FXData.index[len(FXData)-1]; LastDay = LastDay.date()
    FirstDay = FXData.index[0]; FirstDay = FirstDay.date()  
    print('CB data start and end dates: ',StartDate,FirstDay,EndDate,LastDay)

    if LastDay < EndDate or FirstDay > StartDate:
        print('FXData not up to date, pulling new data for '+FXSymbol[1]+' from TV......')
        NewFXData = pd.DataFrame(DataFromTVGen(FXSymbol[1],exchange=FXSymbol[0],start_date=StartDate,end_date=EndDate))
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(NewFXData.index).date)
        NewFXData.set_index(dtIndex,inplace=True)
        NewFXData.index.rename('datetime',inplace=True)
        NewFXData.fillna(method='ffill',inplace=True)
        NewFXData.dropna(inplace=True) 
        if FirstDay > StartDate:
            FXData = NewFXData
        else:
            NewFXData = NewFXData[LastDay::]
            print('FXData to add: ',NewFXData)  
        FXData = pd.concat([FXData,NewFXData],axis=0)
        FXData.to_excel(FXDataPath)
    
    print('FX Data: ',FXData)
 
    BSDataPath = dir+FDel+'GlobalReserves'+FDel+'BalSheets'+FDel+TV_Code[1]+'.xlsx'
    if os.path.isfile(BSDataPath):
        BSData = pd.read_excel(BSDataPath)
        print('Bal sheet Data for '+TV_Code[1]+', loaded from file.')
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(BSData['datetime']).date)
        BSData.set_index(dtIndex,inplace=True)
        BSData.drop('datetime',axis=1,inplace=True)
    else:  ##Get data if no file already containing the data exists in the right spot. 
        BSData = pd.DataFrame(DataFromTVGen(TV_Code[1],exchange=TV_Code[0],start_date=StartDate,end_date=EndDate)) 
        BSData.to_excel(BSDataPath); print('Bal sheet for '+TV_Code[1]+', pulled from TV.')
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(BSData.index).date)
        BSData.set_index(dtIndex,inplace=True)

    BSData.fillna(method='ffill',inplace=True)
    BSData.dropna(inplace=True); BSData.index.rename('datetime',inplace=True) 
    LastDayBS = BSData.index[len(BSData)-1]; LastDayBS = LastDayBS.date()
    FirstDayBS = BSData.index[0]; FirstDayBS = FirstDayBS.date()  
    print(StartDate,FirstDayBS,EndDate,LastDayBS) 

    if LastDayBS < EndDate or FirstDayBS > StartDate:
        print('BSData not up to date, pulling new data for '+TV_Code[1]+' from TV......')
        NewBSData = pd.DataFrame(DataFromTVGen(TV_Code[1],exchange=TV_Code[0],start_date=StartDate,end_date=LastDayBS))
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(NewBSData.index).date)
        NewBSData.set_index(dtIndex,inplace=True)
        NewBSData.index.rename('datetime',inplace=True)
        NewBSData.fillna(method='ffill',inplace=True); NewBSData.dropna(inplace=True) 
        if FirstDayBS > StartDate:
            BSData = NewBSData
        else:
            NewBSData = NewBSData[LastDayBS::]
            print('FXData to add: ',NewBSData)  
        BSData = pd.concat([BSData,NewBSData],axis=0)
        BSData.to_excel(BSDataPath)

    StartDay = pd.to_datetime(StartDate)
    #FXData.resample('D').mean(); FXData.fillna(method='ffill')
    Index = FXData.index.drop_duplicates(); CB_SeriesInfo = {} 
    
    BSData_d = pd.Series(ReSampleToRefIndex(BSData['close'],Index,freq='D'),name=SerName+' BS (bil. USD)')
    BSData_d = BSData_d[BSData_d.index.drop_duplicates()]
    BSData_d = BSData_d[StartDate::] 
    date = FXData.index.searchsorted(StartDay); print('This the first day?',date)
    FXData = FXData[date::]

    if len(BSData_d.index.difference(FXData.index)) > 0 or len(FXData.index.difference(BSData_d.index)) > 0:
        BSData_d, FXData = GetIndiciiSame(BSData_d,FXData)
    BSData_dUS = BSData_d*FXData['close'] #Convert to USD.
    BSData_dUS /= 10**9 #Convert to bilper cats. 
    BSData_dUS.fillna(method='ffill',inplace=True); BSData_dUS.dropna(inplace=True)
    BSData_dUS = pd.Series(BSData_dUS,name=SerName+' BS (bil. USD)')
    CB_SeriesInfo['units'] = 'Billions of U.S dollars'
    CB_SeriesInfo['units_short'] = 'Bil. of USD'
    CB_SeriesInfo['title'] = SerName+': Total Assets in USD worth'
    CB_SeriesInfo['id'] = SerName+' Assets (bil. USD)' 

    return BSData_dUS, CB_SeriesInfo, BSData, FXData


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

