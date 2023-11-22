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
from typing import Union, Tuple, List
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from openpyxl import load_workbook

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

def count_zeros_after_decimal(series: pd.Series = None, value: float = None) -> int:
    if series is not None:
        median_value = series.median()
    else:
        median_value = value   
    
    if median_value < 1 and median_value > 0:
        str_val = str(median_value).split('.')[1] # Convert to string and split by decimal point
        return len(str_val) - len(str_val.lstrip('0')) + 1
    else:
        return 1

def EqualSpacedTicks(numTicks, data: Union[pd.Series, pd.DataFrame] = None,
        LogOrLin:str='linear',LabOffset=None,labPrefix:str=None,labSuffix:str=None,Ymin:float=None,Ymax:float=None):
     
    if data is not None:
        if Ymin is None:
            Ymin = data.min()
        if Ymax is None:  
            Ymax = data.max()    #Major ticks custom right axis. 

    if data is not None:
        decimals = count_zeros_after_decimal(series = data)
    else:
        decimals = count_zeros_after_decimal(value = (Ymax - Ymin)/2)

    if LogOrLin == 'log':
        Ticks = np.logspace(start = np.log10(Ymin), stop = np.log10(Ymax), num=numTicks, base=10); tickLabs = Ticks.copy()
    elif LogOrLin == 'linear':    
        Ticks = np.linspace(start = Ymin, stop = Ymax, num=numTicks); tickLabs = Ticks.copy()
    else:
        print('Must specify whether you want linear "linear" ticks or log10 ticks "log".')    
        quit()
    if LabOffset is not None:
        tickLabs += LabOffset
    Ticks.round(decimals=decimals,out=Ticks); tickLabs.round(decimals=decimals,out=tickLabs)
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

def GetClosestDateInIndex(df: Union[pd.DataFrame, pd.Series], searchDate: str = "2012-01-01"):
    ## searchDate should bee in "YYYY-MM-DD" format. 
    if type(df.index) != pd.DatetimeIndex:
        print('Input dataframe must have a datetime index.')
        return None

    # Convert the Datestring to a Timestamp object
    date_ts = pd.Timestamp(searchDate)
    # Find the closest date in the index
    closest_date = min(df.index, key=lambda x: abs(x - date_ts))
    index = df.index.get_loc(closest_date)
    return closest_date, index

def find_closest_val(series:pd.Series, target_value: Union[int, float]):
    differences = series.sub(target_value).abs()
    idx_closest = differences.idxmin()
    value_closest = series.loc[idx_closest]
    return value_closest, idx_closest

def Percent_OfBaseVal_Series(series: pd.Series, ZeroDate: str = None, median: bool = False, mean: bool = False, start: bool = False) -> pd.Series:
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
                    if re.search(re.escape(search_regexes[0]), s, flags = re.IGNORECASE):
                        matches.append(s)
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
    
def DetermineSeries_Frequency(series: pd.Series):
    MonthlyList = ['M','SM','BM','CBM','MS','SMS','BMS','CBMS']
    QuarterList = ['Q','BQ','QS','BQS']
    AnnualList = ['A', 'Y','BA', 'BY', 'AS', 'YS','BAS', 'BYS']
    multiplier = 1

    frequency_dict = {
                    "Weekly": ['W'],
                    "Monthly": ['WOM', 'LWOM', 'M', 'MS', 'BM', 'BMS', 'CBM', 'CBMS', 'SM', 'SMS'],
                    "Quarterly": ['Q', 'QS', 'BQ', 'BQS', 'REQ'],
                    "Yearly": ['A', 'AS', 'BYS', 'BA', 'BAS', 'RE'],
                    "Daily": ['D', 'B', 'C'],  
                    "Hourly": ['BH', 'CBH', 'H'],
                    "Minutely": ['T', 'min'],
                    "Secondly": ['S'],
                    "Millisecondly": ['L', 'ms'],
                    "Microsecondly": ['U', 'us'],
                    "Nanosecondly": ['N'] }
    periods_in_day = {
                    "Weekly": 1/7,
                    "Monthly": 1/30.4375,
                    "Quarterly": 1/91.3125,
                    "Yearly": 1/365.25,
                    "Daily": 1,  
                    "Hourly": 24,
                    "Minutely": 24*60,
                    "Secondly": 60*60*24,
                    "Millisecondly": 1000*60*60*24,
                    "Microsecondly": 1000000*60*60*24,
                    "Nanosecondly": 1000000000*60*60*24 }
    
    freq = pd.infer_freq(series.index)
    print('Frequency determination function for series: ', series.name, ' frequency: ', freq)
    
    if freq is None:
        print("Couldn't discern frequency in the regular manner, trying manual process....")
        avDelta = manual_frequency(series)
        print('Looks like average index timedelta is: ', avDelta[1],', resampling series to that frequency.')
        Frequency, periods_inDay = DetermineSeries_Frequency(avDelta[0])
        return Frequency, periods_inDay
    else:
        match = re.match(r'(\d+)([A-Za-z]+)', freq)
        if match:
            matches = match.groups()
            multiplier = int(matches[0]); freq = matches[1]
   
    frequency = None
    for freqName in frequency_dict.keys():
        if freq in frequency_dict[freqName]:
            frequency = freqName
        elif freq.split('-')[0] == 'W':
            frequency = 'Weekly'
    if frequency is None:
        print('Could not match the frequency for input series, ', series.name,' reported frequency is: ', freq)    
        frequency = freq

    return frequency, periods_in_day[frequency]/ multiplier

def manual_frequency(series: pd.Series, threshold_multiplier=2.25):
    daysInPeriod = {'1H': 1/24, '4H': 1/6, 'Day': 1, 'Week': 7, 'Month': 30, 'Quarter': 90}
    
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

    # Map to the appropriate frequency
    freq_map = {
        '1H': 'H', '4H': '4H', 'Day': 'D', 'Week': 'W', 'Month': 'M', 'Quarter': 'Q'
    }
    freq = freq_map[closest_period]
    
    resampled_series = series.resample(freq).mean()  # Replace .mean() with an appropriate aggregation function if needed
    return resampled_series, closest_period

if __name__ == "__main__":
    series = pd.read_excel("/Users/jamesbishop/Documents/Python/TempVenv/Bootleg_Macro/Macro_Chartist/SavedData/CNLIVRR.xlsx", sheet_name="Closing_Price", index_col=0)
    series = series[series.columns[0]].resample('B').mean()
    
    print(series)
    SeriesFreq = DetermineSeries_Frequency(series)
    print(SeriesFreq)