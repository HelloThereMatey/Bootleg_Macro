###### Required modules/packages #####################################
import sys
print(sys.path)
import os
FDel = os.path.sep
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
dir = os.path.dirname(wd)
print('System information: ',sys.platform,', directory delimiter: ', FDel, ', working directory: ', wd)
print(wd,dir)
sys.path.append(dir+'/MacroBackend') #This makes sure script can find tvdatafeed module. 

import pandas as pd
from matplotlib import colors as mcolors
import matplotlib.pylab as pl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from tvDatafeedz import TvDatafeed, Interval
import numpy as np
import datetime
import tkinter as tk
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showinfo

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing

################################################### CODE FOR UPDATING EXISTING M2 & FX DATA FOR COUNTRIES SUPPLIED IN A LIST TAKEN FROM EXCEL FILE #############
def PullData(FullInfo:pd.DataFrame,username=None,password=None,Rank:list=None): #Use the full dataframe with M2 and FX ticker infos to pull the data for them from TV.  
    name="NoobTrade181"; pw="4Frst6^YuiT!" #Use username, password to access some data that may be restricted for free TV tiers. 
    tv = TvDatafeed()
    DataDict = {}

    if Rank is not None:
        Countries = Rank
    else:
        Countries = FullInfo.index.to_list()
    for i in range(len(Countries)):
        TheCountry = Countries[i]
        M2Sym = FullInfo.iloc[i].at['M2_Symbol']
        M2Ex = FullInfo.iloc[i].at['M2_exchange']
        FXSym = FullInfo.iloc[i].at['FX_Symbol']
        FXEx = FullInfo.iloc[i].at['FX_Exchange']
        CurrCode = FullInfo.iloc[i].at['M2_currency_code']
        print(TheCountry,M2Sym,M2Ex,FXSym,FXEx)
        M2_Data = tv.get_hist(symbol=M2Sym,exchange=M2Ex,interval=Interval.in_monthly,n_bars=500)
        shitlist = []
        if (CurrCode == 'USD'):
            DataDict[TheCountry] = (M2_Data,"\nNo FX Data. M2 is measured in USD already") 
            continue
        else:
            try:
                FXData = tv.get_hist(symbol=FXSym,exchange=FXEx,interval=Interval.in_monthly,n_bars=500)
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
        CurrCode = FullInfo.iloc[i].at['M2_currency_code']
        FXSym = FullInfo.iloc[i].at['FX_Symbol']
        M2_Data = pd.read_excel(M2Path+FDel+TheCountry+'_M2.xlsx')
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
            FX_Data = pd.read_excel(FXPath+FDel+TheCountry+'_FX.xlsx')
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

def CombineDatasSimp(FullInfo:pd.DataFrame,DataSum:pd.DataFrame,M2Path:str,FXPath:str): #This function makes indexes the same and multiplies M2 and FX data. 
    DataDict = {}
    for i in range(len(DataSum)): #len(DataSum)   #Then saves a DF for each country. 
        Country = DataSum.index[i]; dtStr = 'datetime'
        FXPair = DataSum.iloc[i].at['FX_Symbol']
        CurrCode = DataSum.iloc[i].at['Curr_code']

        M2_Data = pd.read_excel(M2Path+FDel+Country+'_M2.xlsx')
        try:
            FX_Data = pd.read_excel(FXPath+FDel+Country+'_FX.xlsx')
        except:
            FX_Data = M2_Data.copy()
            FX_Data["close"] = 1
        
        M2index = pd.DatetimeIndex(pd.DatetimeIndex(M2_Data[M2_Data.columns[0]]).date)
        M2_Data.set_index(M2index,inplace=True)
        #print(Country,' M2 Data: ',M2_Data)

        index = pd.DatetimeIndex(pd.DatetimeIndex(FX_Data[FX_Data.columns[0]]).date)
        FX_Data.set_index(index,inplace=True); FX_Data.fillna('ffill',inplace=True)
        try:
            FX_Data.drop(["volume","datetime","symbol"],axis=1,inplace=True)
        except:
            pass    
        print(FX_Data)
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

def UpdateData(M2List:pd.DataFrame,M2Path:str,FXPath:str):
    Datas = PullData(M2List); #print(Datas)      ##Pulls the FX & M2 Data for each country in the list. 
    for country in Datas.keys():       #Step 1b: Save the M2 & FX Datas to disk. 
        CuntryData = Datas[country]
        M2_Data = pd.DataFrame(CuntryData[0])
        M2_Data.to_excel(wd+FDel+"TVDataFeed"+FDel+"FinalData"+FDel+"M2_Data"+FDel+country+"_M2.xlsx")
        try:
            FX_Data = pd.DataFrame(CuntryData[1])
            FX_Data.to_excel(wd+FDel+"TVDataFeed"+FDel+"FinalData"+FDel+"FX_Data"+FDel+country+"_FX.xlsx")
        except:
            continue
    DataComp = MakeDataCompFile(M2List,M2Path,FXPath); print(DataComp)   ### Step #2Make a dataframe to summarize data. 
    return DataComp    

if __name__ == "__main__":

    #################################### ACTIVE CODE BELOW, FUNCTIONS ABOVE. #####################################################
    # msg = showinfo(title='Global M2 input data info.',message='Choose Global M2 info excel file (.xlsx only) from the "UpdateM2Infos" folder.'+\
    #     " Must be formatted correctly. I suggest: Bootleg_Macro/Global_M2/UpdateM2INfo/M2Info_Top50.xlsx, or one of the other M2Info files in that folder."+\
    #         " If you use the wrong ticker & exchange codes for a particular country in your dataframe, you'll get NaNs and get f**ked on.")
            
    # filename = askopenfilename(title='Choose Global M2 info excel file (.xlsx only) from the "UpdateM2Infos" folder.',defaultextension='.xlsx',initialdir=wd) 
    # des = filename.rsplit('.',1)[0].rsplit('_',1)[1]
    # print(FDel, filename, '\n', des)
    print('Pulling M2 and FX data for the top 50 economies from TV........')
    filename = wd+FDel+'UpdateM2Infos'+FDel+'M2Info_Top50.xlsx'
    top33path = wd+FDel+'UpdateM2Infos'+FDel+'M2Info_Top33.xlsx'
    long28path = wd+FDel+'UpdateM2Infos'+FDel+'M2Info_Long28.xlsx'
    long27path = wd+FDel+'UpdateM2Infos'+FDel+'M2Info_Long27.xlsx'

    # show an "Open" dialog box and return the path to the selected file
    M2Path = (wd+FDel+'TVDataFeed'+FDel+'FinalData'+FDel+'M2_Data'); 
    FXPath = (wd+FDel+'TVDataFeed'+FDel+'FinalData'+FDel+'FX_Data') ###Change these if changing the folder structure within "Global_M2" folder.
    print('Loading global M2 information from: ',filename)

    FullList = pd.read_excel(filename, index_col=0)   #Step #1 load file that has info on which countries + the M2 & FX codes for data to pull from TV. 
    top33 = pd.read_excel(top33path, index_col=0)
    long28 = pd.read_excel(long28path, index_col=0)
    long27 = pd.read_excel(long27path, index_col=0)

    print("Global M2 initial dataframe: ",FullList)
    split = filename.split(FDel); nam = split[len(split)-1]; split2 = nam.split("."); naml = split2[0]; split3 = naml.split("_"); des = split3[1]

    DataComp = UpdateData(FullList,M2Path,FXPath)        #Step #2 update M2 & FX data if not already done (optional). 
    DataComp.to_excel(wd+FDel+'Datasums'+FDel+des+'_DataComp.xlsx')
    top33Sum = MakeDataCompFile(top33,M2Path,FXPath)
    top33Sum.to_excel(wd+FDel+'Datasums'+FDel+'Top33_DataComp.xlsx')
    long28Sum = MakeDataCompFile(long28,M2Path,FXPath)
    long28Sum.to_excel(wd+FDel+'Datasums'+FDel+'Long28_DataComp.xlsx')
    long27Sum = MakeDataCompFile(long27,M2Path,FXPath)
    long27Sum.to_excel(wd+FDel+'Datasums'+FDel+'Long27_DataComp.xlsx')

    Combos = CombineDatasSimp(FullList,DataComp,M2Path,FXPath) ##Step #3 multiply M2 & FX datas. 
    top33com = CombineDatasSimp(top33,top33Sum,M2Path,FXPath) ##Step #3 multiply M2 & FX datas. 
    long28com = CombineDatasSimp(long28,long28Sum,M2Path,FXPath) ##Step #3 multiply M2 & FX datas. 
    long27com = CombineDatasSimp(long27,long27Sum,M2Path,FXPath) ##Step #3 multiply M2 & FX datas. 

    for country in Combos.keys():
        data = pd.DataFrame(Combos[country])
        data.to_excel(wd+FDel+"TVDataFeed"+FDel+"FinalData"+FDel+country+".xlsx")

    FinDataPath = wd+FDel+"TVDataFeed"+FDel+"FinalData"+FDel
    SaveDataTo = wd+FDel+'M2_USD_Tables'+FDel
    FullDF = MakeMasterM2DF_2(DataComp,FinDataPath) #Step #4: put all the data in a big master DF. 
    FullDF.to_excel(wd+FDel+'M2_USD_Tables'+FDel+des+'_M2_USD.xlsx')

    top33fin = MakeMasterM2DF_2(top33Sum,FinDataPath) #Step #4: put all the data in a big master DF. 
    top33fin.to_excel(SaveDataTo+'Top33_M2_USD.xlsx')
    long28fin = MakeMasterM2DF_2(long28Sum,FinDataPath) #Step #4: put all the data in a big master DF. 
    long28fin.to_excel(SaveDataTo+'Long28_M2_USD.xlsx')
    long27fin = MakeMasterM2DF_2(long27Sum,FinDataPath) #Step #4: put all the data in a big master DF. 
    long27fin.to_excel(SaveDataTo+'Long27_M2_USD.xlsx')

    GM2_ffill_top50 = FullDF['Global M2 (USD, ffill)'].dropna()
    GM2_ffill_top33 = top33fin['Global M2 (USD, ffill)'].dropna()
    GM2_ffill_long28 = long28fin['Global M2 (USD, ffill)'].dropna()
    GM2_ffill_long27 = long27fin['Global M2 (USD, ffill)'].dropna()

    savePath = dir+FDel+'Macro_Chartist'+FDel+'SavedData'+FDel
    SeriesInfo = pd.Series({'units':'US Dollars','units_short': 'USD','title':'Global M2 '+des,'id':'GM2'+des,"Source":"tv"},name='SeriesInfo')
    GM2_ffill_top50.to_excel(savePath+des+'GM2.xlsx',sheet_name='Closing_Price')
    with pd.ExcelWriter(savePath+des+'GM2.xlsx', engine='openpyxl', mode='a') as writer:  
        SeriesInfo.to_excel(writer, sheet_name='SeriesInfo')
    GM2_ffill_top33.to_excel(savePath+'Top33_GM2.xlsx',sheet_name='Closing_Price')
    with pd.ExcelWriter(savePath+'Top33_GM2.xlsx', engine='openpyxl', mode='a') as writer:  
        SeriesInfo.to_excel(writer, sheet_name='SeriesInfo')
    GM2_ffill_long28.to_excel(savePath+'Long28_GM2.xlsx',sheet_name='Closing_Price')
    with pd.ExcelWriter(savePath+'Long28_GM2.xlsx', engine='openpyxl', mode='a') as writer:  
        SeriesInfo.to_excel(writer, sheet_name='SeriesInfo')
    GM2_ffill_long27.to_excel(savePath+'Long27_GM2.xlsx',sheet_name='Closing_Price')
    with pd.ExcelWriter(savePath+'Long27_GM2.xlsx', engine='openpyxl', mode='a') as writer:  
        SeriesInfo.to_excel(writer, sheet_name='SeriesInfo')

    print("Alrighty. M2 & FX data have been updated successfully and the master dataframe of M2 (USD) data has been constructed and \
        saved to: ",wd+FDel+'M2_USD_Tables'+FDel+des+'_M2_USD.xlsx'," The global M2 series by itself has also been exported to: ",savePath,". Now run 'Plot_GM2.py'\
            or use GenericAnalyzer.py to plot GM2 series with other data.") 
