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
import re 

if sys.platform == "linux" or sys.platform == "linux2":        #This detects what operating system you're using so that the right folder delimiter can be use for paths. 
    FDel = '/'; OpSys = 'linux'
elif sys.platform == "darwin":
    FDel = '/'; OpSys = 'mac'
elif sys.platform == "win32":
    FDel = '\\' ; OpSys = 'windows'
print('System information: ',sys.platform, OpSys,', directory delimiter: ', FDel, ', working directory: ', wd)

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

########### Actual script starts from here down #######################################################################
NoString = 'no'
myFredAPI_key = Inputs.loc['API Key'].at['Additional FRED Data']
SaveFREDData = Inputs.loc['SaveFREDData'].at['Additional FRED Data']
NLQ_Color = Inputs.loc['NLQ_Color'].at['Additional FRED Data']
print('FRED API key: ',myFredAPI_key,', Save FRED data to: ',str(wd+FDel+'FRED_Data'))
if pd.isna(SaveFREDData) or str(SaveFREDData).upper() == NoString.upper():    #Optional save FRED series data to disk. 
    SaveFredData = False
else:  
    SaveFredData = True 

## Pull FRED series for net liquidity curve calculation ############# All the important parameters are set here. 
SeriesList = ["WALCL","RRPONTSYD",'WTREGEN'] #These are the 3 main series from FRED for the net lqiuidity curve calculation.
for i in range(1,6,1):
    ExtraSeries = Inputs.loc[i].at['Additional FRED Data']         ###Extra series are optionally added to be pulled from FRED. 
    Display = Inputs.loc[i].at['Display Individually']
    if pd.isna(ExtraSeries):
        pass
    else: 
        SeriesList.append((ExtraSeries,Display))
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

############# Pull data from FRED. ###########################################
for seriesName in SeriesList:
    if isinstance(seriesName,tuple):
        DataPull = PriceImporter.PullFredSeries(seriesName[0],myFredAPI_key,start=DataStart,end=EndDateStr)
        ls = list(DataPull); ls.append(seriesName[1])
        SeriesDict[seriesName[0]] = (tuple(ls))
    else:
        DataPull = PriceImporter.PullFredSeries(seriesName,myFredAPI_key,start=DataStart,end=EndDateStr)
        ls = list(DataPull); ls.append('no')
        SeriesDict[seriesName] = (tuple(ls))
if SaveFredData is True:       ###Save data series pulled from FRED to disk.
    for seriesName in SeriesDict.keys():
        DataPull = SeriesDict[seriesName]
        SeriesInfo = DataPull[0]; SeriesData = DataPull[1]
        df = pd.DataFrame(SeriesInfo)
        FREDSavePath = wd+FDel+'FRED_Data'
        filepath = FREDSavePath+FDel+seriesName+'.xlsx'
        df2 = pd.DataFrame(SeriesData)
        df2.to_excel(filepath,sheet_name='Data')
        with pd.ExcelWriter(filepath, engine='openpyxl', mode='a') as writer:  
            df.to_excel(writer, sheet_name='SeriesInfo')

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

CheckData2 = PriceImporter.PullTGA_Data(AccountName = 'Treasury General Account (TGA) Closing Balance',start_date=LastDate)   #Check the latest data from treasury.
CheckData2.set_index(pd.DatetimeIndex(CheckData2.index),inplace=True); CheckData2.drop(['close_today_bal','account_type'],axis=1,inplace=True)
CheckData2.rename({'open_today_bal':'close_today_bal','open_month_bal':'month_close_bal_ifToday'},axis=1,inplace=True); CheckData2 = CheckData2.astype(int)
CheckData = PriceImporter.PullTGA_Data(AccountName = 'Treasury General Account (TGA) Opening Balance',start_date=LastDate)   #Check the latest data from treasury. 
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
    ComparisonAsset = CompAss[0]; PriceAPI = CompAss[1]; AssetName = CompAss[2]; Color = CompAss[3] ## Here you set the asset you want to compare against data. 
    AssetData = PriceImporter.PullDailyAssetData(ComparisonAsset,PriceAPI,DataStart,endDate=EndDateStr) ##This function tries a range of APIs to get price history for a given asset. 
    AssetData.sort_index(inplace=True)
    AssetData = pd.DataFrame(AssetData[StartDate:EndDate])
    AssetData.to_excel(wd+FDel+'CompAssets'+FDel+AssetName+'.xlsx')
    if i == 0:
        FirstDS = AssetData.copy(); DSMax = FirstDS['Close'].max(); DSMin = FirstDS['Close'].min(); RightLabel = AssetName+' price (USD)'; FirstDSName = AssetName
        print('First dataset: '+AssetName+', other comparison asset datasets will be displayed so as to cover the Y - range of this first dataset.')
        print('First DS range, max: ', DSMax,', min: ',DSMin)
        CADict[AssetName] = (FirstDS,Color) ##The dataframes of comparison asset price history data is stored in a dictionary 'CADict' as a tuple with tracecolor (str) in 2nd position. 
    else:    
        CADict[AssetName] = (AssetData,Color)  ##The dataframes of comparison asset price history data is stored in a dictionary 'CADict' as a tuple with tracecolor in 2nd position. 

for key in SeriesDict.keys():    #Plot all of the fed series along wih comparison asset #1. 
    DataPull = SeriesDict[key]
    if len(DataPull) > 2:
        SeriesInfo = DataPull[0]; SeriesData = DataPull[1]; display = DataPull[2]
    else:
        SeriesInfo = DataPull[0]; SeriesData = DataPull[1] 
    if pd.isna(display) or str(display).upper() == NoString.upper():
        pass
    else:
        Charting.FedFig(SeriesData,SeriesInfo,RightSeries=FirstDS['Close'],rightlab=FirstDSName)

##### Calculate the FED net liquidity as defined by crew such as the legend Darius Dale of 42 Macro. #########
### All of this below reindexes the 3 main series to have the same indexes with daily frequency. 
FedBal = pd.DataFrame(SeriesDict['WALCL'][1]); TGA_FRED = pd.DataFrame(SeriesDict['WTREGEN'][1]); RevRep = pd.DataFrame(SeriesDict['RRPONTSYD'][1])
FedBal.sort_index(inplace=True); TGA_FRED.sort_index(inplace=True); RevRep.sort_index(inplace=True)
Findex = pd.date_range(StartDate,EndDate,freq='D'); #print('Master index: ',Findex)  
FedBal = FedBal.squeeze(); FedBal = pd.Series(FedBal); TGA_FRED = TGA_FRED.squeeze(); TGA_FRED = pd.Series(TGA_FRED); RevRep = RevRep.squeeze(); RevRep = pd.Series(RevRep)
if len(Findex.difference(FedBal.index)) > 0:
    FedBal = PriceImporter.ReSampleToRefIndex(FedBal,Findex,'D')
if len(Findex.difference(TGA_FRED.index)) > 0:
    TGA_FRED = PriceImporter.ReSampleToRefIndex(TGA_FRED,Findex,'D')
if len(Findex.difference(RevRep.index)) > 0:    
    RevRep = PriceImporter.ReSampleToRefIndex(RevRep,Findex,'D')

############ Main NET LIQUIDITY SERIES ##################################################################################### 
NetLiquidity = (SeriesDict['WALCL'][1]-SeriesDict['WTREGEN'][1]-SeriesDict['RRPONTSYD'][1]) #Weekly net liq calculation. No reindexing. Weekly and daily data combos, all FRED data. 
NetLiquidity = pd.Series(NetLiquidity,name='Fed net liq 1 (Bil $)'); NetLiquidity.dropna(inplace=True)
#print('Net liquidity using FRED weekly data: ',NetLiquidity)
NetLiquidity2 = pd.Series((FedBal - TGA_FRED - RevRep),name='Fed net liq 2 (Bil $)')    ##Resampled to daily data calculation. Data from FRED reseampled to daily frequency. 
#print('Net liquidity using FRED weekly data, resampled to daily: ',NetLiquidity2)
NetLiquidity3 = pd.Series((FedBal - TGA_Daily_Series - RevRep),name='Fed net liq 3 (Bil $)') ## Net liquidity calculated using daily data from the treasury in place of the FRED TGA series. 
USD_NetLiq = NetLiquidity3.copy()
#print('Net liquidity using Treasury daily data:',NetLiquidity3)
NetLiquidity.sort_index(inplace=True); FirstDS.sort_index(inplace=True)
savePath = wd+FDel+'NLQ_Data'+FDel+'NLQ_Data.xlsx'
NetLiquidity.to_excel(savePath,sheet_name='Weekly')
with pd.ExcelWriter(savePath, engine='openpyxl', mode='a') as writer:  
    NetLiquidity2.to_excel(writer, sheet_name='Resampled2Daily')
    NetLiquidity3.to_excel(writer, sheet_name='Daily_TGAData')

########## Load data for other CB balance sheets to calculate a global liquidity index in USD terms ###########################
LoadECB = Inputs.loc['Include_ECB'].at['Additional FRED Data']
LoadBOJ = Inputs.loc['Include_BOJ'].at['Additional FRED Data']
LoadPBOC = Inputs.loc['Include_PboC'].at['Additional FRED Data']
LoadBOE = Inputs.loc['Include_BoE'].at['Additional FRED Data']

MainLabel = 'USD Net liquidity (NLQ) = (FED - RevRepo - TGA)\n'                         ###This will be the label for the main NLQ trace on the figures. 

if pd.isna(LoadECB) or str(LoadECB).upper() == NoString.upper():  
    pass
else:  
    ECBData = PriceImporter.GetCBAssets_USD(",ECBASSETSW","FX,EURUSD",DataStart,SerName='ECB')        ##This gets the CB bal. sheet for all of the major
    ECB_USD = ECBData[0]; ECB_USD_Info = ECBData[1]                                     ## central banks of the world to clalculate a 'global liquidity' index.
    if len(Findex.difference(ECB_USD.index)) > 0:
        ECB_USD = PriceImporter.ReSampleToRefIndex(ECB_USD,Findex,'D')
    NetLiquidity = pd.Series((NetLiquidity+ECB_USD),name='NLQ'); NetLiquidity2 = pd.Series((NetLiquidity2+ECB_USD),name='NLQ')
    NetLiquidity3 = pd.Series((NetLiquidity3+ECB_USD),name='NLQ')     
    MainLabel += " + ECB"  
    with pd.ExcelWriter(savePath, engine='openpyxl', mode='a') as writer:  
        NetLiquidity.to_excel(writer, sheet_name='Weekly_plusECB')
        NetLiquidity2.to_excel(writer, sheet_name='Resamp_plusECB')
        NetLiquidity3.to_excel(writer, sheet_name='TGAData_PlusECB')   
if pd.isna(LoadBOJ) or str(LoadBOJ).upper() == NoString.upper():     ###Note: some CB's give recent data while some (like PBoC) make you wait months for update
    pass
else:
    BOJData = PriceImporter.GetBOJ_USD(myFredAPI_key,DataStart,EndDateStr)       # so they can front run your ass and rek the west son. 
    BOJ_USD = BOJData[0]; BOJ_USDInfo = BOJData[1]
    if len(Findex.difference(BOJ_USD.index)) > 0:
        BOJ_USD = PriceImporter.ReSampleToRefIndex(BOJ_USD,Findex,'D')   
    NetLiquidity = pd.Series((NetLiquidity+BOJ_USD),name='NLQ + BOJ'); NetLiquidity2 = pd.Series((NetLiquidity2+BOJ_USD),name='NLQ + BOJ')
    NetLiquidity3 = pd.Series((NetLiquidity3+BOJ_USD),name='NLQ + BOJ')  
    MainLabel += " + BOJ" 
    with pd.ExcelWriter(savePath, engine='openpyxl', mode='a') as writer:  
        NetLiquidity.to_excel(writer, sheet_name='Weekly_plusBOJ')
        NetLiquidity2.to_excel(writer, sheet_name='Resamp_plusBOJ')
        NetLiquidity3.to_excel(writer, sheet_name='TGAData_PlusBOJ')   
if pd.isna(LoadPBOC) or str(LoadPBOC).upper() == NoString.upper():   
    pass
else: 
    PBoCData = PriceImporter.GetCBAssets_USD("ECONOMICS,CNCBBS","FX_IDC,CNYUSD",DataStart,SerName='PBoC')
    PBoC_USD = PBoCData[0]; PBoC_USD_Info = PBoCData[1]
    if len(Findex.difference(PBoC_USD.index)) > 0:
        PBoC_USD = PriceImporter.ReSampleToRefIndex(PBoC_USD,Findex,'D')
    NetLiquidity = pd.Series((NetLiquidity+PBoC_USD),name='NLQ'); NetLiquidity2 = pd.Series((NetLiquidity2+PBoC_USD),name='NLQ')
    NetLiquidity3 = pd.Series((NetLiquidity3+PBoC_USD),name='NLQ')     
    MainLabel += " + PBoC"
    with pd.ExcelWriter(savePath, engine='openpyxl', mode='a') as writer:  
        NetLiquidity.to_excel(writer, sheet_name='Weekly_plusPBoC')
        NetLiquidity2.to_excel(writer, sheet_name='Resamp_plusPBoC')
        NetLiquidity3.to_excel(writer, sheet_name='TGAData_PlusPBoC')      
if pd.isna(LoadBOE) or str(LoadBOE).upper() == NoString.upper():  
    pass
else:  
    BoEData = PriceImporter.GetCBAssets_USD(",GBCBBS","FX,GBPUSD",DataStart,SerName='BoE')
    BoE_USD = BoEData[0]; BoE_USD_Info = BoEData[1]
    if len(Findex.difference(BoE_USD.index)) > 0:
        BoE_USD = PriceImporter.ReSampleToRefIndex(BoE_USD,Findex,'D')
    NetLiquidity = pd.Series((NetLiquidity+BoE_USD),name='NLQ'); NetLiquidity2 = pd.Series((NetLiquidity2+BoE_USD),name='NLQ')
    NetLiquidity3 = pd.Series((NetLiquidity3+BoE_USD),name='NLQ')     
    MainLabel += " + BoE" 
    with pd.ExcelWriter(savePath, engine='openpyxl', mode='a') as writer:  
        NetLiquidity.to_excel(writer, sheet_name='Weekly_plusBoE')
        NetLiquidity2.to_excel(writer, sheet_name='Resamp_plusBoE')
        NetLiquidity3.to_excel(writer, sheet_name='TGAData_PlusBoE') 
MainLabel += " bal. sheets (left axis)"   

#################  Chuck on a moving average of NLQ if requested by user. ############################################
NLQ_MA = Inputs.loc['NLQ_MA (days)'].at['Additional FRED Data']; FaceColor = Inputs.loc['MainFig FaceColor'].at['Additional FRED Data']
if pd.isna(NLQ_MA):
    NLQMA1 = None; NLQMA2 = None; NLQMA3 = None
    pass
else:
    NLQMA1 = pd.Series(NetLiquidity).rolling(NLQ_MA).mean(); NLQMA2 = pd.Series(NetLiquidity2).rolling(NLQ_MA).mean(); NLQMA3 = pd.Series(NetLiquidity3).rolling(NLQ_MA).mean()

print("Moving average for Net liquidity trace: ",NLQ_MA,' days.')
dic = {"id":"Net Liquidity",'title':"Net liquidity = WALCL - WTREGEN - RRPONTSYD","units_short":"USD-$",'frequency':'Weekly'}
dic2 = {"id":"TGA balance",'title':"Treasury General Account Balance (billions of USD)","units_short":"bil. of USD-$",'frequency':'Daily'}
Info = pd.Series(dic)
Info2 = pd.Series(dic2)

##### This is the code for plotting the original weekly series with all data sourced from FRED ########################
FontFamily = Inputs.loc['FontFamily'].at['Additional FRED Data']
DisMF1 = Inputs.loc['MainFig (Weekly)'].at['Additional FRED Data']              ##These variable choose whether or not to display the various charts. 
DisMF2 = Inputs.loc['MainFig (DailyResample)'].at['Additional FRED Data']
DisMF3 = Inputs.loc['MainFig (DailyTGA_Data)'].at['Additional FRED Data']
DisEle= Inputs.loc['FED NLQ Elements'].at['Additional FRED Data']
DisGEle = Inputs.loc['Global NLQ Elements'].at['Additional FRED Data']
NLQSimp = Inputs.loc['NLQ Simple chart'].at['Additional FRED Data']
TGA_D = Inputs.loc['TGA Daily'].at['Additional FRED Data']
G_Ele = Inputs.loc['Global NLQ Elements'].at['Additional FRED Data']

plt.rcParams['figure.dpi'] = 105; plt.rcParams['savefig.dpi'] = 200   ###Set the resolution of the displayed figs & saved fig respectively. 
if pd.isna(FontFamily) is False:     ###Set font family for the figures. 
    print('Using font family: ',FontFamily)
    plt.rcParams.update({'font.family':FontFamily})   

periodsList = Inputs['Correlation Periods'].dropna().astype(int).to_list(); periodsList.append(len(NetLiquidity3)-5)
print('Correlation periods to use on bottom chart: ',periodsList)
Corrs = PriceImporter.AssCorr(NetLiquidity,FirstDS['Close'],periodsList)
LYScale = Inputs.loc['Yscale'].at['Additional FRED Data']; RYScale = Inputs.loc['Yscale'].at['Additional FRED Data']
print('Scaling for main figures: ',LYScale,RYScale)
CorrDF = pd.DataFrame(Corrs[0]); CorrString = 'Correlation over the whole period: '+str(Corrs[1])
if pd.isna(DisMF1) or str(DisMF1).upper() == NoString.upper():
    pass
else:
    NLQ1 = Charting.MainFig(NetLiquidity,CADict,CorrDF,FirstDS,'Net Liquidity Fed weekly (USD)',CorrString,Mainlabel=MainLabel,LYScale=LYScale,RYScale=RYScale,NLQ_Color=NLQ_Color,\
    NLQMA=NLQMA1,background=FaceColor,RightLabel=RightLabel,YAxLabPrefix='$',NLQ_MAPer=NLQ_MA)

Corrs2 = PriceImporter.AssCorr(NetLiquidity2,FirstDS['Close'],periodsList) # Calculate Pearson correlation coefficients between NLQ and asset #1.
Corrs3 = PriceImporter.AssCorr(NetLiquidity3,FirstDS['Close'],periodsList)
CorrDF2 = pd.DataFrame(Corrs2[0]); CorrString2 = 'Correlation over the whole period: '+str(Corrs2[1])
CorrDF3 = pd.DataFrame(Corrs3[0]); CorrString3 = 'Correlation over the whole period: '+str(Corrs3[1])

####### Other figures ##############################################################################################################
if pd.isna(NLQSimp) or str(NLQSimp).upper() == NoString.upper():
    pass
else:
    LiqFig = Charting.FedFig(NetLiquidity,Info,RightSeries=FirstDS['Close'],rightlab=FirstDSName)  #Plot the series from FRED along with asset #1. 
if pd.isna(TGA_D) or str(TGA_D).upper() == NoString.upper():
    pass
else:
    TGA_Daily = Charting.FedFig(TGA_Daily_Series,Info2) 
if pd.isna(DisEle) or str(DisEle).upper() == NoString.upper():
    pass
else:
    Elements = Charting.NLQ_ElementsChart(FedBal,RevRep,TGA_Daily_Series,'Net liquidity elements')
if pd.isna(G_Ele) or str(G_Ele).upper() == NoString.upper():
    pass
else:    
    G_Elements = Charting.GNLQ_ElementsChart(NetLiquidity3,USD_NetLiq,'Global CB money Elements',YScale='linear',ECB=ECB_USD,BOJ=BOJ_USD,PBoC=PBoC_USD,BoE=BoE_USD)
    
########### For the other two NLQ series that have daily frequency, we can optionally transform them to YoY Delta%. ##########
TracesType = Inputs.loc['TracesType'].at['Additional FRED Data']     ##This does a YoY Delta% tarnsformation to the data if that is set in the inputs file. 

if TracesType == 'yoy':
    NetLiquidity2 = pd.Series(PriceImporter.YoYCalcFromDaily(NetLiquidity2)); NetLiquidity3 = pd.Series(PriceImporter.YoYCalcFromDaily(NetLiquidity3))
    NetLiquidity2.fillna(method='ffill',inplace=True); NetLiquidity3.fillna(method='ffill',inplace=True)
    NetLiquidity2.dropna(inplace=True); NetLiquidity3.dropna(inplace=True)
    #print('NLQ after fillna and dropna: ',NetLiquidity3)

    for key in CADict.keys():
        Entry = CADict[key]; Asset = pd.DataFrame(Entry[0]); Asset.set_index(pd.DatetimeIndex((pd.DatetimeIndex(Asset.index).date)),inplace=True)
        Close = Asset['Close']
        YoYAsset = pd.Series(PriceImporter.YoYCalcFromDaily(Close),name='Close'); Asset.drop('Close',axis=1,inplace=True)
        Asset = pd.concat([Asset,YoYAsset],axis=1)
        try:
            Asset = Asset[['Open','High','Low','Close','Volume']]
        except:
            pass    
        #print('YoY change transformed asset price history data: ',Asset.tail(54))
        CADict[key] = (Asset,Entry[1])
        if key == FirstDSName:
            FirstDS = Asset.copy()
    RightYMax = Inputs.loc['Right Ax Ymax'].at['Additional FRED Data']; print('YoY mode, Max of Right axis: ',RightYMax)
    if pd.isna(RightYMax):
        RyMax = FirstDS['Close'].max()
    else:
        RyMax = RightYMax  
    Corrs2 = PriceImporter.AssCorr(NetLiquidity2,FirstDS['Close'],periodsList) # Calculate Pearson correlation coefficients between NLQ and asset #1.
    Corrs3 = PriceImporter.AssCorr(NetLiquidity3,FirstDS['Close'],periodsList)
    CorrDF2 = pd.DataFrame(Corrs2[0]); CorrString2 = 'Correlation over the whole period: '+str(Corrs2[1])
    CorrDF3 = pd.DataFrame(Corrs3[0]); CorrString3 = 'Correlation over the whole period: '+str(Corrs3[1])
    if pd.isna(DisMF2) or str(DisMF2).upper() == NoString.upper():
        pass
    else:
        NLQ2 = Charting.MainFig(NetLiquidity2,CADict,CorrDF2,FirstDS,r'Net Liquidity Fed resampled to daily (YoY $\Delta$%)',CorrString2,\
            NLQ_Color=NLQ_Color,background=FaceColor,RightLabel=FirstDSName+r' YoY $\Delta$%',Xmin=NetLiquidity2.index[0],Xmax=NetLiquidity2.index[len(NetLiquidity2)-1],\
                RYMin=FirstDS['Close'].min(),RYMax=RyMax,LYScale=LYScale,RYScale=RYScale,Mainlabel=MainLabel,NLQ_MAPer=NLQ_MA)
    if pd.isna(DisMF3) or str(DisMF3).upper() == NoString.upper(): 
        print('Permission display strings: ',str(display).upper(),NoString.upper())   
        pass
    else:
        NLQ3 = Charting.MainFig(NetLiquidity3,CADict,CorrDF3,FirstDS,r'Net Liquidity Fed using daily data from Treasury (YoY $\Delta$%)',CorrString3,\
            NLQ_Color=NLQ_Color,background=FaceColor,RightLabel=FirstDSName+r' YoY $\Delta$%',Xmin=NetLiquidity3.index[0],Xmax=NetLiquidity3.index[len(NetLiquidity3)-1],\
                RYMin=FirstDS['Close'].min(),RYMax=RyMax,YLabel=r'YoY $\Delta$%',LYScale=LYScale,RYScale=RYScale,Mainlabel=MainLabel,NLQ_MAPer=NLQ_MA)        
else:
    ## Main figures ######
    if pd.isna(DisMF2) or str(DisMF2).upper() == NoString.upper():
        pass
    else:
        NLQ2 = Charting.MainFig(NetLiquidity2,CADict,CorrDF2,FirstDS,'Net Liquidity Fed resampled to daily (USD)',CorrString2,LYScale=LYScale,RYScale=RYScale,NLQ_Color=NLQ_Color,\
            NLQMA=NLQMA2,RightLabel=RightLabel,background=FaceColor,YAxLabPrefix='$',Mainlabel=MainLabel,NLQ_MAPer=NLQ_MA)
    if pd.isna(DisMF3) or str(DisMF3).upper() == NoString.upper():
        pass
    else:
        NLQ3 = Charting.MainFig(NetLiquidity3,CADict,CorrDF3,FirstDS,'Net Liquidity Fed using daily data from Treasury (USD)',CorrString3,LYScale=LYScale,RYScale=RYScale,\
            NLQ_Color=NLQ_Color,RightLabel=RightLabel,NLQMA=NLQMA3,background=FaceColor,YAxLabPrefix='$',Mainlabel=MainLabel,NLQ_MAPer=NLQ_MA)        
plt.show() # Show figure/s. Function will remain running until you close the figure.
