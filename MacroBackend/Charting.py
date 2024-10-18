import numpy as np
import re
import pandas as pd
from pandas.tseries.frequencies import to_offset
import matplotlib as mpl
from matplotlib import legend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import matplotlib.colors as mcolors
from matplotlib.patches import Rectangle
### These are standard python packages included in the latest python distributions. No need to install them. 
import datetime
from datetime import timedelta
from . import Utilities, Fitting
from typing import Union
import math

###### Global matplotlib parameters that I want always set ###################################
try:
    mpl.use("QtAgg")
except:
    mpl.use("TkAgg")

Mycolors = ['aqua','black', 'blue', 'blueviolet', 'brown'
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

#######UTILTY FUNCYTIONS ############################
def get_fig_ax_sizes(fig: plt.Figure):
    # Assuming 'ax' is your Axes object and 'fig' is your Figure object
    fig_width, fig_height = fig.get_size_inches()  # Size of the whole figure in inches
    ax = fig.get_axes()[0]  # Get the first axes
    ax_position = ax.get_position()  # Position of the axes in figure coordinates

    # Calculate the size of the axes in inches
    ax_width = fig_width * (ax_position.x1 - ax_position.x0)
    ax_height = fig_height * (ax_position.y1 - ax_position.y0)

    return {"fig_width": fig_width, "fig_height": fig_height, "ax_width": ax_width, "ax_height": ax_height, "bottom_left_corner": (ax_position.x0, ax_position.y0)}

def adjust_y_for_legHeight(fig: plt.Figure, leg: legend.Legend, locList: list, dimsdict: dict, heights: list = [], j: int = 0):
    # Assuming 'fig' is your Figure object and 'leg' is your Legend object
    renderer = fig.canvas.get_renderer()
    bbox = leg.get_window_extent(renderer)
    bbox = bbox.transformed(fig.dpi_scale_trans.inverted()) # Convert the bounding box to figure coordinates
    print("Box width, height: ", bbox.width, bbox.height) #These are in inches. 
    
    heights.append(bbox.height)
    # # Calculate the new y-coordinate for the legend
    new_y = locList[j][1] - ((bbox.height-0.216365)/dimsdict["fig_height"])
    print("Old y: ", locList[j][1], "New y: ", new_y)
    # # Set the new location of the legend
    leg.set_bbox_to_anchor((locList[j][0], new_y))
    return heights, new_y

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
    yTicks = np.ndarray.astype(yTicks,dtype=float,copy=False).flatten()
    ax.tick_params(axis='y',which='both',width=0,labelsize=0); ax.minorticks_off() #Had to do this to eliminate pesky ticks that kept coming on top of my custom ones.  
    ax.set_yticks(yTicks); ax.set_yticklabels(yTicks); ax.yaxis.set_major_formatter('{x:1.1f}'); ax.tick_params(axis='y',which='major',width=0.5,labelsize='small') 
    if RightSeries is not None: 
        Eq_ymin = RightSeries.min(); Eq_ymax = RightSeries.max()
        if RYScale == 'log':
            axb.set_yscale('log')
            bTicks = np.real(np.logspace(start = np.log10(Eq_ymin), stop = np.log10(Eq_ymax), num=8, base=10)); #bTicks.round(decimals=0,out=bTicks) 
        else:
            bTicks = np.real(np.linspace(start = Eq_ymin, stop = Eq_ymax, num=8)); #bTicks.round(decimals=0,out=bTicks) 
        bTicks = np.ndarray.astype(bTicks,dtype=float,copy=False).flatten()  
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

def plot_colortable(colors = mcolors.CSS4_COLORS, *, ncols=4, sort_colors=True):

    cell_width = 212
    cell_height = 22
    swatch_width = 48
    margin = 12

    # Sort colors by hue, saturation, value and name.
    if sort_colors is True:
        names = sorted(
            colors, key=lambda c: tuple(mcolors.rgb_to_hsv(mcolors.to_rgb(c))))
    else:
        names = list(colors)

    n = len(names)
    nrows = math.ceil(n / ncols)

    width = cell_width * ncols + 2 * margin
    height = cell_height * nrows + 2 * margin
    dpi = 72

    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    fig.subplots_adjust(margin/width, margin/height,
                        (width-margin)/width, (height-margin)/height)
    ax.set_xlim(0, cell_width * ncols)
    ax.set_ylim(cell_height * (nrows-0.5), -cell_height/2.)
    ax.yaxis.set_visible(False)
    ax.xaxis.set_visible(False)
    ax.set_axis_off()

    for i, name in enumerate(names):
        row = i % nrows
        col = i // nrows
        y = row * cell_height

        swatch_start_x = cell_width * col
        text_pos_x = cell_width * col + swatch_width + 7

        ax.text(text_pos_x, y, name, fontsize=14,
                horizontalalignment='left',
                verticalalignment='center')

        ax.add_patch(
            Rectangle(xy=(swatch_start_x, y-9), width=swatch_width,
                      height=18, facecolor=colors[name], edgecolor='0.7')
        )

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
def GNLQ_ElementsChart(GNLQ:pd.Series,title:str,YScale='linear',US_NLQ:pd.Series=None,ECB:pd.Series=None,
                       BOJ:pd.Series=None,PBoC:pd.Series=None,BoE:pd.Series=None, SNB:pd.Series=None):
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
    if SNB is not None:
        snb = axb.plot(SNB,color="fuchsia",label='SNB bal. sheet (right)',lw=1.5)
    
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
        MA = ax.plot(NLQMA,color='orange',lw=1,label='NLQ MA ('+str(NLQ_MAPer)+'day)')
    legend_1 = ax.legend(loc=2,fontsize='small',bbox_to_anchor=(0,1.06),framealpha=1)
    legend_1.remove(); ax.minorticks_on()
    i = 0; axList = []; Handles= []; Labels = []
    for CA in CADict.keys():
        AssDF = CADict[CA][0]
        if i == 0:
            FirstAss = AssDF; FAName = CA; FAColor = CADict[CA][1]
        if i == 1:
            axc = ax.twinx()
            CA2, = axc.plot(AssDF,label=CA,color=CADict[CA][1]); axc.axis('off')
            axList.append(axc); Handles.append(CA2); Labels.append(CA)
            #axc.set_ylabel(RightLabel,fontweight='bold')
        if i == 2:    
            axd = ax.twinx() 
            CA3, = axd.plot(AssDF,label=CA,color=CADict[CA][1]); axd.axis('off')
            axList.append(axd); Handles.append(CA3); Labels.append(CA)
            # axd.set_ylabel(RightLabel,fontweight='bold')
        if i == 3:
            axe = ax.twinx() 
            CA4, = axe.plot(AssDF,label=CA,color=CADict[CA][1]); axe.axis('off')
            axList.append(axe); Handles.append(CA4); Labels.append(CA)
            # axe.set_ylabel(RightLabel,fontweight='bold')
        if i == 4:
            axf = ax.twinx() 
            CA5, = axf.plot(AssDF,label=CA,color=CADict[CA][1]); axf.axis('off')
            axList.append(axf); Handles.append(CA5); Labels.append(CA) 
            # axf.set_ylabel(RightLabel,fontweight='bold')
        i += 1
    axb = ax.twinx()    
    CA1, = axb.plot(FirstAss,label=FAName,color=FAColor); axList.append(axb); Handles.append(CA1); Labels.append(FAName)
    axb.set_ylabel(RightLabel,fontweight='bold')
    axb.legend(handles=Handles,labels=Labels, loc=1,fontsize='small',bbox_to_anchor=(0.98,1.06),framealpha=1)
    LastAxes = axList[numCAs-1]
    LastAxes.add_artist(legend_1); LastAxes.set_ylabel(RightLabel,fontweight='bold'); LastAxes.axis('on')
    ax.set_title('                         Bootleg Macro CB Global Liquidity Index', fontweight='bold')
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
        Eq_ymax = AssetData.max()
    if RYMin is not None and pd.isna(RYMin) is False: 
        Eq_ymin = RYMin; axb.set_ylim(bottom=Eq_ymin)
    else:    
        Eq_ymin = AssetData.min()
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
    
    bTicks = np.ndarray.astype(bTicks,dtype=float,copy=False).flatten() ; yTicks = np.ndarray.astype(yTicks,dtype=float,copy=False).flatten()  
    axb.grid(visible=True, which='major', axis='both', c='gray',ls=':',lw=0.75)
    axb.tick_params(axis='y',which='both',width=0,labelsize=0); axb.minorticks_off() #Had to do this to eliminate pesky ticks that kept coming on top of my custom ones. 
    axb.tick_params(axis='y',which='major',width=0.5,labelsize='small')     #All this to get y custom evenly spaced log ticks. 
    axb.set_yticks(bTicks)
    ax.tick_params(axis='y',which='both',width=0,labelsize=0); ax.minorticks_off() #Had to do this to eliminate pesky ticks that kept coming on top of my custom ones.    
    ax.set_yticks(yTicks)
    ax.tick_params(axis='y',which='major',width=0.5,labelsize='small') 
    
    if YAxLabPrefix is not None:
        ax.yaxis.set_major_formatter(YAxLabPrefix+' {x:1.0f}'); axb.yaxis.set_major_formatter(YAxLabPrefix+' {x:1.1f}')
    else:
        ax.yaxis.set_major_formatter('{x:1.0f}'); axb.yaxis.set_major_formatter('{x:1.1f}')
    ax.tick_params(axis='y',which='major',width=0.5,labelsize='small')     #All this to get y custom evenly spaced log ticks. 
    ax.tick_params(axis='x',which='both',width=0,labelsize=0) 

    ax1.text(0.45,-0.33,CorrString,horizontalalignment='center',verticalalignment='center', transform=ax.transAxes,fontsize=12)
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
        ax1.text(x=NetLiquidity.index[(round((len(NetLiquidity)/4)*2.5))-12],y=(-1.09),s='Correlation between net liquidity & '+FAName)
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
    
    fig = plt.figure(num=title,figsize=(12,6), tight_layout=True)
    gs1 = GridSpec(1, 1, top = 0.95, bottom=0.14 ,left=0.06,right=0.92)
    ax1 = fig.add_subplot(gs1[0])
    ax1 = fig.axes[0]
    ax1.set_title(title,fontweight='bold')

    if LeftScale == 'log':
        ax1.set_yscale('log')    
    if LeftTicks is not None:    ### Ticks must be input as a tuple of lists or np.arrays. WIth format (Tick positions list, tick labels list)
            ax1.minorticks_off()
            ax1.tick_params(axis='y',which='both',length=0,labelsize=0,left=False,labelleft=False)
            ax1.set_yticks(LeftTicks[0]); ax1.set_yticklabels(LeftTicks[1])
            ax1.tick_params(axis='y',which='major',length=3,labelsize=9,left=True,labelleft=True)
            ax1.set_ylim(LeftTicks[0][0]-LeftTicks[0][0]*0.025,LeftTicks[0][len(LeftTicks[0])-1]+LeftTicks[0][len(LeftTicks[0])-1]*0.025)
    
    #ax1.grid(visible=True, color = "black", lw = 0.75, ls = "--", which = 'major', axis = 'both', alpha = 0.7)
    for trace in LeftTraces.keys():
        ax1.plot(LeftTraces[trace][0],label = trace,color=LeftTraces[trace][1],lw=LeftTraces[trace][2])
        
    if RightTraces is not None:
        ax1b = ax1.twinx()
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
            ax1b.set_ylim(RightTicks[0][0]-RightTicks[0][0]*0.025,RightTicks[0][len(RightTicks[0])-1]+RightTicks[0][len(RightTicks[0])-1]*0.025)
            if RightMinTicks is not None:
                ax1b.set_yticks(RightMinTicks[0],minor=True); 
                ax1b.set_yticklabels(RightMinTicks[1],minor=True)
                ax1b.tick_params(axis='y',which='minor',length=2,labelsize=7)

    if XTicks is not None:
        ax1.xaxis.set_ticks(XTicks) 
        ax1.tick_params(axis='x',length=2,labelsize='small',labelrotation=30)
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

# Define a custom sorting key that extracts the number from each string
def sort_key(s: str):
    print("sort key, s: ", s, type(s))
    # Find all groups of digits in the string
    numbers = re.findall(r'\d+', s)
    # Return the first number as an integer, or 0 if there are no numbers
    return int(numbers[0]) if numbers else 0

class BMP_Fig(Figure):
    
    #LeftTraces:dict,LeftScale:str,LYLabel:str,title:str,XTicks=None,RightTraces:dict=None,RightScale:str=None,RYLabel:str=None,\
               #LeftTicks:tuple=None,RightTicks:tuple=None,RightMinTicks:tuple=None,text1:str=None
    def __init__(self, plotDatas:dict = None, *args, margins:dict=None,numaxii:int=1,DataSourceStr:str="",**kwargs):
        # figsize is a tuple like (width, height). #margins is a dict like {top = 0.95, bottom=0.14 ,left=0.06,right=0.92}
        plt.rcParams['font.family'] = 'serif'
        self.plotDatas = plotDatas
        self.DataSourceStr = DataSourceStr
        self.numaxii = numaxii
        super().__init__(*args,**kwargs)
        self.add_subplot(1, 1, 1)
        self.subplots_adjust(**margins)
        if margins is not None:
            self.subplots_adjust(**margins)
        else:
            self.subplots_adjust(top=0.95, bottom=0.14 ,left=0.06,right=0.92)
        self.ax1 = self.axes[0]
        for axis in ['top','bottom','left','right']:
            self.ax1.spines[axis].set_linewidth(1.5)
        for i in range(1,numaxii,1):
            axis = self.ax1.twinx()
        self.ax1.minorticks_on()
        self.ax1.grid(visible=True,which='major',axis='both',lw=0.75,color='gray',ls=':')    
        self.ax1.tick_params(axis='x',which='both',labelsize=12)   
    
    def AddTraces(self, plotDatas: dict = None): #plotDatas is a nested dict with details of each trace such as color, linewidth etc. 
        if plotDatas is not None:
            self.plotDatas = plotDatas
        elif plotDatas is None:
            plotDatas = self.plotDatas
            if plotDatas is None:
                print("No plot data provided, add the plotDatas dict to either __init__() method or AddTraces. Exiting...")    
                quit()    
        else:
            pass        

        i = 0; AxList =  self.axes
        for axes_name in plotDatas:
            TheAx = AxList[i]; LabOffset = 0; labSuffix = ''
            the_axdict = plotDatas[axes_name]; ymax = the_axdict['Ymax']; ymin = the_axdict['Ymin']
  
            primary_trace = the_axdict['data'][0]
        
            if primary_trace['UnitsType'] not in ['Unaltered','Rolling sum']:
                primary_trace['axlabel'] = primary_trace['UnitsType']

            if pd.isna(ymax) or ymax == '':
                Ymax = None
            else:
                Ymax = ymax
            if pd.isna(ymin) or ymin == '':
                Ymin = None
            else:
                Ymin = ymin 

            scales = ['linear', 'log', 'symlog', 'asinh', 'logit', 'function', 'functionlog']
            nc_scales = ['symlog', 'asinh', 'logit', 'function', 'functionlog']
            if primary_trace['YScale'] in nc_scales or primary_trace['YScale'] not in scales:
                print("Y-scales other than linear or log are not yet supported, choose only linear or log.")
                quit()
            else:    
                TheAx.set_yscale(primary_trace['YScale'])
                print(TheAx, 'Use scale: ', primary_trace['YScale'])

            if primary_trace['YScale'] == 'log' and primary_trace['UnitsType'] not in ['Unaltered','Rolling sum']:
                print('Using offset log axis for series: ',primary_trace['Name'])
                for trace in the_axdict['data']:
                    trace['Data'] += 100
                if Ymin is not None:
                    Ymin += 100
                if Ymax is not None:
                    Ymax += 100    
                LabOffset = -100
                labSuffix = '%'

            TheAx.minorticks_off()
            ticks, ticklabs = Utilities.EqualSpacedTicks(10, primary_trace['Data'], LogOrLin=primary_trace['YScale'],LabOffset=LabOffset,labSuffix=labSuffix,Ymax=Ymax,Ymin=Ymin)
            TheAx.tick_params(axis='y',which='both',length=0,width=0,right=False,labelright=False,labelsize=0)  
            TheAx.set_yticks(ticks); TheAx.set_yticklabels(ticklabs)

            axLabel = primary_trace["axlabel"]
            if pd.isna(axLabel) and primary_trace['UnitsType'] in ['Unaltered','Rolling sum']:
                axLabel = "USD"
            elif pd.isna(axLabel) and primary_trace['UnitsType'] not in ['Unaltered','Rolling sum']: 
                axLabel = primary_trace['UnitsType']   
            else:
                pass

            if i > 0:
                TheAx.tick_params(axis='y',which='major',width=1,length=3,labelsize=8,right=True,labelright=True,labelcolor=primary_trace['TraceColor'],color=primary_trace['TraceColor'])
                TheAx.set_ylabel(axLabel,fontweight='bold',fontsize=9,labelpad=-5,alpha=0.5,color=primary_trace['TraceColor'])  
            else:
                self.ax1.tick_params(axis='y',which='major',width=1,length=3,labelsize=8,right=False,labelright=False,labelcolor=primary_trace['TraceColor'],color=primary_trace['TraceColor'])   
                self.ax1.set_ylabel(axLabel,fontweight='bold')               

            for axData in reversed(the_axdict['data']):
                traceData = axData
                data = traceData['Data']; name = traceData['Name']

                LW = 1.5 if pd.isna(traceData['LW']) else traceData['LW']

                if isinstance(data, pd.DataFrame):
                    for col in data.columns:
                        TheAx.plot(data[col], label = data[col].name, lw=LW)
                else:        
                    TheAx.plot(traceData['Data'],label = traceData['Legend_Name'],color=traceData['TraceColor'],lw=LW)
                print("Plot position: ", traceData['Data'], traceData['Legend_Name'])

                if not pd.isna(traceData['addMA']):
                    period = round(traceData['addMA'])
                    ThisTrace = pd.Series(traceData['Data'])
                    TheAx.plot(ThisTrace.rolling(period).mean(),label = traceData['Legend_Name']+' '+str(period)+'_MA',color=traceData['TraceColor'],lw=1)
                
                if pd.isna(traceData['FitTrend']) or type(data) == pd.DataFrame:
                        pass
                else:
                    print("Fit trend: ", traceData['FitTrend'])
                    try:
                        params = str(traceData['FitTrend']).split(",")
                        fit = Fitting.FitTrend(data)
                        fit.FitData(FitFunc = params[0].strip(), x1 = params[1].strip(), x2 = params[2].strip())
                        # TheAx.plot(fit.fit, color=traceData['TraceColor'], ls = "dashed", lw = 2)
                        TheAx.plot(fit.ext_fit, color=traceData['TraceColor'], ls = "dashed", lw = 1)
                    except Exception as e:
                        print("Fitting trend failed.... Error message: ", e, "\nWill plot trace without trendline...")    
                  
                if i > 1:
                    TheAx.spines.right.set_position(("axes", 1+((i-1)*0.055))); 
                TheAx.margins(0.02,0.02)
                TheAx.spines['right'].set_linewidth(1.5)
                TheAx.spines['right'].set_color(primary_trace['TraceColor'])
            i += 1      

        self.ax1.minorticks_on()
        self.ax1.tick_params(axis='y',which='minor',left=False,labelleft=False,width=0,length=0)
        self.ax1.grid(visible=True,which='major',axis='y',lw=0.75,color='gray',ls=':')     
        self.ax1.grid(visible=True,which='both',axis='x',lw=0.75,color='gray',ls=':')   

        self.org_x_axis()
        print("Figure DPI in rcParams is: ", mpl.rcParams['figure.dpi'])
        
        ####### All this below is to ensure that we get the minorticks in the correct locations. They can be out of sync with majors due to rounding. #############
    def org_x_axis(self):
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
    
        newMinTicks2 = [np.nan for i in range(len(newMinTicks) - len(newMinTicks))]
        newMinTicks3 = [*newMinTicks2, *newMinTicks]
        self.ax1.set_xticks(newMinTicks3, minor=True)
        self.ax1.set_xticks(majList)
        
        # Determine the date format based on the range of the x-axis
        x_min, x_max = self.ax1.get_xlim()
        x_range_years = (mdates.num2date(x_max) - mdates.num2date(x_min)).days / 365.25
        
        if x_range_years < 5:
            date_format = '%b-%Y'
        else:
            date_format = '%Y'
        
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
        self.ax1.margins(0.01, 0.05)
    
    def set_Title(self,title:str):
        self.ax1.set_title(title, fontweight='bold', pad = 5)
        
    def addLogo(self,path):
        logo = plt.imread(path)
        self.figimage(logo,xo=2600,yo=10,origin = 'upper')    

    def make_legend(self, legtype: str = "single"):
        fig = self  # Get the current figure
        axes = list(fig.get_axes())  # Get all axes in the figure
        row_1 = -0.11
        locList = [(-0.045,row_1),(0.375,row_1),(0.75,row_1),(-0.045,-0.21),(0.375,-0.21)]
        self.dimsdict = get_fig_ax_sizes(fig)
        print("Plot dimensions: ", self.dimsdict, "bottom left corner of plot: ", self.dimsdict['bottom_left_corner'])
       
        if legtype == "single":  #One single legend for all traces & axes:
            lines, labels = [], []
            locList = [(-0.02, row_1)]
            for ax in axes:
                line, label = ax.get_legend_handles_labels()
                lines += line
                labels += label
            leg = axes[0].legend(lines, labels, ncol = 5, loc = (-0.02, row_1), fontsize=  "small")
            leg.set_draggable(True)
            heights, new_y = adjust_y_for_legHeight(fig, leg, locList, self.dimsdict); row_ = new_y
            leg_heights = heights[0]/self.dimsdict["ax_height"] 
            bottom = ((leg_heights*3)/self.dimsdict["fig_height"]) + 0.14

        elif legtype == 'one_per_axes':  
            legdict = {}; i = 0; heights = []

            for axes_name in self.plotDatas:
                TheAx = axes[i]
                ax_color = self.plotDatas[axes_name]['data'][0]['TraceColor'] 
                lines, labels = TheAx.get_legend_handles_labels()

                if i == 0:
                    legdict["Left axis: "] = (lines, labels, ax_color)
                else:
                    legdict["Right axis_"+str(i)+": "] = (lines, labels, ax_color)
                i += 1  

                j = 0    
            for axes_name in legdict.keys():    
                if j == 3:
                    print("Legend box heights: ", heights, "max height", max(heights))
                    row2 = row_1 - (max(heights)/self.dimsdict["ax_height"]) -0.01
                    print("Row 2: ", row2)
                    locList = [(-0.025,row_1),(0.375,row_1),(0.75,row_1),(-0.025,row2),(0.375,row2)]
                leg = axes[j].legend(legdict[axes_name][0], legdict[axes_name][1], ncol = 2,  loc = locList[j],
                    fontsize="small", frameon = True, edgecolor = legdict[axes_name][2])#, title = axes_name, title_fontsize = "small")
                leg.set_draggable(True)
                #leg._legend_title_box._text.set_color(legdict[axes_name][2])
                
                heights, _ = adjust_y_for_legHeight(fig, leg, locList, self.dimsdict, heights = heights, j = j)
                
                j += 1

            if self.numaxii <= 3:
                leg_heights =  max(heights[::self.numaxii - 1])/self.dimsdict["ax_height"]
                bottom = ((max(heights[::2])) + min(heights))/self.dimsdict["fig_height"] + 0.08
            else: 
                leg_heights = (max(heights[::2]) + max(heights[3::]))/self.dimsdict["ax_height"]
                bottom = ((max(heights[::2]) + max(heights[3::]) + min(heights))/self.dimsdict["fig_height"]) + 0.08
            print("Leg heights: ", leg_heights)

        else:
            print("Invalid legend type (legtype) specified. Choose 'single' or 'one_per_axes'.") 
            quit()  

        ax = fig.get_axes()[0]  # Get the first axes
        # y0 = ax.get_position().y0; y1 = ax.get_position().y1 # Get the bottom position of the axes
        self.text_box_row = row_1 - leg_heights - 0.015
        print("Text box row should be at: ", self.text_box_row)
        
        print("Heights of legends: ", heights)
        print("Bottom: ", bottom)
        self.bottom = bottom
        self.subplots_adjust(bottom = bottom)    

        # Check if the legend width exceeds the figure width
        legend_width = leg.get_window_extent().width / fig.dpi
        fig_width = fig.get_figwidth()
        if legend_width > fig_width and legtype == "single":
            print("Legend width exceeds figure width. Re-running with legtype='one_per_axes'.")
            leg = None    #Reset the legend from before.
            self.make_legend(legtype="one_per_axes")
        ax.text(-0.05, self.text_box_row , 'Charts by The Macro Bootlegger (twitter: @Tech_Pleb)',fontsize=9,fontweight='bold',color='blue',horizontalalignment='left', transform=self.ax1.transAxes)
        ax.text(1.05, self.text_box_row , self.DataSourceStr, fontsize=9,color='blue',horizontalalignment='right', transform=self.ax1.transAxes)

def DF_DefPlot(data: pd.DataFrame, yLabel: str = "a.u", YScale:str='linear', title: str = "DataFrame contents"):
    plt.rcParams['font.family'] = 'serif'
    fig = plt.figure(figsize=(11, 5), dpi=150)
    ax = fig.add_axes(rect=[0.07,0.06,0.67,0.84])

    colors = list(plt.rcParams['axes.prop_cycle'].by_key()['color']); i = 0
    xkcd_colors = list(mcolors.XKCD_COLORS.keys())
    colors.extend(Mycolors); colors.extend(xkcd_colors)
    
    for col in data.columns:
        ax.plot(data[col],label=col, color = colors[i]); i += 1    
    ax.legend(fontsize=5,loc=2,bbox_to_anchor=(1.005,1.01))
    ax.set_yscale(YScale); 
    ax.set_title(title,fontweight='bold',fontsize=9,loc='left',x = 0.1)

    ax.set_ylabel(yLabel,fontweight='bold',fontsize=9)
    ax.tick_params(axis='both',labelsize=8) 
    ax.minorticks_on(); ax.margins(x=0.02,y=0.02)
    ax.grid(visible=True,axis='both',which='both',lw=0.5,color='gray',ls=':')      
    ax.margins(0.01,0.01)    
    for axis in ['top','bottom','left','right']:
            ax.spines[axis].set_linewidth(1.5)    
    plt.tight_layout() # This will ensure everything fits well    

    return fig      

def gen_subplots_bar(series1: pd.Series, series2: pd.Series, color1: str = "b", color2: str = "r",
                     title: str = "Bar plot...", ylabel: str = "USD"):

        fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
        plot_width = axes[0].get_window_extent().width # Convert from pixels to inches
        width =  (plot_width/ len(series1)) # Width of each bar
       
        # Plot the bars
        axes[0].bar(series1.index, series1, width = width*4, label=series1.name, color = color1)
        axes[1].bar(series2.index, series2, width = width*4, label=series2.name, color = color2)
        axes[1].legend()
        # Set the title and labels
        axes[0].set_title(title)
        for ax in axes:
            ax.set_axisbelow(True)
            ax.legend(fontsize = 11, frameon = True)
            ax.set_ylabel(ylabel)
            ax.margins(0.02, 0.02)
        return fig, axes

class TracesTop_RoC_bottom(Figure):

    def __init__(self, data: Union[pd.DataFrame, pd.Series, dict] = None,  *args, botPanel: bool = False, roc_period_months: int = 12, **kwargs):
        if data is None:
            print("What data you wanna plot man?")
            quit()
        plt.rcParams['font.family'] = 'serif'
        self.data = data
        if type(self.data) == pd.DataFrame:
            self.data_series = self.data[self.data.columns[0]]
        else:
            self.data_series = self.data.copy()    

        self.bot_panel = botPanel
        # Determine the frequency of the dataframe
        self.data_freq = pd.infer_freq(self.data.index); print(self.data_freq)
        # Convert the user-specified RoC period to an equivalent in terms of the data frequency
        self.roc_period = self.convert_period_to_freq(roc_period_months)
        print(self.roc_period)

        if botPanel: 
            kwargs['figsize']=(11,7)
            self.gs = GridSpec(2, 1, top = 0.94, bottom=0.08,left=0.08,right=0.96, height_ratios= [2,1], hspace = 0.02)
        else:    
            kwargs['figsize']=(11,5.5)
            self.gs = GridSpec(1, 1, top = 0.94, bottom=0.08,left=0.08,right=0.96)

        super().__init__(*args,**kwargs)
        self.roc_df = data.pct_change(periods = self.roc_period, fill_method=None)

    def convert_period_to_freq(self, period_months) -> int:
        # Converts a period like '3M' into the number of data frequency periods it represents
        if self.data_freq is None:
            raise ValueError("Data frequency could not be inferred. Please ensure the DataFrame has a DateTime index with a consistent frequency.")
            return None
        else:
            print('Period to freq. function: ', self.data_freq)
            
            freq = Utilities.freqDetermination(self.data_series)
            freq.DetermineSeries_Frequency()
            frequency = freq.frequency

            periodsInMonth = freq.per_in_d*30.4375
            print('Data frequency from Utilities function: ', frequency, 'periods in 1 month: ', periodsInMonth)
            numPeriods = period_months * periodsInMonth
            return int(numPeriods)

    def plot(self, left_traces: dict, axDeets: dict = None, right_traces: dict = None, title: str = 'Here some data'): 
        
        if axDeets  is None:
            axDeets = {'yscale_top_left': 'linear', 'ylabel_top_left': 'a.u',
                       'legend_top': {'loc': 2, 'fontsize': 'small'}
            }
                       
        if self.bot_panel:
            self.ax = self.add_subplot(self.gs[0])
            self.ax2 = self.add_subplot(self.gs[1])
            self.ax2.tick_params(axis='x', which = 'major', labelsize = 11) 
            self.ax2.margins(0.02, 0.02)   
            for axis in ['top','bottom','left','right']:
                self.ax2.spines[axis].set_linewidth(1.5) 
            self.ax2.plot(self.roc_df)
        else:
            self.ax = self.add_subplot(self.gs[0])  
            self.ax.tick_params(axis='x', which = 'major', labelsize = 11) 

        for trace in left_traces.keys():   
            if isinstance(left_traces[trace], dict):
                series_data = left_traces[trace].pop('Series', None)
                if series_data is not None:
                    self.ax.plot(series_data, **left_traces[trace])
            else:
                self.ax.plot(left_traces[trace], label = trace)     

        self.ax.set_title(title)
        self.ax.set_yscale(axDeets['yscale_top_left'])        
        self.ax.set_ylabel(axDeets['ylabel_top_left'], fontsize=10, fontweight='bold') 
        self.ax.legend(**axDeets['legend_top'])
        self.ax.margins(0.02, 0.02) 
        for axis in ['top','bottom','left','right']:
                self.ax.spines[axis].set_linewidth(1.5) 

        if 'yscale_top_right' in axDeets.keys():
            self.axb = self.ax.twinx()
            self.axb.set_yscale(axDeets['yscale_top_right'])
            if 'ylabel_top_right' in axDeets.keys():
                self.axb.set_ylabel(axDeets['ylabel_top_right'], fontsize=10, fontweight='bold')
  

def plot_lin_reg(series1: pd.Series, series2: pd.Series, returns: bool = True, title: str = None):
    ser1_title = series1.name; ser2_title = series2.name

    df = pd.concat([series1, series2], axis=1)
    if returns:
        ser1rets = np.log(df[ser1_title]/df[ser1_title].shift(1)).dropna() 
        ser2rets = np.log(df[ser2_title]/df[ser2_title].shift(1)).dropna()
    else:
        ser1rets = series1.copy(); 
        ser2rets = series2.copy()

    # Perform linear regression using the new API with full=True
    reg, [resid, rank, sv, rcond] = np.polynomial.Polynomial.fit(ser2rets, ser1rets, 1, full=True)
    vals = reg(ser2rets)
    # Calculate the R² value
    ss_res = resid[0]  # Sum of squared residuals
    ss_tot = np.sum((ser1rets - np.mean(ser1rets))**2)
    r_squared = 1 - (ss_res / ss_tot)

    fig, ax = plt.subplots(figsize=(13, 3))
    ax.scatter(ser2rets, ser1rets, alpha=0.6, edgecolor='none')
    ax.plot(ser2rets, vals, 'r', lw=1.5)

    if title:
        ax.set_title(title)
    else:
        if returns:
            ax.set_title("Scatter plot: log returns, series "+ser1_title+" vs "+ser2_title+" with linear regression...")
        else:
            ax.set_title("Scatter plot: series "+ser1_title+" vs "+ser2_title+" with linear regression...")

    # Add a text box with the R² value
    textstr = f'$R^2 = {r_squared:.2f}$'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)

    if returns:
        ax.set_xlabel(f'Log Returns of {ser2_title}')
        ax.set_ylabel(f'Log Returns of {ser1_title}')
    else:
        ax.set_xlabel(f'{ser2_title} values')
        ax.set_ylabel(f'{ser1_title} values')

    return fig