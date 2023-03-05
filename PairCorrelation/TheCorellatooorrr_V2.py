import os
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
dir = os.path.dirname(wd)
print(wd,dir)
import sys ; sys.path.append(dir)
from MacroBackend import PriceImporter ## This is one of my custom scripts holding functions for pulling price data from APIs. Your IDE might not find it yet, it will be found when run. 
import numpy as np
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates
from datetime import timedelta
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing

CURR_DIR = os.path.dirname(os.path.realpath(__file__))

def CovCorrCalc(AssetPrice1: np.ndarray, AssetPrice2: np.ndarray) -> np.ndarray:         #Function for the cov and Corr. 
    num = len(AssetPrice1)
    Numerator = 0; asset1_std = 0; asset2_std = 0
    mean_asset1 = np.mean(AssetPrice1)
    mean_asset2 = np.mean(AssetPrice2)
    CovCorr = []

    for i in range(int(num)):   
        Numerator += (AssetPrice1[i] - mean_asset1)*(AssetPrice2[i] - mean_asset2)
        asset1_std += (AssetPrice1[i] - mean_asset1)**2
        asset2_std += (AssetPrice2[i] - mean_asset2)**2
    Denominator = np.real((asset1_std**0.5)*(asset2_std**0.5))
    CovCorr.append(Numerator/(num-1))     #Co-variance of asset pair over the datasets.
    CovCorr.append(np.real(Numerator/Denominator))  #Correlation co-efficient of asset pair over the datasets.
    
    return CovCorr       #Returns a two number list that has the covariance in the first slot and correlation in the second.

########################## Correlation for certain periods calculated like a moving average function:
def CovCorrMA(period: int, AssetPrice1: np.ndarray, AssetPrice2: np.ndarray, index) -> pd.DataFrame:
    ProperLength = len(index)
    Numerator = 0; asset1_std = 0; asset2_std = 0; count = 0
    num = len(AssetPrice1)
    
    CovColName = 'CV_'+str(period)+'day'
    CorrColName = 'CC_'+str(period)+'day'
    Cov = np.array([]); Corr = np.array([])
    asset1Sublist = []; asset2Sublist = []
    for it in range(num):
        mean_asset1 = np.mean(AssetPrice1[it:(it+(period))])
        mean_asset2 = np.mean(AssetPrice2[it:(it+(period))])            
        if(it > (num-int(period))):
            break 
        for jay in range(int(period)):
            count = (it + jay); #print('Corr calc. man, calc std, period: ',period,'count: ',count, type(count))
            Numerator += (AssetPrice1[count] - mean_asset1)*(AssetPrice2[count] - mean_asset2)
            asset1_std += (AssetPrice1[count] - mean_asset1)**2
            asset2_std += (AssetPrice2[count] - mean_asset2)**2
            asset1Sublist.append(AssetPrice1[count])
            asset2Sublist.append(AssetPrice2[count])
        asset1_std /= period; asset2_std /= period
        asset1_std= asset1_std**0.5; asset2_std= asset2_std**0.5
        C1_std = np.std(asset1Sublist); C2_std = np.std(asset2Sublist)
        Denominator = np.real((asset1_std)*(asset2_std))
        PeriodCov = (np.real(Numerator/(period-1)))
        PeriodCorr = (np.real(PeriodCov/Denominator))
        Cov = np.append(Cov,PeriodCov)
        Corr = np.append(Corr,PeriodCorr)
        Numerator = 0        ## Reset the counter variables.
        asset1_std = 0
        asset2_std = 0
        asset1Sublist = []; asset2Sublist = [] 
    
    Cov = np.pad(Cov,((ProperLength-len(Cov),0)),constant_values=(np.nan))
    Corr = np.pad(Corr,((ProperLength-len(Corr),0)),constant_values=(np.nan))
    CovCorrDict = {CovColName:Cov,CorrColName:Corr}
    CovCorrDF = pd.DataFrame(CovCorrDict, index=index)
    return CovCorrDF       #Dataframe containing the MA for the given period, 1st column co-variance, second column correlation co-efficient. 

def Correlation(Series1:pd.Series, Series2:pd.Series,period='Full'): #Calculate Pearson COrrelation co-efficient between two series with time frame: period. 
    if (period=='Full'):
        Cor = round(Series1.corr(other=Series2,method='pearson', min_periods=len(Series1)),3)
        print('The correlation over the entire length between the two series: '+Series1.name+' and '+Series1.name+' is: '+str(round(Cor,3))+'.')
    else:
        Cor = Series1.rolling(period).corr(Series2) ##Using Pandas to calculate the correlation. 
    return Cor      

 #You can change to manual coin and time length selection instead of auto selection based on what you've already saved in the input .csv file
# by commenting out the relevant 6 lines below here and uncommenting lines 23 - 25. 
#Auto input of coin selection and parameters:
dfIn = pd.read_excel(CURR_DIR+"/PairCorrInput.xlsx")  #We need to make sure the little r is there next to the path string to make it a raw string.
api1 = str(dfIn.loc[0].at["api1"]); api2 = str(dfIn.loc[0].at["api2"])
type1 = str(dfIn.loc[1].at["api1"]); type2 = str(dfIn.loc[1].at["api2"])
mode = str(dfIn.loc[3].at["api1"])
plot2axii = str(dfIn.loc[2].at["api1"])
if api1 == 'tv':
    strAss1 = str(dfIn.loc[0].at["asset1"])
    splits = strAss1.split(',')
    print(splits)
    asset1 = splits[0]
else:
    asset1 = dfIn.loc[0].at["asset1"] 
    strAss1 = asset1    
if api2 == 'tv':
    strAss2 = str(dfIn.loc[0].at["asset2"])
    splits = strAss2.split(',')
    print(splits)
    asset2 = splits[0]
else:    
    asset2 = dfIn.loc[0].at["asset2"] 
    strAss2 = asset2 

CCAvs = pd.Series.dropna(dfIn["CC Averages"])
numCCAvs = len(CCAvs)
print("Correlation averages to calculate: \n",CCAvs,numCCAvs)

TimeLength = int(dfIn.loc[0].at["NumDays"])
end = datetime.date.today()
start = end-timedelta(days=TimeLength)
print(TimeLength,start,end)
DataStart = start.strftime("%Y-%m-%d")

if mode == 'disk':
    filename = askopenfilename(title='Choose excel file (.xlsx only) to load data for asset 1.',defaultextension='.xlsx') 
    pathList = filename.split('/'); namePlusExt = pathList[len(pathList)-1]; nameList = namePlusExt.split('.'); name = nameList[0]
    asset1 = name; strAss1 = name
    # show an "Open" dialog box and return the path to the selected file
    print('Load asset #1 data from: ',filename)
    df = pd.read_excel(filename); print(df[df.columns[0]])
    df.set_index(pd.DatetimeIndex(df[df.columns[0]]),inplace=True)
    print('Asset 1, name of data: ',asset1,'data: ', df)
    filename2 = askopenfilename(title='Choose excel file (.xlsx only) to load data for asset 2.',defaultextension='.xlsx')
    print('Load asset #2 data from: ',filename2)
    pathList = filename2.split('/'); namePlusExt = pathList[len(pathList)-1]; nameList = namePlusExt.split('.'); name = nameList[0]
    asset2 = name; strAss2 = name
    df2 = pd.read_excel(filename2)
    df2.set_index(pd.DatetimeIndex(df2[df2.columns[0]]),inplace=True)
    print('Asset 2, name of data: ',asset2,'data: ', df2)
    df = df[start:df.index[len(df)-1]]; df2 = df2[start:df2.index[len(df2)-1]]
else:    
    #Pull data from APIs:
    print('Asset 1 is: '+str(asset1)); print('Asset 2 is: '+str(asset2))
    df = PriceImporter.PullDailyAssetData(strAss1,api1,DataStart,endDate=None)
    df2 = PriceImporter.PullDailyAssetData(strAss2,api2,DataStart,endDate=None)
    df = df[start:end]; df2 = df2[start:end]

length = len(df); length2 = len(df2)
if(length < length2):
    print('Asset 1 data is shorter than asset 2.')
else:
    print('Asset 2 data is shorter than asset 1.')
print('asset1 length: '+str(length)+ ', asset2 length: '+str(length2)+'.')

df, df2 = PriceImporter.GetIndiciiSame(df,df2) 
print(df,df2)    

print("Number of days into the past before today tracked here: "+str(TimeLength)+'\r')
PriceMatrix1 = pd.DataFrame(df); PriceMatrix2 = pd.DataFrame(df2)
PriceMatrix1.fillna(method='ffill',inplace=True); PriceMatrix2.fillna(method='ffill',inplace=True)
PriceMatrix1.to_excel(CURR_DIR+"/Asset1Data.xlsx")
PriceMatrix2.to_excel(CURR_DIR+"/Asset2Data.xlsx")
print(PriceMatrix1.columns,PriceMatrix2.columns)
if len(PriceMatrix1.columns) < 2:
    Series1 = pd.Series(PriceMatrix1.squeeze(),name=strAss1)
    Price1 = pd.Series.to_numpy(Series1)
else:    
    Series1 = pd.Series(PriceMatrix1['Close'],name=strAss1)
    Price1 = pd.Series.to_numpy(Series1)
if len(PriceMatrix2.columns) < 2:
    Series2 = pd.Series(PriceMatrix2.squeeze(),name=strAss2)
    Price2 = pd.Series.to_numpy(Series2)
else:    
    Series2 = pd.Series(PriceMatrix2['Close'],name=strAss2)
    Price2 = pd.Series.to_numpy(Series2)
#Use my covariance, correlation function: 
CovCorr = CovCorrCalc(Price1, Price2)
CovString = 'Asset pair co-variance over the whole \ntime period (manual): '+str(round(CovCorr[0], 4))
CorrString = 'Asset pair correlation over the whole \ntime period (manual): '+str(round(CovCorr[1], 4))
print(CovString); print(CorrString)

#Check it with numpy and pandas correlation calculations:
print('Standard deviation (numpy) asset1, asset2: ',np.std(Price1),np.std(Price2))
NumpyCorr = np.corrcoef(Price1,Price2)
NumpyCov = np.cov(Price1,Price2)
PandasCorr = Correlation(Series1, Series2)
NPCorrString = 'Asset pair correlation over the whole \ntime period (from numpy): '+str(round(NumpyCorr[1,0], 4))
pdCorrString = 'Asset pair correlation over the whole \ntime period (from pandas): '+str(PandasCorr)
NPCovString = 'Asset pair covariance over the whole \ntime period (from numpy): '+str(round(NumpyCov[1,0], 4))
print(NPCorrString); print(pdCorrString); print(NPCovString)

if type1 == 'yoy':
    Series1 = pd.Series(PriceImporter.YoYCalcFromDaily(Series1),name=strAss1)
if type2 == 'yoy':   
    Series2 = pd.Series(PriceImporter.YoYCalcFromDaily(Series2) ,name=strAss2)
MasterDF = pd.concat([PriceMatrix1,PriceMatrix2],axis=1) # Create the master dataframe to output to csv.  
Index = pd.DatetimeIndex(MasterDF.index)
for i in range(numCCAvs):
    CorrAv = CovCorrMA(int(CCAvs[i]),Price1, Price2,Index)
    PDCor = Correlation(Series1, Series2, period=int(CCAvs[i]))
    PDCor = pd.Series(PDCor, name='Pandas rolling corr ('+str(int(CCAvs[i]))+'d)')
    MasterDF = pd.concat([MasterDF, CorrAv, PDCor],axis=1)
CovCorr_Full = CovCorrMA(TimeLength, Price1, Price2,Index)

MasterDF = pd.concat([MasterDF, CovCorr_Full],axis=1)
MasterDF.to_excel(CURR_DIR+"/PairCorrOutput.xlsx", index = False) 
print('Data output to: '+CURR_DIR+"/PairCorrOutput.csv") 

#Calculate normalised price ratio wave and normalized percentage changed from median wave.
PriceRatio = Series1/Series2
Ratio_norm = (PriceRatio - PriceRatio.min())/ (PriceRatio.max() - PriceRatio.min())
Percentage = PriceRatio
midpoint = np.median(PriceRatio)
points = len(PriceRatio)
print('Median of the '+str(asset1)+'/'+str(asset2)+' data is: '+ str(midpoint),' length of: ',points)
for i in range(int(points)):
    Percentage.iloc[i] = ((Percentage.iloc[i] - midpoint)/midpoint)*100

# # ################################### #Plot figures #############################################################
#Price ratio plot.
fig = plt.figure(figsize=(10,9.5))
gs1 = GridSpec(3, 1, top = 0.96, bottom=0.07, left=0.12, right=0.87, wspace=0.01, height_ratios=[2,2,1], hspace=0)
ratString = str(asset1)+'/'+str(asset2)
ax1 = fig.add_subplot(gs1[0])
TitleString = 'Price ratio '+str(asset1)+'/'+str(asset2)+r', $\Delta$% from median'
ax1.set_title(TitleString, fontsize=12, fontweight = 'bold')
trace3 = ax1.plot(PriceMatrix1.index,Percentage, c = 'black', label=ratString)
ax1.invert_xaxis()
ax1.set_ylabel(r'$\Delta$ price from median (%)', fontsize=12, fontweight = 'bold')
ax1b = ax1.twinx()
ax1b.plot(PriceMatrix1.index,Percentage, c = 'black')
ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
ax1b.yaxis.set_major_formatter(mtick.PercentFormatter())
ax1.legend(loc=2)
for axis in ['top','bottom','left','right']:
        ax1.spines[axis].set_linewidth(1.5)  
xleft = PriceMatrix1.index[0] - timedelta(days = 15); xright = PriceMatrix1.index[len(PriceMatrix1)-1] + timedelta(days = 15)
ax1.set_xlim(xleft, xright)
ax1.minorticks_on(); ax1b.minorticks_on(); ax1.grid(visible=True,which='both',linewidth=0.55,linestyle=':')   
ax1.set_xticklabels([])
ax1.tick_params(axis='x', labelsize=0,labelrotation=90)      

#Price of both assets on the one graph.

ax2 = fig.add_subplot(gs1[1],sharex=ax1)
TitleString = str(asset1)+' vs left axis, '+str(asset2)+' vs right axis'
ax2.set_ylabel('Price (USD)', fontsize=12, fontweight = 'bold')
#ax2.set_title(TitleString, fontsize=12)
trace1 = ax2.plot(Series1, c='black',label =str(asset1)+'\n(left)')
ax2b = ax2.twinx()
trace2 = ax2b.plot(Series2, c='red',label =asset2+'\n(right)')
ax2b.set_ylabel('Price (USD)', fontsize=12, fontweight = 'bold')
ax2.legend(loc=2,fontsize='small'); ax2b.legend(loc=1,fontsize='small')
for axis in ['top','bottom','left','right']:
        ax2.spines[axis].set_linewidth(1.5)  
ax2.minorticks_on(); ax2b.minorticks_on()        
ax2.grid(visible=True,which='both',linewidth=0.55,linestyle=':')   
ax2.set_xticklabels([])
ax2.tick_params(axis='x', labelsize=0,labelrotation=90) 
if plot2axii == 'log':    
    ax2.set_yscale('log'); ax2b.set_yscale('log')

# Correlation fig.:
CorrString = 'Pair correlation over the whole period: '+str(round(float(NumpyCorr[1,0]), 4))
ax3 = fig.add_subplot(gs1[2],sharex=ax1)
ax3.set_title(CorrString, fontsize=9)
ax3.set_ylabel('Correlation', fontsize=12, fontweight = 'bold')
for i in range(numCCAvs):
    traceName = 'CC_'+str(int(CCAvs[i]))+'day'
    traceName2 = 'Pandas rolling corr ('+str(int(CCAvs[i]))+'d)'
    tracelabel = '$CC_{'+str(int(CCAvs[i]))+'d}$'
    r = (i/(numCCAvs-1)); g = 0; b = 1 - (i/(numCCAvs-1))
    LW = 1+(i*0.25)
    #ax3.plot(MasterDF[traceName], c =(r, g, b), label = tracelabel, linewidth = LW)
    ax3.plot(MasterDF['Pandas rolling corr ('+str(int(CCAvs[i]))+'d)'], c =(r, g, b), label = tracelabel, linewidth = LW)
ax3.legend(loc=1, fontsize='small',bbox_to_anchor=(1.15, 0.9))
ax3.set_ylim(-1.1, 1.1)
for axis in ['top','bottom','left','right']:
        ax3.spines[axis].set_linewidth(1.5)  
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%y-%b'))
xmin = Percentage.index[0]; xmax = Percentage.index[len(Percentage)-1]; tick_count = 13
stepsize = (xmax - xmin) / tick_count        
ax3.xaxis.set_ticks(np.arange(xmin, xmax, stepsize))
ax3.tick_params(axis='x', labelsize='small',labelrotation=45)

plt.show() # Show figure. Function will remain running until you close the figure. 