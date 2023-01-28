""" 
USD NET LIQUIDITY SCRIPT - The net lqiuidity metric (NLQ) was originally formulated by Darius Dale and 42Macro, much respect DD, 42 Macro is best in class. If you can afford it, you're best off to
just get a 42 Macro subscription. If however, you are a low-time preferenced, humble, sat-stacking pleb that would rather use that money to stack sats and doesn't mind getting your hands dirty
with coding and data diving, then this approach is for you. The net liquidity time series is the Fed balance sheet (FedBal) - the balance in the reverse repo facility (RevRep) - the treasury general account (TGA). The
three series are available from FRED and this script pulls these series from FRED, does the necessary arithmetic and displays NLQ along with 1-5 comparison assets with data sourced from a range of free price history providers,
inlcuding yahoo finance, google finance and trading view. 
    FedBal is updated on a weekly basis while, revrep and TGA have daily updates of their balance (mon-fri). RevRep series from FRED (RRPONTSYD) is a series with daily frequency while the TGA series
from FRED is a weekly series (average of the week). In order to provide more rapid updating, I'm taking the TGA balance data from the treasury API for the TGA series. The resultant net liquidity series
makes significant moves on a daily basis when TGA and RevRep balances move significantly. NLQ can be viewed on trading view yet only with weekly frequency & this script is possibly a better way
to view NLQ as it updates on a daily basis just like the original 42 macro NLQ series.
    Apart from standard, well vetted, python packages, my script uses another script 'PriceImporter' that contains my functions for pulling price history from different APIs. There is also a package
tvDatafeed which is used. This package is great and allows us to pull data for any asset that you can find on tradingview from tradingview. I'm quite sure that it is safe and have been using it for 
months, it just doesn't achieve legitimancy due to the legal grey area in which it operates.
    How to use scipt: 
     - Place NetLiquidity project folder where you wish. Set working directory to the folder. 
     - Install the necessary modules using requirements.txt.
     - Set your input parameters in the excel file. Correlation will be calculated between NLQ & the asset in slot #1 on excel file.
     - Run script. 
"""

####### Required modules/packages #####################################
import PriceImporter ## This is one of my custom scripts holding functions for pulling price data from APIs. Must be present in same folder as this file. 
#### The below packages need to be installed via pip/pip3 on command line. These are popular, well vetted packages all. Just use 'pip install -r requirements.txt'
import requests    
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
### These are standard python packages included in the latest python distributions. No need to install them. 
import datetime
from datetime import timedelta
import os
import re 
import math
from sys import platform

wd = os.path.dirname(os.path.realpath(__file__)) ## This gets the working directory which is the folder where you have placed this .py file. 
if platform == "linux" or platform == "linux2":        #This detects what operating system you're using so that the right folder delimiter can be use for paths. 
    FDel = '/'; OpSys = 'linux'
elif platform == "darwin":
    FDel = '/'; OpSys = 'mac'
elif platform == "win32":
    FDel = '\\' ; OpSys = 'windows'
print('System information: ',platform, OpSys,', directory delimiter: ', FDel, ', working directory: ', wd)

try:
    Inputs = pd.read_excel(wd+'/NetLiquidity_InputParams.xlsx')     ##Pull input parameters from the input parameters excel file. 
except Exception as e: 
    print(e)
    try:    
        Inputs = pd.read_excel(wd+'\\NetLiquidity_InputParams.xlsx')
    except Exception as e:
        print(e) 
        print("What you using bro? Windows mac or linux supported. If using something else, you'll just need to set the folder delimeter for all path references below.")    
        quit()
Inputs.set_index('Index',inplace=True)        

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

def YoYCalcFromDaily(series:pd.Series):  #Transform a price history series with daily frequency to a YoY % change series with daily freq. 
    series = series.resample('D').mean()
    series.fillna(method='ffill',inplace=True) #This'll make it daily data even if weekly data is input. 
    YoYCalc = [np.nan for i in range(365)]
    for i in range(365,len(series),1):
        YoYCalc.append(((series[i]-series[i-365])/series[i-365])*100)
    YoYSeries = pd.Series(YoYCalc,index=series.index,name='YoY % change')    
    return YoYSeries

def PullFredSeries(series:str,apikey:str,start="1776-07-04",filetype="&file_type=json",outputDataName:str=None,end=datetime.date.today().strftime('%Y-%m-%d')): 
    series_header = "https://api.stlouisfed.org/fred/series?series_id="      ##This pulls data series from FRED API. 
    r = requests.get(series_header+series+"&observation_start="+start+"&api_key="+myFredAPI_key+filetype)
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
    print('Units info for series: ',TheData.name,'Units:',SeriesInfo['units'],'#')
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
        series1,series2 = PriceImporter.GetIndiciiSame(series1,series2)
    elif (len(series2.index.difference(series1.index))) > 0:
        series2,series1 = PriceImporter.GetIndiciiSame(series2,series1)
    else:
        pass    
    periodsList.append(len(series2)-5)
    if SaveDatas is not None:       #This function implements the correlation function on 
        output = pd.concat([series1,series2],axis=1)
        output.to_excel(SaveDatas+".xlsx")
    CorrDict = {}
    for period in periodsList:
        CorrDict["CC_"+str(period)+"d"] = Correlation(series1,series2,period=period) 
    #print('Correlation master function: ',CorrDict)    
    Correlations = pd.DataFrame(CorrDict)  
    return Correlations, Correlation(series1,series2)    

    #######. MatPlotLib Section. Making good figs with MPL takes many lines of code dagnammit.  ###################
def FedFig(TheData:pd.Series,SeriesInfo:pd.Series,RightSeries:pd.Series=None,rightlab="",Lyscale="linear",Ryscale="linear",CustomXAxis=True):
    fig = plt.figure(num=SeriesInfo["id"],figsize=(15,5), tight_layout=True)
    ax = fig.add_subplot()
    plot1 = ax.plot(TheData,color="black",label=SeriesInfo["id"])       ### This is a simple fig template to view series from FRED with a comparison asset. 
    if Lyscale == "log":
        ax.set_yscale('log')
    if RightSeries is not None:
        axb = ax.twinx()
        plot2 = axb.plot(RightSeries,color="red",label=rightlab) 
        if Ryscale == "log":
            axb.set_yscale('log')
        axb.set_ylabel(rightlab+' price (USD)',fontweight='bold')
        axb.legend(loc=1,fontsize='small'); axb.minorticks_on()
    ax.set_title(SeriesInfo["title"])
    ax.set_ylabel(SeriesInfo["units_short"], fontweight='bold')    
    if CustomXAxis == True:
        Xmax = max(TheData.index); Xmin = min(TheData.index)
        stepsize = (Xmax - Xmin) / 20
        XTicks = np.arange(Xmin, Xmax, stepsize); XTicks = np.append(XTicks,Xmax)
        ax.xaxis.set_ticks(XTicks); ax.set_xlim(Xmin-datetime.timedelta(days=15),Xmax+datetime.timedelta(days=15))
        ax.tick_params(axis='x',length=3,labelrotation=45)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%y-%b'))
    frequency = SeriesInfo['frequency']
    ax.text(0.5,0.05,'Series updated: '+frequency,horizontalalignment='center',verticalalignment='center', transform=ax.transAxes)  
    ax.legend(loc=2,fontsize='small')
    for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_linewidth(1.5)
    ax.minorticks_on()
    return fig

######## All this shit below is matplotlib figure generation code. One needs all this shit to get a figure exactly as wanted. ##############
### Main figure with Net liquidity + comparison asset and correlations. #############################
def MainFig(MainSeries:pd.Series,CADict:dict,CorrDF:pd.DataFrame,AssetData:pd.DataFrame,figname:str,CorrString:str,Mainlabel:str='Net liquidity (left)',LYScale:str='linear'\
    ,RYScale:str='linear',NLQ_Color:str='black',NLQMA:pd.Series=None,background=np.nan):
    fig = plt.figure(num=figname,figsize=(15.5,8), tight_layout=True)
    gs = GridSpec(2, 1, top = 0.96, bottom=0.1,left=0.06,right=0.92, height_ratios=[2.5,1], hspace=0)
    NetLiquidity = MainSeries

    ax = fig.add_subplot(gs[0]); ax1 = fig.add_subplot(gs[1],sharex=ax)
    plot1 = ax.plot(NetLiquidity,color=NLQ_Color,lw=2.5,label=Mainlabel)
    if NLQMA is not None:
        MA = ax.plot(NLQMA,color='gold',lw=1,label='NLQ_MA')
    ax.minorticks_on()
    axb = ax.twinx()
    for CA in CADict.keys():
        AssDF = CADict[CA][0]
        axb.plot(AssDF['Close'],label=CA,color=CADict[CA][1]) 
    axb.set_ylabel(RightLabel,fontweight='bold')
    ax.set_title('Net liquidity: Fed bal. sheet - rev. repo bal. - treasury gen. account', fontweight='bold')
    ax.set_ylabel('Bil. of U.S. $', fontweight='bold')
    for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_linewidth(1.5)        
    if ExtraAssets is True:
        ax.text(0.87,1.026,s='Other assets vs right-axis. Norm. to same range.',fontsize='small',horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
    Eq_ymin = math.floor(AssetData['Close'].min()); Eq_ymax = math.ceil(AssetData['Close'].max())
    ymin = math.floor(NetLiquidity.min()); ymax = math.ceil(NetLiquidity.max())

    if LYScale == 'log' and RYScale == 'log':       ##This provides cool looking equally spaced log ticks and tick labels on both y axii. 
        axb.set_yscale('log')
        ax.set_yscale('log')
        bTicks = np.real(np.logspace(start = np.log10(Eq_ymin), stop = np.log10(Eq_ymax), num=8, base=10)); bTicks.round(decimals=0,out=bTicks) 
        yTicks = np.real(np.logspace(start = np.log10(ymin), stop = np.log10(ymax), num=8, base=10)); yTicks.round(decimals=0,out=yTicks)
        ax.text(1.075,0.35,s='Y-scales are logarithmic',fontsize='small',transform=ax.transAxes,horizontalalignment='center',verticalalignment='center',rotation='vertical')
    elif LYScale == 'linear' and RYScale == 'linear': 
        bTicks = np.real(np.linspace(start = Eq_ymin, stop = Eq_ymax, num=8)); bTicks.round(decimals=0,out=bTicks)   
        yTicks = np.real(np.linspace(start = ymin, stop = ymax, num=8)); yTicks.round(decimals=0,out=yTicks)
        ax.text(1.075,0.35,s='Y-scales are linear',fontsize='small',transform=ax.transAxes,horizontalalignment='center',verticalalignment='center',rotation='vertical')
    else:
        print('LYSCale and RYSCale must be set to the same values in the input file. Either log or linear, fatal ERORRRR.')    
        quit()
    bTicks = np.ndarray.astype(bTicks,dtype=int,copy=False); yTicks = np.ndarray.astype(yTicks,dtype=int,copy=False)     
    axb.grid(visible=True, which='major', axis='both', c='gray',ls=':',lw=0.75)
    axb.tick_params(axis='y',which='both',width=0,labelsize=0); axb.minorticks_off() #Had to do this to eliminate pesky ticks that kept coming on top of my custom ones. 
    axb.set_ylim((Eq_ymin), (Eq_ymax)) 
    axb.set_yticks(bTicks); axb.set_yticklabels(bTicks); axb.yaxis.set_major_formatter('${x:1.0f}')
    axb.tick_params(axis='y',which='major',width=0.5,labelsize='small')     #All this to get y custom evenly spaced log ticks. 
    ax.tick_params(axis='y',which='both',width=0,labelsize=0); ax.minorticks_off() #Had to do this to eliminate pesky ticks that kept coming on top of my custom ones. 
    ax.set_ylim((ymin), (ymax)) 
    ax.set_yticks(yTicks); ax.set_yticklabels(yTicks); ax.yaxis.set_major_formatter('${x:1.0f}')
    ax.tick_params(axis='y',which='major',width=0.5,labelsize='small')     #All this to get y custom evenly spaced log ticks. 

    ax1.set_title(CorrString, fontsize=13,alpha=1)
    ax1.set_ylabel('Correlation', fontweight = 'bold'); i = 0
    for column in CorrDF.columns:
        numCCAvs = len(CorrDF.columns)
        traceName = column
        r = (i/(numCCAvs-1)); g = 0; b = 1 - (i/(numCCAvs-1))
        LW = 1+(i*0.25)
        ax1.plot(CorrDF[column], c =(r, g, b), label = traceName, linewidth = LW)
        i += 1
    ax1.legend(loc=1, fontsize='small',bbox_to_anchor=(1.09, 0.9))
    if ExtraAssets is True:
        ax1.text(x=NetLiquidity.index[round(len(NetLiquidity)/4)*3],y=(-0.95),s='Correlation between net liquidity & first asset.')
    ax1.set_ylim(-1.1, 1.1)
    for axis in ['top','bottom','left','right']:
            ax1.spines[axis].set_linewidth(1.5)  

    Xmax = max(NetLiquidity.index); Xmin = min(NetLiquidity.index)
    stepsize = (Xmax - Xmin) / 20
    XTicks = np.arange(Xmin, Xmax, stepsize); XTicks = np.append(XTicks,Xmax)
    ax1.xaxis.set_ticks(XTicks); ax.set_xlim(Xmin-datetime.timedelta(days=15),Xmax+datetime.timedelta(days=15))
    ax.tick_params(axis='x',length=0,labelsize=0)
    ax1.tick_params(axis='x',length=3,labelrotation=45,labelsize='small')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%y-%b'))
    ax1.minorticks_on()
    ax.grid(visible=True,axis='x',color='gray',linestyle='dotted',linewidth=0.75)
    ax1.grid(visible=True,which='both',color='gray',linestyle='dotted',linewidth=0.75)
    ax.legend(loc=2,fontsize='small'); axb.legend(loc=2,fontsize='small',bbox_to_anchor=(0,0.92)); axb.minorticks_on()
    ax.margins(y=0.02)
    if pd.isna(background) is False:
        ax.set_facecolor(background)
    return fig
              
########### Actual script from here down. #######################################################################
myFredAPI_key = Inputs.loc['API Key'].at['Additional FRED Data']
SaveFREDData = Inputs.loc['SaveFREDData'].at['Additional FRED Data']
NLQ_Color = Inputs.loc['NLQ_Color'].at['Additional FRED Data']
print('FRED API key: ',myFredAPI_key,', Save FRED data to: ',str(wd+FDel+'FRED_Data'))
if pd.isna(SaveFREDData) is False:    #Optional save FRED series data to disk. 
    SaveFredData = True
else:
    SaveFredData = False   

## Pull FRED series for net liquidity curve calculation ############# All the important parameters are set here. 
SeriesList = ["WALCL","RRPONTSYD",'WTREGEN'] #These are the 3 main series from FRED for the net lqiuidity curve calculation.
for i in range(1,6,1):
    ExtraSeries = Inputs.loc[i].at['Additional FRED Data']         ###Extra series are optionally added to be pulled from FRED. 
    if pd.isna(ExtraSeries):
        pass
    else: 
        SeriesList.append(ExtraSeries)
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
print('Start date',StartDate,', end date: ',EndDate)

############# Pull data from FRED. ###########################################
for seriesName in SeriesList:
    DataPull = PullFredSeries(seriesName,myFredAPI_key,start=DataStart,end=EndDateStr)
    SeriesDict[seriesName] = DataPull

if SaveFredData is True:       ###Save data series pulled from FRED to disk.
    for seriesName in SeriesDict.keys():
        DataPull = SeriesDict[seriesName]
        SeriesInfo = DataPull[0]; SeriesData = DataPull[1]
        df = pd.DataFrame(SeriesInfo)
        FREDSavePath = wd+FDel+'FRED_Data'
        filepath = FREDSavePath+FDel+seriesName+'.xlsx'
        df.to_excel(filepath,sheet_name='Sheet1')
        df2 = pd.DataFrame(SeriesData)
        with pd.ExcelWriter(filepath, engine='openpyxl', mode='a') as writer:  
            df2.to_excel(writer, sheet_name='Data')

############ Use daily Treasury general data from the US Treasury instead of the weekly data from FRED ##################
TGA_Past = pd.read_excel(wd+FDel+'TreasuryData'+FDel+'TGA_Since2005.xlsx')   #Loading most of the data from a pre-compiled excel file...
dtIndex = pd.DatetimeIndex(TGA_Past['record_date']); dtIndex = pd.DatetimeIndex(dtIndex.date)
TGA_Past.set_index(dtIndex,inplace=True)

for column in TGA_Past.columns:
    if re.search('1',column) is not None or re.search('record_date',column) is not None:
        TGA_Past.drop(column,axis=1,inplace=True)

TGA_Past.index.rename('record_date',inplace=True) 
FirstDay = TGA_Past.index[0].date(); LastDay = TGA_Past.index[len(TGA_Past)-1].date()
LastDate = datetime.datetime.strftime(LastDay,'%Y-%m-%d')
DateDiff = LastDay - FirstDay; Index = pd.date_range(FirstDay,LastDay,freq='D')
print('First day in TGA data: ',FirstDay,'Last day in TGA data: ',LastDay,', Length of data: ',len(TGA_Past),'. Date range: ',DateDiff.days)
#print('TGA data before update: ',TGA_Past)
print('Getting new data for the TGA from Treasury to update the TGA data excel file, please wait............')

CheckData2 = PullTGA_Data(AccountName = 'Treasury General Account (TGA) Closing Balance',start_date=LastDate)   #Check the latest data from treasury.
CheckData2.set_index(pd.DatetimeIndex(CheckData2.index),inplace=True); CheckData2.drop(['close_today_bal','account_type'],axis=1,inplace=True)
CheckData2.rename({'open_today_bal':'close_today_bal','open_month_bal':'month_close_bal_ifToday'},axis=1,inplace=True); CheckData2 = CheckData2.astype(int)
CheckData = PullTGA_Data(AccountName = 'Treasury General Account (TGA) Opening Balance',start_date=LastDate)   #Check the latest data from treasury. 
CheckData.set_index(pd.DatetimeIndex(CheckData2.index),inplace=True); CheckData.drop('close_today_bal',axis=1,inplace=True)
CheckData.replace({'Treasury General Account (TGA) Opening Balance':'Treasury General Account (TGA)'},inplace=True); Acc = CheckData['account_type']
Acc = Acc.astype(str); CheckData.drop('account_type',axis=1,inplace=True); CheckData = CheckData.astype(int)
CheckData = pd.concat([Acc,CheckData,CheckData2],axis=1)
CheckData = CheckData[['account_type','open_today_bal','close_today_bal','open_month_bal','month_close_bal_ifToday']]
LatestDayFromTreasury = pd.Timestamp(CheckData.index[len(CheckData)-1].date()).date()
print('TGA data dates to compare, latest data available at treasury: ',LatestDayFromTreasury,'\nLatest data in excel file: ',LastDate,'\n',type(LatestDayFromTreasury),type(LastDay))

if LatestDayFromTreasury > LastDay:    #This updates the excel file with TGA data, if more recent data is available from the treasury. 
    New_TGA_Data = CheckData.copy(); print('New TGA Data: ',New_TGA_Data)
    print('TGA data on Treasury site, updated last on: ',LatestDayFromTreasury, type(LatestDayFromTreasury))
    if LatestDayFromTreasury <= LastDay:
        print("It looks like there is no new data available from treasury, we'll go with what we've got..")
    else:
        TGA_Past = pd.concat([TGA_Past,New_TGA_Data],axis=0)
        try:
            TGA_Past.drop('record_date',axis=1,inplace=True)
        except:
            pass       
else:
    print('The excel file containing TGA data is up to date.\n')  

Index = pd.date_range(TGA_Past.index[0],TGA_Past.index[len(TGA_Past)-1],freq='D')
Index = pd.DatetimeIndex(Index)
if len(Index.difference(TGA_Past.index)) > 0:
    #print('Resample triggered')
    TGA_PastRS = PriceImporter.ReSampleToRefIndex(TGA_Past,Index,'D')
    #print('Data after resample: ',TGA_PastRS)  
TGA_Past.set_index('record_date',inplace=True)      
TGA_Past = TGA_Past[['account_type','open_today_bal','close_today_bal','open_month_bal','month_close_bal_ifToday']]
#print('TGA data after update: ',TGA_Past)
TGA_Past.to_excel(wd+FDel+'TreasuryData'+FDel+'TGA_Since2005.xlsx',index_label=TGA_Past.index.name)
TGA_PastRS.drop('month_close_bal_ifToday',axis=1,inplace=True)
TGA_PastRS.to_excel(wd+FDel+'TreasuryData'+FDel+'TGA_Since2005_RS.xlsx',index_label=TGA_Past.index.name)

TGA_Daily_Series = pd.Series(TGA_PastRS['close_today_bal'],name='TGA Bal. (Bil. $)')
TGA_Daily_Series /= 1000 # TGA account balance is in millions $ from the Treasury, convert to Billions $.  
TGA_Daily_Series = TGA_Daily_Series[StartDate:EndDate]
#print(TGA_Daily_Series)
print('TGA series, start & end dates: ',TGA_Daily_Series.index[0],TGA_Daily_Series.index[len(TGA_Daily_Series)-1])

################# Pull data for an asset/s to compare against fed liquidity and other FRED data ##############
CADict = {}; CAList = []
for i in range(1,6,1):
    CompAss = (Inputs.loc[i].at['Comparison Assets'],Inputs.loc[i].at['Price API'],\
        Inputs.loc[i].at['Comp. Asset Name'],Inputs.loc[i].at['TraceColor'])
    if pd.isna(CompAss[0]):
        pass
    else: 
        CAList.append(CompAss)   
if len(CAList) > 1:
    ExtraAssets = True  
else: 
    ExtraAssets = False       
print('List of comparison assets to pull data for: ',CAList) 

for i in range(len(CAList)):
    CompAss = CAList[i]
    ComparisonAsset = CompAss[0]; PriceAPI = CompAss[1]; AssetName = CompAss[2]; Color = CompAss[3]  ## Here you set the asset you want to compare against data. 
    AssetData = PriceImporter.PullDailyAssetData(ComparisonAsset,PriceAPI,DataStart,endDate=EndDateStr) ##This function tries a range of APIs to get price history for a given asset. 
    AssetData.sort_index(inplace=True)
    AssetData = AssetData[StartDate:EndDate]
    #print('Asset data pulled using PDAD function: ',AssetData,AssetData.index[0],StartDate,AssetData.index[len(AssetData)-1],EndDate)
    #print('Normalizing comparison assets, asset: ',ComparisonAsset, type(AssetData),AssetData.dtypes)
    if i == 0:
        FirstDS = AssetData.copy(); DSMax = FirstDS['Close'].max(); DSMin = FirstDS['Close'].min(); RightLabel = AssetName+' price (USD)'; FirstDSName = AssetName
        print('First dataset: '+AssetName+', other comparison asset datasets will be normalized to cover the range of this dataset.')
        print('First DS range, max: ', DSMax,', min: ',DSMin)
        CADict[AssetName] = (FirstDS,Color)
    else:
        maxDS = AssetData['Close'].max(); minDS = AssetData['Close'].min()
        AssetData = DSMin +((AssetData - minDS)*(DSMax-DSMin))/(maxDS-minDS) ###Normalize the curve to have range of the first dataset. 
        CADict[AssetName] = (AssetData,Color)

for key in SeriesDict.keys():    #Plot all of the fed series along wih comparison asset #1. 
    DataPull = SeriesDict[key]
    SeriesInfo = DataPull[0]; SeriesData = DataPull[1]
    #print(SeriesInfo)
    FedFig(SeriesData,SeriesInfo,RightSeries=FirstDS['Close'],rightlab=FirstDSName)

##### Calculate the FED net liquidity as defined by crew such as the legend Darius Dale of 42 Macro. #########
### All of this below reindexes the 3 main series to have the same indexes with daily frequency. 
FedBal = pd.DataFrame(SeriesDict['WALCL'][1]); TGA_FRED = pd.DataFrame(SeriesDict['WTREGEN'][1]); RevRep = pd.DataFrame(SeriesDict['RRPONTSYD'][1])
FedBal.sort_index(inplace=True); TGA_FRED.sort_index(inplace=True); RevRep.sort_index(inplace=True)
#FirstDate = min(FedBal.index.min(),TGA_FRED.index.min(),RevRep.index.min()); LastDate = max(FedBal.index.max(),TGA_FRED.index.max(),RevRep.index.max())
Findex = pd.date_range(StartDate,EndDate,freq='D'); #print('Master index: ',Findex)  
FedBal = FedBal.squeeze(); FedBal = pd.Series(FedBal); TGA_FRED = TGA_FRED.squeeze(); TGA_FRED = pd.Series(TGA_FRED); RevRep = RevRep.squeeze(); RevRep = pd.Series(RevRep)
#print('Index differentials, WALCL: ',Findex.difference(FedBal.index),'TGA_FRED: ',Findex.difference(TGA_FRED.index), 'RevRep: ',Findex.difference(RevRep.index))
if len(Findex.difference(FedBal.index)) > 0:
    FedBal = PriceImporter.ReSampleToRefIndex(FedBal,Findex,'D')
if len(Findex.difference(TGA_FRED.index)) > 0:
    TGA_FRED = PriceImporter.ReSampleToRefIndex(TGA_FRED,Findex,'D')
if len(Findex.difference(RevRep.index)) > 0:    
    RevRep = PriceImporter.ReSampleToRefIndex(RevRep,Findex,'D')
# print(TGA_Daily_Series,StartDate,TGA_Daily_Series.index[0],EndDate,TGA_Daily_Series.index[len(TGA_Daily_Series)-1])
# print(FedBal,StartDate,FedBal.index[0],EndDate,FedBal.index[len(FedBal)-1])
# print(TGA_FRED,StartDate,TGA_FRED.index[0],EndDate,TGA_FRED.index[len(TGA_FRED)-1])
# print(RevRep,StartDate,RevRep.index[0],EndDate,RevRep.index[len(RevRep)-1])
 
NetLiquidity = SeriesDict['WALCL'][1]-SeriesDict['WTREGEN'][1]-SeriesDict['RRPONTSYD'][1] #Weekly net liq calculation. No reindexing. Weekly and daily data combos, all FRED data. 
NetLiquidity = pd.Series(NetLiquidity,name='Fed net liq 1 (Bil $)'); NetLiquidity.dropna(inplace=True)
#print('Net liquidity using FRED weekly data: ',NetLiquidity)
NetLiquidity2 = pd.Series((FedBal - TGA_FRED - RevRep),name='Fed net liq 2 (Bil $)')    ##Resampled to daily data calculation. Data from FRED reseampled to daily frequency. 
#print('Net liquidity using FRED weekly data, resampled to daily: ',NetLiquidity2)
NetLiquidity3 = pd.Series((FedBal - TGA_Daily_Series - RevRep),name='Fed net liq 3 (Bil $)') ## Net liquidity calculated using daily data from the treasury in place of the FRED TGA series. 
#print('Net liquidity using Treasury daily data:',NetLiquidity3)
NLQ_MA = Inputs.loc['NLQ_MA (days)'].at['Additional FRED Data']; FaceColor = Inputs.loc['MainFig FaceColor'].at['Additional FRED Data']
if pd.isna(NLQ_MA):
    NLQMA1 = None; NLQMA2 = None; NLQMA3 = None
    pass
else:
    NLQMA1 = pd.Series(NetLiquidity).rolling(NLQ_MA).mean(); NLQMA2 = pd.Series(NetLiquidity2).rolling(NLQ_MA).mean(); NLQMA3 = pd.Series(NetLiquidity3).rolling(NLQ_MA).mean()

dic = {"id":"Net Liquidity",'title':"Net liquidity = WALCL - WTREGEN - RRPONTSYD","units_short":"USD-$",'frequency':'Weekly'}
Info = pd.Series(dic)
#SeriesDict["Net liquidity"] = (Info,NetLiquidity)
NetLiquidity.sort_index(inplace=True); FirstDS.sort_index(inplace=True)

Corrs = AssCorr(NetLiquidity,FirstDS['Close'],[90,180,365])
Corrs2 = AssCorr(NetLiquidity2,FirstDS['Close'],[90,180,365]) # Calculate Pearson correlation coefficients between NLQ and asset #1.
Corrs3 = AssCorr(NetLiquidity3,FirstDS['Close'],[90,180,365])
LiqFig = FedFig(NetLiquidity,Info,RightSeries=FirstDS['Close'],rightlab=FirstDSName)  #Plot the series from FRED along with asset #1. 
CorrDF = pd.DataFrame(Corrs[0]); CorrString = 'Correlation over the whole period: '+str(Corrs[1])
CorrDF2 = pd.DataFrame(Corrs2[0]); CorrString2 = 'Correlation over the whole period: '+str(Corrs2[1])
CorrDF3 = pd.DataFrame(Corrs3[0]); CorrString3 = 'Correlation over the whole period: '+str(Corrs3[1])

## Main figures ######
LYScale = Inputs.loc['Yscale'].at['Additional FRED Data']; RYScale = Inputs.loc['Yscale'].at['Additional FRED Data']
NLQ1 = MainFig(NetLiquidity,CADict,CorrDF,FirstDS,'Net Liquidity Fed weekly (USD)',CorrString,LYScale=LYScale,RYScale=RYScale,NLQ_Color=NLQ_Color,NLQMA=NLQMA1,background=FaceColor)
NLQ2 = MainFig(NetLiquidity2,CADict,CorrDF2,FirstDS,'Net Liquidity Fed resampled to daily (USD)',CorrString2,LYScale=LYScale,RYScale=RYScale,NLQ_Color=NLQ_Color,NLQMA=NLQMA2,background=FaceColor)
NLQ3 = MainFig(NetLiquidity3,CADict,CorrDF3,FirstDS,'Net Liquidity Fed using daily data from Treasury (USD)',CorrString3,LYScale=LYScale,RYScale=RYScale,NLQ_Color=NLQ_Color,NLQMA=NLQMA3,background=FaceColor)
plt.show() # Show figure/s. Function will remain running until you close the figure. 