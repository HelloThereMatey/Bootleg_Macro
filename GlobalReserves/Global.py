####### Required modules/packages #####################################
import os
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
dir = os.path.dirname(wd)
print(wd,dir)
import sys ; sys.path.append(dir)
from MacroBackend import PriceImporter ## This is one of my custom scripts holding functions for pulling price data from APIs. Your IDE might not find it before running script. 
from MacroBackend import Charting    ##This script has all the matplotlib chart formatting code. That code is ugly, best to put it in a second file like this. 
## You may see: 'Import "MacroBackend" could not be resolved' & it looks like MacroBackend can't be found. However, it will be found when script is run. Disregard error. 
#### The below packages need to be installed via pip/pip3 on command line. These are popular, well vetted packages all. Just use 'pip install -r requirements.txt'
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
### These are standard python packages included in the latest python distributions. No need to install them. 
import datetime

if sys.platform == "linux" or sys.platform == "linux2":        #This detects what operating system you're using so that the right folder delimiter can be use for paths. 
    FDel = '/'; OpSys = 'linux'
elif sys.platform == "darwin":
    FDel = '/'; OpSys = 'mac'
elif sys.platform == "win32":
    FDel = '\\' ; OpSys = 'windows'
print('System information: ',sys.platform, OpSys,', directory delimiter: ', FDel, ', working directory: ', wd)
try:
    Inputs = pd.read_excel(wd+'/InputParams.xlsx')     ##Pull input parameters from the input parameters excel file. 
except Exception as e: 
    print(e)
    try:    
        Inputs = pd.read_excel(wd+'\\InputParams.xlsx')
    except Exception as e:
        print(e) 
        print("What you using bro? Windows mac or linux supported. If using something else, you'll just need to set the folder delimeter for all path references below.")    
        quit()
Inputs.set_index('Index',inplace=True);print(Inputs)     

########### Actual script starts from here down #######################################################################
myFredAPI_key = Inputs.loc['API Key'].at['Additional FRED Data']
SaveFREDData = Inputs.loc['SaveFREDData'].at['Additional FRED Data']
SaveJPNAss = Inputs.loc['SaveJPNAss'].at['Additional FRED Data']
print('FRED API key: ',myFredAPI_key,', Save FRED data to: ',str(wd+FDel+'FRED_Data'))
if pd.isna(SaveFREDData) is False:    #Optional save FRED series data to disk. 
    SaveFredData = True
else:
    SaveFredData = False   
if pd.isna(SaveJPNAss) is False:    
    SaveJPNUSD = True
else:
    SaveJPNUSD = False   

## Pull FRED series for net liquidity curve calculation ############# All the important parameters are set here. 
FredSeries = Inputs['Additional FRED Data'][0:5]; SeriesList = FredSeries.to_list()
print('FRED data series to pull: ',SeriesList) 

SeriesDict = {} #Code below gets the starting and ending dates for all data. 
DayOne = Inputs.loc['Start date'].at['Additional FRED Data']; LastDay = Inputs.loc['End date'].at['Additional FRED Data']
print('Data start from input file: ',DayOne,', end: ',LastDay)
if pd.isna(DayOne) is True:
    print('You must specify the starting date to pull data for in the inputs .xlsx file.')
    quit()
else:
    DataStart = str(DayOne)
    StartDate = datetime.datetime.strptime(DataStart,'%Y-%m-%d').date()
if pd.isna(LastDay) is True:
    EndDate = datetime.date.today(); EndDateStr = EndDate.strftime("%Y-%m-%d")
else:
    EndDateStr = str(LastDay)
    EndDate = datetime.datetime.strptime(EndDateStr,'%Y-%m-%d').date()
TimeLength=(EndDate-StartDate).days
print('Pulling data for date range: ',DataStart,' to ',EndDateStr,', number of days: ',TimeLength)
print('Start date:',StartDate,', end date: ',EndDate)

################ PullFX data if wanted #############################################################################
FXData = pd.read_excel(wd+FDel+'FXData'+FDel+'JPYUSD'+'.xlsx')
dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(FXData['datetime']).date)
FXData.set_index(dtIndex,inplace=True); FXData.drop('datetime',axis=1,inplace=True)
FXData = FXData[StartDate::]; FXData.fillna(method='ffill',inplace=True)
FXData.dropna(inplace=True)
print(FXData,FXData.index[0],FXData.index[len(FXData)-1])
LastDay = FXData.index[len(FXData)-1]; LastDay = LastDay.date()
if LastDay < datetime.date.today():
    print('FXData not up to date, pulling new data for JPYUSD from TV......')
    NewFXData = pd.DataFrame(PriceImporter.DataFromTVGen('JPYUSD',exchange='FX_IDC',start_date=StartDate,end_date=EndDate))
    dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(NewFXData.index).date)
    NewFXData.set_index(dtIndex,inplace=True)
    NewFXData.index.rename('Date',inplace=True)
    NewFXData = NewFXData[StartDate::]; NewFXData.fillna(method='ffill',inplace=True)
    NewFXData.dropna(inplace=True); NewFXData = NewFXData[LastDay::]
    print('FXData to add: ',NewFXData)
    FXData = pd.concat([FXData,NewFXData],axis=0)
FXData.index.rename('datetime',inplace=True)    
print(FXData,FXData.index[0],FXData.index[len(FXData)-1]) 
FXData.to_excel(wd+FDel+'FXData'+FDel+'JPYUSD'+'.xlsx')

BOJAss = pd.read_excel(wd+FDel+'FRED_Data'+FDel+'JPNASSETS'+'.xlsx',sheet_name='Data')
BOJAss.set_index('date',inplace=True); BOJAss = pd.Series(BOJAss.squeeze())
BOJAss.fillna(method='ffill',inplace=True); BOJAss.dropna(inplace=True)
BOJLastDay = BOJAss.index[len(BOJAss)-1]; BOJLastDay = BOJLastDay.date()
print(BOJAss,BOJAss.index[0],BOJAss.index[len(BOJAss)-1])

if BOJLastDay < datetime.date.today():
    DPStart = BOJLastDay.strftime('%Y-%m-%d')
    ############# Pull data from FRED. ###########################################
    DataPull = PriceImporter.PullFredSeries("JPNASSETS",myFredAPI_key,start=DPStart,end=EndDateStr)
    NewData = pd.DataFrame(DataPull[1]); print(NewData,type(NewData.index))
    dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(NewData.index).date)
    NewData.set_index(dtIndex,inplace=True); print(NewData)
    LastPoint = NewData.index[len(NewData)-1]; LastPoint = LastPoint.date()
    if LastPoint > BOJLastDay: 
        print('New data available for JPNASSETS from FRED')
        BOJAss = pd.Series(pd.concat([BOJAss,NewData],axis=0))
        BOJAss.to_excel(wd+FDel+'FRED_Data'+FDel+'JPNASSETS'+'.xlsx',sheet_name='Data')
BOJAss = BOJAss[StartDate:EndDate]
print(BOJAss,type(BOJAss.index))
SeriesInfo = pd.read_excel(wd+FDel+'FRED_Data'+FDel+'JPNASSETS'+'.xlsx',sheet_name='SeriesInfo')
SeriesInfo.set_index('Unnamed: 0',inplace=True); SeriesInfo = pd.Series(SeriesInfo.squeeze())
print(SeriesInfo)
Index = FXData.index
BOJAss_d = pd.Series(PriceImporter.ReSampleToRefIndex(BOJAss,Index,freq='D'))
BOJAss_d *= 100000000. #Convert to Yen.
BOJAss_dUS = BOJAss_d*FXData['close'] #Convert to USD.
BOJAss_dUS /= 10**9 #Convert to bilper cats. 
BOJAss_dUS.fillna(method='ffill',inplace=True); BOJAss_dUS.dropna(inplace=True)
SeriesInfo_US = SeriesInfo.copy()
SeriesInfo_US['units'] = 'Billions of U.S dollaridoos'
SeriesInfo_US['units_short'] = 'Billlions of USD'
SeriesInfo_US['title'] = 'Bank of Japan: Total Assets in USD worth'
SeriesInfo_US['id'] = 'BOJ Assets (USD)'
if SaveJPNUSD is True:
    BOJAss_dUS.to_excel(wd+FDel+'FRED_Data'+FDel+'JPNASSETS_USD'+'.xlsx')

fig1 = Charting.FedFig(BOJAss,SeriesInfo,RightSeries=FXData['close'],rightlab='Yen (USD)',LYScale="log",RYScale="log",CustomXAxis=True)
fig2 = Charting.FedFig(BOJAss_dUS,SeriesInfo_US,LYScale="log",CustomXAxis=True)
plt.show()