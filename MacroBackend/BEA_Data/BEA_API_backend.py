import os
wd = os.path.dirname(__file__); Dir = os.path.dirname(wd); FDel = os.path.sep
parent = os.path.dirname(Dir)
from pprint import pprint
from pybea.client import BureauEconomicAnalysisClient
import pandas as pd
import numpy as np
import requests
import re
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from typing import Union
import datetime
import customtkinter as ctk
import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog
from Utilities import StringMathOp

#"https://github.com/areed1192/python-bureau-economic-analysis-api-client?search=1"

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

def DateTime2PeriodIndex(data:Union[pd.DataFrame,pd.Series],frequency:str):   ##Not working, come back to this later. 
    print(data)
    idX = data.index.to_list
    PidX = pd.PeriodIndex(idX,freq=frequency)
    data.set_index(PidX,inplace=True)
    
    return data

# Function to convert numbers with commas to integers
def convert_to_float_with_commas(value):
    if pd.isna(value):
        return value
    else:
        val = str(value)
        return float(val.replace(',', ''))

class BEA_Data(BureauEconomicAnalysisClient):

    def __init__(self, api_key: str, BEA_Info_filePath: str = None) -> None:
        super().__init__(api_key)

        self.baseURL = self.bea_url+"?&UserID="+self.api_key
        self.ResultFormat = "json"

        self.NIPA_Data = None

        if BEA_Info_filePath is not None:
            DataSetList = pd.read_excel(BEA_Info_filePath, sheet_name='Datasets') 
            DataSetList.set_index(DataSetList.columns[0],inplace=True); DataSetList.index.rename('Index',inplace=True) 
            print(DataSetList)
            NIPA_TableNames = pd.read_excel(BEA_Info_filePath, sheet_name='NIPA_TableNames')
            NIPA_TableNames.set_index(NIPA_TableNames.columns[0],inplace=True); NIPA_TableNames.index.rename('Index',inplace=True) 
            print(NIPA_TableNames)
            
        else:  
            # Grab the Dataset List.
            DataSetList = self.get_dataset_list()
            datasets = pd.json_normalize(DataSetList['BEAAPI']['Results']['Dataset'])
            NIPA_Pars = self.get_parameters_list('NIPA')
            NIPA_Params = pd.json_normalize(NIPA_Pars['BEAAPI']['Results']['Parameter'])
            
            print(datasets,NIPA_Params,"\n",NIPA_TableNames)

    def GetInfoAboutDataset(self,dataset:str,parameterName:str):
        
        NReqParameterValues = "&method=GetParameterValues&datasetname="+dataset+"&ParameterName="+parameterName+"&ResultFormat="+self.ResultFormat
        req = requests.get(self.baseURL+NReqParameterValues)
        NIPA_TableNames = pd.json_normalize(req.json()['BEAAPI']['Results']['ParamValue'])
        
        return NIPA_TableNames
        
    def Get_NIPA_Data(self,tCode:str,tDesc:str,frequency:str="M",year:list='ALL'):
        data = self.national_income_and_product_accounts(tCode,frequency=frequency,year=year)
        print(data['BEAAPI'].keys())
        if 'Error' in data['BEAAPI'].keys():
            print('Error pulling data from BEA API. Error message: ',data['BEAAPI']['Error'])
            return
        else:    
            print(data["BEAAPI"]["Results"].keys())

        self.NIPA_Data = {}
        self.NIPA_Data_tCode = tCode
        self.NIPA_Data_name = tDesc
        self.NIPA_Data_freq = frequency
        for key in data["BEAAPI"]["Results"].keys():
            try: 
                self.NIPA_Data[key] = pd.DataFrame.from_dict(data["BEAAPI"]["Results"][key])
            except:
                pass  
        
        Data = pd.DataFrame(self.NIPA_Data['Data'])
        SeriesInfo, FinalData = self.NIPA_Data_2DF(Data,frequency,tDesc)

        self.NIPA_Data['Series_Split'] = FinalData
        self.NIPA_Data['SeriesInfo'] = SeriesInfo


    def NIPA_Data_2DF(self,NIPA_Data:pd.DataFrame,frequency:str,tDesc:str):
        categories = NIPA_Data['LineDescription'].unique()
        SeriesInfo = pd.Series(NIPA_Data.iloc[0],name=tDesc)
        SeriesInfo.drop(['LineDescription','NoteRef','LineNumber','TimePeriod','DataValue'],axis=0,inplace=True)   

    ################## Split the table into separate time-series.
        i = 0; names = []; codes = []
        for cat in categories:
            category = pd.DataFrame(NIPA_Data[NIPA_Data['LineDescription'] == cat])
            category.drop_duplicates("TimePeriod",inplace=True)
            idx = pd.PeriodIndex(category["TimePeriod"],freq = frequency)
            dtI = idx.to_timestamp(freq=frequency, how='start')
            category.set_index(dtI,inplace=True)
            catSeries = pd.Series(category["DataValue"],name=cat)
            names.append(cat); codes.append(str(category['SeriesCode'][0]))

            if i == 0:
                FinalData = catSeries.copy()
                print(FinalData.head(50),FinalData.index)
            else:
                if len(FinalData.index.difference(catSeries.index)) > 0:
                    NanSeries = pd.Series(np.nan,index=FinalData.index.difference(catSeries.index))
                    bilp = pd.concat([NanSeries,catSeries],axis=0); bilp.rename(catSeries.name,inplace=True)
                    print(FinalData.index.difference(bilp.index),"\n")
                    print(bilp.index.difference(FinalData.index),"\n")
                    bilp = bilp.reindex(index=FinalData.index,method='pad')
                    FinalData = pd.concat([FinalData,bilp],axis=1)
                else:    
                    FinalData = pd.concat([FinalData,catSeries],axis=1)
            i += 1
        FinalData.index.rename("TimePeriod",inplace=True)      
        # Apply the conversion function to the entire DataFrame
        for column in FinalData.columns:
            FinalData[column] = FinalData[column].apply(convert_to_float_with_commas)  
        SeriesCodes = pd.Series(codes,index=names)     
        SeriesInfo = pd.concat([SeriesInfo,SeriesCodes],axis=0)
        return SeriesInfo,FinalData   
    
    def Export_BEA_Data(self, filenames:list, saveLoc:str = wd+"/Datasets/"):
        # saveLoc is the directory to save in
        Export = {}
        if self.NIPA_Data is not None:
            Export["NIPA"] = self.NIPA_Data.copy()
    ############# Export data to an Excel file (.xlsx).
        for n, export in enumerate(Export.keys()):
            savePath = saveLoc+filenames[n]+".xlsx"
            ExportData = dict(Export[export])
            print('Exporting BEA data to excel file: ',savePath)
            i = 0
            for key in ExportData.keys():
                df = pd.DataFrame(ExportData[key])
                if i == 0:
                    df.to_excel(savePath, sheet_name=key)
                else:
                    with pd.ExcelWriter(savePath, engine='openpyxl', mode='a') as writer:  
                        df.to_excel(writer, sheet_name=key)    
                i += 1

    def BEAPreviewPlot(self, data: pd.DataFrame = None, YScale:str='linear', seriesInfo: pd.Series=None, title: str = None):
        plt.rcParams['font.family'] = 'serif'
        fig = plt.figure(figsize=(11, 5), dpi=150)
        fig.suptitle('U.S Bureau of Economic Analysis', fontweight='bold')
        ax = fig.add_axes(rect=[0.07,0.06,0.67,0.84])
        
        if seriesInfo is not None:
            pass
        else:
            seriesInfo = pd.Series(self.NIPA_Data['SeriesInfo'])
        if data is not None:
            pass
        else:    
            data = pd.DataFrame(self.NIPA_Data['Series_Split'])
        print(data)    
        for col in data.columns:
            ax.plot(data[col],label=col)    
        ax.legend(fontsize=5,loc=2,bbox_to_anchor=(1.005,1.01))
        
        ax.set_yscale(YScale); 
        if title is not None:
            ax.set_title(title,fontweight='bold',fontsize=9,loc='left',x = 0.1)
        else:    
            ax.set_title(self.NIPA_Data_name,fontweight='bold',fontsize=9,loc='left',x = 0.1)
        units = int(seriesInfo['UNIT_MULT'])
        unit = str(seriesInfo['METRIC_NAME'])
        if unit == 'Current Dollars' or unit == 'Chained Dollars':
            unit = unit.replace('Dollars','$')
            if units == 6:
                yLabel = 'Millions of US '+unit
            elif units == 9:
                yLabel = 'Billions of US '+unit
            elif units == 3:
                yLabel = 'Thousands of US '+unit
            else:
                yLabel = 'US '+unit+r' (x 10$^{'+str(units)+r'}$)'  
        else:
            yLabel = unit   

        #ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=15)) # Adjust the number as needed  
        ax.set_ylabel(yLabel,fontweight='bold',fontsize=9)
        ax.tick_params(axis='both',labelsize=8) 
        #ax.tick_params(axis='x',labelrotation=45)
        ax.minorticks_on(); ax.margins(x=0.02,y=0.02)
        ax.grid(visible=True,axis='both',which='both',lw=0.5,color='gray',ls=':')      
        ax.margins(0.01,0.01)    
        for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_linewidth(1.5)    
        plt.tight_layout() # This will ensure everything fits well         
        return fig  
    
    def ExportCustomIndex(self, savePath):
        if self.NIPA_Data is not None:
            data = self.NIPA_Data['Series_Split']
        else:
            print('Load NIPA table data from BEA first.')    

class CustomIndexWindow(ctk.CTk):

    def __init__(self, dataTable:dict, name: str = 'Dataset', exportPath:str = parent+FDel+'Generic_Macro'+FDel+'SavedData'+FDel+'BEA'):
        super().__init__()
        default_font = ctk.CTkFont('Arial',13)
        self.data = pd.DataFrame(dataTable['Series_Split'])
        self.SeriesInfo = pd.Series(dataTable['SeriesInfo'])
        self.data_name = self.SeriesInfo['METRIC_NAME']
        print(self.data_name,self.data,self.SeriesInfo)
        self.title('Export custom index')

        self.choices = ctk.StringVar(self, value="", name = 'Index_Series')
        self.components = ctk.StringVar(self, value=self.data.columns.to_list(), name = 'ListComponents')
        self.ExportPath = ctk.StringVar(self, value= exportPath, name = 'Export_path')
        self.C_Index_name = ctk.StringVar(self, value="", name = 'Export_name')
        self.exportPath = exportPath
        self.operationString = ctk.StringVar(self, value="", name = 'Operation_String')

        self.frame1 = ctk.CTkFrame(self); self.frame2 = ctk.CTkFrame(self); self.frame3 = ctk.CTkFrame(self); self.frame4 = ctk.CTkFrame(self)
        self.frame1.pack(pady=20,padx=20); self.frame2.pack(pady=20,padx=20); self.frame3.pack(pady=20,padx=20); self.frame4.pack(pady=20,padx=20)
        self.ChoiceList = []
        self.choiceIndex = ctk.StringVar(self, value="", name = 'Choice_Index')
        self.choiceIndexList = []

        def ChooseSeries(event):
            data = self.data
            series = data.columns.to_list()
            curs = SeriesList.curselection()
            self.ChoiceList.append(series[curs[0]])
            self.choices.set(self.ChoiceList)
            self.choiceIndexList.append(len(self.ChoiceList)-1)
            self.choiceIndex.set(self.choiceIndexList)
        
        SeriesList = tk.Listbox(self.frame1,listvariable=self.components, width=0, font=('Arial',12)); SeriesList.bind('<Double-1>',ChooseSeries)
        SeriesList.grid(column=0,row=0,padx=30,pady=30,ipadx=15,ipady=10)
        ChosenSeries = tk.Listbox(self.frame1,listvariable=self.choices, width=0, font=('Arial',12))
        ChosenSeries.grid(column=1,row=0,padx=30,pady=30,ipadx=15,ipady=10)
        indexBox = tk.Listbox(self.frame1,listvariable=self.choiceIndex, width=0, font=('Arial',12),justify='center')
        indexBox.grid(column=2,row=0,padx=15,pady=30,ipadx=5,ipady=10)

        Operation = ctk.CTkEntry(self.frame2,textvariable=self.operationString,font=default_font,width=round(default_font.measure(self.ExportPath.get())/2))
        Operation.pack(padx=10,pady=10)

        self.frame3.columnconfigure(0,weight=1); self.frame3.columnconfigure(1,weight=1)
        self.frame3.columnconfigure(2,weight=1); self.frame3.columnconfigure(3,weight=1)

        Index_Name = ctk.CTkEntry(self.frame3,textvariable=self.C_Index_name); Index_Name.grid(column=0,row=0,padx=5,pady=5)
        reset = ctk.CTkButton(self.frame3, text="RESET",font=('Arial',14,'bold'),text_color='tomato',command=self.ResetBox)
        reset.grid(column=1,row=0,padx=10)
        SetExport = ctk.CTkButton(self.frame3, text="Set export path",font=('Arial',14,'bold'),command=self.SetExpPath)
        SetExport.grid(column=2,row=0)
        ExportC_Index = ctk.CTkButton(self.frame3,font=('Arial',14,'bold'),text='Export Index',text_color='lime',command=self.ExportIndex) 
        ExportC_Index.grid(column=3,row=0,padx=10)
        
        ExpPath = ctk.CTkEntry(self.frame4,textvariable=self.ExportPath,font=default_font,width=default_font.measure(self.ExportPath.get()+'                '))
        ExpPath.pack(padx=10,pady=10)
    
    def ExportIndex(self):
        comps = self.ChoiceList.copy(); compsStr = ""
        indx = self.choiceIndexList.copy()
        for comp in comps:
            compsStr += comp
        print('Making custom index from: ',comps)
        data = self.data
        Cindex = pd.Series(0, index = data.index)
        name = self.C_Index_name.get()
        opString = self.operationString.get(); print(opString)
        print('Will save custom index with name: ', name)

        if len(opString) > 0:
            smo = StringMathOp(data, comps, indx)
            smo.func(opString)
            print('Custom index made using math indicated in the operationString: ', smo.ComputedIndex)
            Cindex = smo.ComputedIndex.copy()
        else:
            print('Adding the index components to produce custom index as no custom operation string provided.')
            for col in comps:
                series = data[col]
                Cindex = Cindex + series
        Cindex.rename(name) ; print('Custom index: ',Cindex)

        ExtraInfo = {'units': str(self.SeriesInfo['CL_UNIT'])+r'(x10$^'+str(self.SeriesInfo['UNIT_MULT'])+r'$)',
                     'units_short': str(self.SeriesInfo['CL_UNIT'])+r'(x10$^'+str(self.SeriesInfo['UNIT_MULT'])+r'$)',
                     'id':name, 'title': 'Custom index: '+compsStr}
        info = pd.Series(ExtraInfo.values(),index=ExtraInfo.keys())
        filename = self.exportPath+FDel+name+'.xlsx'; print(filename)
        Cindex.to_excel(filename,sheet_name='Closing_Price')
        self.SeriesInfo = pd.concat([self.SeriesInfo,info])
        with pd.ExcelWriter(filename, engine='openpyxl', mode='a') as writer:  
            self.SeriesInfo.to_excel(writer, sheet_name='SeriesInfo')

    def ResetBox(self):
        self.ChoiceList = []
        self.choices.set("")

    def SetExpPath(self):
        folder_selected = filedialog.askdirectory(initialdir=self.exportPath)
        self.ExportPath.set(folder_selected)  

if __name__ == "__main__":
    api_key='779F26DA-1DB0-4CC2-94DD-2AE3492DA4FC'
    dataset = "NIPA"
    parameterName = "Tablename"

    TableName = "T10101"
    TableDesc = "Table 2.3.1. Percent Change From Preceding Period in Real Personal Consumption Expenditures by Major Type of Product (A) (Q)"
   
    filepath = wd+"/Datasets/BEAAPI_Info.xlsx"

    # Initalize the new Client.
    bea = BEA_Data(api_key=api_key,BEA_Info_filePath=filepath)

    tCode = 'T20805'
    TableDesc = "Table 2.8.5. Personal Consumption Expenditures by Major Type of Product, Monthly (M)"
    print("Pulling data from BEA API for: ",tCode,TableDesc)

    results = {}; year = []
    yearOne = 2020
    endYear = datetime.datetime.today().year
    endYear = 2022
    for i in range(yearOne,endYear+1,1):
        year.append(str(i))

    # bea.Get_NIPA_Data(tCode,frequency="M",tDesc=TableDesc,year=year)
    # print(bea.NIPA_Data)

    #data = bea.NIPA_Data['Series_Split']
    TheData = pd.read_excel('/Users/jamesbishop/Documents/Python/TempVenv/Plebs_Macro/MacroBackend/BEA_Data/Datasets/T20806.xlsx',sheet_name='Series_Split')
    SeriesInfo = pd.read_excel('/Users/jamesbishop/Documents/Python/TempVenv/Plebs_Macro/MacroBackend/BEA_Data/Datasets/T20806.xlsx',sheet_name='SeriesInfo')
    TheData.set_index(TheData.columns[0],inplace=True); SeriesInfo.set_index(SeriesInfo.columns[0],inplace=True)
    SeriesInfo = pd.Series(SeriesInfo.squeeze(),name='SeriesInfo'); TheData.index.rename('TimePeriod',inplace=True)
    print(TheData,SeriesInfo)

    fig = bea.BEAPreviewPlot(data=TheData,YScale="log",seriesInfo=SeriesInfo,title=TableDesc)
    plt.show()
    # bea.Export_BEA_Data(['T20805_PCE_M'])
    # ############# Export data to Excel. 
    # savePath = wd+"/Datasets/"+tCode+".xlsx"