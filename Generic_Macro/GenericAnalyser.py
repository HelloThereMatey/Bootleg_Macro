###### Required modules/packages #####################################
import os
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
dir = os.path.dirname(wd)
print(wd,dir)
import sys; sys.path.append(dir)
from MacroBackend import PriceImporter ## This is one of my custom scripts holding functions for pulling price data from APIs. Your IDE might not find it before running script. 
from MacroBackend import Charting    ##This script has all the matplotlib chart formatting code. That code is ugly, best to put it in a second file like this. 

## You may see: 'Import "MacroBackend" could not be resolved' & it looks like MacroBackend can't be found. However, it will be found when script is run. Disregard error. 
#### The below packages need to be installed via pip/pip3 on command line. These are popular, well vetted packages all. Just use 'pip install -r requirements.txt'
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter
### These are standard python packages included in the latest python distributions. No need to install them. 
import datetime
import re 

if sys.platform == "linux" or sys.platform == "linux2":        #This detects what operating system you're using so that the right folder delimiter can be use for paths. 
    FDel = '/'; OpSys = 'linux'
elif sys.platform == "darwin":
    FDel = '/'; OpSys = 'mac'
elif sys.platform == "win32":
    FDel = '\\' ; OpSys = 'windows'
print('System information: ',sys.platform, OpSys,', directory delimiter: ', FDel, ', working directory: ', wd)

try:
    Inputs = pd.read_excel(wd+'/Control.xlsx')     ##Pull input parameters from the input parameters excel file. 
except Exception as e: 
    print(e)
    try:    
        Inputs = pd.read_excel(wd+'\\Control.xlsx')
    except Exception as e:
        print(e) 
        print("Check InputParams excel file. If name has been changed from  'NetLiquidity_InputParams.xlsx', or is not there, that is the problem.\
              Issue could also be non-standard OS. If using an OS other than windows, mac or linux you'll just need to set the folder delimeter for all path references below.")    
        quit()
Inputs.set_index('Index',inplace=True)

NoString = 'no'
myFredAPI_key = Inputs.loc['FRED_Key'].at['Series_Ticker']

DayOne = Inputs.loc['StartDate'].at['Series_Ticker']; LastDay = Inputs.loc['EndDate'].at['Series_Ticker']
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

SeriesDict = {}
for i in range(1,6):
    ticker = Inputs.loc[i].at['Series_Ticker']
    if pd.isna(ticker):
        pass
    else:
        source = Inputs.loc[i].at['Source']; type = Inputs.loc[i].at['UnitsType']
        color = Inputs.loc[i].at['TraceColor']; label = Inputs.loc[i].at['Legend_Name']; name = Inputs.loc[i].at['Name']
        axis = Inputs.loc[i].at['Axis']; yscale = Inputs.loc[i].at['Yaxis']; Ymax = Inputs.loc[i].at['Ymax']; resample = Inputs.loc[i].at['Resample2D']
        SeriesDict[name] = {'Ticker': ticker, 'Source': source, 'UnitsType': type, 'TraceColor': color, 'Legend_Name': label, 'Name': name, 'Axis': axis,\
                            'YScale': yscale,'Ymax': Ymax, 'Resample2D': resample} 
        SeriesList = Inputs['Series_Ticker'].copy(); SeriesList = SeriesList[0:5]; SeriesList.dropna(inplace=True); numSeries = len(SeriesList)  
        Axii = Inputs['Axis'].copy(); Axii.dropna(inplace=True); Axii = Axii.unique() ;numAxii = len(Axii)
print('Number of data series: ',numSeries,'Number of axii on chart: ',numAxii)
        
DataPath = wd+FDel+'SavedData'
for series in SeriesDict.keys():
    TheSeries = SeriesDict[series]; Source = TheSeries['Source']; ticker = TheSeries['Ticker']; SeriesInfo = pd.Series()
    ticker = str(ticker); split = ticker.split(','); print("Ticker at first split:",split,len(split))
    if len(split) > 1:
        ticker = (split[0],split[1])
        symbol = split[0]; exchange = split[1]; ticker = split[0]; print('ticker after split',ticker)
    else:
        pass
    
    if Source == 'load':
        SeriesInfo = pd.read_excel(DataPath+FDel+ticker+'.xlsx',sheet_name='SeriesInfo')
        SeriesInfo.set_index(SeriesInfo[SeriesInfo.columns[0]],inplace=True)
        SeriesInfo.drop(SeriesInfo.columns[0],axis=1,inplace=True); SeriesInfo.index.rename('Property',inplace=True)
        SeriesInfo = pd.Series(SeriesInfo.squeeze(),name='Value')
        TheData = pd.read_excel(DataPath+FDel+ticker+'.xlsx',sheet_name='Closing_Price')
        TheData.set_index(TheData[TheData.columns[0]],inplace=True); TheData.index.rename('date',inplace=True)
        TheData.drop(TheData.columns[0],axis=1,inplace=True)
        TheData = pd.Series(TheData.squeeze(),name=ticker)
        OtherInfo = pd.read_excel(DataPath+FDel+ticker+'.xlsx',sheet_name='OtherInfo')
        OtherInfo.set_index(OtherInfo[OtherInfo.columns[0]],inplace=True)
        OtherInfo.drop(OtherInfo.columns[0],axis=1,inplace=True)
        OtherInfo = pd.Series(OtherInfo.squeeze())
        dicton = OtherInfo.to_dict()
        #TheSeries = dicton.copy()
                                            
    elif Source == 'fred':
        SeriesInfo, TheData = PriceImporter.PullFredSeries(ticker,myFredAPI_key,start=DataStart,filetype="&file_type=json",end=EndDateStr)
        AssetName = SeriesInfo['id']
    elif Source == 'yfinance':
        try:
            asset = PriceImporter.pullyfseries(ticker=ticker,start=StartDate,interval="1d")
            TheData = asset[0]; AssetName = asset[1]
            if len(TheData) < 1:
                print('No data for ',ticker,' scored using yfinance package, now trying yahoo_fin package....')
                TheData = PriceImporter.Yahoo_Fin_PullData(ticker, start_date = StartDate, end_date = EndDate)
                TheData = pd.Series(TheData['Close'],name=TheSeries['Name'])
            else:
                print("Data pulled from yfinance for: "+str(AssetName))    
        except:
            print("Could not score data for asset: "+ticker," from yfinance. Trying other APIs.") 
            print("Trying yahoo_fin web scraper.....")   
            TheData = PriceImporter.Yahoo_Fin_PullData(ticker, start_date = StartDate, end_date = EndDate)   
            TheData = pd.Series(TheData['Close'],name=TheSeries['Name'])     
    elif  Source == 'tv': 
        TheData = pd.DataFrame(PriceImporter.DataFromTVDaily(symbol,exchange,start_date=StartDate,end_date=EndDate))
        dtIndex = pd.DatetimeIndex(pd.DatetimeIndex(TheData.index).date)
        TheData.rename({'symbol':'Symbol','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'},axis=1,inplace=True)
        TheData.drop('Symbol',axis=1,inplace=True)
        TheData.set_index(dtIndex,inplace=True); TheData = TheData[StartDate:EndDate]
        TheData = pd.Series(TheData['Close'],name=TheSeries['Name'])
        TheData = TheData.resample('D').mean(); TheData.fillna(method='ffill',inplace=True)
        TheSeries['Ticker'] = ticker
        print('Data pulled from TV for: ',ticker,"\n")
    elif Source == 'coingecko':
        CoinID = PriceImporter.getCoinID(ticker,InputTablePath=dir+FDel+'MacroBackend'+FDel+'AllCG.xlsx')
        TheData = PriceImporter.CoinGeckoPriceHistory(CoinID[1],TimeLength=TimeLength) 
        TheData.rename({"Price (USD)":"Close"},axis=1,inplace=True) 
        TheData = pd.Series(TheData['Close'],name=TheSeries['Name']) 
        TheData = TheData.resample('D').mean()
    elif Source == 'spread':
        add = ticker.split('+'); subtract = ticker.split('-'); mutltiply = ticker.split('*'); divide = ticker.split('/')
        if len(add) > 1:
            tick1 = Inputs.loc[int(add[0])].at['Name']; tick2 = Inputs.loc[int(add[1])].at['Name']
            series1 = SeriesDict[tick1]; series2 = SeriesDict[tick2]; Series1 = pd.Series(series1['Data']); Series2 = pd.Series(series2['Data'])
            TheData = Series1+Series2
        elif len(subtract) > 1:
            tick1 = Inputs.loc[int(subtract[0])].at['Name']; tick2 = Inputs.loc[int(subtract[1])].at['Name']
            series1 = SeriesDict[tick1]; series2 = SeriesDict[tick2]; Series1 = pd.Series(series1['Data']); Series2 = pd.Series(series2['Data'])
            TheData = Series1-Series2
        elif len(mutltiply) > 1:
            tick1 = Inputs.loc[int(mutltiply[0])].at['Name']; tick2 = Inputs.loc[int(mutltiply[1])].at['Name']
            series1 = SeriesDict[tick1]; series2 = SeriesDict[tick2]; Series1 = pd.Series(series1['Data']); Series2 = pd.Series(series2['Data'])
            TheData = Series1*Series2    
        elif len(divide) > 1:
            tick1 = Inputs.loc[int(divide[0])].at['Name']; tick2 = Inputs.loc[int(divide[1])].at['Name']
            series1 = SeriesDict[tick1]; series2 = SeriesDict[tick2]; Series1 = pd.Series(series1['Data']); Series2 = pd.Series(series2['Data'])
            TheData = Series1/Series2    
        else:
            print("If using Source = spread, you must input Series_Ticker as i/j, where i & j are the index numbers of two series already in the chart.")      
    else:
        print("Can't find data for: ",series)    
    if len(SeriesInfo) > 0:
        pass
    else:
        SeriesInfo['units'] = 'US Dollars'; SeriesInfo['units_short'] = 'USD'
        SeriesInfo['title'] = TheSeries['Legend_Name']; SeriesInfo['id'] = TheSeries['Name'] 
    TheData.index.rename('date',inplace=True); TheData = pd.Series(TheData.squeeze(),name=ticker)
    SeriesInfo.index.rename('Property',inplace=True); SeriesInfo = pd.Series(SeriesInfo.squeeze(),name='Value')
    TheSeries['Data'] = TheData
    TheSeries['SeriesInfo'] = SeriesInfo     ###Gotta make series info for the non-FRED series.   
    SeriesDict[series] = TheSeries
    print(ticker,TheData)
########### Resample all series to daily frequency ###############################################################
Index = pd.date_range(start=DataStart,end=EndDateStr,freq='D'); loadStr = 'load'; noStr = 'no'
for series in SeriesDict.keys():
    TheSeries = SeriesDict[series]
    data = TheSeries['Data']; Name = TheSeries['Name']; Ticker = TheSeries['Ticker']; Info = TheSeries['SeriesInfo']
    resamp = TheSeries['Resample2D']; TheSource = TheSeries['Source']
    if pd.isna(resamp) or str(resamp).upper() == noStr.upper():
        pass 
    else:   
        data = PriceImporter.ReSampleToRefIndex(data,Index,'D'); TheSeries['Data'] = data

########################## SAVE DATA #################################################################################### 
SpreadStr = "spread"   
if TheSource.upper() != loadStr.upper() and TheSource.upper() != SpreadStr.upper():
    savePath = DataPath+FDel+Ticker+'.xlsx'; print('Saving to: ',savePath)
    TheRest = pd.Series([TheSeries['Ticker'],TheSeries['Source'],TheSeries['UnitsType'],TheSeries['TraceColor'],TheSeries['Legend_Name'],\
                            TheSeries['Name'],TheSeries['Axis']],index=['Ticker','Source','UnitsType','TraceColor','Legend_Name','Name','Axis'])
    data.to_excel(savePath,sheet_name='Closing_Price')
    with pd.ExcelWriter(savePath, engine='openpyxl', mode='a') as writer:  
        Info.to_excel(writer, sheet_name='SeriesInfo')
        TheRest.to_excel(writer, sheet_name='OtherInfo')
    data = data[StartDate:EndDate]; TheSeries['Data'] = data    

###################### Change series to YoY calculation if that option is chosen #################################
normStr = 'normal'; YoYStr = 'yoy'
for series in SeriesDict.keys():
    TheSeries = SeriesDict[series]; data = pd.Series(TheSeries['Data']); TraceType = str(TheSeries['UnitsType'])
    Freq = str(data.index.inferred_freq); print(data.name,' Inferred frequency: ',Freq)
    if TraceType.upper() == YoYStr.upper():
        if Freq == 'D':
            data = pd.Series(PriceImporter.YoYCalcFromDaily(data))
            TheSeries['Data'] = data
        elif Freq == 'MS' or Freq == 'M': 
            data = pd.Series(PriceImporter.YoY4Monthly(data)); TheSeries['Data'] = data
        else:
            print("For series: ",data.name,", with frequency: ",Freq," is currently imcompatible with YoY % change calculation. Set Resample2D to 'yes' to use daily frequency.")    
            quit()
    else:
        pass    

######### MATPLOTLIB SECTION #################################################################
plt.rcParams['figure.dpi'] = 105; plt.rcParams['savefig.dpi'] = 200   ###Set the resolution of the displayed figs & saved fig respectively. 
fig = plt.figure(num="Macro Data",figsize=(15,6.5), tight_layout=True); i = 0
if numSeries < 4:
    Top = 0.95
else:
    Top = 0.9
gs = GridSpec(1, 1, top = Top, bottom=0.08,left=0.06,right=1-(numAxii*0.036))
CheckAxis = []
print(SeriesDict.keys())
for series in SeriesDict.keys(): 
    TheSeries = SeriesDict[series]; Data = pd.Series(TheSeries['Data']); TraceType = str(TheSeries['UnitsType']); Ymax = TheSeries['Ymax']
    print(i,TheSeries['Name'],TheSeries['Axis'],Data)    ####Trying to figure out how to get plots on the right axis and have some on the same axis. 
    print(CheckAxis,len(CheckAxis),TheSeries['Axis'] in CheckAxis) 
    if len(CheckAxis) == 0:
        print('Plotting new Axis.', TheSeries['Axis'],TheSeries['TraceColor'],TheSeries['Name'],i)
        ax1 = fig.add_subplot(gs[0]); ax1.plot(TheSeries['Data'],color=TheSeries['TraceColor'],label=TheSeries['Legend_Name'],lw=2.5)
        ax1.spines['left'].set_linewidth(1.5); ax1.grid(visible=True,which='major',axis='y')
        ax1.tick_params(axis='y',labelsize=8,color=TheSeries['TraceColor'],labelcolor=TheSeries['TraceColor'])
        ax1.set_yscale(TheSeries['YScale']); ax1.set_xlim(StartDate,EndDate)
        if pd.isna(Ymax):
            pass
        else:
            ax1.set_ylim(TheSeries['Data'].min(),int(Ymax))
        if TraceType.upper() == YoYStr.upper():
            ax1.set_ylabel(r'YoY $\Delta$ %',fontweight='bold',color=TheSeries['TraceColor'])
        else:     
            ax1.set_ylabel(TheSeries['SeriesInfo']['units_short'],fontweight='bold',color=TheSeries['TraceColor'])

    elif len(CheckAxis) > 0: 
        if (TheSeries['Axis'] in CheckAxis) and (TheSeries['Axis'] == 'ax1'): 
            print('Adding to plot ax1')
            ax1.plot(TheSeries['Data'],color=TheSeries['TraceColor'],label=TheSeries['Legend_Name'])
        if (TheSeries['Axis'] in CheckAxis) is False and (TheSeries['Axis'] == 'ax2'):
            print('Plotting new Axis.', TheSeries['Axis'],TheSeries['TraceColor'],TheSeries['Name'],i)
            ax2 = ax1.twinx(); ax2.plot(TheSeries['Data'],color=TheSeries['TraceColor'],label=TheSeries['Legend_Name'])
            ax2.spines['right'].set_linewidth(1.5); ax2.spines['right'].set_color(TheSeries['TraceColor'])
            ax2.tick_params(axis='y',labelsize=8,which='both',color=TheSeries['TraceColor'],labelcolor=TheSeries['TraceColor'])
            ax2.set_yscale(TheSeries['YScale'])
            if pd.isna(Ymax):
                pass
            else:
                ax2.set_ylim(TheSeries['Data'].min(),int(Ymax))
            if TraceType.upper() == YoYStr.upper():
                ax2.set_ylabel(r'YoY $\Delta$ %',fontweight='bold',color=TheSeries['TraceColor'])
            else:     
                ax2.set_ylabel(TheSeries['SeriesInfo']['units_short'],fontweight='bold',color=TheSeries['TraceColor'])
        elif (TheSeries['Axis'] in CheckAxis) and (TheSeries['Axis'] == 'ax2'):
            print('Adding to plot ax2')
            ax2.plot(TheSeries['Data'],color=TheSeries['TraceColor'],label=TheSeries['Legend_Name']) 
        if (TheSeries['Axis'] in CheckAxis) is False and (TheSeries['Axis'] == 'ax3'):
            print('Plotting new Axis.', TheSeries['Axis'],TheSeries['TraceColor'],TheSeries['Name'],i)
            ax3 = ax1.twinx(); ax3.plot(TheSeries['Data'],color=TheSeries['TraceColor'],label=TheSeries['Legend_Name'])
            ax3.legend(loc=2,bbox_to_anchor=(0.66,1.06),fontsize='small')
            ax3.tick_params(axis='y',labelsize=8,which='both',color=TheSeries['TraceColor'],labelcolor=TheSeries['TraceColor'])
            ax3.set_yscale(TheSeries['YScale']); ax3.spines.right.set_position(("axes", 1.06)); ax3.spines['right'].set_linewidth(1.5)
            ax3.spines['right'].set_color(TheSeries['TraceColor'])  
            if pd.isna(Ymax):
                pass
            else:
                ax3.set_ylim(TheSeries['Data'].min(),int(Ymax))
            if TraceType.upper() == YoYStr.upper():
                ax3.set_ylabel(r'YoY $\Delta$ %',fontweight='bold',color=TheSeries['TraceColor'])
            else:     
                ax3.set_ylabel(TheSeries['SeriesInfo']['units_short'],fontweight='bold',color=TheSeries['TraceColor'])    
        elif (TheSeries['Axis'] in CheckAxis) and (TheSeries['Axis'] == 'ax3'): 
            print('Adding to plot ax3')
            ax3.plot(TheSeries['Data'],color=TheSeries['TraceColor'],label=TheSeries['Legend_Name'])
        if (TheSeries['Axis'] in CheckAxis) is False and (TheSeries['Axis'] == 'ax4'):
            print('Plotting new Axis.', TheSeries['Axis'],TheSeries['TraceColor'],TheSeries['Name'],i)
            ax4 = ax1.twinx(); ax4.plot(TheSeries['Data'],color=TheSeries['TraceColor'],label=TheSeries['Legend_Name'])
            ax4.tick_params(axis='y',labelsize=8,which='both',color=TheSeries['TraceColor'],labelcolor=TheSeries['TraceColor'])
            ax4.set_yscale(TheSeries['YScale']); ax4.spines.right.set_position(("axes", 1.12)); ax4.spines['right'].set_linewidth(1.5)
            ax4.spines['right'].set_color(TheSeries['TraceColor'])
            if pd.isna(Ymax):
                pass
            else:
                ax4.set_ylim(TheSeries['Data'].min(),int(Ymax))
            if TraceType.upper() == YoYStr.upper():
                ax4.set_ylabel(r'YoY $\Delta$ %',fontweight='bold',color=TheSeries['TraceColor'])
            else:     
                ax4.set_ylabel(TheSeries['SeriesInfo']['units_short'],fontweight='bold',color=TheSeries['TraceColor'])  
        elif (TheSeries['Axis'] in CheckAxis) and (TheSeries['Axis'] == 'ax4'):  
            print('Adding to plot ax4')
            ax4.plot(TheSeries['Data'],color=TheSeries['TraceColor'],label=TheSeries['Legend_Name'])
        if (TheSeries['Axis'] in CheckAxis) is False and (TheSeries['Axis'] == 'ax5'):
            print('Plotting new Axis.', TheSeries['Axis'],TheSeries['TraceColor'],TheSeries['Name'],i)
            ax5 = ax1.twinx(); ax5.plot(TheSeries['Data'],color=TheSeries['TraceColor'],label=TheSeries['Legend_Name'])  
            ax5.tick_params(axis='y',labelsize=8,which='both',color=TheSeries['TraceColor'],labelcolor=TheSeries['TraceColor'])
            ax5.set_yscale(TheSeries['YScale']); ax5.spines.right.set_position(("axes", 1.17)); ax5.spines['right'].set_linewidth(1.5)
            ax5.spines['right'].set_color(TheSeries['TraceColor'])
            if pd.isna(Ymax):
                pass
            else:
                ax5.set_ylim(TheSeries['Data'].min(),int(Ymax))
            if TraceType.upper() == YoYStr.upper():
                ax5.set_ylabel(r'YoY $\Delta$ %',fontweight='bold',color=TheSeries['TraceColor'])
            else:     
                ax5.set_ylabel(TheSeries['SeriesInfo']['units_short'],fontweight='bold',color=TheSeries['TraceColor'])  
        elif (TheSeries['Axis'] in CheckAxis) and (TheSeries['Axis'] == 'ax5'):  
            print('Adding to plot ax5')
            ax5.plot(TheSeries['Data'],color=TheSeries['TraceColor'],label=TheSeries['Legend_Name'])   
    else:
        print('1: What')        
    CheckAxis.append(TheSeries['Axis']); i += 1
plt.minorticks_on() 
for axis in ['top','bottom','left','right']:
            ax1.spines[axis].set_linewidth(1.5)   
j = 0
for axes in fig.axes:
    axes.margins(0.03,0.03)
    if j < 3:
        axes.legend(loc=2,bbox_to_anchor=(0.4*j,1.06),fontsize='small')
    else: 
        axes.legend(loc=2,bbox_to_anchor=(0.4*(j-3),1.12),fontsize='small')
    for line in axes.lines:
        j += 1          
plt.show()



