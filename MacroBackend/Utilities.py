import numpy as np
import pandas as pd
import datetime
import operator
import re

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
    print('Calculating the',months,'month annualized % change for the series.')
    print('Frequency of input time series, ',':',freq)    
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

    def op(self, MathOpStr:str, counter:int) -> pd.Series:
        alpha = "abcdefghijklmnopqrstuvwxyz".upper()
        for p in self.operators.keys():
            x = 0
            while x < len(MathOpStr)-1 and any(p in str(el) for el in MathOpStr):
                if p in str(MathOpStr[x]):
                    print(f"Operator: ({MathOpStr[x+1]}): {type(MathOpStr[x+1])}")
                    print(f"Left operand ({MathOpStr[x]}): {type(MathOpStr[x])}")
                    print(f"Right operand ({MathOpStr[x-1]}): {type(MathOpStr[x-1])}")
                    print('Running operation: ', self.operators.get(p))
                    replacer = self.operators.get(p)(MathOpStr[x] , MathOpStr[x-1])
                    replacer = pd.Series(replacer, name="RES_"+alpha[counter])
                    MathOpStr[x-1] = replacer
                    del MathOpStr[x:x+2]
                else:
                    x += 1  
        return MathOpStr[0]

    def func(self, MathOpStr:str) -> pd.Series:
        df = self.Data
        results = {}
        counter = 0
        alpha = "abcdefghijklmnopqrstuvwxyz".upper()

        while '(' in MathOpStr:
            start = MathOpStr.rfind('(')
            end = MathOpStr.find(')', start)
            result = self.func(MathOpStr[start+1:end])
            key = 'RES_' + alpha[counter]
            results[key] = result
            MathOpStr = MathOpStr[:start] + key + MathOpStr[end+1:]
            counter += 1

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
                    column = df[self.colMap[column_index]]
                    d.append(column)

        d = self.op(d, counter)
        d.rename('Custom_Index',inplace=True)
        self.ComputedIndex = d.copy()
        return d
