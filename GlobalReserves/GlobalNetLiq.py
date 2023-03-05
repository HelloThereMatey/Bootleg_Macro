import numpy as np
from numpy import NaN, ceil, floor
import pandas as pd
from datetime import timedelta
import datetime
import os
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
dir = os.path.dirname(wd)
print(wd,dir)
import sys ; sys.path.append(dir)
from MacroBackend import PriceImporter ## This is one of my custom scripts holding functions for pulling price data from APIs. Your IDE might not find it before running script. 
from sys import platform
import matplotlib.pyplot as plt

wd = os.path.dirname(os.path.realpath(__file__))
dir = os.path.dirname(wd)
if platform == "linux" or platform == "linux2":
    FDel = '/' # linux
elif platform == "darwin":
    FDel = '/' # OS X
elif platform == "win32":
    FDel = '\\' #Windows...

################ PullFX data to convert bal sheet data to USD  #############################################################################
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

    StartDate = datetime.datetime.strptime(Start,'%Y-%m-%d').date()    ## sTART AND END DATES FOR DATA. 
    if end is not None:
        EndDate = datetime.datetime.strptime(end,'%Y-%m-%d').date(); EndDateStr = end
    else:
        EndDate = datetime.date.today()
    print(StartDate,EndDate,type(StartDate),type(EndDate))    

    FXDataPath = dir+FDel+'GlobalReserves'+FDel+'FXData'+FDel+FXSymbol[1]+'.xlsx' ### Get FX data for currency pair.
    if os.path.isfile(FXDataPath):
        FXData = pd.read_excel(FXDataPath)
        print('FXData for '+FXSymbol[1]+', loaded from file.')
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(FXData['datetime']).date)
        FXData.set_index(dtIndex,inplace=True)
        FXData.drop('datetime',axis=1,inplace=True)
    else:  ##Get data if no file already containing the data exists in the right spot. 
        FXData = pd.DataFrame(PriceImporter.DataFromTVGen(FXSymbol[1],exchange=FXSymbol[0],start_date=StartDate,end_date=EndDate)) 
        FXData.to_excel(FXDataPath); print('FXData for '+FXSymbol[1]+', pulled from TV.')
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(FXData.index).date)
        FXData.set_index(dtIndex,inplace=True)
    
    FXData.fillna(method='ffill',inplace=True)
    FXData.dropna(inplace=True); FXData.index.rename('datetime',inplace=True) 
    LastDay = FXData.index[len(FXData)-1]; LastDay = LastDay.date()
    FirstDay = FXData.index[0]; FirstDay = FirstDay.date()  
    print(StartDate,FirstDay,EndDate,LastDay)

    if LastDay < EndDate or FirstDay > StartDate:
        print('FXData not up to date, pulling new data for '+FXSymbol[1]+' from TV......')
        NewFXData = pd.DataFrame(PriceImporter.DataFromTVGen(FXSymbol[1],exchange=FXSymbol[0],start_date=StartDate,end_date=EndDate))
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
        BSData = pd.DataFrame(PriceImporter.DataFromTVGen(TV_Code[1],exchange=TV_Code[0],start_date=StartDate,end_date=EndDate)) 
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
        NewBSData = pd.DataFrame(PriceImporter.DataFromTVGen(TV_Code[1],exchange=TV_Code[0],start_date=StartDate,end_date=LastDayBS))
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

    Index = FXData.index; CB_SeriesInfo = {}
    BSData_d = pd.Series(PriceImporter.ReSampleToRefIndex(BSData['close'],Index,freq='D'),name=SerName+' BS (bil. USD)')
    BSData_d = BSData_d[StartDate::]; FXData = FXData[StartDate::]
    if len(BSData_d.index.difference(FXData.index)) > 0 or len(FXData.index.difference(BSData_d.index)) > 0:
        BSData_d, FXData = PriceImporter.GetIndiciiSame(BSData_d,FXData)
    BSData_dUS = BSData_d*FXData['close'] #Convert to USD.
    BSData_dUS /= 10**9 #Convert to bilper cats. 
    BSData_dUS.fillna(method='ffill',inplace=True); BSData_dUS.dropna(inplace=True)
    BSData_dUS = pd.Series(BSData_dUS,name=SerName+' BS (bil. USD)')
    CB_SeriesInfo['units'] = 'Billions of U.S dollars'
    CB_SeriesInfo['units_short'] = 'Bil. of USD'
    CB_SeriesInfo['title'] = SerName+': Total Assets in USD worth'
    CB_SeriesInfo['id'] = SerName+' Assets (bil. USD)' 

    return BSData_dUS, CB_SeriesInfo, BSData, FXData

PBoC = GetCBAssets_USD("ECONOMICS,CNCBBS","FX_IDC,CNYUSD","2010-01-01",SerName='PBoC')
ECB = GetCBAssets_USD(",ECBASSETSW","FX,EURUSD","2010-01-01",SerName='ECB')
BoE = GetCBAssets_USD(",GBCBBS","FX,GBPUSD","2010-01-01",SerName='BoE')
BoJ = PriceImporter.GetBOJ_USD("f632119c4e0599a3229fec5a9ac83b1c","2010-01-01")

print(PBoC[0],ECB[0],BoE[0],BoJ[0])
PBoC_SI = PBoC[1]; ECB_SI = ECB[1]; BoE_SI = BoE[1]; BoJ_SI = BoJ[1]

fig = plt.figure()
ax = fig.add_subplot()
pboc = ax.plot(PBoC[0],label=PBoC_SI['id'])
ecb = ax.plot(ECB[0],label=ECB_SI['id'])
boe = ax.plot(BoE[0],label=BoE_SI['id'])
boj = ax.plot(BoJ[0],label=BoJ_SI['id'])
ax.legend()
plt.show()
