import os
wd = os.path.dirname(__file__); Dir = os.path.dirname(wd); FDel = os.path.sep
parent = os.path.dirname(Dir)
import sys
sys.path.append(parent)
from pybea.client import BureauEconomicAnalysisClient
import pandas as pd
import numpy as np
import requests
import re
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
from typing import Union
import datetime
import customtkinter as ctk
import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog
from MacroBackend import Utilities
from pprint import pprint

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

# Function to convert numbers with commas to integers
def convert_to_float_with_commas(value):
    if pd.isna(value):
        return value
    else:
        val = str(value)
        return float(val.replace(',', ''))


class BEA_Data(BureauEconomicAnalysisClient):

    def __init__(self, api_key: str, BEA_Info_filePath: str = "", Refresh_Info: bool = False) -> None:
        super().__init__(api_key)

        self.baseURL = self.bea_url+"?&UserID="+self.api_key
        self.ResultFormat = "json"
        self.Data = None
        
        if os.path.isfile(BEA_Info_filePath) and Refresh_Info is False:
            self.BEAAPI_InfoTables = pd.read_excel(BEA_Info_filePath, sheet_name=None, index_col=0) 
            print("BEA API info loaded from file: ",BEA_Info_filePath)
            DataSets = self.BEAAPI_InfoTables['DataSetList']
            DataSetList = DataSets.index.to_list(); DataSetList2 = []
            DataSetList.remove('APIDatasetMetaData')
            for d in DataSetList:
                DataSetList2.append(d+'_params')
            InfoList = list(self.BEAAPI_InfoTables.keys())
            
            if all(a in InfoList for a in DataSetList2):
                print('Info loaded from excel concerning API parameters is sufficiently complete..')
                pass
            else: 
                print('Updating BEA API info excel file......')
                self.BEAAPI_InfoTables = self.GetAllDatasetParams()
        else:  
            print('No file found at BEA_Info_filePath and/or Refresh_Info is True.')
            self.BEAAPI_InfoTables = self.GetAllDatasetParams()
            
        self.DataSetList = self.BEAAPI_InfoTables['DataSetList'].index.to_list()
        self.DataSetList.remove('APIDatasetMetaData')
        self.SheetsList = [sheet.replace("_params", "") for sheet in list(self.BEAAPI_InfoTables.keys())]
        self.DSTables = [a.replace("_Tables","") for a in self.SheetsList if a not in self.DataSetList and "_Tables" in a]
            
        
        if Refresh_Info is True and len(BEA_Info_filePath) > 0:
            i = 0
            for key in self.BEAAPI_InfoTables.keys():
                df = pd.DataFrame(self.BEAAPI_InfoTables[key])
                if i == 0:
                    df.to_excel(BEA_Info_filePath,sheet_name=key)
                else:    
                    with pd.ExcelWriter(BEA_Info_filePath, engine='openpyxl', mode='a') as writer:  
                        df.to_excel(writer, sheet_name=key)    
                i += 1
            print("Dataset information pulled and saved to: ", BEA_Info_filePath)    

    def GetDS_Params(self, dataset: str = 'NIPA') -> pd.DataFrame:
        # Grab the Dataset List.
        DS_Pars = self.get_parameters_list(dataset)
        try:
            DS_Params = pd.DataFrame(DS_Pars['BEAAPI']['Results']['Parameter'])
            return DS_Params
        except Exception as error:
            print('Could not convert the given parameter data to a Dataframe. Dataset: ', dataset, 'Error: ', error, ', data: \n', DS_Pars)
            return DS_Pars
        
    def GetParamVals(self, dataset: str = 'NIPA', parameterName: str = 'TableName') -> pd.DataFrame:
        NReqParameterValues = "&method=GetParameterValues&datasetname="+dataset+"&ParameterName="+parameterName+"&ResultFormat="+self.ResultFormat
        req = requests.get(self.baseURL+NReqParameterValues)
        ParVals = req.json()['BEAAPI']['Results']['ParamValue']
        ParVals = pd.DataFrame(ParVals)
        ParVals.set_index(ParVals[ParVals.columns[0]],inplace=True)
        return ParVals
    
    def GetAllDatasetParams(self):
        DataSets = self.get_dataset_list()
        DataSetList = pd.DataFrame(DataSets['BEAAPI']['Results']['Dataset'])
        DataSetList.set_index(DataSetList.columns[0], inplace=True)
        NIPA_Tables = self.GetParamVals()
        NIPA_Details = self.GetParamVals(dataset='NIUnderlyingDetail')
        FixedAssets = self.GetParamVals(dataset='FixedAssets')
        BEAAPI_InfoTables = {'DataSetList': DataSetList,
                                    'NIPA_Tables': NIPA_Tables,
                                    'NIPA_Details_Tables': NIPA_Details,
                                    'FixedAsset_Tables': FixedAssets
        }
        for ds in DataSetList.index:
            if ds == 'APIDatasetMetaData':
                pass
            else:
                print('Getting parameters for dataset: ', ds)
                BEAAPI_InfoTables[ds+'_params'] = self.GetDS_Params(dataset=ds)
        return  BEAAPI_InfoTables      
        
    def Get_BEA_Data(self,dataset:str='NIPA',tCode:str='T10101',frequency:str="M",year:list='ALL'):
        print('Pulling data from BEA API dataset: ',dataset,', Table code: ',tCode)
        if dataset == 'NIPA':
            data = self.national_income_and_product_accounts(tCode,year=year,frequency=frequency)
        elif dataset == 'NIPA_Details':   
            data = self.national_income_and_product_accounts_detail(tCode,year=year,frequency=frequency)
        elif dataset == 'FixedAsset':   
            data = self.fixed_assets(tCode,year=year)    
        else:
            print('Dataset specification is not valid.....')
            return  
          
        print(data['BEAAPI'].keys())
        if 'Error' in data['BEAAPI'].keys():
            print('Error pulling data from BEA API. Error message: ',data['BEAAPI']['Error'])
            return
        elif 'Error' in data["BEAAPI"]["Results"].keys():
            print('Error pulling data from BEA API. Error message: ',data['BEAAPI']["Results"]['Error'])
            return
        else:    
            print(data["BEAAPI"]["Results"].keys())
            TabName = str(data["BEAAPI"]["Results"]["Notes"][0]["NoteText"]); print(TabName)
            tDesc = TabName.split('[')[0]; print(tDesc)

        self.Data = {}; AddInfo = {}
        self.Data_tCode = tCode
        self.Data_name = tDesc
        self.Data_freq = frequency
        for key in data["BEAAPI"]["Results"].keys():
            try: 
                if type(data["BEAAPI"]["Results"][key] == dict):
                    self.Data[key] = pd.DataFrame.from_dict(data["BEAAPI"]["Results"][key])
                    self.Data[key] = pd.DataFrame(self.Data[key])
                else:
                    AddInfo[key] = data["BEAAPI"]["Results"][key] 
            except:
                #print('Error encountered trying to convert data from dict to data frame, for BEAAPI data: ', key)
                AddInfo[key] = data["BEAAPI"]["Results"][key]
                pass  
        
        Data = pd.DataFrame(self.Data['Data'])
        SeriesInfo, FinalData = self.Data_2DF(Data,frequency,tDesc)

        self.Data['Series_Split'] = FinalData
        AddInfo["Source"] = "Bureau of economic analysis"
        addThis = pd.Series(AddInfo)
        SeriesInfo = pd.concat([SeriesInfo, addThis])
        self.Data['SeriesInfo'] = SeriesInfo

    def Data_2DF(self,Data:pd.DataFrame,frequency:str,tDesc:str):
        categories = Data['LineDescription'].unique()
        SeriesInfo = pd.Series(Data.iloc[0],name=tDesc)
        SeriesInfo.drop(['LineDescription','NoteRef','LineNumber','TimePeriod','DataValue'],axis=0,inplace=True)   

    ################## Split the table into separate time-series.
        i = 0; names = []; codes = []
        for cat in categories:
            category = pd.DataFrame(Data[Data['LineDescription'] == cat])
            category.drop_duplicates("TimePeriod",inplace=True)
            if frequency == 'M':
                periods = category["TimePeriod"].to_list()
                refd = [str(per).replace('M',"-") for per in periods]
                idx = pd.PeriodIndex(refd,freq = frequency)
                category.drop("TimePeriod",axis=1,inplace=True)
            else:
                idx = pd.PeriodIndex(category["TimePeriod"],freq = frequency)
            dtI = idx.to_timestamp(freq=frequency, how='start')
            category.set_index(dtI,inplace=True)
            catSeries = pd.Series(category["DataValue"],name=cat)
            names.append(cat); codes.append(str(category['SeriesCode'][0]))

            if i == 0:
                FinalData = catSeries.copy()
            else:
                if len(FinalData.index.difference(catSeries.index)) > 0:
                    NanSeries = pd.Series(np.nan,index=FinalData.index.difference(catSeries.index))
                    bilp = pd.concat([NanSeries,catSeries],axis=0); bilp.rename(catSeries.name,inplace=True)
                    if (FinalData.index.is_monotonic_increasing or FinalData.index.is_monotonic_decreasing) and \
                        (bilp.index.is_monotonic_increasing or bilp.index.is_monotonic_decreasing):
                            bilp = bilp.sort_index().reindex(index=FinalData.index.sort_values(), method='pad')
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
        if self.Data is not None:
            Export["Data"] = self.Data.copy()
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
            seriesInfo = pd.Series(self.Data['SeriesInfo'])
        if data is not None:
            pass
        else:    
            data = pd.DataFrame(self.Data['Series_Split'])

        colors = list(plt.rcParams['axes.prop_cycle'].by_key()['color']); i = 0
        xkcd_colors = list(mcolors.XKCD_COLORS.keys())
        colors.extend(Mycolors); colors.extend(xkcd_colors)
        
        for col in data.columns:
            ax.plot(data[col],label=col, color = colors[i]); i += 1    
        ax.legend(fontsize=5,loc=2,bbox_to_anchor=(1.005,1.01))
        
        ax.set_yscale(YScale); 
        if title is not None:
            ax.set_title(title,fontweight='bold',fontsize=9,loc='left',x = 0.1)
        else:    
            ax.set_title(self.Data_name,fontweight='bold',fontsize=9,loc='left',x = 0.1)
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
        plt.show()       
        
    def ExportCustomIndex(self, savePath):
        if self.Data is not None:
            data = self.Data['Series_Split']
        else:
            print('Load NIPA table data from BEA first.')    

class CustomIndexWindow(ctk.CTkToplevel):

    def __init__(self, master, dataTable:dict, name: str = 'Dataset', exportPath:str = parent+FDel+'Generic_Macro'+FDel+'SavedData'+FDel+'BEA'):
        super().__init__(master)
        default_font = ctk.CTkFont('Arial',13)
        self.data = pd.DataFrame(dataTable['Series_Split'])
        self.SeriesInfo = pd.DataFrame(dataTable['SeriesInfo']).copy().squeeze()
        
        self.notes = pd.DataFrame(dataTable['Notes']); self.notes.set_index("NoteRef",inplace=True)
        print(self.notes)
        if len(self.notes.columns) > 1:
            self.notes.drop(self.notes.columns[0],axis=1,inplace=True)
        print("NOTES: ", self.notes)
        self.notes = self.notes.copy().squeeze()

        TabName = str(self.notes[0])
        self.data_name = TabName.split('[')[0]
        self.title('Export custom index')

        self.choices = ctk.StringVar(self, value="", name = 'Index_Series')
        self.components = ctk.StringVar(self, value=self.data.columns.to_list(), name = 'ListComponents')
        self.ExportPath = ctk.StringVar(self, value= exportPath, name = 'Export_path')
        self.C_Index_name = ctk.StringVar(self, value="Custom_Index", name = 'Export_name')
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
        Operation.grid(column=0,row=0,padx=10,pady=10)
        plot = ctk.CTkButton(self.frame2, text="Show Index & components",font=('Arial',12,'bold'),text_color='gold',command=self.PlotButton)
        plot.grid(column=1,row=0,padx=10,pady=10)

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
    
    def ExportIndex(self):   #Save the custom index series to disk. 
        name = self.C_Index_name.get()
        filename = self.ExportPath+FDel+name+'.xlsx'; print(filename)
        print('Saving custom index series as: ',filename)
        self.C_Index.to_excel(filename,sheet_name='Closing_Price')
        with pd.ExcelWriter(filename, engine='openpyxl', mode='a') as writer:  
            self.SeriesInfo.to_excel(writer, sheet_name='SeriesInfo')
       
    def PlotIndex(self, C_Index:pd.Series, YScale:str='linear', title: str = None):     #Chart template.
        plt.rcParams['font.family'] = 'serif'
        fig = plt.figure(figsize=(11, 5), dpi=150)
        fig.suptitle('U.S Bureau of Economic Analysis, custom Index', fontweight='bold')
        ax = fig.add_axes(rect=[0.07,0.06,0.85,0.84])
        
        seriesInfo = pd.Series(self.SeriesInfo)
        data = pd.DataFrame(self.data)
        LeftTraces = self.ChoiceList.copy()
        numColors = len(LeftTraces) + 1
        colors = list(plt.rcParams['axes.prop_cycle'].by_key()['color']); i = 0
        moreColors = Utilities.Colors('viridis',num_colors=numColors)
        colors.extend(moreColors)
        
        for trace in LeftTraces:
            ax.plot(data[trace],label=trace, color = colors[i]); i += 1
        ax.legend(fontsize=7,loc=2)
        axb = ax.twinx()
        axb.plot(C_Index,label = self.C_Index_name.get()+' (right axis)',lw=2.25, color = colors[i])
        axb.legend(fontsize=7,loc=1)
        
        ax.set_yscale(YScale); 
        axb.set_yscale(YScale)
        if title is not None:
            ax.set_title(title,fontweight='bold',fontsize=9,loc='left',x = 0.1)
        else:    
            ax.set_title(self.C_Index_name,fontweight='bold',fontsize=9,loc='left',x = 0.1)
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
       
        ax.set_ylabel(yLabel,fontweight='bold',fontsize=9); axb.set_ylabel(yLabel,fontweight='bold',fontsize=9)
        ax.tick_params(axis='both',labelsize=8); axb.tick_params(axis='both',labelsize=8)
        ax.minorticks_on(); axb.minorticks_on()
        ax.grid(visible=True,axis='both',which='both',lw=0.5,color='gray',ls=':')      
        ax.margins(0.01,0.01)    
        for axis in ['top','bottom','left','right']:
                ax.spines[axis].set_linewidth(1.5)    
        plt.tight_layout() # This will ensure everything fits well 
        return fig        
 
    def PlotButton(self):      ##Construct custom index and chart index along with components of index.
        comps = self.ChoiceList.copy(); compsStr = ""
        indx = self.choiceIndexList.copy()
        for comp in comps:
            compsStr += comp
        print('Making custom index from: ',comps)
        data = self.data
        Cindex = pd.Series(0, index = data.index)
        name = self.C_Index_name.get()
        opString = self.operationString.get()
        print('Will save custom index with name: ', name)

        if len(opString) > 0:
            smo = Utilities.StringMathOp(data, comps, indx)
            smo.func(opString)
            print('Custom index made using math indicated in the operationString: ', opString)
            Cindex = pd.Series(smo.ComputedIndex.copy().to_list(), name = 'Custom_Index', index = self.data.index)
            print('Custom index...:',Cindex)
        else:
            print('Adding the index components to produce custom index as no custom operation string provided.')
            for col in comps:
                series = data[col]
                Cindex = Cindex + series
        Cindex.rename(name) ; print('Custom index: ',Cindex)

        #print('Series Info: ',self.SeriesInfo)
        ExtraInfo = {'units': str(self.SeriesInfo['CL_UNIT'])+r'(x10$^'+str(self.SeriesInfo['UNIT_MULT'])+r'$)',
                     'units_short': str(self.SeriesInfo['CL_UNIT'])+r'(x10$^'+str(self.SeriesInfo['UNIT_MULT'])+r'$)',
                     'id':name, 'title': 'Custom index: '+compsStr}
        info = pd.Series(ExtraInfo)
        self.SeriesInfo = pd.concat([self.SeriesInfo,info])
        self.C_Index = Cindex
        
        info = pd.Series(ExtraInfo.values(),index=ExtraInfo.keys()) 
        fig = self.PlotIndex(self.C_Index, title = self.C_Index_name) 
        plt.show()

    def ResetBox(self):
        self.ChoiceList = []
        self.choices.set("")
        self.choiceIndexList = []
        self.choiceIndex.set("")

    def SetExpPath(self):
        folder_selected = filedialog.askdirectory(initialdir=self.ExportPath)
        self.ExportPath.set(folder_selected)  

if __name__ == "__main__":
    api_key='779F26DA-1DB0-4CC2-94DD-2AE3492DA4FC'
    dataset = "NIPA"
    parameterName = "Tablename"
   
    filepath = wd+"/Datasets/BEAAPI_Info.xlsx"

    # Initalize the new Client.
    bea = BEA_Data(api_key=api_key,BEA_Info_filePath=filepath, Refresh_Info=False)
    print(bea.BEAAPI_InfoTables)
    print(bea.DataSetList, bea.SheetsList, bea.DSTables)

    #tCode = 'T20805'
    # tCode = 'T11705'
    # frequency="Q"
    # print("Pulling data from BEA API for: ",tCode)
    # results = {}; 

    # yearList = []
    # yearStr = ""
    # yearOne = 2000
    # endYear = datetime.datetime.today().year
    
    # for i in range(yearOne,endYear+1,1):
    #     yearList.append(str(i))
    #     if i < endYear:
    #         yearStr += str(i)+','
    #     else:
    #         yearStr += str(i)
    # print(yearList,yearStr)    
 
    # bea.Get_NIPA_Data(tCode,frequency=frequency,year=year)

    # test = "https://apps.bea.gov/api/data/?&SeriesId=30&UserID="+api_key+"&method=GetData&DataSetName=MNE&Year="+yearStr+"&Country=650,699\
    #     &DirectionOfInvestment=Outward&Classification=Country&ResultFormat=json"
    # r = requests.get(test).json()
    # pprint(r)

    # data = pd.DataFrame(bea.NIPA_Data['Series_Split']); print(data.head(50),data.dtypes)
    # SeriesInfo = bea.NIPA_Data['SeriesInfo']
    # loadPath = "C:/Users/jimmi/OneDrive/Documents/Documents/Scripts/VenV/Plebs_Macro/MacroBackend/BEA_Data/Datasets/T20805.xlsx"
    # FullLoad = pd.read_excel(loadPath,sheet_name=None)
    # print(FullLoad.keys())
    # TheData = FullLoad['Series_Split']
    # SeriesInfo = FullLoad['SeriesInfo']
    # Notes = FullLoad['Notes']
    # TheData.set_index(TheData.columns[0],inplace=True); SeriesInfo.set_index(SeriesInfo.columns[0],inplace=True)
    # SeriesInfo = pd.Series(SeriesInfo.squeeze(),name='SeriesInfo'); TheData.index.rename('TimePeriod',inplace=True)
    # TabName = str(Notes['NoteText'][0])
    # tDesc = TabName.split('[')[0]
    # print(tDesc,TheData,SeriesInfo)
    
    # fig = bea.BEAPreviewPlot(data=TheData,YScale="log",seriesInfo=SeriesInfo,title=tDesc)
    # plt.show()
    # bea.Export_BEA_Data(['T20805_PCE_M'])
    # ############# Export data to Excel. 
    # savePath = wd+"/Datasets/"+tCode+".xlsx"

    # def BringItUp():
    # exportWindow = CustomIndexWindow(main, FullLoad,tDesc)  
    # main = ctk.CTk()
    # but = ctk.CTkButton(main, text='WINDOW',command=BringItUp)
    # but.pack()
    # main.mainloop()