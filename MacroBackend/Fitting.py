import numpy as np
from scipy.optimize import curve_fit
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates
import datetime
from datetime import timedelta

data = pd.read_excel('/Users/jamesbishop/Documents/Python/TempVenv/Plebs_Macro/Generic_Macro/SavedData/BTCUSD.xlsx')
data.set_index(pd.DatetimeIndex(pd.DatetimeIndex(data['date']).date),inplace=True)
data.drop('date',axis=1,inplace=True)
StartDate = datetime.date(2012,1,1); start = pd.Timestamp(StartDate)
StartDate2 = datetime.date(2017,7,1); start2 = pd.Timestamp(StartDate2)
data = data[start::]
data = data['BTC']
data2 = data.copy(); data2 = data2[start2::] 

def fitExpTrend(data:pd.Series):
    index = data.index.to_numpy()
    x = np.linspace(1,len(data),len(data)); y = data.to_numpy()

    fit = np.polyfit(x, np.log(y), 1)
    print('Log fit to: ',data.name, ', x, np.log(y), intercept, slope a,b = ',fit)
    a = fit[0]; b = fit[1]

    x = np.linspace(0,len(data-1),len(data))
    fit_y = [];  fit_y2 = []
    for ex in x:
        fit_y.append(np.exp(b+a*ex))
    fitY = pd.Series(fit_y,index=index,name=data.name+" exp trend") 
    TrendDev = ((y - fitY)/fitY)*100+100
    return fitY, TrendDev

def StdDevBands(midline:pd.Series,Mults:int,window:int):
    stdDev = midline.rolling(window=window).std()
    numstd_l = Mults/np.e
    std_u = midline + Mults*stdDev
    std_l = midline - numstd_l*stdDev
    return std_u, std_l

def PCBands(midline:pd.Series,PC:float):
    pcu = midline*((100+PC)/100)
    pcl = midline/((100+PC)/100)
    return pcu, pcl

def Exp_Base10(x, a, b):
    return 10**(a*x+b)

def expLog(x, a, b):  # Define expLog function
    return 10**(a*np.log(x)-b)
    #return np.exp((a*np.log(x)-b))

def logistic_func(x, K, A, r):  # Define logistic function
    return K / (1 + A * np.exp(-r * x))
# Fit logistic function to data

def YoYCalcFromDaily(series:pd.Series): 
    print('\nYoY calcuation on series: ',series.name,', data frequency: ',pd.infer_freq(series.index))
    if series.index.inferred_freq != 'D':
        print('Resampling',series.name,'to daily frequency for YoY calculation....')
        series = series.resample('D').mean()
        series.fillna(method='ffill',inplace=True) #This'l make it daily data even if weekly data is input. 
    YoYCalc = [np.nan for i in range(len(series))]
    YoYSeries = pd.Series(YoYCalc,index=series.index,name=series.name+' YoY % change')
    for i in range(365,len(series),1):
        YoYSeries.iloc[i] = (((series[i]-series[i-365])/series[i-365])*100)
    #print('After YoY calc: ',YoYSeries.tail(54),len(YoYSeries))        
    return YoYSeries  

def FitData(f,data:pd.Series,LogOrLin:str='lin',funcName:str=''):
    x = np.linspace(1,len(data),len(data)); y = data.to_numpy(); yLog = np.log(y)
    if LogOrLin == 'log':
        popt, pcov = curve_fit(f,x,y)
        fit = f(x,*popt)
    else:
        popt, pcov = curve_fit(f,x,yLog)
        fit = np.exp(f(x,*popt))
    Fit = pd.Series(fit,index=data.index,name=data.name+" "+funcName+" fit")   
    print('Trendline fitted to data: ',data.name,' ',funcName,' function used, optimized fitting parameters: ',popt)  
    return Fit, popt, pcov
    
x = np.linspace(1,len(data),len(data)); y = data.to_numpy(); yLog = np.log(y)
print(x, y,yLog)

fitY, TrendDev = fitExpTrend(data)    #Exponential fit (linear on SemiLogY chart)
#fitY = FitData(Exp_Base10,data,funcName='Exponential (base 10)')

fitY2, popt2, pcov2 = FitData(logistic_func,data,funcName='Logistic')
fitY3, popt3, pcov3 = FitData(expLog,data,funcName='ExpLog')

#TrendDev = pd.Series(((y - fitY)/fitY)*100+100)
TrendDev2 = pd.Series(((y - fitY2)/fitY2)*100+100)
TrendDev3 = pd.Series(((y - fitY3)/fitY3)*100+100)
#TrendDev2.to_excel('/Users/jamesbishop/Documents/Python/TempVenv/Plebs_Macro/Generic_Macro/SavedData/BTC_LogisticFitResPC.xlsx')
######### MATPLOTLIB SECTION #################################################################
plt.rcParams['figure.dpi'] = 105; plt.rcParams['savefig.dpi'] = 200   ###Set the resolution of the displayed figs & saved fig respectively. 

#### Traces are input as dict of tuples e.g {"TraceName": (data,color,linewidth)}
def TwoAxisFig(LeftTraces:dict,LeftScale:str,LYLabel:str,title:str,XTicks=None,RightTraces:dict=None,RightScale:str=None,RYLabel:str=None,\
               LeftTicks:tuple=None,RightTicks:tuple=None,RightMinTicks:tuple=None,text1:str=None):
    #plt.rc('text', usete=True)
    fig = plt.figure(num=title,figsize=(13,6.5), tight_layout=True)
    gs1 = GridSpec(1, 1, top = 0.95, bottom=0.14 ,left=0.06,right=0.92)
    ax1 = fig.add_subplot(gs1[0])
    ax1 = fig.axes[0]
    ax1.set_title(title,fontweight='bold')

    for trace in LeftTraces.keys():
        ax1.plot(LeftTraces[trace][0],label = trace,color=LeftTraces[trace][1],lw=LeftTraces[trace][2])
    if LeftTicks is not None:    ### Ticks must be input as a tuple of lists or np.arrays. WIth format (Tick positions list, tick labels list)
            ax1.tick_params(axis='y',which='both',length=0,labelsize=0)
            ax1.set_yticks(LeftTicks[0]); ax1.set_yticklabels(LeftTicks[1])
            ax1.tick_params(axis='y',which='major',length=3,labelsize=9)
    if RightTraces is not None:
        ax1b = ax1.twinx()
        ax1b.margins(0.02,0.03)
        for axis in ['top','bottom','left','right']:
            ax1b.spines[axis].set_linewidth(1.5) 
        for trace in RightTraces.keys():
            ax1b.plot(RightTraces[trace][0],label = trace,color=RightTraces[trace][1],lw=RightTraces[trace][2])
        ax1b.legend(loc=4,fontsize=9)
        if RightScale == 'log':    
            ax1b.set_yscale('log')
        if RYLabel is not None:
            ax1b.set_ylabel(RYLabel,fontweight='bold',labelpad=15,fontsize=11)
        if RightTicks is not None:    
            ax1b.tick_params(axis='y',which='both',length=0,labelsize=0)
            ax1b.set_yticks(RightTicks[0]); ax1b.set_yticklabels(RightTicks[1])
            ax1b.tick_params(axis='y',which='major',length=4,labelsize=10)
            if RightMinTicks is not None:
                ax1b.set_yticks(RightMinTicks[0],minor=True); 
                ax1b.set_yticklabels(RightMinTicks[1],minor=True)
                ax1b.tick_params(axis='y',which='minor',length=2,labelsize=7)

    if LeftScale == 'log':
        ax1.set_yscale('log')
    if XTicks is not None:
        ax1.xaxis.set_ticks(XTicks) 
        ax1.tick_params(axis='x',length=3,labelsize='small',labelrotation=45)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%y-%b'))
        ax1.set_xlim(XTicks[0],XTicks[len(XTicks)-1])
        ax1.set_xlabel('Date (year-month)',fontweight='bold',fontsize=11)
       
    ax1.legend(loc=2,fontsize=9)
    ax1.set_ylabel(LYLabel,fontweight='bold',fontsize=11)
    for axis in ['top','bottom','left','right']:
            ax1.spines[axis].set_linewidth(1.5)
    if text1 is not None:
        ax1.text(text1)
    return fig    

pcBands = PCBands(fitY,200) 
pcBands2 = PCBands(fitY2,200)       ## Bands at set % above and below trendline. 
pcBands3 = PCBands(fitY3,200)

#text1 = '0.9,0.44,s="Price on trendline",color="red",fontsize=9,transform=ax1.transAxes,horizontalalignment="left",verticalalignment="center"'
Ticks = np.array([25, 50, 100, 200, 400, 800, 1600]); ticklabs = Ticks - 100; minors = []  #Major ticks custom right axis. 

for i in range(len(Ticks)-1):        ###Minor ticks for the custom right axis. 
    step = (Ticks[i+1] - Ticks[i])/4
    for j in range(1,4,1):
        minors.append(int(round(Ticks[i]+j*step)))
minTicks = np.array(minors); print(minTicks,minTicks.dtype)
minTickLabs = minTicks - 100; minTicks = minTicks.tolist()
minTickLabs = minTickLabs.astype(str).tolist()

Range = data.index[len(data)-1] - data.index[0]
margs = round((0.02*Range.days),0); print(Range.days,margs)
#### X Ticks for all charts #################################################################################
Xmin = data.index[0]-timedelta(days=margs); Xmax = data.index[len(data)-1]+timedelta(days=margs)
Xmin = Xmin.to_pydatetime(); Xmax = Xmax.to_pydatetime()
stepsize = (Xmax - Xmin) / 20
XTickArr = np.arange(Xmin, Xmax, stepsize) 
XTickArr = np.append(XTickArr, Xmax)
Xmin2 = data.index[0]+timedelta(days=365)-timedelta(days=margs)
XTickArr2 = np.arange(Xmin2, Xmax, stepsize) 


##### Chart 1 ######################################################################################################################
fit2n=r'$\bf{Logistic\ fit:}$'+' '+str(round(popt2[0],2))+" / (1 + "+str(round(popt2[1],2))+" x exp(-"+str(round(popt2[2],6))+" * (Date - "+str(StartDate)+")))"
LeftTraces = {'BTC since 2013':(data,'orangered',2.5),fit2n:(fitY2,'black',1.75),'Logis_UpperBand':(pcBands2[0],'dodgerblue',1.5),'Logis_LowerBand':(pcBands2[1],'dodgerblue',1.5)}
RightTraces = {'Dev. from logistic fit (right)':(TrendDev2,'blue',1)}

plot1 = TwoAxisFig(LeftTraces,'log','Price (USD)','Logistic fit to bitcoin price history',XTicks=XTickArr,\
    RightTraces=RightTraces,RightScale='log',RightTicks=(Ticks,ticklabs),RightMinTicks=(minTicks,minTickLabs),RYLabel='Deviation from trend (%)')
plot = plot1.axes[0]; plotb = plot1.axes[1]
plot.set_ylim(min(data)-0.1*min(data),max(data)+0.1*max(data))
plotb.set_ylim(25,2250)
plotb.axhline(100,color='red',ls='dotted',lw=0.75)
plotb.axhline(46,color='black',linestyle='dotted',lw=1)
plot.minorticks_on()

##### Chart 2 ######################################################################################################################
fit3n = r'$\bf{ExpLog\ fit:}$'+" exp("+str(round(popt3[0],3))+" * ln(Date - "+str(StartDate)+") - "+str(round(popt3[1],3))+')'
LeftTraces2 = {'BTC since 2013':(data,'orangered',2.5),fit3n:(fitY3,'black',1.75),'ExpLog_UpperBand':(pcBands3[0],'lime',1.5),'ExpLog_LowerBand':(pcBands3[1],'lime',1.5)}
RightTraces2 = {'Dev. from explog fit (right)':(TrendDev3,'green',1)}

plot_2 = TwoAxisFig(LeftTraces2,'log','Price (USD)','ExpLog fit to bitcoin price history',XTicks=XTickArr,\
                    RightTraces=RightTraces2,RightScale='log',RightTicks=(Ticks,ticklabs),RightMinTicks=(minTicks,minTickLabs),RYLabel='Deviation from trend (%)')
print(plot1.axes)
plot2 = plot_2.axes[0]; plot2b = plot_2.axes[1]
plot2.set_ylim(min(data)-0.1*min(data),max(data)+0.1*max(data))
plot2b.set_ylim(25,2250)
plot2b.axhline(100,color='red',ls='dotted',lw=0.75)
plot2.minorticks_on()

### Chart 3 ########################################################################################################################################
Pymin = round(min(TrendDev),2); Pymax = round(max(TrendDev),2)
Ticks2 = np.logspace(start = np.log2(Pymin), stop = np.log2(Pymax), num=10, base=2) 
tickLabs2 = Ticks.copy(); tickLabs2 -= 100
Ticks2.round(decimals=0,out=Ticks2); tickLabs2.round(decimals=0,out=tickLabs2)
Ticks2 = np.ndarray.astype(Ticks,dtype=int,copy=False)

LeftTraces3 = {'BTC since 2013':(data,'orangered',2.5),'Exponential growth fit':(fitY,'black',1.75),'UpperBand':(pcBands[0],'fuchsia',1.5),'LowerBand':(pcBands[1],'fuchsia',1.5)}
RightTraces3 = {'Dev. from exp. fit (right)':(TrendDev,'red',1)}
plot_3 = TwoAxisFig(LeftTraces3,'log','Price (USD)','Exponential fit to bitcoin price history',XTicks=XTickArr,\
                    RightTraces=RightTraces3,RightScale='log',RightTicks=(Ticks,ticklabs),RightMinTicks=(minTicks,minTickLabs),RYLabel='Deviation from trend (%)')

plot3 = plot_3.axes[0]; plot3b = plot_3.axes[1]
plot3.set_ylim(min(data)-0.1*min(data),max(data)+0.1*max(data))
plot3b.set_ylim(25,2250)
plot3b.axhline(100,color='red',ls='dotted',lw=0.75)
plot3.minorticks_on()

######## CHART 4 ######################################################################################################################
TicksLin = np.array([0,100,200,300,400,500,600,700,800,900])
TicksLog = np.array([12.5, 25, 50, 100, 200, 400, 800])
LabsLin = TicksLin.copy(); LabsLog = TicksLog.copy()
LabsLin -= 100; LabsLog -= 100

LeftTraces4 = {'Distorted data: linear % axis (left)':(TrendDev,'black',1.5)}
RightTraces4 = {'Non-distorted data: offset log % axis':(TrendDev,'green',1.5)}
plot_4 = TwoAxisFig(LeftTraces4,'linear','Deviation from trend (%)','Linear vs logarithmic % axis',XTicks=XTickArr,LeftTicks=(TicksLin,LabsLin),\
                    RightTraces=RightTraces4,RightScale='log',RightTicks=(TicksLog,LabsLog),RYLabel='Deviation from trend (%)')
plot4 = plot_4.axes[0]; plot4b = plot_4.axes[1]


plot4.axhline(100,color='red',linestyle='dotted',lw=1)
plot4b.axhline(100,color='blue',linestyle='dotted',lw=1)
plot4b.spines['right'].set_color('green')
plot4b.tick_params(axis='y',which='both',color='green',labelsize=9,labelcolor='green')
plot4b.set_ylabel('Deviation from trend (%)',fontweight='bold',color='green')
# ax2.text(0.27,0.11,s="0 % line (linear axis)",color='red',fontsize=9.5,transform=ax2.transAxes,horizontalalignment='left',verticalalignment='center')
plot4b.legend(loc=1,fontsize=9)
plot4.legend(loc=2,fontsize=9,bbox_to_anchor=(0.2,1))
plot4.margins(0.02,0.03); plot4b.margins(0.02,0.03)

######## CHART 5 ######################################################################################################################
BTC_YoY = YoYCalcFromDaily(data); BTC_YoY_log = BTC_YoY.copy() + 100

TicksLin2 = np.array([0,100,1000,2000,3000,4000,5000,6000,7000,8000,9000,10000])
TicksLog2 = np.array([12.5, 25, 50, 100, 200, 400, 800, 1600,3200,6400,10000])
LabsLin2 = TicksLin2.copy(); LabsLog2 = TicksLog2.copy()
LabsLin2 -= 100; LabsLog2 -= 100

LeftTraces5 = {'Distorted data: linear % axis (left)':(BTC_YoY,'darkorange',1.5)}
RightTraces5 = {'Non-distorted data: offset log % axis':(BTC_YoY_log,'blue',1.5)}
plot_5 = TwoAxisFig(LeftTraces5,'linear',r'YoY $\Delta$%','Linear vs logarithmic % axis, '+r'YoY $\Delta$%',LeftTicks=(TicksLin2,LabsLin2),XTicks=XTickArr2,\
                    RightTraces=RightTraces5,RightScale='log',RightTicks=(TicksLog2,LabsLog2),RYLabel=r'YoY $\Delta$%')
plot5 = plot_5.axes[0]; plot5b = plot_5.axes[1]

plot5b.axhline(100,color='blue',linestyle='dotted',lw=1.5)
plot5.axhline(100,color='orangered',linestyle='dotted',lw=1)
plot5b.spines['right'].set_color('blue')
#plot5b.tick_params(axis='y',which='both',width=0,labelsize=0,labelcolor='blue')
plot5.tick_params(axis='y',which='both',labelsize=9)
plot5b.tick_params(axis='y',which='both',color='blue',labelsize=9,labelcolor='blue')
plot5b.set_ylabel(r'YoY $\Delta$%',fontweight='bold',color='blue')
plot5b.legend(loc=1,fontsize=9)
plot5.grid(visible=True,axis='both',which='major',lw=0.75,ls=':',color='black')
#plot5.grid(visible=True,axis='both',which='major',lw=0.75,ls=':',color='black')
plot5.set_axisbelow(True); plot5b.set_axisbelow(True)
plot5.legend(loc=2,fontsize=9,bbox_to_anchor=(0.2,0.97))
plot5.margins(0.02,0.03); plot5b.margins(0.02,0.03)

plt.show() 