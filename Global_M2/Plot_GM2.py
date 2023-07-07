###### Required modules/packages #####################################
import os
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
dir = os.path.dirname(wd)
print(wd,dir)
import sys ; sys.path.append(dir)
from MacroBackend import PriceImporter, Utilities ## This is one of my custom scripts holding functions for pulling price data from APIs. 
#Your IDE might not find it before running script. 
import pandas as pd
from matplotlib import colors as mcolors
import matplotlib.pylab as pl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import numpy as np
import datetime
import tkinter as tk
from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showinfo

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
if sys.platform == "linux" or sys.platform == "linux2":        #This detects what operating system you're using so that the right folder delimiter can be use for paths. 
    FDel = '/'; OpSys = 'linux'
elif sys.platform == "darwin":
    FDel = '/'; OpSys = 'mac'
elif sys.platform == "win32":
    FDel = '\\' ; OpSys = 'windows'
print('System information: ',sys.platform, OpSys,', directory delimiter: ', FDel, ', working directory: ', wd)

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
        YoYm = PriceImporter.YoY4Monthly(M2Trace.copy())
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
    gs = GridSpec(3, 1, top = 0.94, bottom=0.05,left=0.1,right=0.96, height_ratios=[1,0.7,0.33], hspace=0.01)
    ax = fig.add_subplot(gs[0]); ax2 = fig.add_subplot(gs[1],sharex=ax); ax3 = fig.add_subplot(gs[2],sharex=ax)
    ax.set_title('M2 money supply, sum of top '+str(int(round(((len(GlobalM2.columns)-2)/2),0)))+' economies (USD)',fontweight='bold',fontsize=14)
    YoYm2 = PriceImporter.YoY4Monthly(Global_M2.copy())
    Ann6m =  Utilities.MonthPeriodAnnGrowth(Global_M2.copy(),6)
    Ann3m = Utilities.MonthPeriodAnnGrowth(Global_M2.copy(),3)
    Dat2 = ax.plot(Global_M2,label='Global M2 aggregate',color='blue',lw=2)
    yoy2 = ax2.plot(YoYm2,label=r'GM2 YoY $\Delta$%',color='black',lw=3)
    an6m = ax2.plot(Ann6m,label=r'GM2 6m ann. $\Delta$%',color='blue',lw=1.5)
    an3m = ax2.plot(Ann3m,label=r'GM2 3m ann. $\Delta$%',color='orangered',lw=1)
    ax2.legend(loc=2,fontsize=8)
    ax.set_yscale('log'); ax.set_ylabel('M2 Money supply (USD)',fontweight='bold',fontsize=12)
    mom = pd.Series([((((Global_M2[i]-Global_M2[i-1])/Global_M2[i-1])*100)) for i in range(len(Global_M2))],name="GlobalM2_MoM",index=Global_M2.index)
    mom2 = ax3.plot(mom,label=r'Global M2 MoM $\Delta$%',color='green',lw=1)
    ax.tick_params(axis='x',labelsize=0); ax.tick_params(axis='x',labelsize=0); ax2.tick_params(axis='x',labelsize=0)
    ax2.set_ylabel(r'M2 YoY $\Delta$%',fontweight='bold',fontsize=12); ax3.set_ylabel(r'MoM $\Delta$%',fontweight='bold',fontsize=10)
    ax2.axhline(y=0,linestyle='dashed',color='red',lw=1); ax3.axhline(y=0,linestyle='dashed',color='red',lw=0.75)
    ax.legend(loc=1,bbox_to_anchor=(0.1,1.1),fontsize=9)         
    for axis in ['top','bottom','left','right']:
            ax.spines[axis].set_linewidth(1.5); ax2.spines[axis].set_linewidth(1.5) ; ax3.spines[axis].set_linewidth(1.5)      
    ax.minorticks_on(); ax2.minorticks_on(); ax3.minorticks_on()
    ax.margins(0.02,0.02); ax2.margins(0.02,0.02); ax3.margins(0.02,0.02)
    ax.grid(which='both',axis="both",linestyle="dotted")
    ax2.grid(which='both',axis="both",linestyle="dotted"); ax3.grid(which='both',axis="both",linestyle="dotted")

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
        M2Index = pd.read_excel(wd+'/'+M2_DFName+'.xlsx'); M2Index.set_index('Date',inplace=True)
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

#################################### ACTIVE CODE BELOW, FUNCTIONS ABOVE. #####################################################      
filename = askopenfilename(title="Choose excel file (.xlsx only), with M2 (USD) data generated by 'Update_M2.py', e.g: Top33_M2_USD.xlsx",defaultextension='.xlsx',) 
split = filename.split(FDel); nam = split[len(split)-1]; split2 = nam.split("."); naml = split2[0]; split3 = naml.split("_"); des = split3[0]
DataComp = pd.read_excel(wd+FDel+des+'_DataComp.xlsx'); DataComp.set_index('Country',inplace=True)
# show an "Open" dialog box and return the path to the selected file
M2Path = (wd+FDel+'TVDataFeed'+FDel+'FinalData'+FDel+'M2_Data'); FXPath = (wd+FDel+'TVDataFeed'+FDel+'FinalData'+FDel+'FX_Data') ###Change these if changing the folder structure within "Global_M2" folder.
FullDF = pd.read_excel(filename)
index = pd.DatetimeIndex(pd.DatetimeIndex(FullDF['Date']).date)
FullDF.set_index(index,inplace=True); FullDF.drop('Date',axis=1,inplace=True)

######## MatPlotlib functions ########################################################################################################################
plt.rcParams['figure.dpi'] = 105; plt.rcParams['savefig.dpi'] = 200   ###Set the resolution of the displayed figs & saved fig respectively. 
PlotM2Data(FullDF,DataComp,LedgFontSize=7)
DataComp = DataComp[0:30]
PlotM2Data(FullDF,DataComp,LedgFontSize=7,colors=colors)
DataComp = DataComp[0:20]
PlotM2Data(FullDF,DataComp,LedgFontSize=9,colors=colors)
DataComp = DataComp[0:10]
PlotM2Data(FullDF,DataComp,colors=colors)
DataComp = DataComp[0:5]
PlotM2Data(FullDF,DataComp)
Plot_GlobalM2(FullDF['Global M2 (USD, ffill)'],FullDF)
M2List = [('Long27_M2_USD','Top 27 longest data','black'),('Long28_M2_USD','Top 28 longest data','red'),('Top33_M2_USD','Top 33 economies','blue'),
('Top50_M2_USD','Top 50 economies','green')]
Compare_GlobalM2s(M2List)
plt.show()
