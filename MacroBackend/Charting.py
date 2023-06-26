import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
### These are standard python packages included in the latest python distributions. No need to install them. 
import datetime
from datetime import timedelta
from . import Utilities

   #######. MatPlotLib Section. Making good figs with MPL takes many lines of code dagnammit.  ###################
def FedFig(TheData:pd.Series,SeriesInfo:pd.Series,RightSeries:pd.Series=None,rightlab="",LYScale="linear",RYScale="linear",CustomXAxis=True):
    fig = plt.figure(num=SeriesInfo["id"],figsize=(15,5), tight_layout=True)
    ax = fig.add_subplot()
    plot1 = ax.plot(TheData,color="black",label=SeriesInfo["id"])       ### This is a simple fig template to view series from FRED with a comparison asset. 
    if RightSeries is not None:
        axb = ax.twinx()
        plot2 = axb.plot(RightSeries,color="red",label=rightlab) 
        axb.set_ylabel(rightlab+' price (USD)',fontweight='bold')
        axb.legend(loc=1,fontsize='small'); axb.minorticks_on()
    ax.set_title(SeriesInfo["title"])
    ax.set_ylabel(SeriesInfo["units_short"], fontweight='bold')    
    if CustomXAxis == True:
        Xmax = max(TheData.index); Xmin = min(TheData.index)
        stepsize = (Xmax - Xmin) / 20
        XTicks = np.arange(Xmin, Xmax, stepsize); XTicks = np.append(XTicks,Xmax)
        ax.xaxis.set_ticks(XTicks); ax.set_xlim(Xmin-datetime.timedelta(days=15),Xmax+datetime.timedelta(days=15))
        ax.tick_params(axis='x',length=3,labelrotation=45)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%y-%b'))
    ymin = TheData.min(); ymax = TheData.max()
    if LYScale == 'log':      ##This provides cool looking equally spaced log ticks and tick labels on both y axii. 
        ax.set_yscale('log')
        yTicks = np.real(np.logspace(start = np.log10(ymin), stop = np.log10(ymax), num=8, base=10)); #yTicks.round(decimals=0,out=yTicks)
    else:  
        yTicks = np.real(np.linspace(start = ymin, stop = ymax, num=8)); #yTicks.round(decimals=0,out=yTicks)
    yTicks = np.ndarray.astype(yTicks,dtype=float,copy=False)  
    ax.tick_params(axis='y',which='both',width=0,labelsize=0); ax.minorticks_off() #Had to do this to eliminate pesky ticks that kept coming on top of my custom ones.  
    ax.set_yticks(yTicks); ax.set_yticklabels(yTicks); ax.yaxis.set_major_formatter('{x:1.1f}'); ax.tick_params(axis='y',which='major',width=0.5,labelsize='small') 
    if RightSeries is not None: 
        Eq_ymin = RightSeries.min(); Eq_ymax = RightSeries.max()
        if RYScale == 'log':
            axb.set_yscale('log')
            bTicks = np.real(np.logspace(start = np.log10(Eq_ymin), stop = np.log10(Eq_ymax), num=8, base=10)); #bTicks.round(decimals=0,out=bTicks) 
        else:
            bTicks = np.real(np.linspace(start = Eq_ymin, stop = Eq_ymax, num=8)); #bTicks.round(decimals=0,out=bTicks) 
        bTicks = np.ndarray.astype(bTicks,dtype=float,copy=False)  
        axb.tick_params(axis='y',which='both',width=0,labelsize=0); axb.minorticks_off() #Had to do this to eliminate pesky ticks that kept coming on top of my custom ones. 
        axb.set_yticks(bTicks); axb.set_yticklabels(bTicks)
        axb.tick_params(axis='y',which='major',width=0.5,labelsize='small')     #All this to get y custom evenly spaced log ticks.
        axb.yaxis.set_major_formatter('{x:1.1f}')
        axb.yaxis.set_major_formatter('{x:1.1f}')
        axb.tick_params(axis='y',which='major',width=0.5,labelsize='small')     #All this to get y custom evenly spaced log ticks. 
     
    frequency = SeriesInfo['frequency']
    ax.text(0.5,0.05,'Series updated: '+frequency,horizontalalignment='center',verticalalignment='center', transform=ax.transAxes)  
    ax.legend(loc=2,fontsize='small')
    for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_linewidth(1.5)
    ax.minorticks_on()
    return fig

#######. MatPlotLib Section. Making good figs with MPL takes many lines of code dagnammit.  ###################
def NLQ_ElementsChart(FedBal:pd.Series,RevRep:pd.Series,TGA:pd.Series,title:str,YScale='linear',):
    fig = plt.figure(num=title,figsize=(9,8), tight_layout=True)
    ax = fig.add_subplot(); axb = ax.twinx()
    FB = ax.plot(FedBal,color="black",label='Fed bal. sheet')   ### This is a simple fig template to view the 3 NLQ elements in a single chart. 
    ax.fill_between(FedBal.index,FedBal,color='black',alpha=0.35)
    RevRepo = axb.plot(RevRep,color="red",label='Reverse repo bal. (right)',lw=1.5)
    TREGEN = axb.plot(TGA,color="blue",label='Treasury general account (right)',lw=1.5)
    FBMinRR = (FedBal-RevRep); NLQ = (FedBal-RevRep-TGA)
    FBMinRRPl = ax.plot(FBMinRR,color="orange",label='FedBal - RevRepo'); ax.fill_between(RevRep.index,(FedBal-RevRep),color='orange',alpha=0.35)
    NLQPl = ax.plot(NLQ,color="green",label='Net liquidity'); ax.fill_between(RevRep.index,(FedBal-RevRep-TGA),color='green',alpha=0.35)
    if YScale == "log":
        ax.set_yscale('log')
    ax.set_title(title)
    ax.set_ylabel('Billions of USD ($)', fontweight='bold'); axb.set_ylabel('Billions of USD ($)', fontweight='bold')  
    Xmax = max(TGA.index); Xmin = min(TGA.index)
    stepsize = (Xmax - Xmin) / 20
    XTicks = np.arange(Xmin, Xmax, stepsize); XTicks = np.append(XTicks,Xmax)
    ax.xaxis.set_ticks(XTicks); ax.set_xlim(Xmin-datetime.timedelta(days=15),Xmax+datetime.timedelta(days=15))
    ax.tick_params(axis='x',length=3,labelrotation=45)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%y-%b'))
    ax.set_ylim(NLQ.min(),FedBal.max()); ax.margins(y=0.05)
    #frequency = SeriesInfo['frequency']
    #ax.text(0.1,0.05,'Series updated: '+frequency,horizontalalignment='center',verticalalignment='center', transform=ax.transAxes)  
    ax.legend(loc=2,fontsize='small'); axb.legend(loc=2,fontsize='small',bbox_to_anchor=(0,0.9))
    for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_linewidth(1.5)
    ax.minorticks_on();  axb.minorticks_on() 

#######. MatPlotLib Section. Making good figs with MPL takes many lines of code dagnammit.  ###################
def GNLQ_ElementsChart(GNLQ:pd.Series,title:str,YScale='linear',US_NLQ:pd.Series=None,ECB:pd.Series=None,BOJ:pd.Series=None,PBoC:pd.Series=None,BoE:pd.Series=None):
    ######## Figure to plot all the elements of the the global liquidity, much like the Fed NLQ elements. 
    fig = plt.figure(num=title,figsize=(9,8), tight_layout=True)
    ax = fig.add_subplot(); axb = ax.twinx()
    GCBM = ax.plot(GNLQ,color="black",label='Global CB money')   ### This is a simple fig template to view the 3 NLQ elements in a single chart. 
    ax.fill_between(GNLQ.index,GNLQ,color='black',alpha=0.35)
    if US_NLQ is not None:
        Fed = axb.plot(US_NLQ,color="blue",label='Fed Net Liq. (right)',lw=1.5)
    if ECB is not None:
        ecb = axb.plot(ECB,color="aqua",label='ECB bal. sheet (right)',lw=1.5)
    if BOJ is not None:
        boj = axb.plot(BOJ,color="green",label='BoJ bal. sheet (right)',lw=1.5)
    if PBoC is not None:    
        pboc = axb.plot(PBoC,color="red",label='PBoC bal. sheet (right)',lw=1.5)
    if BoE is not None:
        boe = axb.plot(BoE,color="brown",label='BoE bal. sheet (right)',lw=1.5)
    
    if YScale == "log":
        ax.set_yscale('log')
    ax.set_title(title)
    ax.set_ylabel('Billions of USD ($)', fontweight='bold'); axb.set_ylabel('Billions of USD ($)', fontweight='bold')  
    Xmax = max(GNLQ.index); Xmin = min(GNLQ.index)
    stepsize = (Xmax - Xmin) / 20
    XTicks = np.arange(Xmin, Xmax, stepsize); XTicks = np.append(XTicks,Xmax)
    ax.xaxis.set_ticks(XTicks); ax.set_xlim(Xmin-datetime.timedelta(days=15),Xmax+datetime.timedelta(days=15))
    ax.tick_params(axis='x',length=3,labelrotation=45)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%y-%b'))
    ax.set_ylim(GNLQ.min(),GNLQ.max()); ax.margins(y=0.05)
    ax.legend(loc=2,fontsize='small'); axb.legend(loc=2,fontsize='small',bbox_to_anchor=(0,0.9))
    for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_linewidth(1.5)
    ax.minorticks_on();  axb.minorticks_on()    

######## All this shit below is matplotlib figure generation code. One needs all this shit to get a figure exactly as wanted. ##############
### Main figure with Net liquidity + comparison asset and correlations. #############################
def MainFig(MainSeries:pd.Series,CADict:dict,CorrDF:pd.DataFrame,AssetData:pd.DataFrame,figname:str,CorrString:str,YLabel:str='Bil. of U.S. $',Mainlabel:str='Net liquidity (left)',\
    LYScale:str='linear',RYScale:str='linear',NLQ_Color:str='black',NLQMA:pd.Series=None,NLQ_MAPer:int=None,background=np.nan,RightLabel:str='',YAxLabPrefix=None,Xmin=None,Xmax=None,YMin=None,YMax=None,\
        YMargin=None,RYMin=None,RYMax=None):
    fig = plt.figure(num=figname,figsize=(15.5,8), tight_layout=True)
    gs = GridSpec(2, 1, top = 0.96, bottom=0.08,left=0.06,right=0.92, height_ratios=[3,1], hspace=0.02)
    NetLiquidity = MainSeries; numCAs = len(CADict)
    if numCAs > 1:
        ExtraAssets = True
    else:
        ExtraAssets = False

    ax = fig.add_subplot(gs[0]); ax1 = fig.add_subplot(gs[1],sharex=ax)
    plot1 = ax.plot(NetLiquidity,color=NLQ_Color,lw=2.5,label=Mainlabel)
    if NLQMA is not None:
        MA = ax.plot(NLQMA,color='gold',lw=1,label='NLQ MA ('+str(NLQ_MAPer)+'day)')
    legend_1 = ax.legend(loc=2,fontsize='small',bbox_to_anchor=(0,1.06),framealpha=1)
    legend_1.remove(); ax.minorticks_on()
    i = 0; axList = []; Handles= []; Labels = []
    for CA in CADict.keys():
        AssDF = CADict[CA][0]
        if i == 0:
            FirstAss = AssDF['Close']; FAName = CA; FAColor = CADict[CA][1]
        if i == 1:
            axc = ax.twinx()
            CA2, = axc.plot(AssDF['Close'],label=CA,color=CADict[CA][1]); axc.axis('off')
            axList.append(axc); Handles.append(CA2); Labels.append(CA)
            #axc.set_ylabel(RightLabel,fontweight='bold')
        if i == 2:    
            axd = ax.twinx() 
            CA3, = axd.plot(AssDF['Close'],label=CA,color=CADict[CA][1]); axd.axis('off')
            axList.append(axd); Handles.append(CA3); Labels.append(CA)
            # axd.set_ylabel(RightLabel,fontweight='bold')
        if i == 3:
            axe = ax.twinx() 
            CA4, = axe.plot(AssDF['Close'],label=CA,color=CADict[CA][1]); axe.axis('off')
            axList.append(axe); Handles.append(CA4); Labels.append(CA)
            # axe.set_ylabel(RightLabel,fontweight='bold')
        if i == 4:
            axf = ax.twinx() 
            CA5, = axf.plot(AssDF['Close'],label=CA,color=CADict[CA][1]); axf.axis('off')
            axList.append(axf); Handles.append(CA5); Labels.append(CA) 
            # axf.set_ylabel(RightLabel,fontweight='bold')
        i += 1
    axb = ax.twinx()    
    CA1, = axb.plot(FirstAss,label=FAName,color=FAColor); axList.append(axb); Handles.append(CA1); Labels.append(FAName)
    axb.set_ylabel(RightLabel,fontweight='bold')
    axb.legend(handles=Handles,labels=Labels, loc=1,fontsize='small',bbox_to_anchor=(0.98,1.06),framealpha=1)
    LastAxes = axList[numCAs-1]
    LastAxes.add_artist(legend_1); LastAxes.set_ylabel(RightLabel,fontweight='bold'); LastAxes.axis('on')
    ax.set_title('BM Pleb CB Global Liquidity Index', fontweight='bold')
    ax.set_ylabel(YLabel, fontweight='bold')
    for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_linewidth(1.5)        
    if YMin and YMax is not None:     ##Scaling limits of Y axis in main chart. 
        ymin = YMin; ymax = YMax
    else:    
        ymin = NetLiquidity.min(); ymax = NetLiquidity.max()
    if RYMax is not None and pd.isna(RYMax) is False:
        Eq_ymax = RYMax; axb.set_ylim(top=Eq_ymax)
    else:
        Eq_ymax = AssetData['Close'].max()
    if RYMin is not None and pd.isna(RYMin) is False: 
        Eq_ymin = RYMin; axb.set_ylim(bottom=Eq_ymin)
    else:    
        Eq_ymin = AssetData['Close'].min()
    if LYScale == 'log' and RYScale == 'log':       ##This provides cool looking equally spaced log ticks and tick labels on both y axii. 
        for axis in axList:
            axis.set_yscale('log')
        axb.set_yscale('log')
        ax.set_yscale('log')
        bTicks = np.real(np.logspace(start = np.log10(Eq_ymin), stop = np.log10(Eq_ymax), num=8, base=10)); #bTicks.round(decimals=0,out=bTicks) 
        yTicks = np.real(np.logspace(start = np.log10(ymin), stop = np.log10(ymax), num=8, base=10)); #yTicks.round(decimals=0,out=yTicks)
        ax.text(1.075,0.35,s='Y-scales are logarithmic',fontsize='small',transform=ax.transAxes,horizontalalignment='center',verticalalignment='center',rotation='vertical')
    elif LYScale == 'linear' and RYScale == 'linear': 
        bTicks = np.real(np.linspace(start = Eq_ymin, stop = Eq_ymax, num=8)); #bTicks.round(decimals=0,out=bTicks)   
        yTicks = np.real(np.linspace(start = ymin, stop = ymax, num=8)); #yTicks.round(decimals=0,out=yTicks)
        ax.text(1.075,0.35,s='Y-scales are linear',fontsize='small',transform=ax.transAxes,horizontalalignment='center',verticalalignment='center',rotation='vertical')
    else:
        print('LYSCale and RYSCale must be set to the same values in the input file. Either log or linear, fatal ERORRRR.')    
        quit()
    bTicks = np.ndarray.astype(bTicks,dtype=float,copy=False); yTicks = np.ndarray.astype(yTicks,dtype=float,copy=False)     
    axb.grid(visible=True, which='major', axis='both', c='gray',ls=':',lw=0.75)
    axb.tick_params(axis='y',which='both',width=0,labelsize=0); axb.minorticks_off() #Had to do this to eliminate pesky ticks that kept coming on top of my custom ones. 
    axb.set_yticks(bTicks); axb.set_yticklabels(bTicks)
    axb.tick_params(axis='y',which='major',width=0.5,labelsize='small')     #All this to get y custom evenly spaced log ticks. 
    ax.tick_params(axis='y',which='both',width=0,labelsize=0); ax.minorticks_off() #Had to do this to eliminate pesky ticks that kept coming on top of my custom ones.    
    ax.set_yticks(yTicks); ax.set_yticklabels(yTicks)

    if YAxLabPrefix is not None:
        ax.yaxis.set_major_formatter(YAxLabPrefix+' {x:1.0f}'); axb.yaxis.set_major_formatter(YAxLabPrefix+' {x:1.1f}')
    else:
        ax.yaxis.set_major_formatter('{x:1.0f}'); axb.yaxis.set_major_formatter('{x:1.1f}')
    ax.tick_params(axis='y',which='major',width=0.5,labelsize='small')     #All this to get y custom evenly spaced log ticks. 
    ax.tick_params(axis='x',which='both',width=0,labelsize=0) 

    #ax1.set_title(CorrString, fontsize=13,alpha=1)
    ax1.text(0.55,-0.33,CorrString,horizontalalignment='center',verticalalignment='center', transform=ax.transAxes,fontsize=12)
    ax1.set_ylabel('Correlation', fontweight = 'bold'); i = 0
    for column in CorrDF.columns:
        numCCAvs = len(CorrDF.columns)
        traceName = column
        r = (i/(numCCAvs-1)); g = 0; b = 1 - (i/(numCCAvs-1))
        LW = 1+(i*0.25)
        ax1.plot(CorrDF[column], c =(r, g, b), label = traceName, linewidth = LW)
        i += 1
    ax1.legend(loc=1, fontsize='small',bbox_to_anchor=(1.09, 0.9),framealpha=1)
    if ExtraAssets is True:
        ax1.text(x=NetLiquidity.index[(round(len(NetLiquidity)/4)*3)-12],y=(-1.09),s='Correlation between net liquidity & '+FAName)
    ax1.set_ylim(-1.2, 1.1)
    for axis in ['top','bottom','left','right']:
            ax1.spines[axis].set_linewidth(1.5)  
    if Xmin is not None and Xmax is not None:
        pass
    else:
        Xmax = max(NetLiquidity.index); Xmin = min(NetLiquidity.index)
    stepsize = (Xmax - Xmin) / 20
    XTicks = np.arange(Xmin, Xmax, stepsize); XTicks = np.append(XTicks,Xmax)
    ax1.xaxis.set_ticks(XTicks); 
    #ax.set_xlim(Xmin-datetime.timedelta(days=15),Xmax+datetime.timedelta(days=15))
    ax.tick_params(axis='x',length=0,labelsize=0)
    ax1.tick_params(axis='x',length=3,labelrotation=45,labelsize='small'); ax1.tick_params(axis='y',labelsize='small')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%y-%b'))
    ax1.minorticks_on()
    ax.grid(visible=True,axis='x',color='gray',linestyle='dotted',linewidth=0.75)
    ax1.grid(visible=True,which='both',color='gray',linestyle='dotted',linewidth=0.75)
    ax.margins(0.01,0.01); axb.margins(0.01,0.01)
    if pd.isna(background) is False:
        ax.set_facecolor(background)
    return fig

#### Traces are input as dict of tuples e.g {"TraceName": (data,color,linewidth)}
def TwoAxisFig(LeftTraces:dict,LeftScale:str,LYLabel:str,title:str,XTicks=None,RightTraces:dict=None,RightScale:str=None,RYLabel:str=None,\
               LeftTicks:tuple=None,RightTicks:tuple=None,RightMinTicks:tuple=None,text1:str=None):
    
    fig = plt.figure(num=title,figsize=(13,6.5), tight_layout=True)
    gs1 = GridSpec(1, 1, top = 0.95, bottom=0.14 ,left=0.06,right=0.92)
    ax1 = fig.add_subplot(gs1[0])
    ax1 = fig.axes[0]
    ax1.set_title(title,fontweight='bold')

    for trace in LeftTraces.keys():
        ax1.plot(LeftTraces[trace][0],label = trace,color=LeftTraces[trace][1],lw=LeftTraces[trace][2])
    if LeftScale == 'log':
        ax1.set_yscale('log')    
    if LeftTicks is not None:    ### Ticks must be input as a tuple of lists or np.arrays. WIth format (Tick positions list, tick labels list)
            ax1.minorticks_off()
            ax1.tick_params(axis='y',which='both',length=0,labelsize=0,left=False,labelleft=False)
            ax1.set_yticks(LeftTicks[0]); ax1.set_yticklabels(LeftTicks[1])
            ax1.tick_params(axis='y',which='major',length=3,labelsize=9,left=True,labelleft=True)
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
            ax1b.tick_params(axis='y',which='both',length=0,width=0,right=False,labelright=False,labelsize=0)  
            ax1b.set_yticks(RightTicks[0]); ax1b.set_yticklabels(RightTicks[1])
            ax1b.tick_params(axis='y',which='major',width=1,length=3,labelsize=9,right=True,labelright=True)
            if RightMinTicks is not None:
                ax1b.set_yticks(RightMinTicks[0],minor=True); 
                ax1b.set_yticklabels(RightMinTicks[1],minor=True)
                ax1b.tick_params(axis='y',which='minor',length=2,labelsize=7)

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

class BMP_Fig(Figure):
    
    #LeftTraces:dict,LeftScale:str,LYLabel:str,title:str,XTicks=None,RightTraces:dict=None,RightScale:str=None,RYLabel:str=None,\
               #LeftTicks:tuple=None,RightTicks:tuple=None,RightMinTicks:tuple=None,text1:str=None
    def __init__(self,*args,margins:dict=None,numaxii:int=1,DataSourceStr:str="",**kwargs):  #margins is a dict like {top = 0.95, bottom=0.14 ,left=0.06,right=0.92}
        # figsize is a tuple like (width, height).
        plt.rcParams['font.family'] = 'serif'
        print(kwargs)
        super().__init__(*args,**kwargs)
        if margins is not None:
            print('Using margin dict unpacking')
            self.gs = GridSpec(1, 1, **margins)
            bot = margins["bottom"]
        else:
            self.gs = GridSpec(1, 1, top = 0.95, bottom=0.14 ,left=0.06,right=0.92)    
            bot = 0.14
        print("Chart bottom: ",bot)    
        self.add_subplot(self.gs[0])
        self.ax1 = self.axes[0]; axDict = {}
        for axis in ['top','bottom','left','right']:
            self.ax1.spines[axis].set_linewidth(1.5)
        for i in range(1,numaxii,1):
            axDict['ax'+str(i)] = self.ax1.twinx()
        self.ax1.minorticks_on()
        self.ax1.grid(visible=True,which='major',axis='both',lw=0.75,color='gray',ls=':')    
        self.ax1.tick_params(axis='x',which='both',labelsize=12)
          
        if bot < 0.14: 
            self.ax1.text(0, -0.135 , 'Charts by the Bootleg Macro Pleb (twitter: @Tech_Pleb)',fontsize=9,fontweight='bold',color='blue',horizontalalignment='left', transform=self.ax1.transAxes)
            self.ax1.text(1, -0.135 , DataSourceStr,fontsize=9,color='blue',horizontalalignment='right', transform=self.ax1.transAxes)
        else:
            self.ax1.text(0, -0.195, 'Charts by the Bootleg Macro Pleb (twitter: @Tech_Pleb)',fontsize=9,fontweight='bold',color='blue',horizontalalignment='left', transform=self.ax1.transAxes)  
            self.ax1.text(1, -0.195 , DataSourceStr,fontsize=9,color='blue',horizontalalignment='right', transform=self.ax1.transAxes)       
    
    def AddTraces(self,Traces:dict): #Traces is a nested dict with details of each trace such as color, linewidth etc. 
        i = 0; AxList =  self.axes
        locList = [(-0.025,-0.11),(0.375,-0.11),(0.7,-0.11),(-0.025,-0.16),(0.375,-0.16)]
        for trace in Traces.keys():
            print(i)
            TheTrace = Traces[trace]
            TheAx = AxList[i]; ymax = TheTrace['Ymax']
            if pd.isna(ymax):
                Ymax = None
            else:
                Ymax = ymax
            if pd.isna(TheTrace['LW']):
                LW = 1.5
            else:
                LW = TheTrace['LW']    
            print(trace,TheTrace,TheAx)
        
            if TheTrace['YScale'] == 'log':
                TheAx.set_yscale('log')  
            if i > 0:
                TheAx.tick_params(axis='y',which='both', labelsize=8,color=TheTrace['TraceColor'],labelcolor=TheTrace['TraceColor']) 
                TheAx.set_ylabel(TheTrace['axlabel'],fontsize=9,fontweight='bold',labelpad=-5,alpha=0.5,color=TheTrace['TraceColor'])
            else:
                TheAx.tick_params(axis='y',which='both',labelsize=10,color=TheTrace['TraceColor'],labelcolor=TheTrace['TraceColor'])
                TheAx.set_ylabel(TheTrace['axlabel'],fontweight='bold') 

                ticks, ticklabs = Utilities.EqualSpacedTicks(TheTrace['Data'],10,LogOrLin=TheTrace['YScale'],Ymax=Ymax)
                self.ax1.tick_params(axis='y',which='both',length=0,width=0,right=False,labelright=False,labelsize=0)  
                self.ax1.set_yticks(ticks); TheAx.set_yticklabels(ticklabs)  
                self.ax1.tick_params(axis='y',which='major',length=3,width=1,right=False,labelright=False,labelsize=9)  

            if TheTrace['YScale'] == 'log'and TheTrace['UnitsType'] != 'Unaltered':
                TheTrace['Data'] += 100; TheAx.minorticks_off()
                TheAx.plot(TheTrace['Data'],label = TheTrace['Legend_Name'],color=TheTrace['TraceColor'],lw=LW)
                ticks, ticklabs = Utilities.EqualSpacedTicks(TheTrace['Data'],10,LogOrLin='log',LabOffset=-100,labSuffix='%',Ymax=Ymax)
                TheAx.tick_params(axis='y',which='both',length=0,width=0,right=False,labelright=False,labelsize=0)  
                TheAx.set_yticks(ticks); TheAx.set_yticklabels(ticklabs) 
                if i > 0:
                    TheAx.tick_params(axis='y',which='major',width=1,length=3,labelsize=8,right=True,labelright=True,labelcolor=TheTrace['TraceColor'])
                else:
                     TheAx.tick_params(axis='y',which='major',width=1,length=3,labelsize=8,right=False,labelright=False,labelcolor=TheTrace['TraceColor'])

            else:    
                TheAx.plot(TheTrace['Data'],label = TheTrace['Legend_Name'],color=TheTrace['TraceColor'],lw=LW)
            if Ymax is not None:
                    TheAx.set_ylim(TheTrace['Data'].min(),round(Ymax))    
            if i > 1:
                TheAx.spines.right.set_position(("axes", 1+((i-1)*0.055))); 
            TheAx.margins(0.02,0.02)
            TheAx.spines['right'].set_linewidth(1.5)
            TheAx.spines['right'].set_color(TheTrace['TraceColor'])
            TheAx.legend(fontsize=9,loc=locList[i])  # ,bbox_to_anchor=LedgeOff[i]
            self.ax1.minorticks_on()
            self.ax1.tick_params(axis='y',which='minor',left=False,labelleft=False,width=0,length=0)
            self.ax1.grid(visible=True,which='major',axis='y',lw=0.75,color='gray',ls=':') 
            i += 1      
        self.ax1.grid(visible=True,which='both',axis='x',lw=0.75,color='gray',ls=':')      
        
        ####### All this below is to ensure that we get the minorticks in the correct locations. They can be out of sync with majors due to rounding. #############
        majList = self.ax1.xaxis.get_majorticklocs(); dist = []; newMinTicks = []; majTicks = []
        minTickLocs = self.ax1.xaxis.get_minorticklocs()
        for i in range(len(majList)):
            if i == len(majList)-1:
                dist.append(dist[i-1])
            else:    
                dist.append(majList[i+1]-majList[i]) 
            for j in range(1,4,1):
                if j == 1:
                    newMinTicks.append(majList[i]); majTicks.append(majList[i])
                newMinTicks.append(majList[i]+j*(dist[i]/4))
                majTicks.append(np.nan)
        majList2 = [np.nan for i in range(len(newMinTicks)-len(majList))]; minTickLocs2 = [np.nan for i in range(len(newMinTicks)-len(minTickLocs))]
        newMinTicks2 = [np.nan for i in range(len(newMinTicks)-len(newMinTicks))]
        majList3 = [*majList2,*majList]; minTickLocs3 = [*minTickLocs2,*minTickLocs]; newMinTicks3 = [*newMinTicks2,*newMinTicks]
        tickDict = {'MajTickLocs':majTicks,'NewMinTickLocs':newMinTicks3,"OldTickLocs":minTickLocs3}
        tickDF = pd.DataFrame(tickDict) #;print(tickDF.head(50))
        self.ax1.set_xticks(newMinTicks3,minor=True); self.ax1.set_xticks(majList)
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        self.ax1.margins(0.02,0.05)
    
    def set_Title(self,title:str):
        self.ax1.set_title(title, fontweight='bold', pad = 5)
        
    def addLogo(self,path):
        logo = plt.imread(path)
        self.figimage(logo,xo=2600,yo=10,origin = 'upper')    
