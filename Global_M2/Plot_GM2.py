###### Required modules/packages #####################################
import os
wd = os.path.dirname(__file__)  ## This gets the working direectory which is the folder where you have placed this .py file. 
parent = os.path.dirname(wd)
print(wd,parent)
fdel = os.path.sep
import sys ; sys.path.append(parent)
from MacroBackend import PriceImporter, Utilities, Charting ## This is one of my custom scripts holding functions for pulling price data from APIs. 
#Your IDE might not find it before running script. 
import pandas as pd
import matplotlib
from matplotlib import colors as mcolors
import matplotlib.pylab as pl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import numpy as np
import tkinter as tk
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename

matplotlib.use("QtAgg")
plt.rcParams['font.family'] = 'serif'
plt.rcParams['figure.dpi'] = 105; plt.rcParams['savefig.dpi'] = 200   ###Set the resolution of the displayed figs & saved fig respectively. 


Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
fdel = os.path.sep
print('System information: ',sys.platform,', directory delimiter: ', fdel, ', working directory: ', wd)

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

 # Summarize data and plot. ######
def PlotM2Data(GlobalM2:pd.DataFrame,DataSum:pd.DataFrame,Rank:list=None,LedgFontSize:int=9,colors:list = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)):
    if str(type(colors)) == "<class 'dict'>":
        colors = [color for color in colors.keys()]
    figure = plt.figure(figsize=(11,8.5), tight_layout=True); numEcons = len(DataSum)
    gs = GridSpec(2, 1, top = 0.94, bottom=0.05,left=0.08,right=0.85, height_ratios=[1,1], hspace=0)
    ax = figure.add_subplot(gs[0]); ax2 = figure.add_subplot(gs[1],sharex=ax)
    ax.set_title('M2 money supply (in USD value), top '+str(numEcons)+' economies',fontweight='bold',fontsize=14)
    if Rank is not None:
        iterator = Rank
    else:
        iterator = DataSum.index.to_list()
    #colors = pl.cm.copper(np.linspace(0,1,len(iterator)))

    for i in range(len(iterator)):
        #thick = (0.5+(numEcons*0.1))-(0.5+(i*0.1))
        ranNum = np.random.random(); culNum = int(round(ranNum*(len(colors)-1-i),0)); culla = colors[culNum]
        Country = str(iterator[i])
        M2Trace = GlobalM2[Country].copy(); print(Country+', latest print: '+str(M2Trace[len(M2Trace)-1])+', one before that: '+str(M2Trace[len(M2Trace)-2]))
        print(M2Trace.tail(10))
        YoYm = M2Trace.copy().pct_change(periods=12)*100
        print(M2Trace.tail(10))
        Dat = ax.plot(M2Trace,label=Country,color=colors[culNum])
        yoy = ax2.plot(YoYm,label=Country,color=colors[culNum])
        colors.remove(colors[culNum])
    ax.set_yscale('log'); ax.set_ylabel('M2 Money supply (USD)',fontweight='bold',fontsize=12)
    ax.tick_params(axis='x',labelsize=0)
    ax.text(1.08,1,s='Ranked by M2',fontsize=11,transform=ax.transAxes,horizontalalignment='center',verticalalignment='center')
    ax2.set_ylabel(r'M2 YoY $\Delta$%',fontweight='bold',fontsize=12)
    ax.legend(loc=1,bbox_to_anchor=(1.19,0.95),fontsize=LedgFontSize)         
    for axis in ['top','bottom','left','right']:
            ax.spines[axis].set_linewidth(1.5); ax2.spines[axis].set_linewidth(1.5)        
    ax.minorticks_on(); ax2.minorticks_on()
    ax.margins(0.02,0.02); ax2.margins(0.02,0.02)

def Plot_GlobalM2(Global_M2:pd.Series,GlobalM2:pd.DataFrame):
    fig = plt.figure(figsize=(11,9), tight_layout=True)
    gs = GridSpec(4, 1, top = 0.94, bottom=0.05,left=0.1,right=0.96, height_ratios=[1,0.7,0.33,0.33], hspace=0.01)
    ax = fig.add_subplot(gs[0]); ax2 = fig.add_subplot(gs[1],sharex=ax); ax3 = fig.add_subplot(gs[2],sharex=ax); ax4 = fig.add_subplot(gs[3],sharex=ax)
    ax.set_title('M2 money supply, sum of top '+str(int(round(((len(GlobalM2.columns)-2)/2),0)))+' economies (USD)',fontweight='bold',fontsize=14)
    YoYm2 = Global_M2.copy().pct_change(periods=12)*100
    temp = YoYm2.copy()+100
    sd = temp.pct_change(periods=12)*100
    print(sd)
    Ann6m =  Utilities.MonthPeriodAnnGrowth(Global_M2.copy(),6)
    Ann3m = Utilities.MonthPeriodAnnGrowth(Global_M2.copy(),3)
    Dat2 = ax.plot(Global_M2,label='Global M2 aggregate',color='blue',lw=2)
    yoy2 = ax2.plot(YoYm2,label=r'GM2 YoY $\Delta$%',color='black',lw=2.25)
    
    an6m = ax2.plot(Ann6m,label=r'GM2 6m ann. $\Delta$%',color='blue',lw=1.5)
    an3m = ax2.plot(Ann3m,label=r'GM2 3m ann. $\Delta$%',color='orangered',lw=1)
    ax2.legend(loc=2,fontsize=8)
    ax.set_yscale('log'); ax.set_ylabel('M2 Money supply (USD)',fontweight='bold',fontsize=12)
    mom = pd.Series([((((Global_M2[i]-Global_M2[i-1])/Global_M2[i-1])*100)) for i in range(len(Global_M2))],name="GlobalM2_MoM",index=Global_M2.index)

    ax.minorticks_on(); ax2.minorticks_on(); ax3.minorticks_on()
    ax.margins(0.02,0.02); ax2.margins(0.02,0.02); ax3.margins(0.02,0.02)
    ax.grid(which='both',axis="both",linestyle="dotted")
    ax2.grid(which='both',axis="both",linestyle="dotted"); ax3.grid(which='both',axis="both",linestyle="dotted")
    exM, whyM = ax3.margins()
    DateRange = (mom.index[len(mom)-1] - mom.index[0]).days
    DateRangeAct = DateRange - (2*exM)*DateRange
    print('Date range covers ',DateRangeAct, 'days.')
    BarWidth = np.floor(DateRangeAct/len(mom))

    mom2 = ax3.bar(x = mom.index, height = mom, width = BarWidth, label=r'Global M2 MoM $\Delta$%',color='green',lw=1)
    SeconDeriv = ax4.plot(sd,label=r'YoY $\Delta$% of YoY $\Delta$% of global M2',color='red',lw=1)
    ax3.set_axisbelow(True)
    ax.tick_params(axis='x',labelsize=0); ax.tick_params(axis='x',labelsize=0); ax2.tick_params(axis='x',labelsize=0)
    ax2.set_ylabel(r'M2 YoY $\Delta$%',fontweight='bold',fontsize=12); ax3.set_ylabel(r'MoM $\Delta$%',fontweight='bold',fontsize=10)
    ax2.axhline(y=0,linestyle='dashed',color='red',lw=1); ax3.axhline(y=0,linestyle='dashed',color='red',lw=0.75)
    ax4.set_ylabel(r'YoY$^{2}$ $\Delta$%', fontweight='bold',fontsize=11)
    ax4.grid(which='both',axis="both",linestyle="dotted"); ax4.legend(loc=2,fontsize='small')
    ax.legend(loc=1,bbox_to_anchor=(0.1,1.1),fontsize=9)         
    for axis in ['top','bottom','left','right']:
            ax.spines[axis].set_linewidth(1.5); ax2.spines[axis].set_linewidth(1.5) ; ax3.spines[axis].set_linewidth(1.5)     
            ax4.spines[axis].set_linewidth(1.5)   

    laggers = []; latestPrint = GlobalM2.index[len(GlobalM2)-1]; print('Latest data print: ',latestPrint); M2Total = 0; missingT = 0
    for i in range(2,len(GlobalM2.columns),1):
        split = str(GlobalM2.columns[i]).split('_')
        if len(split) > 1:
            pass
        else:
            Last_M2 = GlobalM2.iloc[len(GlobalM2.index)-1].at[GlobalM2.columns[i]]; l = 0
            if pd.isna(Last_M2):
                while pd.isna(Last_M2):
                    l += 1
                    Last_M2 = GlobalM2.iloc[len(GlobalM2.index)-2-l].at[GlobalM2.columns[i]]
            country = pd.Series(GlobalM2[GlobalM2.columns[i]],name=GlobalM2.columns[i])
            country.dropna(inplace=True); CountryLatest = country.index[len(country)-1]
            M2Total += Last_M2
            if CountryLatest < latestPrint:
                laggers.append(country.name)
                LastM2 = GlobalM2.iloc[len(GlobalM2.index)-2].at[country.name]
                while pd.isna(LastM2):
                    i += 1
                    LastM2 = GlobalM2.iloc[len(GlobalM2.index)-2-l].at[GlobalM2.columns[i]]
                missingT += LastM2
    print("Countries that haven't reported latest M2 for the month: ",laggers)
    MissedProportion = round((missingT/M2Total)*100,2)
    mesg = 'Proportion of data missing from latest data point: '+str(MissedProportion)+'%.'
    print(mesg)   
    ax.text(0.55,0.05,s=mesg,fontsize=11,transform=ax.transAxes,horizontalalignment='center',verticalalignment='center') 
 
def Compare_GlobalM2s(M2List:list,title:str='M2 money supply global, index comparisons.'):  ##Put in multiple global M2 traces to compare them. 
    fig = plt.figure(figsize=(11,8.5), tight_layout=True)  #M2List has format: [('GlobalM2_MasterDFName','Label','Color'),('GlobalM2_MasterDFName','Label','Color')]
    gs = GridSpec(2, 1, top = 0.94, bottom=0.1,left=0.1,right=0.96, height_ratios=[1,1], hspace=0)
    ax = fig.add_subplot(gs[0]); ax2 = fig.add_subplot(gs[1],sharex=ax)
    ax.set_title(title,fontweight='bold',fontsize=14)
    for i in range(len(M2List)):
        tup = tuple(M2List[i]); M2_DFName = str(tup[0]); label = str(tup[1]); culla = str(tup[2])
        M2Index = pd.read_excel(wd+fdel+'M2_USD_Tables'+fdel+M2_DFName+'.xlsx'); M2Index.set_index('Date',inplace=True)
        M2_Trace = M2Index['Global M2 (USD, ffill)']
        YoYm2 = PriceImporter.YoY4Monthly(M2_Trace)
        ax.plot(M2_Trace,label=label,color=culla,lw=2)
        ax2.plot(YoYm2,label=r'Global M2 YoY $\Delta$%',color=culla,lw=1.75)
    ax.set_yscale('log'); ax.set_ylabel('M2 Money supply (USD)',fontweight='bold',fontsize=12)
    ax.tick_params(axis='x',labelsize=0)
    ax2.set_ylabel(r'M2 YoY $\Delta$%',fontweight='bold',fontsize=12)
    ax2.axhline(y=0,linestyle='dashed',color='red')
    ax.legend(loc=2,fontsize=9)         
    for axis in ['top','bottom','left','right']:
            ax.spines[axis].set_linewidth(1.5); ax2.spines[axis].set_linewidth(1.5)        
    ax.minorticks_on(); ax2.minorticks_on()
    ax.margins(0.02,0.02); ax2.margins(0.02,0.02)

class USD_vs_nativeCurr(object):    

    def __init__(self, folderPath: str):
        self.top50_info = pd.read_excel(wd+fdel+'UpdateM2Infos'+fdel+'M2Info_Top50.xlsx', index_col=0)
        self.top50 = self.top50_info.index.to_list()
        self.data_folderPath = folderPath
        
    def MakeCompDFs(self):
        i = 0
        for country in self.top50:
            local_M2 = pd.read_excel(self.data_folderPath + fdel + country + ".xlsx", index_col=0)
            local_M2.drop(local_M2.columns[1], axis = 1, inplace=True)
            if i == 0:
                self.AllM2data = local_M2
            else:
                self.AllM2data = pd.concat([self.AllM2data, local_M2], axis = 1)  
            i += 1          

    def exportM2Data(self):
        fdel = os.path.sep
        self.AllM2data.to_excel(self.data_folderPath+fdel+"M2Data_top50.xlsx")
    
    def PlotPercentageChanges(self, ZeroDate: str = None, median: bool = False, mean: bool = False, title: str = r"M2 Monetary Aggregates:  Growth (%) in Native Currencies",
            start: bool = False, NumCountries: int = 5, yaxis: str = 'log', startDate: str = None):   

        self.nativeList = [cunt for cunt in self.AllM2data.columns.to_list() if "USD" not in cunt]
        self.nativeList.insert(1, 'United States_M2 (USD)')

        self.M2_pcChanges = {}
        for country in self.nativeList[0:NumCountries]:
            TheSeries = self.AllM2data[country]
            if startDate is not None:
                print("Reduced range chosen, start date: ", startDate)
                newStart = Utilities.GetClosestDateInIndex(TheSeries,startDate)[0]
                ReducedSeries = TheSeries[newStart::]
                percentSeries = Utilities.Percent_OfBaseVal_Series(ReducedSeries, ZeroDate=ZeroDate, median=median, mean=mean, start=start)
            else:
                percentSeries = Utilities.Percent_OfBaseVal_Series(TheSeries, ZeroDate=ZeroDate, median=median, mean=mean, start=start)
            self.M2_pcChanges[country] = percentSeries

        plt.rcParams['font.family'] = 'serif'
        self.fig = plt.figure(figsize=(11,7), tight_layout=True)
        gs = GridSpec(2, 1, top = 0.94, bottom=0.08,left=0.08,right=0.97, height_ratios=[2,1], hspace= 0.02)
        ax = self.fig.add_subplot(gs[0]); ax2 = self.fig.add_subplot(gs[1], sharex = ax)
        ax.set_title(title, fontsize=14)
        ax.set_yscale('log')        
        ax.set_ylabel('M2 growth (% of median)', fontsize=10, fontweight='bold') 
        ax2.set_ylabel(r'YoY $\Delta$%', fontsize=10, fontweight='bold') 

        for cuntry in self.M2_pcChanges.keys():
            TheDataSeries = self.M2_pcChanges[cuntry]
            ax.plot(TheDataSeries, label = self.M2_pcChanges[cuntry].name)
            ax2.plot(TheDataSeries.pct_change(12)*100)

        ylims = ax.get_ylim()
        ax.tick_params(axis='y',which='both',length=0,width=0,right=False,labelright=False,labelsize=0)  
        ticks, ticklabs = Utilities.EqualSpacedTicks(11, LogOrLin = yaxis, Ymin=ylims[0], Ymax=ylims[1], LabOffset=-100, labSuffix='%')
        ax.set_yticks(ticks); ax.set_yticklabels(ticklabs) 
        ax.tick_params(axis='y', which='major', width=1, length=3, labelsize=8, left=True, labelleft=True)    
        ax.tick_params(axis='x', which='both', width=0, length=0, labelsize=0)  

        ax.legend(loc=2,fontsize=9)
        ax.minorticks_on(); ax2.minorticks_on()
        ax.grid(visible=True, which='major', axis = 'both', lw = 0.75, ls = ":")        
        ax2.grid(visible=True, which='major', axis = 'both', lw = 0.75, ls = ":")   
        ax2.tick_params(axis='x', which = 'major', labelsize = 11)  

        for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_linewidth(1.5) 
                ax2.spines[axis].set_linewidth(1.5) 
        ax.margins(0.02, 0.02)        
        ax2.margins(0.02, 0.02) 
     
class YoY_forecast(object):
      
    def __init__(self, series: pd.Series, convert_units: int = 1):
        self.series = series/convert_units
        self.Series_freq  = Utilities.DetermineSeries_Frequency(series)[0]
        if self.Series_freq != 'Monthly':
            print('Resampling...', self.series.name)
            self.series = series.resample('MS').mean()
        
        self.series_MoM = series.pct_change()*100
        self.series_MoM_3MMA = self.series_MoM.rolling(3).mean()
        self.series_YoY = series.pct_change(12)*100

    def MakeForecastSeries(self, moms: list = [-1, -0.5, -0.25, -0.1, 0, 0.1, 0.25, 0.5, 1]):
        nextYear = pd.date_range(start = self.series.index[len(self.series)-1] + pd.Timedelta(weeks=4), periods = 12, freq = 'MS')
        self.forecasted = {}; self.nanfc = {}
        latest_3M_av = self.series_MoM_3MMA[self.series_MoM_3MMA.index[-1]]
        moms.append(latest_3M_av)  # Last forecast trace will be the average of last 3 months MoM growth rates. 
    
        latest_val = self.series[self.series.index[-1]]
        padSeries = pd.Series(np.nan, index = self.series.index); padSeries2 = pd.Series(np.nan, index = nextYear)
        fullPad = pd.concat([padSeries, padSeries2], axis = 0); fullIndex = fullPad.index

        self.x_min = fullIndex[0]; self.x_max = fullIndex[len(fullIndex)-1]
        self.margin = round((self.x_max - self.x_min).days * 0.025)
        print("Margin (days): ", self.margin)
        print('Average of last 3M MoM move: ', latest_3M_av)
        print('Latest value in GM2 series: ', latest_val)
        self.av3m_name = 'Average_last_3_months'
        
        for i in range(len(moms)):
            if i == len(moms)-1:
                multName = self.av3m_name
            else:
                multName = str(moms[i])+" "+r'$\Delta$%'+' MoM'

            # Create an array with the same length as nextYear
            serList = np.empty(len(nextYear))

            # Calculate the multiplier
            multiplier = 1 + (moms[i])/100

            # For the first element, use latest_val, for the rest use the previous value
            serList[0] = latest_val * multiplier
            for i in range(1, len(serList)):
                serList[i] = serList[i-1] * multiplier

            TheSer  = pd.Series(serList, index=nextYear, name=multName)
            self.forecasted[multName] = pd.concat([self.series, TheSer], axis = 0)
            self.nanfc[multName+"_n"] = pd.concat([padSeries, TheSer], axis = 0)

        self.casted_YoY = {}
        for cast in self.forecasted.keys():
            self.casted_YoY[cast] =  self.forecasted[cast].pct_change(12) * 100    

    def PlotEm(self, title, ax_ylabel: str = 'USD', ax2_ylabel: str = r'YoY $\Delta$%', yaxis: str = 'log'):
        plt.rcParams['font.family'] = 'serif'
        fig = plt.figure(figsize=(11,8.5), tight_layout=True)  #M2List has format: [('GlobalM2_MasterDFName','Label','Color'),('GlobalM2_MasterDFName','Label','Color')]
        gs = GridSpec(2, 1, top = 0.94, bottom=0.08,left=0.08,right=0.96, height_ratios=[10,8], hspace=0.01)
        ax = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1],sharex=ax)
        ax.set_title(title,fontweight='bold',fontsize=16)

        ax.set_yscale(yaxis); ax.set_ylabel(ax_ylabel, fontweight='bold',fontsize=12)

        maxes = {}
        for forecast in self.forecasted.keys():
            if forecast == self.av3m_name:
                ax.plot(self.forecasted[forecast], label = forecast, color = "dodgerblue", lw = 2)
            else:
                ax.plot(self.forecasted[forecast], label = forecast, lw = 1)
            maxVal = max(self.forecasted[forecast]); maxes[forecast] = maxVal
            print(self.forecasted[forecast].index[0])    
        ax.plot(self.series, color = 'black', label = self.series.name, lw = 2.5)    
       
        maxestSeries = max(maxes, key = maxes.get)
        print('Series on top axis with the highest values is: ', maxestSeries)
        ax.tick_params(axis='y',which='both',length=0,width=0,right=False,labelright=False,labelsize=0)  
        ticks, ticklabs = Utilities.EqualSpacedTicks(11, data = self.forecasted[maxestSeries], LogOrLin = yaxis)
        ax.set_yticks(ticks); ax.set_yticklabels(ticklabs) 
        ax.tick_params(axis='y', which='major', width=1, length=3, labelsize=9, left=True, labelleft=True)

        ax2.set_ylabel(ax2_ylabel, fontweight='bold',fontsize=12)
        ax2.axhline(y=0,linestyle='dashed',color='red')    
        for forecast in self.casted_YoY.keys():
            if forecast == self.av3m_name:
                ax2.plot(self.casted_YoY[forecast], label = forecast, color = "dodgerblue", lw = 2)
            else:
                ax2.plot(self.casted_YoY[forecast], label = forecast, lw = 1)

        ax2.plot(self.series_YoY, label = self.series_YoY.name +r" YoY $\Delta$%", color = 'black', lw = 2)

        ax.tick_params(axis='x',labelsize=0)
        ax.legend(loc=2,fontsize=9)         
        for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_linewidth(1.5) 
                ax2.spines[axis].set_linewidth(1.5)        
        ax.minorticks_on(); ax2.minorticks_on()
        ax.set_xlim(self.x_min - pd.Timedelta(days= self.margin), self.x_max + pd.Timedelta(days= self.margin))
        ax2.tick_params(axis='x',labelsize=14)
        ax.grid(visible = True, which = 'major', axis = 'both', lw = 0.75, ls = ":")
        ax2.grid(visible = True, which = 'major', axis = 'both', lw = 0.75, ls = ":")

    def save_em(self, savePath: str = parent + fdel + 'User_Data' + fdel + 'SavedData'):
        for forecast in self.forecasted.keys():
            SeriesInfo = pd.Series({'units':'US Dollars','units_short': 'USD','title':forecast,'id':forecast,"Source":"tv"},name='SeriesInfo')
            saveName = savePath+fdel+"GM2_fc_"+forecast.replace(" ", "").replace("-","neg").replace(r'$\Delta$%', "_")\
                .replace("Average_last_3_months", "Av3m")+'.xlsx'
            saveName2 = saveName.replace(".xlsx", "_n.xlsx")
            pd.Series(self.forecasted[forecast]*(10**12), name = forecast).to_excel(saveName, sheet_name='Closing_Price')
            pd.Series(self.nanfc[forecast+"_n"]*(10**12), name = forecast).to_excel(saveName2, sheet_name='Closing_Price')
            with pd.ExcelWriter(saveName, engine='openpyxl', mode='a') as writer:  
                SeriesInfo.to_excel(writer, sheet_name='SeriesInfo')
            with pd.ExcelWriter(saveName2, engine='openpyxl', mode='a') as writer2:  
                SeriesInfo.to_excel(writer2, sheet_name='SeriesInfo')

if __name__ == '__main__':

    dataPath = parent + fdel + 'User_Data' + fdel + "GM2_Data" + fdel + 'FinalData'    
    m2s = USD_vs_nativeCurr(folderPath=dataPath)
    m2s.MakeCompDFs()
    m2s.PlotPercentageChanges(ZeroDate="2017-01-01", startDate= '2012-01-01')

    data = m2s.AllM2data.resample('M').mean()
    data_dict = data.iloc[:, 0:6].to_dict(orient='series')
    data_dict['China_M2 (USD)'] = {'Series': data_dict['China_M2 (USD)'], 'lw': 2.25, 'ls': ":", 'label': data_dict['China_M2 (USD)'].name}
    for cuntry in data_dict.keys():
        data_dict[cuntry] = {'Series': data[cuntry], 'label': data[cuntry].name}
    
    template = plt.figure(FigureClass = Charting.TracesTop_RoC_bottom, data = data.iloc[:, 0:6], botPanel = True)
    axDeets = {'yscale_top_left': 'log', 'ylabel_top_left': 'USD',
                       'legend_top': {'loc': 2, 'fontsize': 'small'}
            }
    
    template.plot(left_traces=data_dict, axDeets = axDeets, title = 'M2 monetary aggregates, top 50 economies')

#################################### ACTIVE CODE BELOW, FUNCTIONS ABOVE. #####################################################      
    filename = None
    ##Set a default file to use or comment this out to use the file dialog.
    filename = wd+fdel+'M2_USD_Tables'+fdel+'Top50_M2_USD.xlsx'

    if filename is None:
        filename = askopenfilename(title="Choose excel file (.xlsx only), with M2 (USD) data generated by 'Update_M2.py', e.g: Top33_M2_USD.xlsx",defaultextension='.xlsx',initialdir=wd) 
    des = filename.rsplit('.',1)[0].rsplit(fdel,1)[1].split('_')[0]
    print(des, wd+fdel+'Datasums'+fdel+des+'_DataComp.xlsx')

    DataComp = pd.read_excel(wd+fdel+'Datasums'+fdel+des+'_DataComp.xlsx'); DataComp.set_index('Country',inplace=True)
    # show an "Open" dialog box and return the path to the selected file
    M2Path = (wd+fdel+'TVDataFeed'+fdel+'FinalData'+fdel+'M2_Data'); FXPath = (wd+fdel+'TVDataFeed'+fdel+'FinalData'+fdel+'FX_Data') ###Change these if changing the folder structure within "Global_M2" folder.
    FullDF = pd.read_excel(filename)
    index = pd.DatetimeIndex(pd.DatetimeIndex(FullDF['Date']).date)
    FullDF.set_index(index,inplace=True); FullDF.drop('Date',axis=1,inplace=True)

    ######## MatPlotlib functions ########################################################################################################################

    DataComp = DataComp[0:5]
    PlotM2Data(FullDF,DataComp)
    Plot_GlobalM2(FullDF['Global M2 (USD, ffill)'], FullDF)

    series = pd.read_excel(parent+fdel+'User_Data'+fdel+'SavedData'+fdel+'Top50GM2.xlsx', sheet_name='Closing_Price', index_col=0)
    series = series[series.columns[0]].rename('Global M2 aggregate (top 50)')

    fore = YoY_forecast(series, convert_units = 10**12) #GM2 series units is trillions of USD.
    print(fore.series)
    fore.MakeForecastSeries(moms=[-1, -0.5, 0, 0.5, 1]) # default growth rate range: [-1, -0.5, -0.25, -0.1, 0, 0.1, 0.25, 0.5, 1]
    fore.PlotEm('Forecasting GM2 based on constant MoM changes', ax_ylabel='USD (trillions of doCllaridoos)')
    fore.save_em()
    plt.show()