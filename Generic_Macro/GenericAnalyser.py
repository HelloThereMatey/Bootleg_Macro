###### Required modules/packages #####################################
import os
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
dir = os.path.dirname(wd)
print(wd,dir)
import sys; sys.path.append(dir)
from MacroBackend import PriceImporter ## This is one of my custom scripts holding functions for pulling price data from APIs. Your IDE might not find it before running script. 
from MacroBackend import Charting    ##This script has all the matplotlib chart formatting code. That code is ugly, best to put it in a second file like this. 
from MacroBackend import Utilities
import mplfinance
## You may see: 'Import "MacroBackend" could not be resolved' & it looks like MacroBackend can't be found. However, it will be found when script is run. Disregard error. 
#### The below packages need to be installed via pip/pip3 on command line. These are popular, well vetted packages all. Just use 'pip install -r requirements.txt'
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec

### These are standard python packages included in the latest python distributions. No need to install them. 
import datetime
from datetime import timedelta
import re 
import tkinter as tk

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
print(Inputs)

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

SeriesDict = {}; SpreadStr = "spread"; GNstr = 'GNload'; loadStr = 'load'; noStr = 'no'
Title = Inputs.loc['CHART TITLE'].at['Series_Ticker']
recession_bars = Inputs.loc['RECESSION_BARS'].at['Series_Ticker']
alignZeros = Inputs.loc['Align_ZeroPos'].at['Series_Ticker']
G_YMin = Inputs.loc['Global_Ymin'].at['Series_Ticker']
G_YMax = Inputs.loc['Global_Ymax'].at['Series_Ticker']

for i in range(1,6):
    ticker = Inputs.loc[i].at['Series_Ticker']
    if pd.isna(ticker):
        pass
    else:
        source = Inputs.loc[i].at['Source']; Tipe = Inputs.loc[i].at['UnitsType']
        color = Inputs.loc[i].at['TraceColor']; label = Inputs.loc[i].at['Legend_Name']; name = Inputs.loc[i].at['Name']
        yscale = Inputs.loc[i].at['Yaxis']; Ymax = Inputs.loc[i].at['Ymax']; resample = Inputs.loc[i].at['Resample2D']
        axlabel = Inputs.loc[i].at['Axis_Label']; idx = Inputs.index[i-1]; MA =  Inputs.loc[i].at['Sub_MA']; LW = Inputs.loc[i].at['LineWidth']
        convert = Inputs.loc[i].at['ConvertUnits']; Ymin = Inputs.loc[i].at['Ymin']
        SeriesDict[name] = {'Index':idx,'Ticker': ticker, 'Source': source, 'UnitsType': Tipe, 'TraceColor': color, 'Legend_Name': label, 'Name': name,\
                            'YScale': yscale,'axlabel': axlabel,'Ymax': Ymax,'Resample2D': resample, 'useMA': MA, 'LW': LW, 'Ticker_Source':ticker,
                            'ConvertUnits':convert,'Ymin': Ymin }      

SeriesList = Inputs['Series_Ticker'].copy(); SeriesList = SeriesList[0:5]; SeriesList.dropna(inplace=True); numSeries = len(SeriesList) 
numAxii = numSeries
print('Number of data series: ',numSeries,'Number of axii on chart: ',numAxii)
print(SeriesDict)

DataPath = wd+FDel+'SavedData'; GNPath = DataPath+FDel+'Glassnode'
for series in SeriesDict.keys():
    TheSeries = SeriesDict[series]; Source = TheSeries['Source']; ticker = TheSeries['Ticker']; TheIndex = TheSeries['Index']
    SeriesInfo = pd.Series([],dtype=str)
    ticker = str(ticker); split = ticker.split(','); #print("Ticker at first split:",split,len(split))
    if len(split) > 1:
        ticker = (split[0],split[1])
        symbol = split[0]; exchange = split[1]; ticker = split[0]
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
        TheSeries['Source'] = SeriesInfo['Source']
    elif Source == 'GNload':
        TheData = pd.read_excel(GNPath+FDel+ticker+'.xlsx')
        TheData.set_index(TheData[TheData.columns[0]],inplace=True); TheData.index.rename('date',inplace=True)
        TheData.drop(TheData.columns[0],axis=1,inplace=True)
        if type(TheData) == pd.DataFrame:
            pass
        else:
            TheData = pd.Series(TheData.squeeze(),name=ticker)
    elif Source == 'fred':
        SeriesInfo, TheData = PriceImporter.PullFredSeries(ticker,myFredAPI_key,start=DataStart,filetype="&file_type=json",end=EndDateStr)
        AssetName = SeriesInfo['id']
        if pd.isna(TheSeries['axlabel']):
            TheSeries['axlabel'] = SeriesInfo['units_short']
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
        TheData = pd.Series(TheData['Close'],name=TheSeries['Name'])  ##### Just take the closing price for this application. 
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
        add = ticker.split('+'); subtract = ticker.split('-'); multiply = ticker.split('*'); divide = ticker.split('/')
        print('Spread chosen for series at position',TheIndex)
        try:
            if len(add) > 1:
                tick1 = Inputs.loc[int(add[0])].at['Name']; tick2 = Inputs.loc[int(add[1])].at['Name']
                series1 = SeriesDict[tick1]; series2 = SeriesDict[tick2]; Series1 = pd.Series(series1['Data']); Series2 = pd.Series(series2['Data'])
                TheData = Series1+Series2
                print('Series',TheIndex,'is series',tick1,'plus',tick2)
            elif len(subtract) > 1:
                tick1 = Inputs.loc[int(subtract[0])].at['Name']; tick2 = Inputs.loc[int(subtract[1])].at['Name']
                series1 = SeriesDict[tick1]; series2 = SeriesDict[tick2]; Series1 = pd.Series(series1['Data']); Series2 = pd.Series(series2['Data'])
                TheData = Series1-Series2
                print('Series',TheIndex,'is series',tick1,'minus',tick2)
            elif len(multiply) > 1:
                tick1 = Inputs.loc[int(multiply[0])].at['Name']; tick2 = Inputs.loc[int(multiply[1])].at['Name']
                series1 = SeriesDict[tick1]; series2 = SeriesDict[tick2]; Series1 = pd.Series(series1['Data']); Series2 = pd.Series(series2['Data'])
                TheData = Series1*Series2 
                print('Series',TheIndex,'is series',tick1,'times',tick2)   
            elif len(divide) > 1:
                tick1 = Inputs.loc[int(divide[0])].at['Name']; tick2 = Inputs.loc[int(divide[1])].at['Name']
                series1 = SeriesDict[tick1]; series2 = SeriesDict[tick2]; Series1 = pd.Series(series1['Data']); Series2 = pd.Series(series2['Data'])
                TheData = Series1/Series2   
                print('Series',TheIndex,'is series',tick1,'divided by',tick2) 
            else:
                print("If using Source = spread, you must input Series_Ticker as i/j, where i & j are the index numbers of two series already in the chart.")  
            TheData.dropna(inplace=True)      
        except Exception as e:
            print(e)
            print("If using Source = spread, you must input Series_Ticker as i/j, where i & j are the index numbers of two series already in the chart.")     
            quit()      
    else:
        print("Can't find data for: ",series)    
    if len(SeriesInfo) > 0 and Source != 'load':
        SeriesInfo['Source'] = Source
        pass
    else:
        SeriesInfo['units'] = 'US Dollars'; SeriesInfo['units_short'] = 'USD'
        SeriesInfo['title'] = TheSeries['Legend_Name']; SeriesInfo['id'] = TheSeries['Name']
        SeriesInfo['Source'] = Source
    
    ######### Applies to all data loaded #####################
    TheData.index.rename('date',inplace=True)
    SeriesInfo.index.rename('Property',inplace=True); #SeriesInfo = pd.Series(SeriesInfo,name="Value")
    TheData2 = TheData.copy()
    
    if type(TheData2) == pd.Series:
        pass
    else:
        if len(TheData2.columns) > 1:
            TheData2.name = TheSeries["Name"]
            pass
        else:
            TheData2 = pd.Series(TheData2[TheData2.columns[0]],name=TheSeries['Name'])
    print('Data pull function, data series name: ',TheSeries['Name'],'Datatype:  ',type(TheData2))    
    TheData2 = TheData2[StartDate:EndDate]
    TheSeries['Data'] = TheData2
    TheSeries['SeriesInfo'] = SeriesInfo     ###Gotta make series info for the non-FRED series.   
    SeriesDict[series] = TheSeries
    if pd.isna(TheSeries['axlabel']):
        try:
            TheSeries['axlabel'] = SeriesInfo['units_short']
        except:
            pass  

    ########################## SAVE DATA ####################################################################################
    if Source.upper() != loadStr.upper() and Source.upper() != SpreadStr.upper() and Source.upper() != GNstr.upper():
        savePath = DataPath+FDel+ticker+'.xlsx'
        print('Saving new data set: ',ticker,'to: ',savePath)
        TheData2.to_excel(savePath,sheet_name='Closing_Price')
        with pd.ExcelWriter(savePath, engine='openpyxl', mode='a') as writer:  
            SeriesInfo.to_excel(writer, sheet_name='SeriesInfo')
 
keys = list(SeriesDict.keys()); print(keys)

########### Resample all series to daily frequency and/or convert units ###############################################################
Index = pd.date_range(start=DataStart,end=EndDateStr,freq='D')
for series in SeriesDict.keys():
    TheSeries = SeriesDict[series]
    data = TheSeries['Data']; Name = TheSeries['Name']; Ticker = TheSeries['Ticker']; Info = TheSeries['SeriesInfo']
    convert = TheSeries['ConvertUnits']; resamp = TheSeries['Resample2D']; TheSource = TheSeries['Source']
    if pd.isna(resamp) or str(resamp).upper() == noStr.upper():
        pass 
    else:   
        data = PriceImporter.ReSampleToRefIndex(data,Index,'D')
    if pd.isna(convert):
        pass
    else:
        data /= convert
    TheSeries['Data'] = data    

#### Substitute a data series for an MA of that series if wanted. ##########################################################################################    
for series in SeriesDict.keys():
    TheSeries = SeriesDict[series]
    if pd.isna(TheSeries["useMA"]):
        pass
    else:
        try:
            ma = int(TheSeries["useMA"])
            data = pd.Series(TheSeries['Data'],name=data.name)
            data = data.rolling(ma).mean(); data.dropna(inplace=True)
            TheSeries['Data'] = data
            label = str(TheSeries['Legend_Name'])
            label += " "+str(ma)+' day MA'
            TheSeries['Legend_Name'] = label
        except:
            print('Sub_MA must be an integer if you want to use an MA.')    

###################### Change series to YoY or other annualized rate calcs if that option is chosen #################################
normStr = 'Unaltered'; YoYStr = 'Year on year % change'; devStr = '% deviation from fitted trendline'; ann3mStr = 'Annualised 3-month % change'
ann6mStr = 'Annualised 6-month % change'; momStr = 'Month on month % change'
for series in SeriesDict.keys():
    TheSeries = SeriesDict[series]; 
    data = TheSeries['Data']; name = TheSeries['Name']
    print('Before first deriv calc.: ',data)
    TraceType = str(TheSeries['UnitsType'])
    idx = pd.DatetimeIndex(data.index)
    Freq = str(idx.inferred_freq); print(name,' Inferred frequency: ',Freq)
    Freqsplit = Freq.split("-")

    if TraceType.upper() == YoYStr.upper():
        # if Freq == 'D':
        #     data = Utilities.MonthPeriodAnnGrowth2(data,12)
        # elif Freqsplit[0] == 'W':    
        #     data = Utilities.MonthPeriodAnnGrowth2(data,12) 
        # elif Freq == 'MS' or Freq == 'M': 
        #     data = PriceImporter.YoY4Monthly(data)
        # else:
        #     print("For series: ",data.name,", with frequency: ",Freq," is currently imcompatible with YoY % change calculation. Set Resample2D to 'yes' to use daily frequency.")    
        #     quit()
        data = Utilities.MonthPeriodAnnGrowth2(data,12)
        data.dropna(inplace=True)    
    elif TraceType.upper() == ann3mStr.upper():    
        print('3 month annualized % change transformation chosen for dataset: ',name)
        data = Utilities.MonthPeriodAnnGrowth2(data,3)  #The period here for this function is months. 
        data.dropna(inplace=True) 
    elif TraceType.upper() == ann6mStr.upper():    
        print('6 month annualized % change transformation chosen for dataset: ',name)
        data = Utilities.MonthPeriodAnnGrowth2(data,6) 
        data.dropna(inplace=True)   
    elif TraceType.upper() == momStr.upper():    
        print('Month on month annualized % change transformation chosen for dataset: ',name)
        data = Utilities.MonthPeriodAnnGrowth2(data,1)   
        data.dropna(inplace=True)    
    # elif  TraceType.upper() == devStr.upper():      
    #     fitY, std_u, std_l, TrendDev = fitExpTrend(data)
    else:
        pass    
    print('After first deriv calc.: ',data)
    TheSeries['Data'] = data

######## Look at the Y-range of each series and adjust Y-axis so that the 0-position of each chart will align if chosen. #######################
if alignZeros == 'yes':
    mins = {}; macks = {}
    for series in SeriesDict.keys():
        TheSeries = SeriesDict[series] 
        data = pd.Series(TheSeries['Data']).copy()
        whymax = np.nanmax(data); whyminh = np.nanmin(data)
        mins[data.name] = whyminh
        macks[data.name] = whymax    
    if pd.isna(G_YMin) and pd.isna(G_YMax):    
        WhyMin = min(mins.values())
        YMacks = max(macks.values()) 
    elif pd.isna(G_YMin) and pd.isna(G_YMax) is False:
        WhyMin = min(mins.values())
        YMacks = G_YMax
    elif pd.isna(G_YMin) is False and pd.isna(G_YMax):
        WhyMin = G_YMin
        YMacks = max(macks.values()) 
    else:
        WhyMin = G_YMin
        YMacks = G_YMax
    
    for series in SeriesDict.keys():
        TheSeries = SeriesDict[series]     
        TheSeries['Ymin'] = WhyMin
        TheSeries['Ymax'] = YMacks

######### MATPLOTLIB SECTION #################################################################
plt.rcParams['figure.dpi'] = 105; plt.rcParams['savefig.dpi'] = 300   ###Set the resolution of the displayed figs & saved fig respectively. 
#### X Ticks for all charts #################################################################################
print(SeriesDict, keys[0])
Series1 = SeriesDict[keys[0]]; Data = Series1['Data']
print(Series1,Data, len(Data)) 
if type(Data) == pd.DataFrame:
    Data = pd.DataFrame(Data)
else:
    Data = pd.Series(Data) 
print(Data, len(Data))    
Range = Data.index[len(Data)-1] - Data.index[0]
margs = round((0.02*Range.days),0); print(Range.days,margs)
Xmin = Data.index[0]-timedelta(days=margs); Xmax = Data.index[len(Data)-1]+timedelta(days=margs)
Xmin = Xmin.to_pydatetime(); Xmax = Xmax.to_pydatetime()
stepsize = (Xmax - Xmin) / 20
XTickArr = np.arange(Xmin, Xmax, stepsize) 
XTickArr = np.append(XTickArr, Xmax)
if numSeries < 4:
    Bot = 0.125
else:
    Bot = 0.165
margins = {'top':0.95, 'bottom':Bot ,'left':0.06,'right':1-(numAxii*0.035)}

print('######################## PLOTTING ####################################################################')
def get_curr_screen_geometry():
    """
    Workaround to get the size of the current screen in a multi-screen setup.
    Returns:
        geometry (str): The standard Tk geometry string.
            [width]x[height]+[left]+[top]
    """
    root = tk.Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    geometry = root.winfo_geometry()
    root.destroy()
    return geometry

screen = get_curr_screen_geometry()   
split = screen.split('+'); geo = split[0]
split2 = geo.split("x"); cm = 2.54
sw = int(split2[0]); sh = int(split2[1]) 
px = (1/plt.rcParams['figure.dpi'])*25.4  ##Pixel size in mm. 
print('Pixel size (mm):',px,'Screen width (pixels):',sw,'Screen height (pixels):',sh,'\n'\
      ,'Screen width (mm):',sw*px,'Screen height (mm):',sh*px,'Screen width (cm):',(sw*px)/10,'Screen height (cm):',(sh*px)/10)
fwid = ((14*cm)*10); fhght =  ((7*cm)*10) #Figsize in mm.
figsize = (fwid/(cm*10), fhght/(cm*10))   #Figsize in inches.
figsize_px = (round(fwid/px),round(fhght/px))
print('figsize (cm):',figsize,'figsize (pixels):',figsize_px)

############ This organises a list of data sources to add at bottom of chart. 
DS_List = []
for series in SeriesDict.keys():
    TheSeries = SeriesDict[series]; source = TheSeries['Source']; ticker = str(TheSeries['Ticker_Source'])
    split = ticker.split(','); tickName = split[0]
    if len(split) > 1:
        exchange = split[1]
    if source == 'tv' and len(split) > 1:
        if exchange == 'INDEX':
            pass
        else:
            source = exchange   
    DS_List.append(source)
DataSource = np.unique(DS_List); strList = ""; i = 0
for source in DataSource:
    if i == 0:
        strList += source
    elif i == len(DataSource)-1:
        strList += ", "+source+"."
    else:    
        strList += ", "+source; 
    i +=1 
DataSourceStr = 'Source: '+strList
Replaces = {"GNload":"Glassnode","fred":"Federal reserve","yfinance":"Yahoo","yfinance":"Yahoo","tv":"Trading view","coingecko":"Coin gecko"}
for word in Replaces.keys():
    DataSourceStr = DataSourceStr.replace(word,Replaces[word])

smolFig = plt.figure(FigureClass = Charting.BMP_Fig,margins=margins,numaxii=numAxii,DataSourceStr=DataSourceStr,figsize=figsize)
smolFig.set_Title(Title)

smolFig.AddTraces(SeriesDict)
#path2image = wd+FDel+'Images'+FDel+'BMPleb2.png'
ex = figsize_px[0]-0.1*figsize_px[0]; why = figsize_px[1] - 0.9*figsize_px[1]

if alignZeros == 'yes':
    smolFig.ax1.axhline(100,color='black',lw=1,ls=":")
#smolFig.addLogo(path2image,ex,why,0.66)

############## Add recession bars on chart if desired ###################################################################
if recession_bars == 'yes':
    bar_dates = PriceImporter.GetRecessionDates(StartDate)
    bar_dates = pd.Series(bar_dates)
    bar_dates = bar_dates[pd.Timestamp(StartDate)::]
    vals = bar_dates.to_list(); dates = bar_dates.index.to_list()
    start_dates = []; end_dates = []
    if vals[0] == 1:
            start_dates.append(dates[0])
    for i in range(1,len(dates),1):
        val = vals[i]
        lastVal = vals[i-1]
        if val == 1 and lastVal == 0:
            start_dates.append(dates[i])
        elif val == 0 and lastVal == 1:   
            end_dates.append(dates[i-1])      
    ax1 = smolFig.axes[0]; lims = ax1.get_ylim()
    for i in range(len(start_dates)):
        ax1.axvspan(start_dates[i],end_dates[i],color='blue',alpha=0.25,label="Recessions (NBER)")
    if Bot < 0.14: 
        ax1.text(0.4,-0.135 ,"Shaded vertcial bars indicate recession periods (NBER).",fontsize='small',color='blue',horizontalalignment='left', transform=ax1.transAxes)
    else:
        ax1.text(0.4,-0.195,"Shaded vertcial bars indicate recession periods (NBER).",fontsize='small',color='blue',horizontalalignment='left', transform=ax1.transAxes)

plt.show()




