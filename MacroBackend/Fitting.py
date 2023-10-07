import sys
import os
wd = os.path.dirname(__file__); dire = os.path.dirname(wd)
sys.path.append(dire)

import numpy as np
from scipy.optimize import curve_fit
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates
from MacroBackend import Utilities
import datetime
from datetime import timedelta

class FitFunction():
    def __init__(self):
        ### Define function formula as a function below, and define tuple in self.functions with (callable function, Yscale of data display).. 
        self.functions = {"Line": (self.FitLine, 'linear'),
                        'Exp_Base10':(self.Exp_Base10, 'log'), 
                        "Exponential": (None,'log'),
                        "ExpLog": (self.expLog, 'log'),
                        "LinExpLog": (self.expLog, 'linear'),
                        "Logistic": (self.logistic_func, 'log')}
        print("Data fitting engine, fit function options are: ",list(self.functions.keys()))

    ## Mathematical functions to fit to data.
    def FitLine(self, x, m, b):
        self.funcName = "Line"
        return (m*x) + b
    
    def Exp_Base10(self, x, a, b):
        self.funcName = "Exp_Base10"
        return 10**(a*x+b)

    def expLog(self, x, a, b):  # Define expLog function
        self.funcName = "ExpLog"
        return 10**(a*np.log(x)-b)
        #return np.exp((a*np.log(x)-b))

    def logistic_func(self, x, K, A, r):  # Define logistic function
        self.funcName = "Logistic"
        return K / (1 + A * np.exp(-r * x))
    # Fit logistic function to data

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

class FitTrend():

    def __init__(self, data: pd.Series) -> None:
        self.name = data.name
        self.original_data = data

    def fitExpTrend(self):
        index = self.original_data.index.to_numpy()
        x = np.linspace(1,len(index),len(index)); y = self.original_data.to_numpy()

        fit = np.polyfit(x, np.log(y), 1)
        print('Exponential fit to: ',self.original_data.name, ', x, np.log(y), intercept, slope a,b = ',fit)
        a = fit[0]; b = fit[1]

        x = np.linspace(0,len(self.original_data-1),len(self.original_data))
        fit_y = []
        for ex in x:
            fit_y.append(np.exp(b+a*ex))
        fitY = pd.Series(fit_y,index=index,name=self.original_data.name+" exp_fit") 
        TrendDev = ((self.original_data - fitY)/fitY)*100; print('Dev from trend max, min: ',TrendDev.max(),TrendDev.min())
        self.fit = fitY
        fit_res = ((self.original_data - fitY)**2).sum(); print("Residual squared: ", fit_res)
        ss_tot = ((self.original_data - self.original_data.mean())**2).sum(); print("Total sum of squares: ", fit_res)
        r2 = round(1 - (fit_res / ss_tot),3); print("R squared value from fit: ",r2)
        self.PctDev = TrendDev; self.PctDev.rename('Percentage_dev_from_fit',inplace=True)
        self.Fit_Info = {"Fit function":"Exponential",
                    "gradient": a,
                    "intercept": b,
                    "R_Squared": r2}

    def FitData(self, FitFunc: str = "ExpLog"):  #Fit trend to data. 
        data = self.original_data.copy()
        func = FitFunction()
        x = np.linspace(1,len(data),len(data)); y = data.to_numpy(); yLog = np.log(y)
        f = func.functions[FitFunc][0]; funcName = FitFunc
        LogOrLin = func.functions[FitFunc][1]
        if funcName == "Exponential":
            self.fitExpTrend()
            return
        if LogOrLin == 'linear':
            try:
                popt, pcov = curve_fit(f,x,y)
                fit = f(x,*popt)
            except Exception as error:    
                print('Devo, fit failed bro.. error message: ',error,'\n',"Try running fit again with LogOrLin set to 'log'") 
                quit()   
        elif LogOrLin == 'log':
            try:
                popt, pcov = curve_fit(f,x,yLog)
                fit = np.exp(f(x,*popt))
            except Exception as error:    
                print('Devo, fit failed bro.. error message: ',error,'\n',"Try running fit again with LogOrLin set to 'linear'") 
                quit()                 
         
        Fit = pd.Series(fit,index=data.index,name=data.name+" "+funcName+" fit")   
        print('Trendline fitted to data: ',data.name,' ',funcName,' function used, optimized fitting parameters: ',popt)  
        self.fit = Fit
        fit_res = ((data - Fit)**2).sum(); print("Residual squared: ", fit_res)
        ss_tot = ((data - data.mean())**2).sum(); print("Total sum of squares: ", fit_res)
        r2 = round(1 - (fit_res / ss_tot),3); print("R squared value from fit: ",r2)
        TrendDev = ((data - Fit)/Fit)*100; print('Dev from trend max, min: ',TrendDev.max(),TrendDev.min())
        self.PctDev = TrendDev; self.PctDev.rename('Percentage_dev_from_fit',inplace=True)
        self.Fit_Info = {"Fit function":funcName,
                        "p_opt": popt,
                        "p_cov": pcov,
                        "R_Squared": r2}
        if funcName == "ExpLog":
            self.fit[0:round(0.02*len(self.fit))] = np.nan
            self.PctDev[0:round(0.02*len(self.PctDev))] = np.nan
        elif funcName == "Exp_Base10":
            print("Note: 'Exp_Base10 fit was not working last timme I checked. Use 'Exponential' instead.")    
    
    def StdDevBands(self, multiples:int, periods:int):
        stdDev = self.fit.rolling(window=periods).std()
        numstd_l = multiples/np.e
        self.std_u = self.fit + multiples*stdDev; self.std_u.rename('Upper std. dev. band',inplace=True)
        self.std_l = self.fit - numstd_l*stdDev; self.std_l.rename('Lower std. dev. band',inplace=True)

    def PCBands(self, PC_Offset:float):
        self.pcu = self.fit*((100+PC_Offset)/100); self.pcu.rename('Upper '+str(PC_Offset)+'% band',inplace=True)
        self.pcl = self.fit/((100+PC_Offset)/100); self.pcu.rename('Lower '+str(PC_Offset)+'% band',inplace=True)

    def ShowFit(self, yaxis: str = "linear", YLabel: str = "Price (USD)"):
        if self.fit is None:
            print('Run fitting funnction first before trying to plot the fit.')    
            return
        
        else:
            fig = plt.figure(figsize=(13,6.5), tight_layout=True)
            gs1 = GridSpec(1, 1, top = 0.95, bottom=0.07, left=0.08, right=0.92)
            ax1 = fig.add_subplot(gs1[0]); axb = ax1.twinx()
            title = self.fit.name + ", fit quality assessment chart."
            ax1.set_title(title,fontweight='bold')
            pct = self.PctDev.copy()

            if yaxis == 'log':
                ax1.set_yscale('log'); axb.set_yscale('log')
                lTicks, lTickLabs = Utilities.EqualSpacedTicks(self.original_data, numTicks=10, LogOrLin='log')
                pct += 100
                rTicks, rTickLabs = Utilities.EqualSpacedTicks(pct, numTicks=10, LogOrLin='log',LabOffset=-100,labSuffix="%")
                ax1.tick_params(axis='y',which='both',length=0,width=0,right=False,labelright=False,labelsize=0)  
                ax1.set_yticks(lTicks); ax1.set_yticklabels(lTickLabs)
                ax1.tick_params(axis='y',which='major',width=1,length=3,labelsize=8,left=True,labelleft=True)
                axb.tick_params(axis='y',which='both',length=0,width=0,right=False,labelright=False,labelsize=0) 
                axb.set_yticks(rTicks); axb.set_yticklabels(rTickLabs)
                axb.tick_params(axis='y',which='major',width=1,length=3,labelsize=8,right=True,labelright=True)

            ax1.plot(self.original_data, label = self.original_data.name, color = "black", lw = 2.5)
            ax1.plot(self.fit,label = self.fit.name, color = "blue", lw=1.75)
            axb.plot(pct, label = self.PctDev.name, color = "green", lw = 1.25)
            axb.set_ylabel('% deviation from fitted trend', fontsize = 10, fontweight = 'bold')
            ax1.set_ylabel(YLabel, fontsize = 10, fontweight = 'bold')

            ax1.legend(loc=2, fontsize = 'small'); axb.legend(loc=1, fontsize = 'small')
            ax1.grid(visible=True,axis='both',which='major',lw=0.75,ls=":",color='gray')
            ax1.grid(visible=True,axis='x',which='both',lw=0.75,ls=":",color='gray')
            ax1.minorticks_on()
            ax1.set_ylim((self.original_data.min()-0.05*self.original_data.min()),(self.original_data.max()+0.05*self.original_data.max()))
            printr2 = "R-squared value from fit: "+str(self.Fit_Info['R_Squared'])
            ax1.text(x=0.37, y = 0.97, s= printr2,horizontalalignment='left',verticalalignment='center', transform=ax1.transAxes )
            # axb.set_ylim(self.PctDev[round(0.25*len(self.PctDev)):len(self.PctDev)].min(),self.PctDev[round(0.25*len(self.PctDev)):len(self.PctDev)].max())

            for axis in ['top','bottom','left','right']:
                ax1.spines[axis].set_linewidth(1.5)
                
            return fig

if __name__ == '__main__':
    data = pd.read_excel('/Users/jamesbishop/Documents/Python/TempVenv/Plebs_Macro/Generic_Macro/SavedData/BTCUSD.xlsx')
    data.set_index(pd.DatetimeIndex(pd.DatetimeIndex(data['date']).date),inplace=True)
    data.drop('date',axis=1,inplace=True)
    StartDate = datetime.date(2011,1,1); start = pd.Timestamp(StartDate)
    data = data[start::]; data = pd.Series(data.squeeze(),name="BTC (USD)")
    print(data)
    fit = FitTrend(data)
    fit.FitData(FitFunc='Logistic')

    figure = fit.ShowFit(yaxis='log')
    plt.show()