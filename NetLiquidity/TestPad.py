import requests    
import numpy as np
import pandas as pd
import datetime
from collections import OrderedDict
import sys
import os

path = sys.path
sys.path.append('/Users/jamesbishop/Documents/Python/venv/Plebs_Macro')
print(path)

from MacroBackend import PriceImporter


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
            
    return FullData, MetaData, data

RunDict = OrderedDict(); i = 1
RunDict['Federal Reserve Account'] = '2010-01-01'
RunDict['Treasury General Account (TGA)'] = '2021-10-01'
RunDict['Treasury General Account (TGA) Closing Balance'] = '2022-04-16'
RunDict['Treasury General Account (TGA) Opening Balance'] = '2022-04-16'

# for key in RunDict.keys():
#     LittleCat = PullTGA_Data(AccountName = key,start_date=RunDict[key])
#     print(LittleCat[0]); print('\n',LittleCat[1]); print('\n',LittleCat[2])
#     FedResAc = pd.DataFrame(LittleCat[0]); Header = pd.DataFrame(LittleCat[1]); AllData = pd.DataFrame(LittleCat[2])
#     SavePath = '/Users/jamesbishop/Documents/Financial/Investment/MACRO_STUDIES/NLQ/'
#     Header.to_excel(SavePath+'TGA_Data'+str(i)+'.xlsx',sheet_name='Data_Info')
#     with pd.ExcelWriter(SavePath+'TGA_Data'+str(i)+'.xlsx', engine='openpyxl', mode='a') as writer:  
#         AllData.to_excel(writer, sheet_name='AllData')
#         FedResAc.to_excel(writer, sheet_name='FedResAcc')
#     i += 1

# LittleCat = PullTGA_Data(AccountName = 'Treasury General Account (TGA) Opening Balance',start_date='2022-04-16')
# print(LittleCat[0]); print('\n',LittleCat[1]); print('\n',LittleCat[2])
# FedResAc = pd.DataFrame(LittleCat[0]); Header = pd.DataFrame(LittleCat[1]); AllData = pd.DataFrame(LittleCat[2])
# SavePath = '/Users/jamesbishop/Documents/Financial/Investment/MACRO_STUDIES/NLQ/'
# Header.to_excel(SavePath+'TGA_Data4.xlsx',sheet_name='Data_Info')
# with pd.ExcelWriter(SavePath+'TGA_Data4.xlsx', engine='openpyxl', mode='a') as writer:  
#     AllData.to_excel(writer, sheet_name='AllData')
#     FedResAc.to_excel(writer, sheet_name='TGA')

# Purpies = "I’ve written a python script to pull and display the daily NLQ series so you don’t have to.\
#      Script pulls the Fed bal. sheet (weekly) & RevRepo bal (daily) data from FRED. It gets the TGA bal. direct from treasury site (daily data).\
#          You can choose up to 5 assets to also plot for comparison. Correlation (CC) is calculated for the first asset (BTC here below)."
# print(len(Purpies))

# TGA_Data = pd.read_excel('/Users/jamesbishop/Documents/Python/venv/NetLiquidity/TreasuryData/TGA_Since2005.xlsx')
# TGAData2 = TGA_Data.copy()
# TGAMess = pd.concat([TGA_Data,TGAData2],axis=0)
# TGAMess.sort_index(inplace=True)
# print(TGAMess.head(55))
# TGA_DataFin = TGAMess[~TGAMess.index.drop_duplicates()]
# print(TGA_DataFin.head(55))

# print(TGA_Data,type(TGA_Data.index))
# print(len(TGA_Data))
# TGA_Data.drop_duplicates(subset='record_date',inplace=True)
# TGA_Data.set_index('record_date',inplace=True)
# print(TGA_Data,type(TGA_Data.index))
# print(len(TGA_Data))
# TGA_Data.to_excel('/Users/jamesbishop/Documents/Python/venv/NetLiquidity/TreasuryData/TGA_Since2005.xlsx')

Cat = '1/ USD NET LIQUIDITY (NLQ): this has become an important macro metric to track. Originally formulated by @DariusDale and 42 Macro. This provides a\
    daily estimate of the total liquidity being provided to markets by the Fed, treasury and big money funds.'

DataStart = '2014-01-01'
Data = PriceImporter.PullDailyAssetData("AAPL,NASDAQ",'tv',DataStart,endDate=None)    
print(Data)

