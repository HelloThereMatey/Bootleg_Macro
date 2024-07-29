import numpy as np
import pandas as pd
import datetime
import tkinter as tk
from tkinter import filedialog
import tkinter.font as tkfont
import customtkinter as ctk
import operator
import sys
import os
import re
import json
from typing import Union, Tuple, List
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from openpyxl import load_workbook
import sys

wd = os.path.dirname(__file__); parent = os.path.dirname(wd)
fdel = os.path.sep
sys.path.append(parent)

from MacroBackend import Charting

def qd_corr(series1: pd.Series, series2: pd.Series) -> float:
    """
    Calculates the correlation between two pandas Series using the Quant-Dare method.

    :param series1: The first pandas Series. When calculating rolling correlations, this will be a slice over the window of the series. 
    :param series2: The second pandas Series. When calculating rolling correlations, this will be a slice over the window of the series.

    :return: The Quant-Dare correlation between the two Series.
    """

    # Calculate the sum of the products of the deviations from the mean
    sum_products = (series1 * series2).sum()

    # Calculate the sum of the squares of the deviations from the mean
    sum_squares1 = (series1 ** 2).sum()
    sum_squares2 = (series2 ** 2).sum()

    # Calculate the Quandt-Dichotomous correlation
    qd_corr = sum_products / np.sqrt(sum_squares1 * sum_squares2)

    return qd_corr

def rolling_qd(series1: pd.Series, series2: pd.Series, window: int = 1) -> pd.Series:
    """
    Calculates the rolling Quant-Dare correlation between two pandas Series.

    :param series1: The first pandas Series.
    :param series2: The second pandas Series.
    :param window: The size of the rolling window.

    :return: A pandas Series containing the rolling Quant-Dare correlation values.
    """

    if len(series1) != len(series2):
        raise ValueError("Series must have the same length")
    
    rolling_corrs = []
    for i in range(window - 1, len(series1)):
        window_series1 = series1[i - (window - 1):i + 1]
        window_series2 = series2[i - (window - 1):i + 1]
        corr = qd_corr(window_series1, window_series2)
        rolling_corrs.append(corr)
    
    return pd.Series(rolling_corrs, index=series1.index[window - 1:])

def basic_load_dialog(initialdir: str = wd, title: str ='Choose your file...', 
                    filetypes: tuple = (('Image files', '*.png *.bmp *.jpg *.jpeg *.pdf *.svg *.tiff *.tif'),
                                                  ('All files', '*.*'))):
    window = tk.Tk()
    window.withdraw()
    file_path = filedialog.askopenfilename(filetypes=filetypes, initialdir=initialdir, parent=window, title=title)
    window.withdraw()  
    return file_path

def append_to_column(workbook_path, sheet_name:str = 'Sheet1', column:str = 'A', data_list: list = []):
    """
    Appends a list of strings to a specified column in an Excel sheet using openpyxl.

    :param workbook_path: Path to the Excel workbook.
    :param sheet_name: Name of the sheet to append data to.
    :param column: Column letter to append data to.
    :param data_list: List of strings to append.
    """
    # Load the workbook and select the sheet
    workbook = load_workbook(workbook_path)
    sheet = workbook[sheet_name]

    # Find the first empty row in the specified column
    row = 1
    while sheet[f"{column}{row}"].value is not None:
        row += 1

    # Append data to the column
    for item in data_list:
        sheet[f"{column}{row}"].value = item
        row += 1

    # Save the workbook
    workbook.save(workbook_path)

def count_zeros_after_decimal(median_value: float) -> int:
    if median_value < 1 and median_value > 0:
        str_val = str(median_value).split('.')[1] # Convert to string and split by decimal point
        return len(str_val) - len(str_val.lstrip('0')) + 1
    else:
        return 1

def EqualSpacedTicks(numTicks, data: Union[pd.Series, pd.DataFrame] = None,
        LogOrLin:str='linear',LabOffset=None,labPrefix:str=None,labSuffix:str=None,Ymin:float=None,Ymax:float=None):
    print("Equal spaced ticks fucntion, ", Ymax, Ymin)
     
    if data is not None:
        print("Data is not None.")
        if Ymin is None:
            print('No Ymin specified, using minimum of input data.')
            if isinstance(data, pd.DataFrame):
                Ymin = data.min().min()
            else:
                Ymin = data.min()    
        if Ymax is None:  
            print('No Ymax specified, using maximum of input data.')
            if isinstance(data, pd.DataFrame):
                Ymax = data.max().max()    #Major ticks custom right axis. 
            else:
                Ymax = data.max()

    decimals = count_zeros_after_decimal(median_value = (Ymax - Ymin)/2)

    if LogOrLin == 'log':
        Ticks = np.logspace(start = np.log10(Ymin), stop = np.log10(Ymax), num=numTicks, base=10); tickLabs = Ticks.copy()
    elif LogOrLin == 'linear':    
        Ticks = np.linspace(start = Ymin, stop = Ymax, num=numTicks); tickLabs = Ticks.copy()
    else:
        print('Must specify whether you want linear "linear" ticks or log10 ticks "log".')    
        quit()
    if LabOffset is not None:
        tickLabs += LabOffset
    #Ticks.round(decimals=decimals,out=Ticks); 
    tickLabs.round(decimals=decimals,out=tickLabs)
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
    MonthlyList = ['M','SM','BM','CBM','MS','SMS','BMS','CBMS', 'WOM']
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
    MonthlyList = ['M','SM','BM','CBM','MS','SMS','BMS','CBMS', 'WOM']
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
        print(np.mod(months,3))
        if months < 3 or np.mod(months,3) != 0:
            print('You have quarterly data, months input must be a multiple of 3.')
            quit()
        else: 
            period = int(months/3); print(period)
        print('Ann. period = ',period,"quarters.")    
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

    def op(self, MathOpStr: list) -> pd.Series:
        for p in self.operators.keys():
            x = 0
            while x < len(MathOpStr)-1 and any(p in el for el in str(MathOpStr)):
                if re.search(f"^\{p}", str(MathOpStr[x])) and type(MathOpStr[x]) == str:
                    print(f"Operator: ({MathOpStr[x]}): {type(MathOpStr[x])}")
                    print(f"Left operand ({MathOpStr[x-1].name}): {type(MathOpStr[x-1])}")
                    print(f"Right operand ({MathOpStr[x+1].name}): {type(MathOpStr[x+1])}")
                    print('Running operation: ', self.operators.get(p))
                    replacer = self.operators.get(p)(MathOpStr[x-1] , MathOpStr[x+1])
                    replacer = pd.Series(replacer, name="RES_"+str(self.counter))
                    print("Result: ",replacer.name)
                    MathOpStr[x-1] = replacer
                    del MathOpStr[x:x+2]
                x += 1     
        return MathOpStr[0]
    
    def func(self, MathOpStr:str) -> pd.Series:
        print('MathOpStr @ start of func: ',MathOpStr,', iteration: ', self.counter)
        df = self.Data
        results = {}; d = []

        while '(' in MathOpStr:
            start = MathOpStr.rfind('(')
            end = MathOpStr.find(')', start)
            result = self.func(MathOpStr[start+1:end])
            key = 'RES_' + str(self.counter)
            results[key] = result
            MathOpStr = MathOpStr[:start] + key + MathOpStr[end+1:]
            self.counter += 1

        tokens = re.split(r'(\W)', MathOpStr)
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
                    column = df[self.colMap[column_index]]
                    d.append(column)
        result = self.op(d); print("Finished op run. ")
        result = pd.Series(result.to_list(), index = df.index, name = result.name)
        
        self.ComputedIndex = result.copy()
        return result


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

def GetClosestDateInIndex(df_index: Union[pd.DataFrame, pd.Series, pd.DatetimeIndex], searchDate: str = "2012-01-01"):
    ## searchDate should bee in "YYYY-MM-DD" format. 
    if isinstance(df_index, pd.DatetimeIndex):
        index = df_index
    elif isinstance(df_index, pd.DataFrame) or isinstance(df_index, pd.Series):
        index = df_index.index
    else:
        print('Input dataframe/series or index must have/be a datetime index.')
        return None

    # Convert the Datestring to a Timestamp object
    date_ts = pd.Timestamp(searchDate)
    # Find the closest date in the index
    closest_date = min(index, key=lambda x: abs(x - date_ts))
    index = index.get_loc(closest_date)
    return closest_date, index

import pandas as pd
from typing import Union

def find_closest_val(series: pd.Series, target_value: Union[int, float]):
    """
    Finds the value in a pandas Series that is closest to a given target value.

    Parameters:
        series (pd.Series): The input pandas Series to search for the closest value.
        target_value (Union[int, float]): The target value to find the closest match for.

    Returns:
        tuple: A tuple containing the closest value and its corresponding index in the series.

    Example:
        series = pd.Series([1.2, 2.5, 3.8, 4.1, 5.3])
        target_value = 3.6
        closest_value, closest_index = find_closest_val(series, target_value)
        print(closest_value)     # Output: 3.8
        print(closest_index)     # Output: 2
    """
    # Calculate the absolute differences between each value in the series and the target value
    differences = series.sub(target_value).abs()

    # Find the index of the value with the smallest difference
    idx_closest = differences.idxmin()

    # Retrieve the closest value using the index
    value_closest = series.loc[idx_closest]

    # Return the closest value and its index
    return value_closest, idx_closest

def Percent_OfBaseVal_Series(series: pd.Series, ZeroDate: str = None, median: bool = False, mean: bool = False, start: bool = False) -> pd.Series:
    """
    Calculates the percentage change of values in a pandas Series relative to a base value.

    Parameters:
    - series (pd.Series): The input pandas Series containing the values.
    - ZeroDate (str, optional): The date to consider as the base date. If not provided, a base index will be used instead.
    - median (bool, optional): Flag indicating whether to use the median of the series as the base value.
    - mean (bool, optional): Flag indicating whether to use the mean of the series as the base value.
    - start (bool, optional): Flag indicating whether to use the first value of the series as the base value.

    Returns:
    - percentage (pd.Series): A new pandas Series with the calculated percentage change relative to the base value.

    Note:
    - The base value is determined either by the specified ZeroDate, or by the median, mean, or start of the series.
    - If ZeroDate is provided, the closest date in the series' index will be used as the base index.
    - If both median and mean flags are True, the median will take precedence over the mean.
    - If none of the base options (ZeroDate, median, mean, start) are specified, the first value of the series will be used as the base value.
    """
    # Implementation of the function...
    if ZeroDate is not None:
        ZeroIndex = GetClosestDateInIndex(series, searchDate = ZeroDate)[1]
        print(series.name, "base date: ",ZeroDate, ZeroIndex)
    if median:
        val = series.median()   
        print(series.name, "Median: ",val)
        findIndex = find_closest_val(series, val); print(findIndex)
        index = series.index.get_loc(findIndex[1])
        ZeroIndex = index
    if mean:
        val = series.mean()   
        print(series.name, "mean: ",val)
        findIndex = find_closest_val(series, val); print(findIndex)
        index = series.index.get_loc(findIndex[1])
        ZeroIndex = index
    if start:
        ZeroIndex = 0
    
    baseVal = series.iloc[ZeroIndex]; print(series.name, baseVal)
    percentage = (series/baseVal)*100 #- 100
    return percentage

def get_global_min_max(ax: plt.axes):
    min_vals = []
    max_vals = []

    # Iterate over all lines on the axes
    for line in ax.get_lines():
        y_data = line.get_ydata()
        min_vals.append(np.min(y_data))
        max_vals.append(np.max(y_data))

    global_min = min(min_vals)
    global_max = max(max_vals)

    return global_min, global_max

class TkinterSizingVars():

    def __init__(self) -> None:
        self.root = tk.Tk()
        #self.allCharsStr = "abcdefghijklmnopqrstuvwxyz " !@#$%^&*=-,.|()?+[]\/~1234567890 ><"";
        self.allCharsStr = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        
    def SetScreenInfoFile(self):
        ###### Determine what OS this is running on and get appropriate path delimiter. #########
        print("Operating system: ",sys.platform, "Path separator character: ", fdel)
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
    
    def ExportVars(self,folder = wd + fdel + 'SystemInfo'):
        filePath = folder+fdel+"ScreenData.json"
        with open(filePath, 'w') as f:
            json.dump(self.ScreenData, f, indent=4)


import tkinter as tk
import tkinter.font as tkfont

class HoverInfo(tk.Toplevel):
    def __init__(self, parent, text, command=None):
        super().__init__(parent, bg='white', padx=1, pady=1)
        self.transient(parent)
        self.overrideredirect(True)
        self.text = text
        self._com = command
        self.label = tk.Label(self, text=text, justify=tk.LEFT, background='#ffffe0', relief=tk.SOLID, borderwidth=1, font=tkfont.Font(family='Arial', size=10))
        self.label.pack(ipadx=1, ipady=1)
        self._displayed = False
        self.parent = parent
        self.parent.bind("<Enter>", self.display)
        self.parent.bind("<Leave>", self.remove)

        # Bind the Esc key to the remove method
        self.bind_all("<Return>", self.remove)

        # Hide the tooltip initially
        self.withdraw()

    def display(self, event):
        if not self._displayed:
            self._displayed = True
            x, y, cx, cy = self.parent.bbox("anchor")
            x += self.parent.winfo_rootx() + 25
            y += self.parent.winfo_rooty() + 25
            self.geometry(f'+{x}+{y}')
            self.deiconify()
        if self._com is not None:
            self.parent.bind("<Return>", self.click)

    def remove(self, event=None):
        if self._displayed:
            self._displayed = False
            self.withdraw()
        if self._com is not None:
            self.parent.unbind("<Return>")
        self.withdraw()    

    def click(self, event):
        if self._com:
            self._com()

    
class InfoWindow:
    def __init__(self, parent, title, info_text):
        self.parent = parent
        self.title = title
        self.info_text = info_text
        self.window = None

    def open(self):
        if self.window is not None:
            return  # Prevent opening multiple windows

        self.window = tk.Toplevel(self.parent)
        self.window.title(self.title)
        #self.window.geometry("300x200")  # Adjust the size as needed

        text = tk.Text(self.window, wrap='word', font = tkfont.nametofont("TkDefaultFont"))
        text.insert('1.0', self.info_text)
        text.config(state='disabled', bg=self.window.cget('bg'))  # Making the Text widget read-only
        text.pack(expand=True, fill='both', padx=10, pady=10)

        close_button = tk.Button(self.window, text="Close", command=self.close)
        close_button.pack(pady=5)

    def close(self):
        self.window.destroy()
        self.window = None

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None

    def show_tooltip(self):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()  

def create_tooltip(widget, text):
    tooltip = Tooltip(widget, text)
    widget.bind("<Enter>", lambda e: tooltip.show_tooltip())
    widget.bind("<Leave>", lambda e: tooltip.hide_tooltip())

def Search_df(df:Union[pd.DataFrame, pd.Series], searchTerm:str):
    matches = []; match_indices = []; match_col = []; i = 0
    matchDF = pd.DataFrame()
    search_regex = re.compile(searchTerm.replace('*', '.*'), re.IGNORECASE)
    for col in df.columns:
        i = 0
        for s in df[col]:
            if search_regex.search(s):
                matches.append(s)
                match_indices.append(i)
                match_col.append(col)
                matchRow = df.iloc[[i]]
                matchDF = pd.concat([matchDF,matchRow],axis=0)
            i += 1   
    return matches, match_indices, match_col, matchDF

def Search_DF(df: Union[pd.DataFrame, pd.Series], searchTerm: str):
    # Split the search term by comma if any
    searchTerms = []
    if re.search(".*,.*",searchTerm):
        searchTerms.extend(searchTerm.split(','))
    else:
        searchTerms.append(searchTerm) 

    # Create list of compiled regular expressions
    search_regexes = [term.strip().replace('*', '.*') for term in searchTerms]
    print("Original search terms list: ", search_regexes)

    def innerSearch(df: Union[pd.DataFrame, pd.Series], search_regexs):
        matches = []; match_indices = []; match_col = []; matchDF = pd.DataFrame()

        if not search_regexs:
            return df
        else:
            for col in df.columns:
                i = 0
                for s in df[col]:
                    if re.search(re.escape(search_regexes[0]), str(s), flags = re.IGNORECASE):
                        matches.append(str(s))
                        match_indices.append(i)
                        match_col.append(col)
                        matchRow = df.iloc[[i]]
                        matchDF = pd.concat([matchDF,matchRow],axis=0)
                    i += 1   
            if len(matchDF.columns) == 1:
                matchDF = pd.Series(matchDF.squeeze())     
            search_regexs.pop(0)
        return innerSearch(matchDF, search_regexs)
    
    finalMatchDF = innerSearch(df, search_regexes)
    return finalMatchDF

def CheckIndexDifference(series1:Union[pd.DataFrame, pd.Series], series2:Union[pd.DataFrame, pd.Series]):
    diffs = (series1.index.difference(series2.index), series2.index.difference(series1.index))
    differences = False
    for diff in diffs:
        if len(diff) > 0:
            differences = True
            return differences, diff
        else:
            pass
    return differences

class freqDetermination(object):
    def __init__(self, series: pd.Series, p_in_d_mult = 1):
        self.series = series
        self.freq = pd.infer_freq(self.series.index)
        self.periods_in_day = None
        self.freq_str = None
        self.multiplier = p_in_d_mult
        self.frequency = None

        self.frequency_dict = {
            "Nanosecondly": ['N'],
            "Microsecondly": ['U', 'us'],
            "Millisecondly": ['L', 'ms'],
            "Secondly": ['S'],
            "Minutely": ['T', 'min'],
            "Hourly": ['BH', 'CBH', 'H'],
            "Daily": ['D', 'B', 'C'],
            "Weekly": ['W'],
            "Monthly": ['WOM', 'LWOM', 'M', 'ME', 'MS', 'BM', 'BMS', 'CBM', 'CBMS', 'SM', 'SMS'],
            "Quarterly": ['Q', 'QS', 'BQ', 'BQS', 'REQ'],
            "Yearly": ['A', 'AS', 'BYS', 'BA', 'BAS', 'RE', 'YE']}
        self.freq_list = pd.Series(list(self.frequency_dict.keys()))

        self.periods_in_day = {
            "Nanosecondly": 1000000000*60*60*24,
            "Microsecondly": 1000000*60*60*24,
            "Millisecondly": 1000*60*60*24,
            "Secondly": 60*60*24,
            "Minutely": 24*60,
            "Hourly": 24,
            "Daily": 1,
            "Weekly": 1/7,
            "Monthly": 1/30.4375,
            "Quarterly": 1/91.3125,
            "Yearly": 1/365.25}
        
        self.resample_map = {
            "Nanosecondly": 'N',
            "Microsecondly": 'U',
            "Millisecondly": 'L',
            "Secondly": 'S',
            "Minutely": 'T',
            "Hourly": 'H',
            "Daily": 'D',
            "Weekly": 'W',
            "Monthly": "M",
            "Quarterly": 'Q',
            "Yearly": 'A'}

    def DetermineSeries_Frequency(self):

        if isinstance(self.series, pd.DataFrame):
            self.series = self.series[self.series.columns[0]]
        
        print('Frequency determination function for series: ', self.series.name, ' frequency: ', self.freq)
        if self.freq is not None and len(self.freq.split("-")) > 1:
            self.freq = self.freq.split("-")[0]
        
        if self.freq is None:
            print("Couldn't discern frequency in the regular manner, trying manual process....")
            avDelta = manual_frequency(self.series)
            print('Looks like average index timedelta is: ', avDelta[1],', resampling series to that frequency.')
            self.freq = avDelta[1]
            self.series = avDelta[0]
        else:
            match = re.match(r'(\d+)([A-Za-z]+)', self.freq)
            if match:
                matches = match.groups()
                self.multiplier = int(matches[0]); self.freq = matches[1]
    
        self.frequency = None
        for freqName in self.frequency_dict.keys():
            if self.freq in self.frequency_dict[freqName]:
                self.frequency = freqName
            elif self.freq.split('-')[0] == 'W':
                self.frequency = 'Weekly'
        if self.frequency is None:
            print('Could not match the frequency for input series, ', self.series.name,' reported frequency is: ', self.freq,\
                  ", setting self.frequency to that...")    
            self.frequency = self.freq
        
        if self.freq is None:
            self.freq = self.resample_map[self.frequency]
        self.per_in_d = self.periods_in_day[self.frequency]/ self.multiplier

def manual_frequency(series: pd.Series, threshold_multiplier=2.25):
    daysInPeriod = {'1H': 1/24, '4H': 1/6, "D": 1, 'W': 7, 'M': 30, 'Q': 90}
    
    if not isinstance(series.index, pd.DatetimeIndex):
        print('Series must have a datetime index for frequency determination. Exiting...')
        return None
    
    # Calculate timedelta in days between each point
    deltas = series.index.to_series().diff().dt.total_seconds() / (3600 * 24)  # Convert to days
    deltas = deltas.dropna()  # Drop the first NaN value

    # Identify the typical delta (we use median to avoid extreme values)
    typical_delta = deltas.median()

    # Filter out deltas that are significantly larger than the typical delta
    filtered_deltas = deltas[deltas <= typical_delta * threshold_multiplier]

    # Calculate the average of the filtered deltas
    average = filtered_deltas.mean()

    # Find the period whose number of days is closest to the average timedelta
    closest_period = min(daysInPeriod, key=lambda p: abs(daysInPeriod[p] - average))
    
    resampled_series = series.resample(closest_period).ffill()  # Replace .mean() with an appropriate aggregation function if needed
    return resampled_series, closest_period

 # Create a custom legend handle for the red dashed lines
def add_line_to_legend(ax: plt.Axes, label: str, color: str = "r", linestyle: str = "--", lw: float = 1.0,\
                        fontsize: str = "small", bbox_to_anchor: tuple = (1, 1)):
    line_handle = Line2D([0], [0], color=color, linestyle=linestyle, lw=1, label=label)
    handles, labels = ax.get_legend_handles_labels()
    handles_combined = handles + [line_handle]
    labels_combined = labels + [label]
    ax.legend(handles=handles_combined, labels=labels_combined, fontsize = fontsize, bbox_to_anchor=bbox_to_anchor)
    return ax

def ensure_series(input_data):
    if isinstance(input_data, pd.DataFrame):
        # Convert the first column of the DataFrame to a Series
        return input_data[input_data.columns[0]]
    elif isinstance(input_data, pd.Series):
        # It's already a Series, return as is
        return input_data
    else:
        # Raise an error if the input is neither a DataFrame nor a Series
        raise ValueError('Input must be a pandas Series or DataFrame.')

def match_series_lengths(series1: pd.Series, series2: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Ensure two pandas Series are of equal length by trimming the longer series.
    If series have different frequencies, this might lead to data loss.
    Returns the modified series.
    """
    # Find the common date range
    start_date = max(series1.index[0], series2.index[0])
    end_date = min(series1.index[-1], series2.index[-1])
    
    # Trim both series to the common date range
    series1_trimmed = series1.loc[start_date:end_date]
    series2_trimmed = series2.loc[start_date:end_date]

    return series1_trimmed, series2_trimmed

class Pair_stats(object):
    """"
    Class to calculate stats between two series for a number of different window lengths. 
    Stats such as correlation.
    Determines frequency and downsamples a series to match the other if necessary..
    
    Parameters (__init__):
    - series1 (pd.Series): The first input series.
    - series2 (pd.Series): The second input series.
    - windows (list): A list of window lengths for which to calculate the rolling correlation.

    Key Attributes:
    - self (pd.DataFrame inherited): A DataFrame containing the original series and their log and pcercent returns, as well as the rolling correlations.
    - This is just a dataframe but it has a self.name attribute. 
    - self.full_corr (float): The full correlation between the two series over the whole length. 
    """

    def __init__(self, series1: pd.Series, series2: pd.Series, windows: list = [30, 90, 180, 365], 
                 ser1_title: str = "", ser2_title: str = "", watchlist_meta: pd.DataFrame = pd.DataFrame(),
                 downsample_to: str = ""):
        super().__init__()
  
        self.series1 = series1
        self.series2 = series2
        self.downsample_to = downsample_to  #Use pandas frequency strings to resample both series and decrease the frequency. e.g "W", "M", "MS"

        if len(ser1_title) == 0:
            self.ser1_title = self.series1.name
        else:
            self.ser1_title = ser1_title
        if len(ser2_title) == 0:
            self.ser2_title = ser2_title = self.series2.name
        else:
            self.ser2_title = ser2_title

        if watchlist_meta.empty:
            self.watchlist_meta = None
        else:
            self.watchlist_meta = watchlist_meta

        print("Series names: ",self.series2.name, self.series1.name)
        self.frequency = ""
        self.windows = windows 
        print("Windows: ", self.windows)
        self.windows.append(min(len(self.series1), len(self.series2))-2)
        
        self.check_input_series()
        self.name = f'{self.ser1_title} and {self.ser2_title}'
        self.data = self.returns_df()
        self.rolling_stats()
    
    def check_input_series(self):
            #Ensure that both are series first:
        try:
            series1 = ensure_series(self.series1)
            series2 = ensure_series(self.series2)
            print("Input series object types: ", type(series1), type(series2))
        except ValueError as e:
            print(e)
            print("Input series object types: ", type(series1), type(series2))
        
            ## Ensure that the two series are of the same frequency and length. 
        freq1 = freqDetermination(series1); freq1.DetermineSeries_Frequency()
        freq2 = freqDetermination(series2); freq2.DetermineSeries_Frequency()
        print(freq1.frequency, freq2.frequency)

        if freq1.frequency != freq2.frequency:
            print("Frequency of series do not match, downsampling the higher freq series to match...")
            try:
                s1_rank = freq1.freq_list[freq1.freq_list == freq1.frequency].index.to_list()[0]
                s2_rank = freq2.freq_list[freq2.freq_list == freq2.frequency].index.to_list()[0]
            except Exception as e:
                print('Error getting frequency rank for resampling, ', e)
                return None
            
            if s1_rank > s2_rank:
                print('Resampling series 2 to match series 1...')
                series2 = series2.resample(freq1.freq).last()
                self.frequency = freq1.frequency
                print(freq1.frequency, self.frequency)
            elif s1_rank < s2_rank:
                print('Resampling series 1 to match series 2...')
                series1 = series1.resample(freq2.freq).last()
                self.frequency = freq2.frequency
                print(freq1.frequency, self.frequency)
            else:
                print("Are the two series of the same frequency?...")
                return None
        else:
            self.frequency = freq1.frequency

        if len(self.downsample_to) > 0: 
            self.series1 = series1.resample(self.downsample_to).last() #Must use a lower frequency than original freq, e.g "W"from "D"..
            self.series2 = series2.resample(self.downsample_to).last()
            freqCheck = freqDetermination(self.series1)
            freqCheck.DetermineSeries_Frequency();  self.frequency = freqCheck.frequency
        else:
            self.series1 = series1
            self.series2 = series2
    
    def returns_df(self):
            # # Let's calulate some returns innit...
        df = pd.concat([self.series1, self.series2], axis = 1)
        
        df["ret_"+self.ser1_title] = np.log(df[self.series1.name]/df[self.series1.name].shift(1))
        df["ret_"+self.ser2_title] = np.log(df[self.series2.name]/df[self.series2.name].shift(1))
        df["retPct_"+self.ser1_title] = df[self.series1.name].pct_change(fill_method=None)
        df["retPct_"+self.ser2_title] = df[self.series2.name].pct_change(fill_method=None)
        df.dropna(inplace=True)
        return df

    def rolling_stats(self):
        ## Now for correlations...
        self.full_corr = self.data[self.series1.name].corr(self.data[self.series2.name], method = 'pearson')
        print("Whole time correlation, "+self.ser1_title+" vs "+self.ser2_title, ":", self.full_corr)
        self.full_RetCorr = self.data["ret_"+self.ser1_title].corr(self.data["ret_"+self.ser2_title], method = 'pearson')
        print("Whole time correlation between log returns, "+self.ser1_title+" vs "+self.ser2_title+":", self.full_RetCorr)
        self.full_PctRetCorr = self.data["retPct_"+self.ser1_title].corr(self.data["retPct_"+self.ser2_title], method = 'pearson')
        print("Whole time correlation between percentage returns,"+self.ser1_title+" vs "+self.ser2_title+":",self.full_PctRetCorr)
        self.full_qdCorr = qd_corr(self.data["ret_"+self.ser1_title], self.data["ret_"+self.ser2_title])
        print("Whole time qd correlation between log returns,"+self.ser1_title+" vs "+self.ser2_title+":",self.full_qdCorr)
        print("Rolling stats Windows: ", self.windows)
        names = self.ser1_title+"_"+self.ser2_title

        for window in self.windows:
            self.data[names+"_Corr_"+str(window)] = self.data[self.series1.name].rolling(window).corr(self.data[self.series2.name])
            self.data[names+"_RetCorr_"+str(window)] = self.data["ret_"+self.ser1_title].rolling(window).corr(self.data["ret_"+self.ser2_title])
            self.data[names+"_PctRetCorr_"+str(window)] = self.data["retPct_"+self.ser1_title].rolling(window).corr(self.data["retPct_"+self.ser2_title])
            self.data[names+"_qdCorr_"+str(window)] = rolling_qd(self.data["ret_"+self.ser1_title], self.data["ret_"+self.ser2_title], window)
            self.data[names+"_beta_"+str(window)] = self.data[names+"_Corr_"+str(window)] * (self.data["ret_"+self.ser1_title].rolling(window=window).std()\
                        / self.data["ret_"+self.ser2_title].rolling(window=window).std())
            self.data[names+"_alpha_"+str(window)] = self.data[self.series1.name].rolling(window=window).mean() - self.data[names+"_beta_"+str(window)]\
                  * self.data[self.series2.name].rolling(window=window).mean()

    def plot_corrs(self, trim_windows: int = 0):
        ## Using plt directly...

        #Step 1: Create subplots
        fig, axes = plt.subplots(4, 1, figsize=(11, 7), sharex=True)  # Adjust figsize as needed

        # Step 2: Plot data
        # Assuming self.data is a DataFrame with the necessary columns
        for i in range(trim_windows, len(self.windows), 1):
            corr_col = f"{self.ser1_title}_{self.ser2_title}_Corr_{self.windows[i]}"
            retcorr_col = f"{self.ser1_title}_{self.ser2_title}_RetCorr_{self.windows[i]}"
            pctRetcorr_col = f"{self.ser1_title}_{self.ser2_title}_PctRetCorr_{self.windows[i]}"
            qdcorr_col = f"{self.ser1_title}_{self.ser2_title}_qdCorr_{self.windows[i]}"
            
            if corr_col in self.data.columns:
                axes[0].plot(self.data.index, self.data[corr_col], label=f"{self.windows[i]} periods")
            if retcorr_col in self.data.columns:
                axes[1].plot(self.data.index, self.data[retcorr_col], label=f"{self.windows[i]} periods")
            if pctRetcorr_col in self.data.columns:
                axes[2].plot(self.data.index, self.data[pctRetcorr_col], label=f"{self.windows[i]} periods")
            if qdcorr_col in self.data.columns:
                axes[3].plot(self.data.index, self.data[qdcorr_col], label=f"{self.windows[i]} periods")

        fig.subplots_adjust(left=0.08, bottom=0.06, right = 0.97, top = 0.95, hspace=0.11)  # Adjust the right margin to fit the legend
        # Step 3: Style (mimicking pandas.plot)
        for ax in axes:
            ax.set_ylabel('Correlation', fontweight = 'bold', fontsize = 10)
       
        axes[0].axhline(self.full_corr, color="r", linestyle="--", lw=1)
        axes[1].axhline(self.full_RetCorr, color="r", linestyle="--", lw=1)
        axes[2].axhline(self.full_PctRetCorr, color="r", linestyle="--", lw=1)
        axes[3].axhline(self.full_qdCorr, color="r", linestyle="--", lw=1)

        # Optional: Titles, labels, etc.
        axes[0].set_title(f"Correlation: {self.ser1_title} vs {self.ser2_title}", fontsize = 11, pad = 2.5)
        axes[1].set_title(f"Log returns correlation.", fontsize = 10, pad = 2.5)
        axes[2].set_title(f"Percentage returns correlation.", fontsize = 10, pad = 2.5)
        axes[3].set_title(f"QuantDare returns correlation.", fontsize = 10, pad = 2.5)

        print("Frequency of the pair: ", self.frequency)
        line_handle = Line2D([0], [0], color="r", linestyle="--", lw=1, label="Correlation\nfull length")
        handles, labels = axes[2].get_legend_handles_labels()
        handles_combined = handles + [line_handle]
        labels_combined = labels + ["Correlation\nfull length"]
        axes[3].legend(handles=handles_combined, labels=labels_combined, fontsize = 10, bbox_to_anchor=(0.95, -0.1), ncol = 6)
        # axes[1] = add_line_to_legend(axes[1], "Correlation\nfull length", color="r", linestyle="--", lw=1)
        # axes[2] = add_line_to_legend(axes[1], "Correlation\nfull length", color="r", linestyle="--", lw=1)
        fig.text(0.865, 0.96, 'Data frequency: '+self.frequency, ha='center', va='center')
    
    def plot_series(self):
        
        leftTraces = {self.ser1_title: (self.series1, "black", 1.5)}
        rightTraces = {self.ser2_title: (self.series2, "blue", 1.5)}
        
        #print(self.watchlist_meta.loc["units", self.series1.name])
        try:
            lylabel = self.watchlist_meta.loc["units", self.series1.name] if not pd.isna(self.watchlist_meta.loc["units", self.series1.name]) else "USD"
        except:
            lylabel = "USD"
        try:
            rylabel = self.watchlist_meta.loc["units", self.series2.name] if not pd.isna(self.watchlist_meta.loc["units", self.series2.name]) else "USD"
        except:
            rylabel = "USD"

        ytr = EqualSpacedTicks(10, self.series1, "log"); print("Left ticks: ", ytr) 
        ytr2 = EqualSpacedTicks(10, self.series2, "log")

        self.fig1 = Charting.TwoAxisFig(leftTraces, "log", lylabel, title=self.name,
            RightTraces=rightTraces, RightScale="log", RYLabel=rylabel, LeftTicks=ytr, RightTicks=ytr2)
        
    def find_optimal_lag(self, n):
        correlations = []; backcorrs = []
        for i in range(n+1):
            shifted_series2 = self.series2.shift(i)
            correlation = self.series1.corr(shifted_series2)
            correlations.append(correlation)
        for i in range(n+1):
            shifted_series1 = self.series1.shift(i)
            backcorr = self.series2.corr(shifted_series1)
            backcorrs.append(backcorr)

        print("Correlations for shifted series2: ", correlations)
        optimal_lag = correlations.index(max(correlations))
        highest_correlation = max(correlations)
        backcorr_ser = pd.Series(backcorrs[::-1], index=range(-(n+1), 0))
        self.lag_test = pd.concat([backcorr_ser, pd.Series(correlations, index=range(n+1))], axis=0)
        
        return optimal_lag, highest_correlation
    
    def find_optimal_ret_lag(self, n):
        correlations = []; backcorrs = []
        ser1 = self.data["ret_"+self.ser1_title]
        ser2 = self.data["ret_"+self.ser2_title]

        for i in range(n+1):
            shifted_series2 = ser2.shift(i)
            correlation = ser1.corr(shifted_series2)
            correlations.append(correlation)
        for i in range(n+1):
            shifted_series1 = ser2.shift(i)
            backcorr = ser1.corr(shifted_series1)
            backcorrs.append(backcorr)

        print("Correlations for shifted series2: ", correlations)
        optimal_lag = correlations.index(max(correlations))
        highest_correlation = max(correlations)
        backcorr_ser = pd.Series(backcorrs[::-1], index=range(-(n+1), 0))
        self.ret_lag_test = pd.concat([backcorr_ser, pd.Series(correlations, index=range(n+1))], axis=0)
        
        return optimal_lag, highest_correlation

class api_keys():

    def __init__(self, JSONpath: str = wd+fdel+"SystemInfo", keyfileName: str = 'API_Keys.json'):

        keyFile = None; default_keyFile = None
        self.keys = None
        self.path = JSONpath
        self.keyFileName = keyfileName

        try: 
            print('Looking for api keys in SystemInfo folder...', JSONpath+fdel+self.keyFileName)
            keyFile = open(self.path+fdel+self.keyFileName)
            try:
                default_keyFile = open(JSONpath+fdel+'API_Keys_demo.json')
            except:
                pass    
        except Exception as e:
            print('Error loading API keys, ', e)
            pass    
        if keyFile is not None and default_keyFile is not None:
            print('API_keys found but the "API_Keys_demo.json" file is still present... Delete that file to silence this warning.')
            self.keys = json.load(keyFile)
        elif keyFile is not None and default_keyFile is None:   
            self.keys = json.load(keyFile)
            print("Key file found, all good bruv. ")
        elif default_keyFile is not None and keyFile is None:    
            print("No file: 'API_Keys.json' found in 'MacroBackend/SystemInfo'folder. However 'API_Keys_demo.json' was found. \nYou need to paste in your API keys\
                  into 'API_Keys_demo.json', save the filee and then get rid of the '_demo' to leave the file named as 'API_Keys.json'. After this your API keys\
                  should be available to access data from GlassNode, BEA and/or FRED. Alternatively you can paste the keys in here now and we'll save them into API_Key.json file.\
                  \nDo you have 1 or more of the API keys ready to paste into the terminal?")
            if input('Enter y for yes or n for no.').upper() == 'N':
                print('Go get one or more of those keys and then re-run script.')
                quit()    
            else: 
                self.MakeKeyFile(fileName='API_Keys.json')
        else:
            print("No file: 'API_Keys.json' found in 'MacroBackend/SystemInfo'folder. You need to have API keys saved into that .json file in dict format with keynames 'fred', 'glassnode' and"+\
                  "\n'bea', in order to be able to access data from those sources. You can paste the keys in here now and we'll save them into API_Key.json file.\
                  \nDo you have 1 or more of the API keys ready to paste into the terminal?")
            if input('Enter y for yes or n for no.').upper() == 'N':
                print('Go get one or more of those keys and then re-run script.')
                quit()    
            else: 
                self.MakeKeyFile(fileName='API_Keys.json')   

    def MakeKeyFile(self, fileName: str = 'API_Keys.json'):
        if self.keys is not None:
            print('API_Keys.json was found in MacroBackend/SystemInfo folder. Do you want to overwrite?')    
            if input('Enter y for yes or n for no.').upper() == 'N':
                return
        
        fredKey = input('Paste in your FRED API key and hit enter. Hit enter with no input to skip.')
        bea_key = input('Paste in your BEA API key and hit enter. Hit enter with no input to skip.')
        gn_key = input('Paste in your GlassNode API key and hit enter. Hit enter with no input to skip.')
        quandl_key = input('Paste in your Quandl (NASDAQ data link) API key and hit enter. Hit enter with no input to skip.')

        keyData = {'fred': fredKey,
                   'bea': bea_key,
                   'glassnode': gn_key,
                   'quandl': quandl_key}
        
        with open(self.path+fdel+fileName, 'w') as f:
            json.dump(keyData, f, indent=4)

        self.reload_keys()    

    def reload_keys(self):
        keyFile = open(self.path+fdel+self.keyFileName)
        self.keys = json.load(keyFile)

    def add_key(self, source: str = 'Unknown'):
        print(f"Here you can paste in your API key for the new source: {source}.")    
        new_key = input(f"Enter your API key for {source}")

        self.keys[source] = new_key
        with open(self.path+fdel+self.keyFileName, 'w') as f:
            json.dump(self.keys, f, indent=4)
        self.reload_keys()    

if __name__ == "__main__":
    # series = pd.read_excel("/Users/jamesbishop/Documents/Python/TempVenv/Bootleg_Macro/Macro_Chartist/SavedData/CNLIVRR.xlsx", sheet_name="Closing_Price", index_col=0)
    # series = series[series.columns[0]].resample('B').mean()
    
    # print(series)
    # SeriesFreq = DetermineSeries_Frequency(series)
    # print(SeriesFreq)

    # keyz = api_keys(JSONpath='/Users/jamesbishop/Documents/Python/Bootleg_Macro/MacroBackend/SystemInfo')
    # print(keyz.keys)
    # keyz.MakeKeyFile(fileName='API_Keys_test.json')
    # keyz.reload_keys()
    # print(keyz.keys)
    import random
    import string

    # Generate a DataFrame with 100 rows and 4 columns
    df = pd.DataFrame({
        0: [' '.join(random.choices(string.ascii_lowercase, k=3)) for _ in range(100)],
        1: [random.randint(100000, 999999) for _ in range(100)],
        2: [''.join(random.choices(string.ascii_letters + string.digits, k=8)) for _ in range(100)],
        3: [''.join(random.choices(string.ascii_letters + string.digits, k=8)) for _ in range(100)]
    })

    print(df)
    resultz = Search_DF(df, "5pj")
    print(resultz)