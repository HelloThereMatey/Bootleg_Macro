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
grampa = os.path.dirname(wd); grampa = os.path.dirname(grampa)

import sys ; sys.path.append(grampa)
from MacroBackend import PriceImporter, Utilities, Charting, Pull_Data ## This is one of my custom scripts holding functions for pulling price data from APIs. Your IDE might not find it before running script. 
 ##This script has all the matplotlib chart formatting code. That code is ugly, best to put it in a second file like this. 
## You may see: 'Import "MacroBackend" could not be resolved' & it looks like MacroBackend can't be found. However, it will be found when script is run. Disregard error. 
#### The below packages need to be installed via pip/pip3 on command line. These are popular, well vetted packages all. Just use 'pip install -r requirements.txt'
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
### These are standard python packages included in the latest python distributions. No need to install them. 
import datetime
import re 

plt.rcParams['figure.dpi'] = 105; plt.rcParams['savefig.dpi'] = 205   ###Set the resolution of the displayed figs & saved fig respectively. 

if sys.platform == "linux" or sys.platform == "linux2":        #This detects what operating system you're using so that the right folder delimiter can be use for paths. 
    fdel = '/'; OpSys = 'linux'
elif sys.platform == "darwin":
    fdel = '/'; OpSys = 'mac'
elif sys.platform == "win32":
    fdel = '\\' ; OpSys = 'windows'
print('System information: ',sys.platform, OpSys,', directory delimiter: ', fdel, ', working directory: ', wd)

Inputs = pd.read_excel(wd+fdel+'NetLiquidity_InputParams.xlsx', index_col=0)     ##Pull input parameters from the input parameters excel file. 
  
inputs_main_col = Inputs['Additional FRED Data'].to_dict()
mainLabelGenDict = {"Fed_BS_Full_Or_QE": ("USD Net liquidity (NLQ) = (FED (total) - RevRepo - TGA)\n", 'USD Net liquidity (NLQ) = (FED (QE only) - RevRepo - TGA)\n'), 
                    "Include_Remit": (' + Fed remittances ',""), "Include_ECB":  (" + ECB",""), "Include_BOJ":  (" + BOJ",""), "Include_PboC":  (" + PboC",""),
                    "Include_BoE":  (" + BOE",""), "Include_SNB":  (" + SNB","")}
MainLabel = ""
for key in mainLabelGenDict.keys():
    if key == "Fed_BS_Full_Or_QE":
        if inputs_main_col[key] == 'total':
            MainLabel += mainLabelGenDict[key][0]
        else:
            MainLabel += mainLabelGenDict[key][1]  
    else:
        if inputs_main_col[key] == 'yes':
            MainLabel += mainLabelGenDict[key][0]
        else:
            MainLabel += mainLabelGenDict[key][1]  
bals = ['Include_ECB', 'Include_BOJ', "Include_PboC", "Include_BoE", "Include_SNB"]            
if any(inputs_main_col[bal] == "yes" for bal in bals):   
    MainLabel += " bal. sheets (left axis)"       

################# Pull data for an asset/s to compare against fed liquidity and other FRED data ##############
def pull_comp_asset_data(Inputs: pd.DataFrame) -> dict:
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
    start_date = str(Inputs.loc["Start date"].at["Additional FRED Data"])
    end_date = str(Inputs.loc["End date"].at["Additional FRED Data"])
    if pd.isna(end_date) or end_date.upper() == "NAN":
        end_date = datetime.date.today().strftime("%Y-%m-%d")

    for i in range(1, len(CAList)+1, 1):
        ComparisonAsset = str(Inputs.loc[i].at['Comparison Assets'])
        source = Inputs.loc[i].at['Price API']
        AssetName = Inputs.loc[i].at['Comp. Asset Name']
        Color = Inputs.loc[i].at['TraceColor']
        if source == "tv":
            spli = ComparisonAsset.strip().split(","); ComparisonAsset = spli[0]; exchange = split[1]
        else:
            exchange = None    
        
        ## Here you set the asset you want to compare against data
        pulled_data = Pull_Data.dataset()
        pulled_data.get_data(source, ComparisonAsset, start_date, exchange_code=exchange, end_date=end_date, capitalize_column_names=True)
        AssetData = pulled_data.data; SeriesInfo = pulled_data.SeriesInfo
        print(f"Data pulled from {source} for {ComparisonAsset} from {start_date} to {end_date}. Datatype: ", type(AssetData))

        savePath = grampa+fdel+"User_Data"+fdel+'SavedData'+fdel+AssetName+'.xlsx'
        print('Saving new data set: ',ComparisonAsset,'to: ',savePath)
        AssetData.to_excel(savePath,sheet_name='Closing_Price')
        with pd.ExcelWriter(savePath, engine='openpyxl', mode='a') as writer:  
            SeriesInfo.to_excel(writer, sheet_name='SeriesInfo')
        AssetData.sort_index(inplace=True)
        AssetData = pd.DataFrame(AssetData[StartDate:EndDate])    

        if i == 1:
            FirstDS = AssetData.copy(); DSMax = FirstDS.max(); DSMin = FirstDS.min(); RightLabel = AssetName+' price (USD)'; FirstDSName = AssetName
            print('First dataset: '+AssetName+', other comparison asset datasets will be displayed so as to cover the Y - range of this first dataset.')
            print('First DS range, max: ', DSMax,', min: ',DSMin)
            CADict[AssetName] = (FirstDS,Color) ##The dataframes of comparison asset price history data is stored in a dictionary 'CADict' as a tuple with tracecolor (str) in 2nd position. 
        else:    
            CADict[AssetName] = (AssetData,Color)  ##The dataframes of comparison asset price history data is stored in a dictionary 'CADict' as a tuple with tracecolor in 2nd position. 
    return CADict, ExtraAssets, RightLabel,  FirstDSName

def fred_series(SeriesList: list, SaveFredData: bool = True):
    for seriesName in SeriesList:
        if isinstance(seriesName,tuple):
            DataPull = PriceImporter.PullFredSeries(seriesName[0],myFredAPI_key,start=DataStart,end=EndDateStr,Con2Bil=True)
            ls = list(DataPull); ls.append(seriesName[1])
            SeriesDict[seriesName[0]] = (tuple(ls))
        else:
            DataPull = PriceImporter.PullFredSeries(seriesName,myFredAPI_key,start=DataStart,end=EndDateStr,Con2Bil=True)
            ls = list(DataPull); ls.append('no')
            SeriesDict[seriesName] = (tuple(ls))
    if SaveFredData is True:       ###Save data series pulled from FRED to disk.
        for seriesName in SeriesDict.keys():
            DataPull = SeriesDict[seriesName]
            SeriesInfo = DataPull[0]; SeriesData = DataPull[1]
            df = pd.DataFrame(SeriesInfo)
            FREDSavePath = grampa+fdel+"User_Data"+fdel+'FRED_Data'
            filepath = FREDSavePath+fdel+seriesName+'.xlsx'
            df2 = pd.DataFrame(SeriesData)
            df2.to_excel(filepath,sheet_name='Data')
            with pd.ExcelWriter(filepath, engine='openpyxl', mode='a', if_sheet_exists="overlay") as writer:  
                df.to_excel(writer, sheet_name='SeriesInfo')
    return SeriesDict      

############ Use daily Treasury general data from the US Treasury instead of the weekly data from FRED ##################
def get_nlq_data(Findex: pd.DatetimeIndex):
    TGA_Past = pd.read_excel(grampa+fdel+"User_Data"+fdel+'TreasuryData'+fdel+'TGA_Since2005.xlsx')   #Loading most of the data from a pre-compiled excel file...
    dtIndex = pd.DatetimeIndex(TGA_Past['record_date']); dtIndex = pd.DatetimeIndex(dtIndex.date)
    TGA_Past.set_index(dtIndex,inplace=True); 
    try:    
        TGA_Past.drop("account_type",axis=1,inplace=True)  
    except:
        pass
    for column in TGA_Past.columns:
        if re.search('1',column) is not None or re.search('record_date',column) is not None:
            TGA_Past.drop(column,axis=1,inplace=True)

    TGA_Past.index.rename('record_date',inplace=True); 
    FirstDay = TGA_Past.index[0].date(); LastDay = TGA_Past.index[len(TGA_Past)-1].date()
    LastDate = datetime.datetime.strftime(LastDay,'%Y-%m-%d')
    DateDiff = LastDay - FirstDay; Index = pd.date_range(FirstDay,LastDay,freq='D')
    print('First day in TGA data: ',FirstDay,'Last day in TGA data: ',LastDay,', Length of data: ',len(TGA_Past),'. Date range: ',DateDiff.days)
    print('Getting new data for the TGA from Treasury to update the TGA data excel file, please wait............')

    CheckData2 = PriceImporter.PullTGA_Data(AccountName = 'Treasury General Account (TGA) Closing Balance',start_date=LastDate)   #Check the latest data from treasury.
    CheckData2.set_index(pd.DatetimeIndex(CheckData2.index),inplace=True); CheckData2.drop(['close_today_bal','account_type'],axis=1,inplace=True)
    CheckData2.rename({'open_today_bal':'close_today_bal','open_month_bal':'month_close_bal_ifToday'},axis=1,inplace=True); CheckData2 = CheckData2.astype(int)
    CheckData = PriceImporter.PullTGA_Data(AccountName = 'Treasury General Account (TGA) Opening Balance',start_date=LastDate)   #Check the latest data from treasury. 
    CheckData.set_index(pd.DatetimeIndex(CheckData2.index),inplace=True); CheckData.drop('close_today_bal',axis=1,inplace=True)
    CheckData.replace({'Treasury General Account (TGA) Opening Balance':'Treasury General Account (TGA)'},inplace=True); Acc = CheckData['account_type']
    Acc = Acc.astype(str); CheckData.drop('account_type',axis=1,inplace=True); CheckData = CheckData.astype(int)
    CheckData = pd.concat([Acc,CheckData,CheckData2],axis=1)
    CheckData = CheckData[['open_today_bal','close_today_bal','open_month_bal','month_close_bal_ifToday']]
    LatestDayFromTreasury = pd.Timestamp(CheckData.index[len(CheckData)-1].date()).date()
    print('TGA data dates to compare, latest data available at treasury: ',LatestDayFromTreasury,'\nLatest data in excel file: ',LastDate,'\n',type(LatestDayFromTreasury),type(LastDay))

    if LatestDayFromTreasury > LastDay:    #This updates the excel file with TGA data, if more recent data is available from the treasury. 
        New_TGA_Data = CheckData.copy(); 
        #print('New TGA Data: ',New_TGA_Data)
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
        
    TGA_Past = TGA_Past[['open_today_bal','close_today_bal','open_month_bal','month_close_bal_ifToday']]
    TGA_Past.to_excel(grampa+fdel+"User_Data"+fdel+'TreasuryData'+fdel+'TGA_Since2005.xlsx',index_label=TGA_Past.index.name)

    TGA_Daily_Series = pd.Series(TGA_Past['close_today_bal'],name='TGA Bal. (Bil. $)')
    if len(Index.difference(TGA_Daily_Series.index)) > 0:
        TGA_PastRS = PriceImporter.ReSampleToRefIndex(TGA_Daily_Series.copy(),Index,'D') 
    TGA_Daily_Series /= 1000 # TGA account balance is in millions $ from the Treasury, convert to Billions $.  
    TGA_Daily_Series = TGA_Daily_Series[StartDate:EndDate]
    print('TGA series, start & end dates: ',TGA_Daily_Series.index[0],TGA_Daily_Series.index[len(TGA_Daily_Series)-1])
        
    ##### Calculate the FED net liquidity as defined by crew such as the legend Darius Dale of 42 Macro. #########
    ### All of this below reindexes the 3 main series to have the same indexes with daily frequency.  
    if BS_Series == 'nan'or BS_Series.upper() == TotStr.upper():
        FedBal = pd.DataFrame(SeriesDict['WALCL'][1])   #Use the total fed balance sheet in the calculation. 
        NetLiquidity = (SeriesDict['WALCL'][1]-SeriesDict['WTREGEN'][1]-SeriesDict['RRPONTSYD'][1]) #Weekly net liq calculation. No reindexing. Weekly and daily data combos, all FRED data. 
        NetLiquidity = pd.Series(NetLiquidity,name='Fed net liq 1 (Bil $)'); NetLiquidity.dropna(inplace=True)
    elif BS_Series.upper() == QEStr.upper():
        FedBal = pd.DataFrame(SeriesDict['RESPPNTNWW'][1]) #Use the QE only part of the fed balance sheet in the calculation (better IMO). 
        NetLiquidity = (SeriesDict['RESPPNTNWW'][1]-SeriesDict['WTREGEN'][1]-SeriesDict['RRPONTSYD'][1]) 
        NetLiquidity = pd.Series(NetLiquidity,name='Fed net liq 1 (Bil $)'); NetLiquidity.dropna(inplace=True)
    else:
        print("Which series do you want to use for the Fed balance sheet. Set Fed_BS_Full_Or_QE parameter in input file to either 'QE' or 'total'")    
        quit()

    TGA_FRED = pd.DataFrame(SeriesDict['WTREGEN'][1]); RevRep = pd.DataFrame(SeriesDict['RRPONTSYD'][1])
    FedBal.sort_index(inplace=True); TGA_FRED.sort_index(inplace=True); RevRep.sort_index(inplace=True)
    FedBal = FedBal.squeeze(); FedBal = pd.Series(FedBal); TGA_FRED = TGA_FRED.squeeze(); TGA_FRED = pd.Series(TGA_FRED); RevRep = RevRep.squeeze(); RevRep = pd.Series(RevRep)
    if len(Findex.difference(FedBal.index)) > 0:
        FedBal = PriceImporter.ReSampleToRefIndex(FedBal,Findex,'D')
    if len(Findex.difference(TGA_FRED.index)) > 0:
        TGA_FRED = PriceImporter.ReSampleToRefIndex(TGA_FRED,Findex,'D')
    if len(Findex.difference(RevRep.index)) > 0:    
        RevRep = PriceImporter.ReSampleToRefIndex(RevRep,Findex,'D')
    if len(Findex.difference(TGA_Daily_Series.index)) > 0:    
        TGA_Daily_Series = PriceImporter.ReSampleToRefIndex(TGA_Daily_Series,Findex,'D')    

    ############ Main NET LIQUIDITY SERIES ##################################################################################### 
    #print('Net liquidity using FRED weekly data: ',NetLiquidity)
    NetLiquidity2 = pd.Series((FedBal - TGA_FRED - RevRep),name='Fed net liq 2 (Bil $)')    ##Resampled to daily data calculation. Data from FRED reseampled to daily frequency. 
    #print('Net liquidity using FRED weekly data, resampled to daily: ',NetLiquidity2)
    NetLiquidity3 = pd.Series((FedBal - TGA_Daily_Series - RevRep),name='Fed net liq 3 (Bil $)') ## Net liquidity calculated using daily data from the treasury in place of the FRED TGA series. 
    USD_NetLiq = NetLiquidity3.copy()
    #print('Net liquidity using Treasury daily data:',NetLiquidity3)
    #NetLiquidity.sort_index(inplace=True); FirstDS.sort_index(inplace=True)
    return NetLiquidity, NetLiquidity2, NetLiquidity3, USD_NetLiq, FedBal, TGA_FRED, RevRep, TGA_Daily_Series

def get_cb_bs_data(bs_dict: dict, nlq: pd.Series, nlq2: pd.Series, nlq3: pd.Series, data_start: str, savePath: str):
    NoString = 'no'; outName = 'US_NLQ'; cb_bal_sheets = {}; saveAt = grampa+fdel+"User_Data"+fdel+'NLQ_Data'+fdel+'CB_Bal_Sheets.xlsx'; i = 0
    for bs in bs_dict.keys():
        if pd.isna(bs_dict[bs][0]) or str(bs_dict[bs][0]).upper() == NoString.upper():  
            pass
        else:
            bal_sheet, CB_SeriesInfo, BSData, FXData = PriceImporter.GetCBAssets_USD(bs_dict[bs][1],bs_dict[bs][2],data_start, SerName= bs_dict[bs][3])
            cb_bal_sheets[bs_dict[bs][3]] = bal_sheet
            nlq = pd.Series((nlq+bal_sheet),name='Net liq. agg.')
            nlq2 = pd.Series((nlq2+bal_sheet),name='Net liq. agg.')
            nlq3 = pd.Series((nlq3+bal_sheet),name='Net liq. agg.')
            if os.path.exists(saveAt):
                with pd.ExcelWriter(saveAt, engine='openpyxl', mode='a', if_sheet_exists="overlay") as saver:
                    bal_sheet.to_excel(saver, sheet_name=bs_dict[bs][3])
            else:    
                bal_sheet.to_excel(saveAt, sheet_name=bs_dict[bs][3])

            outName += bs_dict[bs][4]
            with pd.ExcelWriter(savePath, engine='openpyxl', mode='a', if_sheet_exists="overlay") as writer:  
                nlq.to_excel(writer, sheet_name='Weekly_plus'+bs_dict[bs][3])
                nlq2.to_excel(writer, sheet_name='Resamp_plus'+bs_dict[bs][3])
                nlq3.to_excel(writer, sheet_name='TGAData_Plus'+bs_dict[bs][3])       
    return nlq, nlq2, nlq3, outName, cb_bal_sheets

if __name__ == "__main__":
    ########### Actual script starts from here down #######################################################################
    NoString = 'no'
    myFredAPI_key = Inputs.loc['API Key'].at['Additional FRED Data']
    if pd.isna(myFredAPI_key):
        keys = Utilities.api_keys()
        myFredAPI_key = keys.keys['fred']
    SaveFREDData = Inputs.loc['SaveFREDData'].at['Additional FRED Data']
    NLQ_Color = Inputs.loc['NLQ_Color'].at['Additional FRED Data']
    print('FRED API key: ',myFredAPI_key,', Save FRED data to: ',str(grampa+fdel+"User_Data"+fdel+'FRED_Data'))
    if pd.isna(SaveFREDData) or str(SaveFREDData).upper() == NoString.upper():    #Optional save FRED series data to disk. 
        SaveFredData = False
    else:  
        SaveFredData = True 
    savePath = grampa+fdel+"User_Data"+fdel+'NLQ_Data'+fdel+'NLQ_Data.xlsx'    

    ## Pull FRED series for net liquidity curve calculation ############# All the important parameters are set here. 
    BS_Series = str(Inputs.loc['Fed_BS_Full_Or_QE'].at['Additional FRED Data']); QEStr = 'qe'; TotStr = 'total'
    SeriesList = ["WALCL","RRPONTSYD",'WTREGEN'] #These are the 3 main series from FRED for the net lqiuidity curve calculation.
    if BS_Series.upper() == QEStr.upper():
        SeriesList.append('RESPPNTNWW')
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
        DataStart = str(DayOne); split = DataStart.split(' '); DataStart = split[0]
        StartDate = datetime.datetime.strptime(DataStart,'%Y-%m-%d').date()

    if pd.isna(LastDay) is True:
        EndDate = datetime.date.today(); EndDateStr = EndDate.strftime('%Y-%m-%d')
    else:
        EndDateStr = str(LastDay); split = EndDateStr.split(' '); EndDateStr = split[0]
        EndDate = datetime.datetime.strptime(EndDateStr,'%Y-%m-%d').date()
    TimeLength=(EndDate-StartDate).days
    print('Pulling data for date range: ',DataStart,' to ',EndDateStr,', number of days: ',TimeLength)
    print('Start date:',StartDate,', end date: ',EndDate)
    Findex = pd.date_range(StartDate,EndDate,freq='D')

    ############# Pull data from FRED. ###########################################
    NLQ_source = Inputs.loc['NLQ Source'].at['Additional FRED Data']

    CADict, ExtraAssets, RightLabel, FirstDSName = pull_comp_asset_data(Inputs)
    FirstDS = CADict[FirstDSName][0]
    SeriesDict = fred_series(SeriesList, SaveFredData=SaveFREDData)
    if NLQ_source == "load_latest":
        loadPath = grampa+fdel+"User_Data"+fdel+"NLQ_Data"+fdel+"NLQ_Data.xlsx"
        NetLiquidity = pd.read_excel(loadPath, sheet_name = "Weekly",index_col=0).squeeze()
        NetLiquidity2 = pd.read_excel(loadPath, sheet_name = "Resampled2Daily",index_col=0).squeeze()
        NetLiquidity3 = pd.read_excel(loadPath, sheet_name = "Daily_TGAData",index_col=0).squeeze()
        FedBal = pd.read_excel(loadPath, sheet_name='Fed_Bal_Sheet', index_col=0).squeeze()
        RevRep = pd.read_excel(loadPath, sheet_name='RRP', index_col=0).squeeze()
        TGA_Daily_Series = pd.read_excel(loadPath, sheet_name='TGA', index_col=0).squeeze()
        cb_bal_sheets = pd.read_excel(grampa+fdel+"User_Data"+fdel+'NLQ_Data'+fdel+'CB_Bal_Sheets.xlsx', sheet_name=None, index_col=0)
        USD_NetLiq = FedBal - RevRep - TGA_Daily_Series
        print('NLQ loaded from file rather than updating data. Loaded from: ', grampa+fdel+"User_Data"+fdel+"NLQ_Data"+fdel+"NLQ_Data.xlsx")
        
    else:
        NetLiquidity, NetLiquidity2, NetLiquidity3, USD_NetLiq, FedBal, TGA_FRED, RevRep, TGA_Daily_Series = get_nlq_data(Findex)

    for key in SeriesDict.keys():    #Plot all of the fed series along wih comparison asset #1. 
        DataPull = SeriesDict[key]
        if len(DataPull) > 2:
            SeriesInfo = DataPull[0]; SeriesData = DataPull[1]; display = DataPull[2]
        else:
            SeriesInfo = DataPull[0]; SeriesData = DataPull[1] 
        if pd.isna(display) or str(display).upper() == NoString.upper():
            pass
        else:
            Charting.FedFig(SeriesData,SeriesInfo,RightSeries=FirstDS,rightlab=FirstDSName) 

    ################ Add the weekly remittances from Fed to TGA to the NLQ series if desired ##################################################   
    AddFedBills = Inputs.loc['Include_Remit'].at['Additional FRED Data'] 
    ChartFedBills = Inputs.loc['FED remittances'].at['Additional FRED Data'] 
    filePath = grampa+fdel+'User_Data'+fdel+'SavedData'+fdel+'RESPPLLOPNWW.xlsx'

    if AddFedBills == 'yes':
        print("Getting weekly Fed TGA remittances from FRED.")
        if ChartFedBills == 'yes':
            FedBills, plot = PriceImporter.GetFedBillData(filePath,StartDate,SepPlot=True)
        else:
            FedBills = PriceImporter.GetFedBillData(filePath,StartDate)
        FedBills = pd.Series(FedBills,name='Weekly remittances FED -> TGA')
        FedBills /= 7
        lastVal = FedBills[len(FedBills)-1]
        FedBills[pd.Timestamp(EndDate)] = lastVal
        FedBills = FedBills.resample('D').mean()
        FedBills = PriceImporter.ReSampleToRefIndex(FedBills, Findex, freq = 'D')
        FedBills.fillna(0, inplace=True)
        FedBills.fillna(method='ffill', inplace=True)
        FedBills.to_excel(grampa+fdel+"User_Data"+fdel+'NLQ_Data'+fdel+'Fed_Remittances.xlsx')
        if NLQ_source != 'load_latest':
            NetLiquidity3 -= FedBills

    ########## Load data for other CB balance sheets to calculate a global liquidity index in USD terms ###########################
    LoadECB = Inputs.loc['Include_ECB'].at['Additional FRED Data']
    LoadBOJ = Inputs.loc['Include_BOJ'].at['Additional FRED Data']
    LoadPBOC = Inputs.loc['Include_PboC'].at['Additional FRED Data']
    LoadBOE = Inputs.loc['Include_BoE'].at['Additional FRED Data']
    LoadSNB = Inputs.loc['Include_SNB'].at['Additional FRED Data']      ####Add Swiss National bank CB - not yet added. 

    bs_dict = {"Include_ECB": (LoadECB, ",ECBASSETSW", "FX,EURUSD", 'ECB', "_ECB"), 'Include_BOJ': (LoadBOJ, "ECONOMICS,JPCBBS","FX_IDC,JPYUSD", 'BOJ', "_BOJ"),
                'Include_PboC': (LoadPBOC, "ECONOMICS,CNCBBS","FX_IDC,CNYUSD", 'PBoC', "_PBoC"), 'Include_BoE': (LoadBOE, "ECONOMICS,GBCBBS","FX,GBPUSD", 'BoE', "_BoE"), 
                'Include_SNB': (LoadSNB, "ECONOMICS,CHBBS","FX_IDC,CHFUSD", 'SNB', "_SNB")}
    
    if NLQ_source != 'load_latest':
        NetLiquidity, NetLiquidity2, NetLiquidity3, outName, cb_bal_sheets  = get_cb_bs_data(bs_dict, NetLiquidity, NetLiquidity2, NetLiquidity3, 
                                                                            data_start=DataStart, savePath=savePath) 

    Get_DXY = Inputs.loc['Get_DXY'].at['Additional FRED Data']  #Get DXY and divide the foreign CB bal sheets by DXY to norm. for dollar strength. 
    if pd.isna(Get_DXY) or str(Get_DXY).upper() == NoString.upper():
        Norm2DXY = False
    else:
        DXY = Pull_Data.dataset("yfinance","DX-Y.NYB", DataStart,endDate=EndDateStr).data  #Plot the series from FRED along with asset #1. 
        DXY = PriceImporter.ReSampleToRefIndex(DXY,Findex,'D') 
        Norm2DXY = True
        NetLiquidity3 = NetLiquidity3/(1/DXY)

    if Inputs.loc['Include_Deficit'].at['Additional FRED Data'] == 'yes':
        print("Getting US budget deficit data from FRED.")
        deficit_info, deficit = PriceImporter.PullFredSeries("MTSDS133FMS",myFredAPI_key,start=DataStart,end=EndDateStr,Con2Bil=True)
        last_value = pd.Series([deficit.iloc[-1]], index=[deficit.index[-1] + pd.offsets.MonthEnd(1)])
        deficit = pd.concat([deficit, last_value])  
        deficit_d = deficit.resample('D').ffill()
        # Divide each month's data by the number of days in that month
        deficit_d = deficit_d.groupby(deficit_d.index.to_period('M')).transform(lambda x: x / len(x))
        # deficit_cs = deficit_d.cumsum()
        deficit_de = PriceImporter.ReSampleToRefIndex(deficit_d,Findex,'D') 
        NetLiquidity3 -= deficit_de
    
        deficit.to_excel(grampa+fdel+"User_Data"+fdel+'NLQ_Data'+fdel+'US_Budget_Deficit.xlsx', sheet_name='Data')
        with pd.ExcelWriter(grampa+fdel+"User_Data"+fdel+'NLQ_Data'+fdel+'US_Budget_Deficit.xlsx', engine='openpyxl', mode='a', if_sheet_exists="replace") as writer:  
            deficit_info.to_excel(writer, sheet_name='SeriesInfo')
            deficit_d.to_excel(writer, sheet_name='Daily_Avg')
        MainLabel += '\n+ Gov. deficit'    
        if Inputs.loc['Fed_Deficit'].at['Additional FRED Data'] == 'yes':
            left = {"Fed_Def": (deficit_d,"red",1.5)}
            red_hole_fig = Charting.TwoAxisFig(left, "linear", "USD (bil. of $)", "U.S Gov getting deep in the red son...., daily resample")

    if Inputs.loc['Include_BTFP'].at['Additional FRED Data'] == 'yes':
        print("Getting BTFP balance data from FRED.")
        btfp_meta, btfp = PriceImporter.PullFredSeries("H41RESPPALDKNWW",myFredAPI_key,start=DataStart,end=EndDateStr,Con2Bil=True)
        btfp_d = btfp.resample('D').ffill()
        btfp_d = PriceImporter.ReSampleToRefIndex(btfp_d,Findex,'D') 
        NetLiquidity3 += btfp_d
        MainLabel += ' + BTFP'
        if Inputs.loc['BTFP'].at['Additional FRED Data'] == 'yes':
            left = {"BTFP_Bal": (btfp_d,"black",1.5)}
            btfp_fig = Charting.TwoAxisFig(left, "linear", "USD (bil. of $)", "Bank Term Funding Program balance, daily resample")

    #################  Chuck on a moving average of NLQ if requested by user. ############################################
    NLQ_MA = Inputs.loc['NLQ_MA (days)'].at['Additional FRED Data']; FaceColor = Inputs.loc['MainFig FaceColor'].at['Additional FRED Data']
    Smooth = Inputs.loc['Use_Smoothed'].at['Additional FRED Data']
    if pd.isna(Smooth) or Smooth == 'no':
        Use_Smoothed = False
    else:
        Use_Smoothed = True
    if pd.isna(NLQ_MA):
        NLQMA1 = None; NLQMA2 = None; NLQMA3 = None
        pass
    elif pd.isna(NLQ_MA) is False and Use_Smoothed is True:
        NLQMA1 = pd.Series(NetLiquidity).rolling(NLQ_MA).mean(); NLQMA2 = pd.Series(NetLiquidity2).rolling(NLQ_MA).mean(); NLQMA3 = pd.Series(NetLiquidity3).rolling(NLQ_MA).mean()
        NetLiquidity = NLQMA1.copy(); NetLiquidity2 = NLQMA2.copy(); NetLiquidity3 = NLQMA3.copy()
        MainLabel += ' '+str(NLQ_MA)+' MA '
    else:
        NLQMA1 = pd.Series(NetLiquidity).rolling(NLQ_MA).mean(); NLQMA2 = pd.Series(NetLiquidity2).rolling(NLQ_MA).mean(); NLQMA3 = pd.Series(NetLiquidity3).rolling(NLQ_MA).mean()

    print("Moving average for Net liquidity trace: ",NLQ_MA,' days.')

    ############### SAVE FINAL DATA ##########################################################
    if NLQ_source != 'load_latest':
        dic = {"id":"Net Liquidity",'title':"Net liquidity = WALCL - WTREGEN - RRPONTSYD","units_short":"USD-$",'frequency':'Weekly'}
        dic2 = {"id":"TGA balance",'title':"Treasury General Account Balance (billions of USD)","units_short":"bil. of USD-$",'frequency':'Daily'}
        Info = pd.Series(dic)
        Info2 = pd.Series(dic2)
        NLQ_Info = {"id":"CB bal. sheets",'title':"Central bank Balance sheet aggregate","units_short":"bil. of USD-$",
                    'frequency':'Daily', 'Source': 'SavedData', 'LegendName': MainLabel, 'name': outName}
        
        NetLiquidity.to_excel(savePath,sheet_name='Weekly')
        with pd.ExcelWriter(savePath, engine='openpyxl', mode='a', if_sheet_exists="replace") as writer:  
            NetLiquidity2.to_excel(writer, sheet_name='Resampled2Daily')
            NetLiquidity3.to_excel(writer, sheet_name='Daily_TGAData')
            FedBal.to_excel(writer, sheet_name='Fed_Bal_Sheet')
            RevRep.to_excel(writer, sheet_name='RRP')
            TGA_Daily_Series.to_excel(writer, sheet_name='TGA')

        ########  Export_Series to macro_chartist as well
        savePath_2 = grampa+fdel+'User_Data'+fdel+'SavedData'+fdel+outName+'.xlsx'
        print('Saving aggregated NLQ as: ',savePath)
        NetLiquidity3.to_excel(savePath_2,sheet_name='Closing_Price')
        with pd.ExcelWriter(savePath_2, engine='openpyxl', mode='a', if_sheet_exists="replace") as writer:  
            pd.Series(NLQ_Info).to_excel(writer, sheet_name='SeriesInfo')

######### MATPLOTLIB RELATED CODE BELOW HERE ################################################################################
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

    if pd.isna(FontFamily) is False:     ###Set font family for the figures. 
        print('Using font family: ',FontFamily)
        plt.rcParams.update({'font.family':FontFamily})   

    periodsList = Inputs['Correlation Periods'].dropna().astype(int).to_list(); periodsList.append(len(NetLiquidity3)-5)
    print('Correlation periods to use on bottom chart: ',periodsList)
    Corrs = PriceImporter.AssCorr(NetLiquidity,FirstDS,periodsList)
    LYScale = Inputs.loc['Yscale'].at['Additional FRED Data']; RYScale = Inputs.loc['Yscale'].at['Additional FRED Data']
    print('Scaling for main figures: ',LYScale,RYScale)
    CorrDF = pd.DataFrame(Corrs[0]); CorrString = 'Correlation over the whole period: '+str(Corrs[1])
    if pd.isna(DisMF1) or str(DisMF1).upper() == NoString.upper():
        pass
    else:
        NLQ1 = Charting.MainFig(NetLiquidity,CADict,CorrDF,FirstDS,'Net Liquidity Fed weekly (USD)',CorrString,Mainlabel=MainLabel,LYScale=LYScale,RYScale=RYScale,NLQ_Color=NLQ_Color,\
        NLQMA=NLQMA1,background=FaceColor,RightLabel=RightLabel,YAxLabPrefix='$',NLQ_MAPer=NLQ_MA)

    Corrs2 = PriceImporter.AssCorr(NetLiquidity2,FirstDS,periodsList) # Calculate Pearson correlation coefficients between NLQ and asset #1.
    Corrs3 = PriceImporter.AssCorr(NetLiquidity3,FirstDS,periodsList)
    CorrDF2 = pd.DataFrame(Corrs2[0]); CorrString2 = 'Correlation over the whole period: '+str(Corrs2[1])
    CorrDF3 = pd.DataFrame(Corrs3[0]); CorrString3 = 'Correlation over the whole period: '+str(Corrs3[1])

    ####### Other figures ##############################################################################################################
    if pd.isna(NLQSimp) or str(NLQSimp).upper() == NoString.upper():
        pass
    else:
        LiqFig = Charting.FedFig(NetLiquidity,Info,RightSeries=FirstDS,rightlab=FirstDSName)  #Plot the series from FRED along with asset #1. 
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
        if Norm2DXY is True:
            G_Elements = Charting.GNLQ_ElementsChart(NetLiquidity3,'Global CB money Elements',YScale='linear',ECB=cb_bal_sheets['ECB'],BOJ=cb_bal_sheets['BOJ'],PBoC=cb_bal_sheets['PBoC']) #BoE=BoE_USD
        else:
            G_Elements = Charting.GNLQ_ElementsChart(NetLiquidity3,'Global CB money Elements',YScale='linear',US_NLQ=USD_NetLiq,ECB=cb_bal_sheets['ECB'],BOJ=cb_bal_sheets['BOJ'],PBoC=cb_bal_sheets['PBoC'],SNB=cb_bal_sheets['SNB'])    
        
    ########### For the other two NLQ series that have daily frequency, we can optionally transform them to YoY Delta%. ##########
    TracesType = Inputs.loc['TracesType'].at['Additional FRED Data']     ##This does a YoY Delta% tarnsformation to the data if that is set in the inputs file. 

    if TracesType == 'Year on year % change':
        NetLiquidity2 = pd.Series(PriceImporter.YoYCalcFromDaily(NetLiquidity2)); NetLiquidity3 = pd.Series(PriceImporter.YoYCalcFromDaily(NetLiquidity3))
        NetLiquidity2.ffill(inplace=True); NetLiquidity3.ffill(inplace=True)
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
            RyMax = FirstDS.max()
        else:
            RyMax = RightYMax  
        Corrs2 = PriceImporter.AssCorr(NetLiquidity2,FirstDS,periodsList) # Calculate Pearson correlation coefficients between NLQ and asset #1.
        Corrs3 = PriceImporter.AssCorr(NetLiquidity3,FirstDS,periodsList)
        CorrDF2 = pd.DataFrame(Corrs2[0]); CorrString2 = 'Correlation over the whole period: '+str(Corrs2[1])
        CorrDF3 = pd.DataFrame(Corrs3[0]); CorrString3 = 'Correlation over the whole period: '+str(Corrs3[1])
        if pd.isna(DisMF2) or str(DisMF2).upper() == NoString.upper():
            pass
        else:
            NLQ2 = Charting.MainFig(NetLiquidity2,CADict,CorrDF2,FirstDS,r'Net Liquidity Fed resampled to daily (YoY $\Delta$%)',CorrString2,\
                NLQ_Color=NLQ_Color,background=FaceColor,RightLabel=FirstDSName+r' YoY $\Delta$%',Xmin=NetLiquidity2.index[0],Xmax=NetLiquidity2.index[len(NetLiquidity2)-1],\
                    RYMin=FirstDS.min(),RYMax=RyMax,LYScale=LYScale,RYScale=RYScale,Mainlabel=MainLabel,NLQ_MAPer=NLQ_MA)
        if pd.isna(DisMF3) or str(DisMF3).upper() == NoString.upper(): 
            print('Permission display strings: ',str(display).upper(),NoString.upper())   
            pass
        else:
            NLQ3 = Charting.MainFig(NetLiquidity3,CADict,CorrDF3,FirstDS,r'Net Liquidity Fed using daily data from Treasury (YoY $\Delta$%)',CorrString3,\
                NLQ_Color=NLQ_Color,background=FaceColor,RightLabel=FirstDSName+r' YoY $\Delta$%',Xmin=NetLiquidity3.index[0],Xmax=NetLiquidity3.index[len(NetLiquidity3)-1],\
                    RYMin=FirstDS.min(),RYMax=RyMax,YLabel=r'YoY $\Delta$%',LYScale=LYScale,RYScale=RYScale,Mainlabel=MainLabel,NLQ_MAPer=NLQ_MA)        
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
