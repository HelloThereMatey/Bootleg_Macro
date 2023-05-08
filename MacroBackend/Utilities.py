import numpy as np
import pandas as pd


def EqualSpacedTicks(data,numTicks,LogOrLin:str='linear',LabOffset=None,labPrefix:str=None,labSuffix:str=None):
    Ymin = round(min(data),2); Ymax = round(max(data),2)    #Major ticks custom right axis. 
    if LogOrLin == 'log':
        Ticks = np.logspace(start = np.log10(Ymin), stop = np.log10(Ymax), num=numTicks, base=10); tickLabs = Ticks.copy()
    elif LogOrLin == 'linear':    
        Ticks = np.linspace(start = Ymin, stop = Ymax, num=numTicks); tickLabs = Ticks.copy()
    else:
        print('Must specify whether you want linear "linear" ticks or log10 ticks "log".')    
        quit()
    if LabOffset is not None:
        tickLabs += LabOffset
    Ticks.round(decimals=0,out=Ticks); tickLabs.round(decimals=0,out=tickLabs)
    Ticks = np.ndarray.astype(Ticks,dtype=int,copy=False)
    tickLabs = np.ndarray.astype(tickLabs,dtype=int,copy=False)
    tickLabs = np.ndarray.astype(tickLabs,dtype=str,copy=False)
    Ticks = Ticks.tolist(); tickLabs = tickLabs.tolist()
    if labPrefix is not None:
        tickLabs = [labPrefix+char for char in tickLabs]
    if labSuffix is not None:
        tickLabs = [char+labSuffix for char in tickLabs]
    return Ticks, tickLabs