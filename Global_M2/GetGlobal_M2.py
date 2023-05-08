import os
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
dir = os.path.dirname(wd)
print(wd,dir)
import sys ; sys.path.append(dir)
from MacroBackend import tvDatafeedz
import pandas as pd
from matplotlib import colors as mcolors
import matplotlib.pylab as pl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import re 
import numpy as np
import datetime
wd = os.path.dirname(os.path.realpath(__file__)); print(wd)

colors = ['aqua','black', 'blue', 'blueviolet', 'brown'
 , 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral', 'cornflowerblue', 'crimson', 'cyan', 'darkblue', 'darkcyan', 
 'darkgoldenrod', 'darkgray', 'darkgreen', 'darkgrey', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 
 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkslategrey', 'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue', 
 'dimgray', 'dimgrey', 'dodgerblue', 'firebrick', 'forestgreen', 'fuchsia', 'gold', 'goldenrod', 
 'gray', 'green', 'greenyellow', 'grey','hotpink', 'indianred', 'indigo', 'khaki',
 'lawngreen', 'lemonchiffon','lime', 
 'limegreen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 
 'mediumspringgreen', 'mediumturquoise', 'mediumvioletred', 'midnightblue', 'moccasin', 'navy', 
 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'palegreen', 'paleturquoise', 'palevioletred',
 'peru', 'plum', 'purple', 'rebeccapurple', 'red', 'rosybrown', 'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 
 'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'slategrey', 'springgreen', 'steelblue', 'tan', 'teal', 'tomato', 
 'turquoise', 'violet','yellowgreen']

#China_M2 = tv.get_hist(symbol="CNM2",exchange="ECONOMICS",interval=Interval.in_monthly,n_bars=1000)
def TVSearchSymList(loadpath:str,savepath:str):   #Load a list of tradingview symbols from an excel file and serach them all.
    tv = tvDatafeedz.TvDatafeed()       ##Compile results in output excel file. 
    SymbolList = pd.read_excel(loadpath)
    SymList = SymbolList['Symbol'].to_list(); ExList = SymbolList['Exchange'].to_list()
    MultiList = []; nullList = []
    SearchData = pd.DataFrame()

    for i in range(len(SymList)):
        searchRes = tv.search_symbol(text=SymList[i],exchange=ExList[i])
        if len(searchRes)> 1:
            print("This search term: "+SymList[i]+" has yielded multiple results")
            MultiList.append(SymList[i])
            for j in range(len(searchRes)):
                dic = dict(searchRes[j])
                ser =pd.Series(dic.values(),index=dic.keys())
                ser.drop(["economic_category","source2","params"],axis=0,inplace=True)
                ser = pd.Series(ser,index=ser.index,name=ser["country"])
                ser.drop(["country"],axis=0,inplace=True)
                print(ser)
                SearchData = pd.concat([SearchData,ser],axis=1)
        elif len(searchRes) == 1:
            dic = dict(searchRes[0])
            ser =pd.Series(dic.values(),index=dic.keys())
            ser.drop(["economic_category","source2","params"],axis=0,inplace=True)
            ser = pd.Series(ser,index=ser.index,name=ser["country"])
            ser.drop(["country"],axis=0,inplace=True)
            print(ser)
            SearchData = pd.concat([SearchData,ser],axis=1)
        else:
            print("This search term: "+SymList[i]+" has yielded a null result")
            nullList.append(SymList[i])
            continue
    SearchData = SearchData.T 
    SearchData.sort_index(inplace=True)   
    print(SearchData)
    return SearchData

def GetFXTickers(Currencies:pd.DataFrame):   #Input dataframe containing list of currencies and countries from above function. 
    tv = tvDatafeedz.TvDatafeed()              #In order to get a list of FX data tickers on tradingview for these currencies. 
    M2DataTab = Currencies
    M2DataTab.set_index('Country',inplace=True)
    print(M2DataTab)
    Exchanges = pd.read_excel(wd+"/TVDataFeed/ExchangeList.xlsx")
    FxExchangesList = Exchanges['Exchange'].to_list()
    FxDataDict = {'Country':[],'Symbol':[],'Description':[],'Exchange':[],'Currency Code':[]}

    for i in range(len(M2DataTab)): #len(M2DataTab)
        searchTerms = ("USD"+M2DataTab['currency_code'][i],M2DataTab['currency_code'][i]+"USD")   
        for l in range(2):
            if searchTerms[l] == "USDUSD":
                FxDataDict["Country"].append(M2DataTab.index[i]); FxDataDict["Symbol"].append(searchTerms[l])
                FxDataDict["Currency Code"].append(M2DataTab['currency_code'][i])
                FxDataDict["Description"].append("They use USD"); FxDataDict["Exchange"].append("N/A")
            elif searchTerms[l] == "EURUSD" or searchTerms[l] == "USDEUR":
                FxDataDict["Country"].append(M2DataTab.index[i]); FxDataDict["Symbol"].append(searchTerms[l])
                FxDataDict["Currency Code"].append(M2DataTab['currency_code'][i])
                FxDataDict["Description"].append("Eurozone country"); FxDataDict["Exchange"].append("IDC")
            else: 
                searchRes = tv.search_symbol(text=searchTerms[l])
                for j in range(len(searchRes)):
                    dic = dict(searchRes[j])
                    ser =pd.Series(dic.values(),index=dic.keys())
                    if ser['type'] == 'forex':
                        FxDataDict["Country"].append(M2DataTab.index[i]); FxDataDict["Symbol"].append(ser['symbol'])
                        FxDataDict["Currency Code"].append(ser['currency_code'])
                        FxDataDict["Description"].append(ser['description']); FxDataDict["Exchange"].append(ser['exchange'])
                    else:
                        FxDataDict["Country"].append(M2DataTab.index[i]); FxDataDict["Symbol"].append(searchTerms[l])
                        FxDataDict["Currency Code"].append(M2DataTab['currency_code'][i])
                        FxDataDict["Description"].append("Found diddly squat.."); FxDataDict["Exchange"].append("No ex from tv for "+searchTerms[l])

    SearchSummary = pd.DataFrame(FxDataDict)
    for b in range(len(SearchSummary)):
        description = SearchSummary['Description'][b]
        if description == "Found diddly squat..":
            SearchSummary.drop(b,axis=0,inplace=True)
        else:
            continue
    print(SearchSummary)
    return SearchSummary

def TrimFxList(FXList:pd.DataFrame,M2DataSum:pd.DataFrame): #Put in the FX list results output from previous function to trim list down. 
    SearchSummary = FXList            #Also uses the M2 data summary from the first function. 
   
    for i in range(len(SearchSummary)):
        sym = SearchSummary['Symbol'][i]
        CurrCode = SearchSummary['Currency Code'][i]
        match = re.search(CurrCode,sym)
        if match is not None:
            pair = CurrCode+"USD"
            pairInv = "USD"+CurrCode
            if sym != pair and sym != pairInv:
                SearchSummary.drop(i,axis=0,inplace=True)
            else:
                continue    
        else: 
            SearchSummary.drop(i,axis=0,inplace=True)     

    M2DataSum.set_index('Country',inplace=True)
    print(M2DataSum)
    resultantDF = pd.DataFrame()

    for i in range(len(M2DataSum)): 
        country = M2DataSum.index[i]
        currency = M2DataSum['currency_code'][i]
        Rows = SearchSummary[SearchSummary['Country'] == country]
        Rows.reset_index(inplace=True)
        for j in range(len(Rows)):
            if (Rows['Country'][j] == str(country)) and (Rows['Currency Code'][j] == str(currency)):
                pass
            else:
                Rows.drop(j,axis=0,inplace=True)
        resultantDF = pd.concat([resultantDF,Rows],axis=0)    
         
    FXList = resultantDF
    FXList.drop_duplicates(subset='Symbol',keep='first',inplace=True)
    print(FXList)
    return FXList

def ConcatFrames(M2DataSum,FXList): #Stick the M2 dataframe and the FX info frame toegether, to make one master info frame. 
    Final = pd.DataFrame()
    for i in range(len(M2DataSum)):
        try:
            FXRow = FXList.loc[[M2DataSum.index[i]]]
        except:
            dicDict = {'Country':[],'Symbol':[],'Description':[],'Exchange':[],'Currency Code':[]}
            dicDict["Currency Code"].append(np.nan); dicDict["Description"].append(np.nan)
            dicDict["Symbol"].append(np.nan);dicDict["Exchange"].append(np.nan)
            dicDict["Country"].append(M2DataSum.index[i])
            FXRow = pd.DataFrame(dicDict)
            FXRow.set_index('Country',inplace=True)
        m2Row = M2DataSum.loc[[M2DataSum.index[i]]]
        #print("\n",m2Row,"\n",FXRow)
        FullRow = pd.concat([m2Row,FXRow],axis=1)
        #print("\n",FullRow)
        #Row = pd.concat([M2DataSum[M2DataSum.index[i]],FxRow])
        Final = pd.concat([Final,FullRow],axis=0)
    print(Final)  
    return Final  

# M2DataSum = pd.read_excel(wd+"/TVDataFeed/TVSearchResults.xlsx")
# FXList = pd.read_excel(wd+"/TVDataFeed/FXTVSearchResults2.xlsx")
# M2DataSum.set_index('Country',inplace=True)
# FXList.drop_duplicates(subset='Country',keep='first',inplace=True)
# FXList.set_index('Country',inplace=True)
# print(M2DataSum,FXList)
#Final.to_excel(wd+"/TVDataFeed/FullList.xlsx")

def PullData(FullInfo:pd.DataFrame,username=None,password=None,Rank:list=None): #Use the full dataframe with M2 and FX ticker infos to pull the data for them from TV.  
    name="NoobTrade181"; pw="4Frst6^YuiT!" #Use username, password to access some data that may be restricted for free TV tiers. 
    tv = tvDatafeedz.TvDatafeed()
    DataDict = {}

    if Rank is not None:
        Countries = Rank
    else:
        Countries = FullInfo.index.to_list()
    for i in range(len(Countries)):
        TheCountry = Countries[i]
        M2Sym = FullInfo['M2_Symbol'][i]
        M2Ex = FullInfo['M2_exchange'][i]
        FXSym = FullInfo['FX_Symbol'][i]
        FXEx = FullInfo['FX_Exchange'][i]
        CurrCode = FullInfo['M2_currency_code'][i]
        print(TheCountry,M2Sym,M2Ex,FXSym,FXEx)
        M2_Data = tv.get_hist(symbol=M2Sym,exchange=M2Ex,interval=Interval.in_monthly,n_bars=500)
        #M2_Data.to_excel(wd+"/TVDataFeed/M2_Data/"+TheCountry+'_M2.xlsx')
        shitlist = []
        if (CurrCode == 'USD'):
            DataDict[TheCountry] = (M2_Data,"\nNo FX Data. M2 is measured in USD already") 
            continue
        else:
            try:
                FXData = tv.get_hist(symbol=FXSym,exchange=FXEx,interval=Interval.in_monthly,n_bars=500)
                #FXData.to_excel(wd+"/TVDataFeed/FX_Data/"+TheCountry+'_FunnyMoney2USD.xlsx')
            except:
                print('TVDataFeed failed to get data for: '+FXSym+', for country: '+TheCountry)
                shitlist.append(TheCountry+'_'+FXSym+'_'+FXEx)
        DataDict[TheCountry] = (M2_Data,FXData)        
    print('Could not get data for these: ',shitlist)   
    return DataDict         

def MakeDataCompFile(FullInfo:pd.DataFrame,M2Path:str,FXPath:str):
    DataComp = {"Country":[],"Curr_code":[],"M2_Len":[],"FX_Len":[],"M2_1stDate":[],"M2_LastDate":[],"FX_1stDate":[],"FX_LastDate":[],\
                "Past Limit":[],"Present Limit":[],"FX_Symbol":[]}
    for i in range(len(FullInfo)): 
        TheCountry = FullInfo.index[i]
        CurrCode = FullInfo['M2_currency_code'][i]
        FXSym = FullInfo['FX_Symbol'][i]
        M2_Data = pd.read_excel(M2Path+"/"+TheCountry+'_M2.xlsx')
        index = pd.DatetimeIndex(pd.DatetimeIndex(M2_Data[M2_Data.columns[0]]).date)
        M2_Data.set_index(index,inplace=True); l = 0
        print(i,TheCountry) 
        for column in M2_Data.columns:
            if column == 'symbol':
                break
            else:
                M2_Data.drop(column,axis=1,inplace=True)
            l += 1   

        try:
            FX_Data = pd.read_excel(FXPath+"/"+TheCountry+'_FX.xlsx')
            index = pd.DatetimeIndex(pd.DatetimeIndex(FX_Data[FX_Data.columns[0]]).date)
            FX_Data.set_index(index,inplace=True); 
        except: 
            DataComp["Country"].append(TheCountry);DataComp["Curr_code"].append(CurrCode)
            DataComp["M2_Len"].append(len(M2_Data)); DataComp["FX_Len"].append(np.nan)
            DataComp["M2_1stDate"].append(M2_Data.index[0]); DataComp["M2_LastDate"].append(M2_Data.index[len(M2_Data)-1])
            DataComp["FX_1stDate"].append(np.nan); DataComp["FX_LastDate"].append(np.nan)    
            DataComp["Past Limit"].append('Equal'); DataComp["Present Limit"].append('Equal')
            DataComp["FX_Symbol"].append('USD')
            continue
        b = 0
        for column in FX_Data.columns:
            if column == 'symbol':
                break
            else:
                FX_Data.drop(column,axis=1,inplace=True)
            b += 1  
        #print(FX_Data)
      
        DataComp["Country"].append(TheCountry); DataComp["Curr_code"].append(CurrCode)
        DataComp["M2_Len"].append(len(M2_Data)); DataComp["FX_Len"].append(len(FX_Data))
        DataComp["M2_1stDate"].append(M2_Data.index[0]); DataComp["M2_LastDate"].append(M2_Data.index[len(M2_Data)-1])
        DataComp["FX_1stDate"].append(FX_Data.index[0]); DataComp["FX_LastDate"].append(FX_Data.index[len(FX_Data)-1])
        DataComp["FX_Symbol"].append(FXSym)
        if M2_Data.index[0] < FX_Data.index[0]:
            DataComp["Past Limit"].append('FX_limited')
        elif M2_Data.index[0] == FX_Data.index[0]:
            DataComp["Past Limit"].append('Equal')
        else:
            DataComp["Past Limit"].append('M2_limited')
        if M2_Data.index[len(M2_Data)-1] < FX_Data.index[len(FX_Data)-1]:
            DataComp["Present Limit"].append('M2_limited')
        elif M2_Data.index[len(M2_Data)-1] == FX_Data.index[len(FX_Data)-1]:
            DataComp["Present Limit"].append('Equal')
        else:
            DataComp["Present Limit"].append('FX_limited')    
           
    print(len(DataComp["Country"]),len(DataComp["Curr_code"]),len(DataComp["M2_Len"]),len(DataComp["FX_Len"]),len(DataComp["M2_1stDate"]),\
        len(DataComp["M2_LastDate"]),len(DataComp["FX_1stDate"]),len(DataComp["FX_LastDate"]),\
                len(DataComp["Past Limit"]),len(DataComp["Present Limit"]),DataComp["Past Limit"],DataComp["Present Limit"])    
    DataSum = pd.DataFrame(DataComp); DataSum.set_index('Country',inplace=True)
    return DataSum

def GetMissedData(FullInfo:pd.DataFrame,DataSum:pd.DataFrame):
    tv = tvDatafeedz.TvDatafeed()
    MissList = []
    for i in range(len(FullInfo)):
        TheCountry = FullInfo.index[i]
        NoGaps = TheCountry.replace(" ","")
        DatSumCunt = DataSum.index[i]
        CurrCode = DataSum['Curr_code'][DatSumCunt]
        FXlen = DataSum['FX_Len'][DatSumCunt]
        if NoGaps != DatSumCunt:
            print('Index mismatch for ',TheCountry)
        if CurrCode != 'USD' and pd.isna(FXlen):
            print('FX data missing for ',TheCountry)
            MissList.append(TheCountry)

    for i in range(len(MissList)):
        Country = MissList[i]
        NoGaps = Country.replace(" ","")
        FXTicker = FullInfo['FX_Symbol'][Country]
        FXEx = FullInfo['FX_Exchange'][Country]
        print(FXTicker,FXEx)
        FXData = tv.get_hist(symbol=FXTicker,exchange=FXEx,interval=Interval.in_monthly,n_bars=500)
        print(FXData)
        FXData.to_excel(wd+'/TVDataFeed/FX_Data2/'+NoGaps+"_FXData.xlsx")

def CombineDatasSimp(FullInfo:pd.DataFrame,DataSum:pd.DataFrame,M2Path:str,FXPath:str): #This function makes indexes the same and multiplies M2 and FX data. 
    DataDict = {}
    for i in range(len(DataSum)): #len(DataSum)   #Then saves a DF for each country. 
        Country = DataSum.index[i]; dtStr = 'datetime'
        FXPair = DataSum['FX_Symbol'][i]
        CurrCode = DataSum['Curr_code'][i]

        M2_Data = pd.read_excel(M2Path+"/"+Country+'_M2.xlsx')
        try:
            FX_Data = pd.read_excel(FXPath+"/"+Country+'_FX.xlsx')
        except:
            FX_Data = M2_Data.copy()
            FX_Data["close"] = 1
        
        M2index = pd.DatetimeIndex(pd.DatetimeIndex(M2_Data[M2_Data.columns[0]]).date)
        M2_Data.set_index(M2index,inplace=True)
        #print(Country,' M2 Data: ',M2_Data)

        index = pd.DatetimeIndex(pd.DatetimeIndex(FX_Data[FX_Data.columns[0]]).date)
        FX_Data.set_index(index,inplace=True); FX_Data.fillna('ffill',inplace=True)
        FX_Data = FX_Data.resample('MS').mean()
        #print(Country,' FX Data: ',FX_Data)

        M2Close = pd.Series(M2_Data['close'],name='M2_'+Country)
        FXClose = pd.Series(FX_Data['close'],name='FX_'+Country)
        FXClose = FXClose.loc[FXClose.index[0]:M2Close.index[len(M2Close)-1]]

        if CurrCode == "USD":
            pass
        else:
            if FXPair == 'USD'+CurrCode:
                FXClose = 1/FXClose
                #print(Country+' FX data inverted, now: ',rsFX)
            elif FXPair == CurrCode+'USD':    
                pass
            else:
                print(Country+', does not match FXPair valid format.')
    
        M2_Cunt = pd.Series(np.nan,index=M2index,name=Country+'_M2 ('+CurrCode+')')
        FX_long = pd.Series(np.nan,index=M2index,name=Country+'_FX (USD)')
        
        for l in range(len(M2Close)):
            M2_Cunt[M2Close.index[l]] = M2Close[M2Close.index[l]]
        for j in range(len(FXClose)):
            FX_long[FXClose.index[j]] = FXClose[FXClose.index[j]]  

        M2_USD = pd.Series(M2_Cunt*FX_long,name=Country+'_M2 (USD)')
        M2_Cunt.sort_index(inplace=True); FX_long.sort_index(inplace=True)
        M2_USD.sort_index(inplace=True)
        if CurrCode == 'USD':
            DF = pd.concat([M2_Cunt,FX_long],axis=1)
        else:    
            DF = pd.concat([M2_Cunt,FX_long,M2_USD],axis=1)    
        DataDict[Country] = DF
    return DataDict    

def ReDoDataSum(DataSum:pd.DataFrame): #ReDo datasum comparison table using the FinalData files instead. 
    DataComp = {"Country":[],"Curr_code":[],"M2_Len":[],"FX_Len":[],"M2_1stDate":[],"M2_LastDate":[],"FX_1stDate":[],"FX_LastDate":[]}
    for i in range(len(DataSum)):  #len(FullInfo)
        TheCountry = DataSum.index[i]
        CurrCode = DataSum['Curr_code'][i]
        Fin_Data = pd.read_excel(wd+"/TVDataFeed/FinalData/"+TheCountry+'.xlsx')
        Fin_Data.set_index(pd.DatetimeIndex(Fin_Data['Date']).date)
        Fin_Data.drop("Date",axis=1,inplace=True)
        M2_Data = pd.read_excel(wd+"/TVDataFeed/M2_Data/"+TheCountry+'_M2.xlsx')
        index = pd.DatetimeIndex(M2_Data['DateTime']).date
        M2_Data.set_index(index,inplace=True)
        M2_Data.drop("Date",axis=1,inplace=True)
        
        try:
            FX_Data = pd.read_excel(wd+"/TVDataFeed/FX_Data/"+TheCountry+'_FXData.xlsx')
        except: 
            DataComp["Country"].append(TheCountry);DataComp["Curr_code"].append(CurrCode)
            DataComp["M2_Len"].append(len(Fin_Data[TheCountry+'_M2 ('+CurrCode+')'])); DataComp["FX_Len"].append(len(Fin_Data[TheCountry+'_FX (USD)']))
            DataComp["M2_1stDate"].append(M2_Data.index[0]); DataComp["M2_LastDate"].append(M2_Data.index[len(M2_Data)-1])
            DataComp["FX_1stDate"].append(np.nan); DataComp["FX_LastDate"].append(np.nan)    
            continue
        
        FX_Data.drop("Date",axis=1,inplace=True)
        index = pd.DatetimeIndex(FX_Data['DateTime']).date
        FX_Data.set_index(index,inplace=True)

        DataComp["Country"].append(TheCountry); DataComp["Curr_code"].append(CurrCode)
        DataComp["M2_Len"].append(len(Fin_Data[TheCountry+'_M2 ('+CurrCode+')'])); DataComp["FX_Len"].append(len(Fin_Data[TheCountry+'_FX (USD)']))
        DataComp["M2_1stDate"].append(M2_Data.index[0]); DataComp["M2_LastDate"].append(M2_Data.index[len(M2_Data)-1])
        DataComp["FX_1stDate"].append(FX_Data.index[0]); DataComp["FX_LastDate"].append(FX_Data.index[len(FX_Data)-1])
    DataSum = pd.DataFrame(DataComp)
    print(DataSum)
    return DataSum  

def MakeMasterM2DF_2(DataSum:pd.DataFrame,FinDataPath:str):
    LongestM2 = (DataSum['M2_Len'].max(),DataSum['M2_Len'].idxmax())
    LongestFX = (DataSum['FX_Len'].max(),DataSum['FX_Len'].idxmax())
    print('Longest data: ',LongestFX,LongestM2)
    LongestData = pd.read_excel(FinDataPath+str(LongestFX[1])+'.xlsx')
    LongestData.set_index(LongestData[LongestData.columns[0]],inplace=True)
    GlobalIndex = pd.DatetimeIndex(pd.DatetimeIndex(LongestData.index).date)
    GlobalDF = pd.Series(0,index=GlobalIndex,name='Global M2 (USD)')
    GlobalDF_fill = pd.Series(0,index=GlobalIndex,name='Global M2 (USD, ffill)')
    GlobalDF = pd.concat([GlobalDF,GlobalDF_fill],axis=1)

    for i in range(len(DataSum)): #len(DataSum)
        Country = DataSum.index[i]
        print("Country: ",Country)
        M2_Data = pd.read_excel(FinDataPath+Country+'.xlsx')
        index = pd.DatetimeIndex(pd.DatetimeIndex(M2_Data[M2_Data.columns[0]]).date)
        M2_Data.set_index(index,inplace=True); M2_Data = M2_Data.reindex(GlobalIndex)
        M2_Data.drop(M2_Data.columns[0],axis=1,inplace=True)
        M2_USD = pd.Series(M2_Data[Country+"_M2 (USD)"],name=Country+"_M2 (USD)")
        FullLength = pd.Series(np.nan,index=GlobalIndex,name=Country)
        FullLength[M2_USD.index] = M2_USD
        FullFilled = pd.Series(FullLength.fillna(method='ffill'),name=Country+'_f')     ##Filling forward nans at end of series. This means that countries
        #that make you wait for updated M2 data will just use the latest available value. 
        GlobalDF = pd.concat([GlobalDF,FullLength,FullFilled],axis=1)
        GlobalDF['Global M2 (USD)'] = GlobalDF['Global M2 (USD)']+FullLength
        GlobalDF['Global M2 (USD, ffill)'] = GlobalDF['Global M2 (USD, ffill)']+FullFilled
    GlobalDF.index.rename('Date',inplace=True)
    print(GlobalDF)
    return GlobalDF    

def Reorder_M2List(M2List:pd.DataFrame,Rank:list):
    NewList = pd.DataFrame()
    for country in Rank:
        Line = M2List.loc[[country]]
        NewList = pd.concat([NewList,Line],axis=0)
    print(NewList)    
    return(NewList)

def UpdateData(M2List:pd.DataFrame,M2Path:str,FXPath:str):
    Datas = PullData(M2List); #print(Datas)      ##Pulls the FX & M2 Data for each country in the list. 
    for country in Datas.keys():       #Step 1b: Save the M2 & FX Datas to disk. 
        CuntryData = Datas[country]
        M2_Data = pd.DataFrame(CuntryData[0])
        M2_Data.to_excel(wd+"/TVDataFeed/FinalData/M2_Data/"+country+"_M2.xlsx")
        try:
            FX_Data = pd.DataFrame(CuntryData[1])
            FX_Data.to_excel(wd+"/TVDataFeed/FinalData/FX_Data/"+country+"_FX.xlsx")
        except:
            continue
    DataComp = MakeDataCompFile(M2List,M2Path,FXPath); print(DataComp)   ### Step #2Make a dataframe to summarize data. 
    return DataComp
  
########### Do stuff code ###########################
# FullInfo = pd.read_excel(wd+"/TVDataFeed/M2Info_FullList.xlsx")
# FullInfo.set_index('Country',inplace=True); print(FullInfo)
# FullList = FullInfo.index.to_list(); FullList2 = []; print(FullList)
# G20List = ['Argentina', 'China', 'United States', 'Euro Area', 'Japan', 'United Kingdom',\
# 'South Korea', 'Hong Kong', 'Taiwan', 'Australia', 'Canada', 'Switzerland','Russia', 'Brazil', 'India',\
# 'Mexico', 'Singapore', 'Saudi Arabia', 'Indonesia','Sweden', 'Malaysia', 'Poland', 'South Africa', 'Turkey']
# G20 = FullInfo.loc[G20List]; print(G20,len(G20))
# G20.to_excel(wd+"/TVDataFeed/M2Info_G20.xlsx")
# # for country in G20List:
#     Row = FullInfo[FullInfo.index == country]
#     print(Row)   
# DataSum2 = pd.read_excel(wd+"/TVDataFeed/M2_FX_DataComp2.xlsx")
# DataSum2.set_index('Country',inplace=True)
# DataSum2['M2_1stDate'] = DataSum2['M2_1stDate'].astype('timestamp.date')
# print(DataSum2)
# limitStart = pd.Series(np.nan,index=DataSum2.index,name='Start limiter')
# limitEnd = pd.Series(np.nan,index=DataSum2.index,name='End limiter')
# for i in range(len(DataSum2)): 
#     if DataSum2['M2_1stDate'][i] < DataSum2['FX_1stDate'][i]:
#         limitStart.iloc[i] = 'FX'
#     elif DataSum2['M2_1stDate'][i] > DataSum2['FX_1stDate'][i]: 
#         limitStart.iloc[i] = 'M2'
#     else:
#         limitStart.iloc[i] = 'equal' 
#     if DataSum2['M2_LastDate'][i] < DataSum2['FX_LastDate'][i]:
#         limitEnd.iloc[i] = 'M2'
#     elif DataSum2['M2_LastDate'][i] > DataSum2['FX_LastDate'][i]: 
#         limitEnd.iloc[i] = 'FX'
#     else:
#         limitEnd.iloc[i] = 'equal'  
# DataSum2 = pd.concat([DataSum2,limitStart,limitEnd],axis=1)
# DataSum2.to_excel(wd+"/TVDataFeed/M2_FX_DataComp3.xlsx")
# FullOn = MakeMasterM2DF(DataSum2)
# print(FullOn)
# FullOn.to_excel(wd+"/TVDataFeed/GlobalM2.xlsx")
#print(len(FullInfo),len(DataSum))
#CombineDatas(FullInfo,DataSum)
# All_M2USD = pd.read_excel(wd+"/TVDataFeed/GlobalM2.xlsx")
# All_M2USD.set_index('Date', inplace=True)
# for column in All_M2USD.columns:
#     if re.search('1',column) is not None:
#         print(column)
#         All_M2USD.drop(column,axis=1,inplace=True)

################### ACtive code here. Functions above. ###########################################################################################
# Rank = ['China','UnitedStates','EuroArea','Japan','UnitedKingdom','SouthKorea','HongKong','Australia','Taiwan','Canada','Switzerland','Brazil','Russia',
#         'India','Malaysia','Mexico','Singapore','SaudiArabia','Indonesia','Poland','Sweden','Turkey','SouthAfrica','Argentina']

FullList = pd.read_excel(wd+"/M2Info_Top50.xlsx")  #Step #1 load file that has info on which countries + the M2 & FX codes for data to pull from TV. 
FullList.set_index('Country',inplace=True)
#CutList = pd.read_excel(wd+"/M2Info_Top50.xlsx",sheet_name='CutList')
# cut = CutList['Country'].to_list()
# for country in cut:
#     FullList.drop(country,axis=0,inplace=True)
# print(FullList)  
#FullList.to_excel(wd+'/M2Info_Long'+str(len(FullList))+'.xlsx')  
#FullList = FullList[22::]
# Rank = pd.read_excel(wd+'/Curated_Rank.xlsx')
# Rank.set_index('Country',inplace=True)x
# rank = Rank.index.to_list(); print(rank,len(rank))
# NewDF = Reorder_M2List(FullList,rank); print(NewDF)
# NewDF.to_excel(wd+"/M2Info_FullList_2.xlsx")
M2Path = (wd+'/TVDataFeed/FinalData/M2_Data'); FXPath = (wd+'/TVDataFeed/FinalData/FX_Data')
#DataComp = UpdateData(FullList,M2Path,FXPath)        #Step #2 update M2 & FX data if not already done (optional). 
# DataComp = MakeDataCompFile(FullList,M2Path,FXPath); print(DataComp)   ### Step #2Make a dataframe to summarize data. 
# DataComp.to_excel(wd+"/DataSum_Long27.xlsx")

DataComp = pd.read_excel(wd+"/DataSum_Top50.xlsx")
DataComp.set_index('Country',inplace=True); print(DataComp)
# Combos = CombineDatasSimp(FullList,DataComp,M2Path,FXPath); print(Combos) ##Step #3 multiply M2 & FX datas. 
# for country in Combos.keys():
#     data = pd.DataFrame(Combos[country])
#     data.to_excel(wd+"/TVDataFeed/FinalData/"+country+".xlsx")
# FullDF = MakeMasterM2DF_2(DataComp,wd+"/TVDataFeed/FinalData/") #Step #4: put all the data in a big master DF. 
# print(FullDF)
#FullDF.to_excel(wd+'/Long27_M2_USD.xlsx')
 