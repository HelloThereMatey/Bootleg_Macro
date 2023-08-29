import numpy as np
import pandas as pd
import datetime
import tkinter as tk
import tkinter.font as tkfont
import operator
import sys
import os
import re
import json
import matplotlib.cm as cm
import matplotlib.pyplot as plt

def EqualSpacedTicks(data,numTicks,LogOrLin:str='linear',LabOffset=None,labPrefix:str=None,labSuffix:str=None,Ymin:float=None,Ymax:float=None):
    if type(data) == pd.DataFrame:
        data = pd.Series(data[data.columns[0]])

    if Ymin is not None:
        pass
    else:
        Ymin = np.nanmin(data)
    if Ymax is not None:
        pass
    else:    
        Ymax = np.nanmax(data)    #Major ticks custom right axis. 

    if LogOrLin == 'log':
        #print('Using log scale for series: ', data.name, Ymin, Ymax)
        Ticks = np.logspace(start = np.log10(Ymin), stop = np.log10(Ymax), num=numTicks, base=10); tickLabs = Ticks.copy()
    elif LogOrLin == 'linear':    
        #print('Using linear scale for series: ', data.name, Ymin, Ymax
        Ticks = np.linspace(start = Ymin, stop = Ymax, num=numTicks); tickLabs = Ticks.copy()
    else:
        print('Must specify whether you want linear "linear" ticks or log10 ticks "log".')    
        quit()
    if LabOffset is not None:
        tickLabs += LabOffset
    Ticks.round(decimals=1,out=Ticks); tickLabs.round(decimals=1,out=tickLabs)
    Ticks = np.ndarray.astype(Ticks,dtype=float,copy=False)
    tickLabs = np.ndarray.astype(tickLabs,dtype=float,copy=False)
    tickLabs = np.ndarray.astype(tickLabs,dtype=str,copy=False)
    Ticks = Ticks.tolist(); tickLabs = tickLabs.tolist()
    if labPrefix is not None:
        tickLabs = [labPrefix+char for char in tickLabs]
    if labSuffix is not None:
        tickLabs = [char+labSuffix for char in tickLabs]
    return Ticks, tickLabs

#def CAGR(series:pd.Series,period:int):     ##Calculates the compounded annual growth rate of the series for period. 

def MonthPeriodAnnGrowth(data:pd.Series,months:int): ###### Calculate the X month annualized growth in a series e.g 3M annualized %. 
    freq = pd.infer_freq(data.index);           #months is the number of months to calculate the annualized % change over.  
    print('Calculating the',months,'month annualized % change for the series: ',data.name)
    print('Frequency of input time series, ',data.name,':',freq)    
    split = freq.split('-')
    MonthlyList = ['M','SM','BM','CBM','MS','SMS','BMS','CBMS']
    QuarterList = ['Q','BQ','QS','BQS']
    AnnualList = ['A', 'Y','BA', 'BY', 'AS', 'YS','BAS', 'BYS']

    if split[0] == 'B' or split[0] == 'C':
        print('Resampling business day frequency to daily....')
        data = data.resample('D').mean()
        data.fillna(method='ffill',inplace=True)
        freq = pd.infer_freq(data.index); split = freq.split('-')
        print('Frequency after resample:, ',freq)
    elif split[0] == 'H' or split[0] == 'BH':
        print('Resampling hourly frequency to daily....')
        data = data.resample('D').mean()
        freq = pd.infer_freq(data.index); split = freq.split('-')
        print('Frequency after resample:, ',freq)
    DeltaPC = data.pct_change(); DeltaPC *= 100   #Seems that pct_change give 0 - 1 not 0 - 100 %. 
    print("DeltaPC: ",DeltaPC)
    
    if split[0] == 'D':
        print('Daily frequency period.')
        period = months*30; print('Ann. period = ',period,"days.")
        MA = DeltaPC.rolling(period).mean()
        print(MA)
        MA *= 365.25/period
        print(MA)
    elif split[0] == 'W':
        print('Weekly frequency period.')
        period = months*4
        MA = DeltaPC.rolling(period).mean()
        MA *= 52.18/period
    elif any(split[0] == monthly for monthly in MonthlyList):
        print('Monthly frequency period.')
        period = months
        MA = DeltaPC.rolling(period).mean()
        MA *= 12/period
    elif any(split[0] == quarter for quarter in QuarterList):  
        print('Quarter frequency period.')  
        print(np.mod(months,3))
        if months < 3 or np.mod(months,3) != 0:
            print('You have quarterly data, months input must be a multiple of 3.')
            quit()
        else: 
            period = int(months/3); print(period)
            MA = DeltaPC.rolling(period).mean()
            MA *= 4/period
    elif any(split[0] == year for year in AnnualList):    
        print('Yearly frequency period.')
        if months < 12:
            print('You have yearly data, so cannot calculate an annualized rate for < 12 months.')
            quit()
        else:    
            period = int(months/12)
            MA = DeltaPC.rolling(period).mean()
    else:
        print('What is the frequency of the data series, ',data.name,'. Get that sorted first. ')
        quit()    
    return MA

def MonthPeriodAnnGrowth2(data,months:int): ###### Calculate the X month annualized growth in a series e.g 3M annualized %. 
    if type(data) == pd.DataFrame:
        data = pd.DataFrame(data)
    else:
        data = pd.Series(data)    
    freq = pd.infer_freq(data.index);           #months is the number of months to calculate the annualized % change over.  
   
    if freq is None:
        print('Could not infer frequency of series, resampling to daily...')
        data = data.resample('D').mean(); data.fillna(method='ffill', inplace=True)
        freq = 'D'

    print('Calculating the',months,'month annualized % change for the series.')
    print('Frequency of input time series:',freq)    
    if '-' in freq:
        split = freq.split('-')
    else:
        split = freq    
    MonthlyList = ['M','SM','BM','CBM','MS','SMS','BMS','CBMS']
    QuarterList = ['Q','BQ','QS','BQS']
    AnnualList = ['A', 'Y','BA', 'BY', 'AS', 'YS','BAS', 'BYS']

    if split[0] == 'B' or split[0] == 'C':
        print('Resampling business day frequency to daily....')
        data = data.resample('D').mean()
        data.fillna(method='ffill',inplace=True)
        freq = pd.infer_freq(data.index); split = freq.split('-')
        print('Frequency after resample:, ',freq)
    elif split[0] == 'H' or split[0] == 'BH':
        print('Resampling hourly frequency to daily....')
        data = data.resample('D').mean()
        freq = pd.infer_freq(data.index); split = freq.split('-')
        print('Frequency after resample:, ',freq)
    
    if split[0] == 'D':
        print('Daily frequency period.'); d_freq = 'D'
        period = months*30.416; print('Ann. period = ',period,"days.")
    elif split[0] == 'W':
        print('Weekly frequency period.'); d_freq = 'W'
        period = months*4 ; print('Ann. period = ',period,"weeks.")
    elif any(split[0] == monthly for monthly in MonthlyList):
        print('Monthly frequency period.'); d_freq = 'M'
        period = months ; print('Ann. period = ',period,"months.")
    elif any(split[0] == quarter for quarter in QuarterList):  
        print('Quarter frequency period.'); d_freq = 'Q'
        print(np.mod(months,3));  print('Ann. period = ',period,"quarters.")
        if months < 3 or np.mod(months,3) != 0:
            print('You have quarterly data, months input must be a multiple of 3.')
            quit()
        else: 
            period = int(months/3); print(period)
    elif any(split[0] == year for year in AnnualList):    
        print('Yearly frequency period.'); d_freq = 'Y'
        if months < 12:
            print('You have yearly data, so cannot calculate an annualized rate for < 12 months.')
            quit()
        else:    
            period = int(months/12)
        print('Ann. period = ',period,"years.")    
    else:
        print('What is the frequency of the data series, ','. Get that sorted first. ')
        quit()
    print(round(period),d_freq)
    AnnPC = data.pct_change(periods=round(period))
    AnnPC *= 100; print(AnnPC) 
   
    return AnnPC

class StringMathOp:
    def __init__(self, data: pd.DataFrame, components: list, indexes: list):
        self.operators = {
            '/': operator.truediv,
            '*': operator.mul,
            '+': operator.add,
            '-': operator.sub,
        }
        self.Data = data
        self.components = components
        self.indexes = indexes
        self.colMap = {}
        for i in range(len(self.indexes)):
            self.colMap[self.indexes[i]] = self.components[i]
        print(self.colMap)   
        self.counter = 0 

    def op(self, MathOpStr:str) -> pd.Series:
        alpha = "abcdefghijklmnopqrstuvwxyz".upper()
        for p in self.operators.keys():
            x = 0
            while x < len(MathOpStr)-1 and any(p in str(el) for el in MathOpStr):
                if p in str(MathOpStr[x]):
                    print(f"Operator: ({MathOpStr[x]}): {type(MathOpStr[x])}")
                    print(f"Left operand ({MathOpStr[x-1]}): {type(MathOpStr[x-1])}")
                    print(f"Right operand ({MathOpStr[x+1]}): {type(MathOpStr[x+1])}")
                    print('Running operation: ', self.operators.get(p))
                    replacer = self.operators.get(p)(MathOpStr[x-1] , MathOpStr[x+1])
                    replacer = pd.Series(replacer, name="RES_"+alpha[self.counter])
                    replacer.reset_index(inplace=True,drop=True)
                    print("Replacing: ",MathOpStr[x-1], ' with: ',replacer)
                    MathOpStr[x-1] = replacer
                    print("Will delete: ",MathOpStr[x:x+2])
                    del MathOpStr[x:x+2]
                else:
                    x += 1; self.counter += 1  
        return MathOpStr[0]
    
    def func(self, MathOpStr:str) -> pd.Series:
        df = self.Data
        results = {}
        alpha = "abcdefghijklmnopqrstuvwxyz".upper()

        while '(' in MathOpStr:
            start = MathOpStr.rfind('(')
            end = MathOpStr.find(')', start)
            result = self.func(MathOpStr[start+1:end])
            key = 'RES_' + alpha[self.counter]
            results[key] = result
            MathOpStr = MathOpStr[:start] + key + MathOpStr[end+1:]
            self.counter += 1

        d = []
        tokens = re.split('(\W)', MathOpStr)
        for i in range(len(tokens)):
            if tokens[i]:
                if tokens[i] in self.operators:
                    d.append(tokens[i])
                    if i == len(tokens) - 1 or tokens[i+1] in self.operators:
                        raise ValueError("Operator must be followed by an operand")
                elif tokens[i] in results:
                    result = results[tokens[i]]
                    d.append(result)
                elif tokens[i].isdigit():
                    column_index = int(tokens[i])
                    column = df[self.colMap[column_index]].reset_index(drop=True)
                    d.append(column)
        
        d = self.op(d)
        d = pd.Series(d.to_list(), index = df.index)
        print(d)
        self.ComputedIndex = d.copy()
        return d

def Colors(map:str, num_colors:int):
    # Create the colormap
    cm = plt.get_cmap(map)  # You can choose another colormap here
    # Create the list of colors
    colors = [cm(1.*i/num_colors) for i in range(num_colors)]    
    return colors


def GetAxesDims(fig: plt.Figure, ax: plt.Axes) -> dict:
    print(fig, ax)
    # Get the Bbox of the axes in display coordinates
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    x_margin, y_margin = ax.margins()
    print(f"x margin: {x_margin*100}%")
    print(f"y margin: {y_margin*100}%")

    width_inches_T = bbox.width
    height_inches_T = bbox.height
    width_inches = width_inches_T-x_margin*width_inches_T
    height_inches = height_inches_T-y_margin*height_inches_T
    # Width and height in points (1 inch = 72 points)
    width_points = width_inches * 72
    width_points_T = width_inches_T * 72
    height_points = height_inches * 72
    height_points_T = height_inches_T * 72
    # Width and height in centimeters (1 inch = 2.54 cm)
    width_cm = width_inches * 2.54
    width_cm_T = width_inches_T * 2.54
    height_cm = height_inches * 2.54
    height_cm_T = height_inches_T * 2.54

    dims = {'width_inches_total': width_inches_T,
            'width_inches': width_inches,
            'width_points_total': width_points_T,
            'width_points': width_points,
            'width_cm_total': width_cm_T,
            'width_cm': width_cm,
            'height_inches_total': height_inches_T,
            'height_inches': height_inches,
            'height_points_total': height_points_T,
            'height_points': height_points,
            'height_cm_total': height_cm_T,
            'height_cm': height_cm
    }
    return dims

def SecondDerivative(input: pd.Series, periods:int) -> pd.Series:
    FirstDer = input.pct_change(periods=periods)*100
    FirstDer += 100
    SecDer = FirstDer.pct_change(periods=periods)*100
    return SecDer

def RoCYoY(input: pd.Series) -> pd.Series:
    inPut_YoY = MonthPeriodAnnGrowth2(input,12) + 100 
    RocYoY = inPut_YoY.pct_change(periods=1)*100
    return RocYoY

def RoCofRoC(input: pd.Series,periods:int = 1 ) -> pd.Series:
    roc = input.diff(periods=periods)
    return roc.diff(periods=periods)

class TkinterSizingVars():

    def __init__(self) -> None:
        self.root = tk.Tk()
        #self.allCharsStr = "abcdefghijklmnopqrstuvwxyz " !@#$%^&*=-,.|()?+[]\/~1234567890 ><"";
        self.allCharsStr = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.FDel = os.path.sep
        
    def SetScreenInfoFile(self):
        ###### Determine what OS this is running on and get appropriate path delimiter. #########
        print("Operating system: ",sys.platform, "Path separator character: ", self.FDel)
        if sys.platform == 'win32':
            username = os.environ['USERNAME']
        else:
            username = os.environ['USER']

        self.ScreenData = {'OS': sys.platform,
                    "USER": username}

        # Get screen size
        self.root.update_idletasks()
        self.root.attributes('-fullscreen', True)
        self.root.state('iconic')
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        print(f'Screen size: {screen_width}x{screen_height}')
        self.ScreenData['Screen_width'] = screen_width
        self.ScreenData['Screen_height'] = screen_height

        px = (1/plt.rcParams['figure.dpi'])*25.4  ##Pixel size in mm. 
        self.ScreenData['Pixel size (mm)'] = px
        self.ScreenData['Screen width (cm)'] = (screen_width*px)/10
        self.ScreenData['Screen height (cm)'] = (screen_height*px)/10

        # Get character size
        label = tk.Label(self.root, text="M")
        label.pack()
        self.root.update_idletasks()
        char_width = label.winfo_width()
        char_height = label.winfo_height()
        
        print(f'Character size: {char_width}x{char_height}')
        self.ScreenData['Char_width'] = char_width
        self.ScreenData['Char_height'] = char_height
        self.ScreenData['Def_font'] =  self.get_def_FontInfo()
   
        self.root.destroy()

    def get_def_FontInfo(self):
        print("Measuring default font... all characters: ","\n", self.allCharsStr,len(self.allCharsStr))
        default_font = tkfont.nametofont("TkDefaultFont")
        lengthAll = default_font.measure(self.allCharsStr)
        defFontInfo = {'name': default_font.name ,
                    'family': default_font.actual('family'),
                    'size': default_font.actual('size'),
                    #'char_width (pixels)': default_font.measure('C'),
                    'char_width (pixels)': round(lengthAll/len(self.allCharsStr)),
                    'char_height (pixels)': default_font.metrics("linespace")}
        return defFontInfo
    
    def ExportVars(self,folder:str):
        filePath = folder+self.FDel+"ScreenData.json"
        with open(filePath, 'w') as f:
            json.dump(self.ScreenData, f, indent=4)

