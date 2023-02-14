####### Required modules/packages #####################################
import os
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
dir = os.path.dirname(wd)
print(wd,dir)
import sys ; sys.path.append(dir)
from MacroBackend import Charting 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
### These are standard python packages included in the latest python distributions. No need to install them. 
import datetime
if sys.platform == "linux" or sys.platform == "linux2":        #This detects what operating system you're using so that the right folder delimiter can be use for paths. 
    FDel = '/'; OpSys = 'linux'
elif sys.platform == "darwin":
    FDel = '/'; OpSys = 'mac'
elif sys.platform == "win32":
    FDel = '\\' ; OpSys = 'windows'
print('System information: ',sys.platform, OpSys,', directory delimiter: ', FDel, ', working directory: ', wd)

BOJAss = pd.read_excel(wd+FDel+'FRED_Data'+FDel+'JPNASSETS_USD'+'.xlsx')
BOJAss.set_index('datetime',inplace=True); BOJAss = pd.Series(BOJAss.squeeze(),name='BOJ Bal. (bil. USD)')
BOJAss.dropna(inplace=True)
NLQ = pd.read_excel(dir+FDel+'NetLiquidity'+FDel+'NLQ_Data'+FDel+'NLQ_DailyTGA'+'.xlsx')
NLQ.set_index('Unnamed: 0',inplace=True); NLQ = pd.Series(NLQ.squeeze()); NLQ.index.rename('datetime',inplace=True)
NLQ.dropna(inplace=True)

FirstDay = max(NLQ.index[0],BOJAss.index[0]); LastDay = min(NLQ.index[len(NLQ)-1],BOJAss.index[len(BOJAss)-1])
print(FirstDay,LastDay)
BOJAss = BOJAss[FirstDay:LastDay]; NLQ = NLQ[FirstDay:LastDay]
d1 = BOJAss.index.difference(NLQ.index); d2 = NLQ.index.difference(BOJAss.index)
print(NLQ,BOJAss,d1,d2)

Sum = NLQ + BOJAss
Sum.to_excel(wd+FDel+'ComboNetLiq'+FDel+'NLQ_BOJ.xlsx')
SeriesInfo = {'units':'Billions of U.S dollaridoos','units_short':'Billlions of USD','title':'Fed Net liquidity + BOJ Balance sheet (USD)',"id":"FED NLQ + BOJ bal.",\
              'frequency':'Daily'}
SeriesInfo2 = {'units':'Billions of U.S dollaridoos','units_short':'Billlions of USD','title':'BOJ Balance sheet (USD)',"id":"BOJ bal.",\
              'frequency':'Daily'}


fig1 = Charting.FedFig(Sum,SeriesInfo,RightSeries=NLQ,rightlab='Fed Net Liquidity (right)',LYScale="log",RYScale="log",CustomXAxis=True)
fig2 = Charting.FedFig(BOJAss,SeriesInfo2,RightSeries=NLQ,rightlab='Fed Net Liquidity (right)',LYScale="log",RYScale="log",CustomXAxis=True)
plt.show()