import pandas as pd
import numpy as np
import os
import re
import datetime

wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
dir = os.path.dirname(wd)
print(wd,dir)

TargetDir = '/home/imbobbilly/Documents/Financial/MACRO_STUDIES/PBoC/'
Files = os.listdir(TargetDir)
Files = [file for file in Files if 'BalSheet' in file]
Files.sort()
print(Files)

PBoC_BS = pd.Series([],name=r'PBoC BS (10$^8$ Yuan)')
for file in Files:
    Years = re.findall('(\d+)',file); Year = int(Years[0])
    BalSheet = pd.read_excel(TargetDir+file)
    BalSheet.set_index(BalSheet.columns[0],inplace=True)
    Lines = BalSheet.index.to_list()
    Lines2 = [item for item in Lines if not (pd.isnull(item) == True)]
    for line in Lines2:
        search = re.search(r"\*Total  Liabilities\*",line); 
        if search is not None:
            BottomLine = search.group(); print(BottomLine)
#     BottomLine = [line for line in Lines2 if 'Total  Liabilities' in line]; print(Year, BottomLine)
#     start = datetime.date(Year,1,1).strftime('%Y-%m'); end = datetime.date((Year+1),1,1).strftime('%Y-%m')
#     Dates = pd.date_range(start,end,freq='M')
#     if len(BottomLine) > 0:
#         Liabilities = BalSheet.loc[BottomLine[0]]
#         List = Liabilities.to_list()
#         BS = pd.Series(List,index=Dates,name=r'PBoC BS (10$^8$ Yuan)')
#         PBoC_BS = pd.concat([PBoC_BS,BS],axis=0)    
# print(PBoC_BS)    