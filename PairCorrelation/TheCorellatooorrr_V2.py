import os
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
dir = os.path.dirname(wd)
print(wd,dir); fdel =os.path.sep
import sys ; sys.path.append(dir)
from MacroBackend import PriceImporter, Pull_Data ## This is one of my custom scripts holding functions for pulling price data from APIs. Your IDE might not find it yet, it will be found when run. 
from MacroBackend import Utilities
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
### This is a slow, bullshit, manual way to do this that I wrote early on in my coding career.
## Must replace with a more efficient method that uses numpy and pandas to do the same thing.   
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

def efficient_cov_corr(period, asset_price1, asset_price2):
    # Convert the numpy arrays to pandas Series
    asset_price1 = pd.Series(asset_price1)
    asset_price2 = pd.Series(asset_price2)

    # Calculate rolling covariance
    rolling_cov = asset_price1.rolling(window=period).cov(asset_price2)

    # Calculate rolling correlation
    rolling_corr = asset_price1.rolling(window=period).corr(asset_price2)

    # Create a DataFrame from the results
    df = pd.DataFrame({
        'CV_'+str(period)+'day': rolling_cov,
        'CC_'+str(period)+'day': rolling_corr
    })

    return df

def Correlation(Series1:pd.Series, Series2:pd.Series,period='Full'): #Calculate Pearson Correlation co-efficient between two series with time frame: period. 
    if (period=='Full'):
        Cor = round(Series1.corr(Series2),3)
        print('The correlation over the entire length between the two series: '+Series1.name+' and '+Series2.name+' is: '+str(round(Cor,3))+'.')
    else:
        Cor = Series1.rolling(period).corr(Series2) ##Using Pandas to calculate the correlation. 
    return Cor      

#You can change to manual coin and time length selection instead of auto selection based on what you've already saved in the input .csv file
# by commenting out the relevant 6 lines below here and uncommenting lines 23 - 25. 
#Auto input of coin selection and parameters:
dfIn = pd.read_excel(wd+fdel+"/PairCorrInput.xlsx", index_col=0)  #We need to make sure the little r is there next to the path string to make it a raw string.


scamFimode = dfIn.loc["Defi_LP_mode"].at["asset1"] == "True"
save_data = dfIn.loc["OUTPUT DATA"].at["asset1"] == "True"
dollabillzyo = dfIn.loc["add_$_ax2"].at["asset1"] == "True"

if scamFimode is True:
    print("Are you some kind of degen fuck? Stop playing with silly circular number scams and learn what money is.")
    LP_Entry_Date = str(dfIn.loc["LP_Entry_Date"].at["asset1"])
    LP_Exit_Date = str(dfIn.loc["LP_Exit_Date"].at["asset1"])
    LP_Entry = datetime.datetime.strptime(LP_Entry_Date.split(' ')[0],'%Y-%m-%d').date()
    LP_Exit = datetime.datetime.strptime(LP_Exit_Date.split(' ')[0],'%Y-%m-%d').date()
    print("Scamfi mode on, entry, exit dates: ", LP_Entry, LP_Exit)

api1 = str(dfIn.loc['assets'].at["api1"]); api2 = str(dfIn.loc['assets'].at["api2"])
type1 = str(dfIn.loc['type'].at["asset1"]); type2 = type1
mode = str(dfIn.loc['Mode'].at["asset1"])

ax1scale = str(dfIn.loc['ax1scale'].at["asset1"])
ax2scale = str(dfIn.loc['ax2scale'].at["asset1"])
strAss1 = str(dfIn.loc['assets'].at["asset1"])
strAss2 = str(dfIn.loc['assets'].at["asset2"])
ax2left = str(dfIn.loc['ax2labels'].at["asset1"])
ax2right = str(dfIn.loc['ax2labels'].at["asset2"])

if pd.isna(ax2left):
    ax2left = "Price (USD)"
if pd.isna(ax2right):
    ax2left = "Price (USD)"

if api1 == 'tv':
    splits = strAss1.split(',')
    asset1 = splits[0]
else:
    asset1 = strAss1 
if api2 == 'tv':
    splits = strAss2.split(',')
    asset2 = splits[0]
else:    
    asset2 = strAss2

CCAvs = dfIn["CC Averages"].dropna()
numCCAvs = len(CCAvs)
print("Correlation averages to calculate: \n",CCAvs,numCCAvs)

TimeLength = int(dfIn.loc['assets'].at["NumDays"])
end = datetime.date.today()
Start_Date = dfIn.loc['Start_Date'].at["asset1"].date()
End_Date = dfIn.loc['End_Date'].at["asset1"].date()

start = Start_Date.strftime("%Y-%m-%d")

if mode == 'load_dialogue':
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
elif mode == 'local':  
    df = pd.read_excel(wd+fdel+"asset1Data.xlsx")
    df2 = pd.read_excel(wd+fdel+"asset2Data.xlsx")
elif mode == 'api':    
    #Pull data from APIs:
    print('Asset 1 is: '+str(asset1)); print('Asset 2 is: '+str(asset2))
    dat = Pull_Data.dataset(); dat.get_data(api1, strAss1, start)
    df = dat.data; ass1Info = dat.SeriesInfo
    dat2 = Pull_Data.dataset(); dat2.get_data(api2, strAss2, start)
    df2 = dat2.data; ass2Info = dat2.SeriesInfo
    df = df[Start_Date:end]
    df2 = df2[Start_Date:end]
else:
    print('Mode not recognised, please check the input file for errors in the "Mode" field.')
    quit()

act_start = pd.to_datetime(df.index[0]).date()
req_start = datetime.datetime.strptime(start,'%Y-%m-%d').date()
if req_start < act_start:
    print("Requested start data earlier than actual start date....")
    if scamFimode is True:
        print("Are you some kind of degen fuck? Stop playing with silly circular number scams and learn what money is.\
              Suckle upon some SBF nutzz....")
        LP_Entry_Date = act_start.strftime('%Y-%m-%d')
        LP_Entry = datetime.datetime.strptime(LP_Entry_Date,'%Y-%m-%d').date()
    
# if Start_Date 
length = len(df); length2 = len(df2)
if(length < length2):
    print('Asset 1 data is shorter than asset 2.')
else:
    print('Asset 2 data is shorter than asset 1.')
print('asset1 length: '+str(length)+ ', asset2 length: '+str(length2)+'.')

df, df2 = PriceImporter.GetIndiciiSame(df,df2) 
print(df,df2)    

PriceMatrix1 = pd.DataFrame(df); PriceMatrix2 = pd.DataFrame(df2)
PriceMatrix1.fillna(method='ffill',inplace=True); PriceMatrix2.fillna(method='ffill',inplace=True)
PriceMatrix1 = PriceMatrix1[Start_Date:End_Date]; PriceMatrix2 = PriceMatrix2[Start_Date:End_Date]
PriceMatrix1.to_excel(wd+fdel+"asset1Data.xlsx",sheet_name='Closing_Price')
with pd.ExcelWriter(wd+fdel+"asset1Data.xlsx", engine='openpyxl', mode='a') as writer:  
    ass1Info.to_excel(writer, sheet_name='SeriesInfo')

PriceMatrix2.to_excel(wd+fdel+"asset2Data.xlsx",sheet_name='Closing_Price')
with pd.ExcelWriter(wd+fdel+"asset2Data.xlsx", engine='openpyxl', mode='a') as writer:  
    ass2Info.to_excel(writer, sheet_name='SeriesInfo')

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
    #CorrAv = CovCorrMA(int(CCAvs[i]),Price1, Price2,Index)
    CorrAv = efficient_cov_corr(int(CCAvs[i]), Price1, Price2)
    PDCor = Correlation(Series1, Series2, period=int(CCAvs[i]))
    PDCor = pd.Series(PDCor, name='Pandas rolling corr ('+str(int(CCAvs[i]))+'d)')
    MasterDF = pd.concat([MasterDF, CorrAv, PDCor],axis=1)
CovCorr_Full = efficient_cov_corr(TimeLength, Price1, Price2)
#CovCorrMA(TimeLength, Price1, Price2,Index)

MasterDF = pd.concat([MasterDF, CovCorr_Full],axis=1)
if save_data:
    MasterDF.to_excel(wd+fdel+"PairCorrOutput.xlsx", index = False) 
    print('Data output to: '+wd+fdel+"PairCorrOutput.csv") 

#Calculate normalised price ratio wave and normalized percentage changed from median wave.
print(Series1,Series2)
PriceRatio = Series1/Series2
print(PriceRatio)
Ratio_norm = (PriceRatio - PriceRatio.min())/ (PriceRatio.max() - PriceRatio.min())
Percentage = PriceRatio
midpoint = np.median(PriceRatio)
points = len(PriceRatio)
print('Median of the '+str(asset1)+'/'+str(asset2)+' data is: '+ str(midpoint),' length of: ',points)
for i in range(int(points)):
    Percentage.iloc[i] = ((Percentage.iloc[i] - midpoint)/midpoint)*100+100

# # ################################### #Plot figures #############################################################
Ticks, tickLabs = Utilities.EqualSpacedTicks(10,data=Percentage,LogOrLin=ax1scale,LabOffset=-100,labSuffix='%')

#Price ratio plot.
fig = plt.figure(figsize=(10,9.5))
gs1 = GridSpec(3, 1, top = 0.96, bottom=0.07, left=0.1, right=0.9, wspace=0.01, height_ratios=[2,2,1], hspace=0)
ratString = str(asset1)+'/'+str(asset2)
ax1 = fig.add_subplot(gs1[0])
TitleString = 'Price ratio: '+str(asset1)+'/'+str(asset2)+r', $\Delta$% from median'
ax1.set_title(TitleString, fontsize=12, fontweight = 'bold')
trace3 = ax1.plot(Percentage, c = 'black', label=ratString)
ax1.invert_xaxis(); ax1.minorticks_off()
ax1.set_yscale(ax1scale)
ax1.tick_params(axis='both',which='both',length=0,width=0,labelsize=0,labelleft=False,left=False)
ax1.set_yticks(Ticks); ax1.set_yticklabels(tickLabs)
ax1.tick_params(axis='y',which='major',length=3,width=1,labelsize=9,left=True,right=True,labelright=True,labelleft=True)
ax1.grid(axis='y',visible=True,which='major',linewidth=0.6,linestyle=':')
ax1.grid(axis='x',visible=True,which='both',linewidth=0.6,linestyle=':')
ax1.set_ylabel(r'$\Delta$ price from median (%)', fontsize=12, fontweight = 'bold')
ax1.axhline(y=100,color='red',lw=0.75,ls=':')
ax1.legend(loc=1,framealpha=1,fontsize=10)   
ax1.tick_params(axis='x', labelsize=0,labelrotation=90)  
for axis in ['top','bottom','left','right']:
        ax1.spines[axis].set_linewidth(1.5)  

if scamFimode is True:     
    entry = ax1.axvline(LP_Entry,ls=":",lw=1.25,color='green')     
    exit = ax1.axvline(LP_Exit,ls=":",lw=1.25,color='red') 
    middle = Percentage.index[round(len(Percentage)/2)]

    ent = Utilities.GetClosestDateInIndex(Series1, LP_Entry.strftime("%Y-%m-%d"))[1]
    ex = Utilities.GetClosestDateInIndex(Series2, LP_Exit.strftime("%Y-%m-%d"))[1]
    mid = Percentage.index[round((ex - ent)/2)]
    print("Midpoint of the date range: ",mid, round((ex - ent)/2))
    
    print(Series1.index)
    entryPratio = Series1[ent]/Series2[ent]
    exitPratio = Series1[ex]/Series2[ex]
    PratioDelta = round(((exitPratio-entryPratio)/entryPratio)*100,2)

    ax1.axhline(Percentage[ent],ls=":",lw=1.5,color='green')
    ax1.axhline(Percentage[ex],ls=":",lw=1.5,color='red')
    ax1.annotate("",xy=(mid,Percentage[ent]),xytext=(mid,Percentage[ex]),xycoords='data',textcoords="data",arrowprops={'arrowstyle':'<->'})
    ax1.text(0.25,0.5,"LP ratio delta: "+str(PratioDelta)+"%",horizontalalignment='left', #bbox=dict(facecolor='none', edgecolor='black', boxstyle='round,pad=0'), 
        transform=ax1.transAxes,backgroundcolor='white',alpha=1,fontsize=9)
    ax1.text(ent,Percentage[ent]+(0.05*Percentage[ent]),"LP entry",horizontalalignment='left', bbox = None, alpha=1,fontsize=9,c='green', fontweight='bold')
    ax1.text(ex,Percentage[ex]+(0.05*Percentage[ex]),"LP exit",horizontalalignment='right', bbox = None, alpha=1, fontsize=9,c='red', fontweight='bold')
    il = round((2*((PratioDelta/100)+1)**0.5/(2+(PratioDelta/100))-1)*100,2)             
    #IL(k) = (2*SQRT((k/100)+1)/(2+(k/100))-1)*100, k = delta price ratio in %. 
    ax1.text(0.35,0.15,"IL: "+str(il)+"%",horizontalalignment='left', transform=ax1.transAxes, 
             backgroundcolor='white',alpha=1,fontsize=10,c='black')

XMargin = round(0.01*TimeLength)
xleft = PriceMatrix1.index[0] - timedelta(days = XMargin); xright = PriceMatrix1.index[len(PriceMatrix1)-1] + timedelta(days = XMargin)
ax1.set_xlim(xleft, xright)    
#Price of both assets on the one graph.
Ticks2, tickLabs2 = Utilities.EqualSpacedTicks(8, data = Series1, LogOrLin=ax2scale)
Ticks3, tickLabs3 = Utilities.EqualSpacedTicks(8, data = Series2, LogOrLin=ax2scale)

ax2 = fig.add_subplot(gs1[1],sharex=ax1)
TitleString = str(asset1)+' vs left axis, '+str(asset2)+' vs right axis'
ax2.set_ylabel(ax2left, fontsize=12, fontweight = 'bold')
trace1 = ax2.plot(Series1, c='black',label =str(asset1)+'\n(left)')
ax2b = ax2.twinx()
trace2 = ax2b.plot(Series2, c='red',label =asset2+'\n(right)')
ax2b.set_ylabel(ax2right, fontsize=12, fontweight = 'bold')
ax2.legend(loc=2,fontsize='small'); ax2b.legend(loc=1,fontsize='small')
ax2.set_yscale(ax2scale); ax2b.set_yscale(ax2scale)

ax2.tick_params(axis='both',which='both',length=0,width=0,labelsize=0,labelleft=False,left=False,labelright=False,right=False)
ax2b.tick_params(axis='both',which='both',length=0,width=0,labelsize=0,labelleft=False,left=False,labelright=False,right=False)
ax2.set_yticks(Ticks2); ax2.set_yticklabels(tickLabs2)
ax2b.set_yticks(Ticks3); ax2b.set_yticklabels(tickLabs3)
ax2.tick_params(axis='y',which='major',length=3,width=1,labelsize=9,left=True,labelleft=True)
ax2b.tick_params(axis='y',which='major',length=3,width=1,labelsize=9,right=True,labelright=True)
if dollabillzyo:
    ax2.yaxis.set_major_formatter('${x}')
    ax2b.yaxis.set_major_formatter('${x}')  
ax2.grid(visible=True,axis='y',which='major',linewidth=0.55,linestyle=':')   

for axis in ['top','bottom','left','right']:
        ax2.spines[axis].set_linewidth(1.5)       
ax2.grid(visible=True,axis='x',which='both',linewidth=0.55,linestyle=':')   
ax2.set_xticklabels([])
ax2.tick_params(axis='x', labelsize=0,labelrotation=90) 


# Correlation fig.:
CorrString = 'Pair correlation over the whole period: '+str(round(float(NumpyCorr[1,0]), 4))
ax3 = fig.add_subplot(gs1[2],sharex=ax1)
ax3.set_title(CorrString, fontsize=10)
ax3.set_ylabel('Correlation', fontsize=12, fontweight = 'bold')
for i in range(numCCAvs):
    traceName = 'CC_'+str(int(CCAvs[i]))+'day'
    traceName2 = 'Pandas rolling corr ('+str(int(CCAvs[i]))+'d)'
    tracelabel = '$CC_{'+str(int(CCAvs[i]))+'d}$'
    r = (i/(numCCAvs-1)); g = 0; b = 1 - (i/(numCCAvs-1))
    LW = 1+(i*0.25)
    #ax3.plot(MasterDF[traceName], c =(r, g, b), label = tracelabel, linewidth = LW)
    ax3.plot(MasterDF['Pandas rolling corr ('+str(int(CCAvs[i]))+'d)'], c =(r, g, b), label = tracelabel, linewidth = LW)
ax3.legend(loc=1, fontsize=9,bbox_to_anchor=(1.12, 0.9))
ax3.set_ylim(-1.1, 1.1)
for axis in ['top','bottom','left','right']:
        ax3.spines[axis].set_linewidth(1.5)  
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%y-%b'))
xmin = Percentage.index[0]; xmax = Percentage.index[len(Percentage)-1]; tick_count = 13
stepsize = (xmax - xmin) / tick_count        
ax3.xaxis.set_ticks(np.arange(xmin, xmax, stepsize))
ax3.tick_params(axis='x', labelsize='small',labelrotation=45)
ax3.minorticks_on(); ax3.grid(visible=True,which='both',axis='both')
ax3.axhline(y=0,c='red',lw=1,ls=':')

plt.show() # Show figure. Function will remain running until you close the figure. 