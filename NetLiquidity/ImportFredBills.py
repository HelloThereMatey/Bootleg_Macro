###### Required modules/packages #####################################
import os
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
dir = os.path.dirname(wd)
print(wd,dir)
import sys; sys.path.append(dir)
from MacroBackend import PriceImporter

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import datetime

filePath = '/Users/jamesbishop/Documents/Python/TempVenv/Plebs_Macro/Generic_Macro/SavedData/RESPPLLOPNWW.xlsx'
startDate = datetime.date(2010,1,6)


FedBills, plot = PriceImporter.GetFedBillData(filePath,startDate,SepPlot=True)
print(FedBills.tail(50))

plt.show()