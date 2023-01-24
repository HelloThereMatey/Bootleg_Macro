####### Required packages #####################################
import PriceImporter ## This is one of my custom scripts holding functions for pulling price data from APIs. Must be present in same folder as this file. 
#### These packages need to be installed via pip/pip3 on command line. 
import requests    
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
### These are standard python packages inludied in the latest distributions, I think. 
import datetime
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

def Correlation(Series1:pd.Series, Series2:pd.Series,period='Full'): #Calculate Pearson COrrelation co-efficient between two series with time frame: period. 
    if (period=='Full'):
        Cor = round(Series1.corr(other=Series2,method='pearson', min_periods=len(Series1)),3)
        try:
            print('The correlation over the entire length between the two series: '+Series1.name+' and '+Series1.name+' is: '+str(round(Cor,3))+'.')
        except:
            pass    
    else:
        Cor = Series1.rolling(period).corr(Series2) ##Using Pandas to calculate the correlation. 
        #print('Correlation sub-function, data series: ',Cor, type(Cor))
    return Cor 

def YoYCalcFromDaily(series:pd.Series):  #Transform a price history series with daily frequency to a YoY % change series with daily freq. 
    series = series.resample('D').mean()
    series.fillna(method='ffill',inplace=True) #This'l make it daily data even if weekly data is input. 
    YoYCalc = [np.nan for i in range(365)]
    for i in range(365,len(series),1):
        YoYCalc.append(((series[i]-series[i-365])/series[i-365])*100)
    YoYSeries = pd.Series(YoYCalc,index=series.index,name='YoY % change')    
    return YoYSeries

def PullFredSeries(series:str,apikey:str,start="1776-07-04",filetype="&file_type=json",outputDataName:str=None):    ##This pulls data series from FRED API. 
    series_header = "https://api.stlouisfed.org/fred/series?series_id="  
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
    #print('Units info for series: ',TheData.name,'Units:',SeriesInfo['units'],'#')
    units = SeriesInfo['units']
    
    if re.search('Millions',units) is not None:
        TheData /= 1000
    elif re.search('Billions',units) is not None:
        pass
    elif re.search('Thousands',units) is not None:
        TheData /= 1000000
    elif re.search('Trillions',units) is not None: 
        TheData *= 1000
    else: 
        print('CAUTION: Data units: ',SeriesInfo['units'],'are not standard for this calc, units may be incorrect.')
    if outputDataName is not None:
        df2.to_excel(wd+FDel+outputDataName+".xlsx")
        #dfraw.to_excel(wd+FDel+outputDataName+"_raw.xlsx")
    return SeriesInfo, TheData    

def PullTGA_Data(AccountName = 'Federal Reserve Account',start_date='2000-01-01'):
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
def MainFig(MainSeries:pd.Series,CADict:dict,CorrDF:pd.DataFrame,AssetData:pd.DataFrame,figname:str,CorrString:str,Mainlabel='Net liquidity (left)',LYScale='linear',RYScale='linear'):
    fig = plt.figure(num=figname,figsize=(15.5,7.5), tight_layout=True)
    gs = GridSpec(2, 1, top = 0.96, bottom=0.1,left=0.06,right=0.92, height_ratios=[2,1], hspace=0)
    NetLiquidity = MainSeries

    ax = fig.add_subplot(gs[0]); ax1 = fig.add_subplot(gs[1],sharex=ax)
    plot1 = ax.plot(NetLiquidity,color="blue",lw=2.25,label=Mainlabel)
    ax.minorticks_on()
    if LYScale == 'linear':
        ax.set_yscale('log')
    axb = ax.twinx()
    for CA in CADict.keys():
        AssDF = CADict[CA][0]
        axb.plot(AssDF['Close'],label=CA,color=CADict[CA][1]) 
    axb.set_ylabel(RightLabel,fontweight='bold')
    axb.legend(loc=2,fontsize='small',bbox_to_anchor=(0,0.92)); axb.minorticks_on()
    ax.set_title('Net liquidity: Fed bal. sheet - rev. repo bal. - treasury gen. account', fontweight='bold')
    ax.set_ylabel('Bil. of U.S. $', fontweight='bold')
    for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_linewidth(1.5)        
    ax.legend(loc=2,fontsize='small')
    if ExtraAssets is True:
        ax.text(0.85,0.95,s='Other assets vs right axis.\nNormalized to cover same range.',horizontalalignment='center',verticalalignment='center', transform=ax.transAxes)
    Eq_ymin = math.floor(AssetData['Close'].min()); Eq_ymax = math.ceil(AssetData['Close'].max())
    ymin = math.floor(NetLiquidity.min()); ymax = math.ceil(NetLiquidity.max())

    if LYScale == 'log' and RYScale == 'log':       ##This provides cool looking equally spaced log ticks and tick labels on both y axii. 
        axb.set_yscale('log')
        bTicks = np.real(np.logspace(start = np.log10(Eq_ymin), stop = np.log10(Eq_ymax), num=8, base=10)); bTicks.round(decimals=0,out=bTicks) 
        yTicks = np.real(np.logspace(start = np.log10(ymin), stop = np.log10(ymax), num=8, base=10)); yTicks.round(decimals=0,out=yTicks)
    elif LYScale == 'linear' and RYScale == 'linear': 
        bTicks = np.real(np.linspace(start = Eq_ymin, stop = Eq_ymax, num=8)); bTicks.round(decimals=0,out=bTicks)   
        yTicks = np.real(np.linspace(start = ymin, stop = ymax, num=8)); yTicks.round(decimals=0,out=yTicks)
    else:
        print('LYSCale and RYSCale must be set to the same values in the input file. Either log or linear, fatal ERORRRR.')    
        quit()
    bTicks = np.ndarray.astype(bTicks,dtype=int,copy=False); yTicks = np.ndarray.astype(yTicks,dtype=int,copy=False)     
    axb.grid(visible=True, which='major', axis='both', c='gray',ls=':',lw=0.75)
    axb.tick_params(axis='y',which='both',width=0,labelsize=0); axb.minorticks_off() #Had to do this to eliminate pesky ticks that kept coming on top of my custom ones. 
    axb.set_ylim((Eq_ymin-Eq_ymin*0.01), (Eq_ymax+Eq_ymax*0.01)) 
    axb.set_yticks(bTicks); axb.set_yticklabels(bTicks); axb.yaxis.set_major_formatter('${x:1.0f}')
    axb.tick_params(axis='y',which='major',width=0.5,labelsize='small')     #All this to get y custom evenly spaced log ticks. 
    ax.tick_params(axis='y',which='both',width=0,labelsize=0); ax.minorticks_off() #Had to do this to eliminate pesky ticks that kept coming on top of my custom ones. 
    ax.set_ylim((ymin-ymin*0.01), (ymax+ymax*0.01)) 
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
    return fig
              
########### Actual script from here down. #######################################################################
myFredAPI_key = Inputs.loc['API Key'].at['Additional FRED Data']
SaveFREDData = Inputs.loc['SaveFREDData'].at['Additional FRED Data']
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
if pd.isna(DayOne) is True:
    print('You must specify the starting date to pull data for in the inputs .xlsx file.')
    quit()
else:
    DataStart = str(DayOne)
    StartDate = datetime.datetime.strptime(DataStart,'%Y-%M-%d').date()

if pd.isna(LastDay) is True:
    EndDate = datetime.date.today(); EndDateStr = EndDate.strftime("%Y-%m-%d")
TimeLength=(EndDate-StartDate).days
print('Pulling data for date range: ',DataStart,' to ',EndDateStr,', number of days: ',TimeLength)

############# Pull data from FRED. ###########################################
for seriesName in SeriesList:
    DataPull = PullFredSeries(seriesName,myFredAPI_key,start=DataStart)
    SeriesDict[seriesName] = DataPull

if SaveFredData is True:
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
TGA_Past.set_index(pd.DatetimeIndex(TGA_Past['record_date']),inplace=True)
FirstDay = TGA_Past.index[0]; LastDay = TGA_Past.index[len(TGA_Past)-1]
#FirstDate = datetime.datetime.strptime(FirstDay,'%Y-%m-%d').date()
LastDate = datetime.datetime.strftime(LastDay,'%Y-%m-%d')
DateDiff = LastDay - FirstDay; Index = pd.date_range(FirstDay,LastDay,freq='D')
print('First day in TGA data: ',FirstDay,'Last day in TGA data: ',LastDay,', Length of data: ',len(TGA_Past),'. Date range: ',DateDiff.days)
print('Getting new data for the TGA from Treasury to update the TGA data excel file, please wait............')

CheckData = PullTGA_Data(AccountName = 'Treasury General Account (TGA) Closing Balance',start_date=LastDate)   #Check the latest data from treasury. 
CheckData.set_index(pd.DatetimeIndex(CheckData.index),inplace=True)

if CheckData.index[len(CheckData)-1] > LastDay:
    print(CheckData)
    CheckData2 = CheckData[['open_today_bal','open_month_bal']].astype(float)
    print('CheckData2: ',CheckData2)
    CheckData3 = CheckData['close_today_bal']; CheckData3.replace({'null':np.nan},inplace=True)
    CheckData.drop(['close_today_bal','open_today_bal','open_month_bal'],axis=1,inplace=True)
    New_TGA_Data = pd.concat([CheckData,CheckData3,CheckData2],axis=1)
    print(New_TGA_Data.dtypes,type(New_TGA_Data.index))
    LatestDayFromTreasury = CheckData.index[len(CheckData)-1]  # datetime.datetime.strptime(New_TGA_Data.index[len(New_TGA_Data)-1],'%Y-%m-%d')
    print('TGA data on Treasury site, updated last on: ',LatestDayFromTreasury, type(LatestDayFromTreasury))
    if LatestDayFromTreasury <= LastDay:
        print("It looks like there is no new data available from treasury, we'll go with what we've got..")
    else:
        TGA_Past = pd.concat([TGA_Past,New_TGA_Data],axis=0)
        print(TGA_Past.columns)
        TGA_Past.drop('record_date',axis=1,inplace=True)
        print(TGA_Past)
else:
    print('The excel file containing TGA data is up to date.\n')  

Index = pd.date_range(TGA_Past.index[0],TGA_Past.index[len(TGA_Past)-1],freq='D')
if len(TGA_Past.index.difference(Index)) > 0:
    TGA_Past = PriceImporter.ReSampleToRefIndex(TGA_Past,Index,'D')
TGA_Past.to_excel(wd+FDel+'TreasuryData'+FDel+'TGA_Since2005.xlsx')

TGA_Daily_Series = pd.Series(TGA_Past['open_today_bal'],name='TGA Bal. (Bil. $)')
TGA_Daily_Series /= 1000 # TGA account balance is in millions $ from the Treasury, convert to Billions $. 
if len(TGA_Daily_Series.index.difference(Index)) > 0:
    TGA_Daily_Series = PriceImporter.ReSampleToRefIndex(TGA_Daily_Series,Index,'D')

print('Daily TGA series from Treasury: ',TGA_Daily_Series)

################# Pull data for an asset to compare against fed liquidity and other FRED data ##############
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
    AssetData = PriceImporter.PullDailyAssetData(ComparisonAsset,PriceAPI,DataStart) ##This function tries a range of APIs to get price history for a given asset. 
    #print('Normalizing comparison assets, asset: ',ComparisonAsset, type(AssetData),AssetData.dtypes)
    if i == 0:
        FirstDS = AssetData; DSMax = FirstDS['Close'].max(); DSMin = FirstDS['Close'].min(); RightLabel = AssetName+' price (USD)'
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
    FedFig(SeriesData,SeriesInfo,RightSeries=AssetData['Close'],rightlab=AssetName)

##### Calculate the FED net liquidity as defined by crew such as the legend Darius Dale of 42 Macro. #########
### All of this reindexes the 3 main series to have the same indexes with daily frequency. 
FedBal = pd.DataFrame(SeriesDict['WALCL'][1]); TGA_FRED = pd.DataFrame(SeriesDict['WTREGEN'][1]); RevRep = pd.DataFrame(SeriesDict['RRPONTSYD'][1])
FirstDate = min(FedBal.index.min(),TGA_FRED.index.min(),RevRep.index.min()); LastDate = max(FedBal.index.max(),TGA_FRED.index.max(),RevRep.index.max())
Index = pd.date_range(FirstDate,LastDate,freq='D'); print('Master index: ',Index)
FedBal = FedBal.squeeze(); FedBal = pd.Series(FedBal); TGA_FRED = TGA_FRED.squeeze(); TGA_FRED = pd.Series(TGA_FRED); RevRep = RevRep.squeeze(); RevRep = pd.Series(RevRep)
print('Index differentials, WALCL: ',Index.difference(FedBal.index),'TGA_FRED: ',Index.difference(TGA_FRED.index), 'RevRep: ',Index.difference(RevRep.index))
if len(Index.difference(FedBal.index)) > 0:
    FedBal = PriceImporter.ReSampleToRefIndex(FedBal,Index,'D')
if len(Index.difference(TGA_FRED.index)) > 0:
    TGA_FRED = PriceImporter.ReSampleToRefIndex(TGA_FRED,Index,'D')
if len(Index.difference(RevRep.index)) > 0:    
    RevRep = PriceImporter.ReSampleToRefIndex(RevRep,Index,'D')
TGA_Daily_Series = TGA_Daily_Series[FirstDate:LastDate]
#print(TGA_Daily_Series,FirstDate,TGA_Daily_Series.index[0],LastDate,TGA_Daily_Series.index[len(TGA_Daily_Series)-1])
if (TGA_Daily_Series.index[len(TGA_Daily_Series)-1] < LastDate ):
    TGA_Daily_Series[LastDate] = TGA_Daily_Series[TGA_Daily_Series.index[len(TGA_Daily_Series)-1]]
    TGA_Daily_Series = TGA_Daily_Series.resample('D').mean()
    TGA_Daily_Series.fillna(method='ffill',inplace=True)
else:
    pass    

NetLiquidity = SeriesDict['WALCL'][1]-SeriesDict['WTREGEN'][1]-SeriesDict['RRPONTSYD'][1] #Original net liq calculation. No reindexing. Weekly and daily data combos. 
NetLiquidity = pd.Series(NetLiquidity,name='Fed net liq 1 (Bil $)'); NetLiquidity.dropna(inplace=True)
#print('Net liquidity using FRED weekly data: ',NetLiquidity)
NetLiquidity2 = pd.Series((FedBal - TGA_FRED - RevRep),name='Fed net liq 2 (Bil $)')    ##Resampled to daily data calculation.. NetLiquidity2 = pd.Series(NetLiquidity2)
#print('Net liquidity using FRED weekly data, resampled to daily: ',NetLiquidity2)
NetLiquidity3 = pd.Series((FedBal - TGA_Daily_Series - RevRep),name='Fed net liq 3 (Bil $)') ## Net liquidity calculated using daily data from the treasury. 
#print('Net liquidity using Treasury daily data:',NetLiquidity3)

dic = {"id":"Net Liquidity",'title':"Net liquidity = WALCL - WTREGEN - RRPONTSYD","units_short":"USD-$",'frequency':'Weekly'}
Info = pd.Series(dic)
SeriesDict["Net liquidity"] = (Info,NetLiquidity)
NetLiquidity.sort_index(inplace=True); AssetData.sort_index(inplace=True)

Corrs = AssCorr(NetLiquidity,AssetData['Close'],[90,180,365])
Corrs2 = AssCorr(NetLiquidity2,AssetData['Close'],[90,180,365])
Corrs3 = AssCorr(NetLiquidity3,AssetData['Close'],[90,180,365])
LiqFig = FedFig(NetLiquidity,Info,RightSeries=AssetData['Close'],rightlab=AssetName) #yscale="log",Ryscale='log'
CorrDF = pd.DataFrame(Corrs[0]); CorrString = 'Correlation over the whole period: '+str(Corrs[1])
CorrDF2 = pd.DataFrame(Corrs2[0]); CorrString2 = 'Correlation over the whole period: '+str(Corrs2[1])
CorrDF3 = pd.DataFrame(Corrs3[0]); CorrString3 = 'Correlation over the whole period: '+str(Corrs3[1])

## Main figure ######
LYScale = Inputs.loc['Yscale'].at['Additional FRED Data']; RYScale = Inputs.loc['Yscale'].at['Additional FRED Data']
NLQ1 = MainFig(NetLiquidity,CADict,CorrDF,FirstDS,'Net Liquidity Fed weekly (USD)',CorrString,LYScale=LYScale,RYScale=RYScale)
#NLQ2 = MainFig(NetLiquidity2,CADict,CorrDF2,FirstDS,'Net Liquidity Fed resampled to daily (USD)',CorrString2,LYScale=LYScale,RYScale=RYScale)
NLQ3 = MainFig(NetLiquidity3,CADict,CorrDF3,FirstDS,'Net Liquidity Fed using daily data from Treasury (USD)',CorrString3,LYScale=LYScale,RYScale=RYScale)
plt.show() # Show figure. Function will remain running until you close the figure. 