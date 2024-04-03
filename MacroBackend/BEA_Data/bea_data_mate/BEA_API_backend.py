import os
wd = os.path.dirname(__file__) 
fdel = os.path.sep
parent = os.path.dirname(wd); grampa = os.path.dirname(parent); ancestor = os.path.dirname(grampa)
import sys
sys.path.append(grampa); sys.path.append(ancestor)

from pybea.client import BureauEconomicAnalysisClient
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
from typing import Union
import customtkinter as ctk
import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog
from MacroBackend import Utilities
from pprint import pprint
import custom_FI

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
        plt.rcParams['figure.dpi'] = 200
        plt.rcParams['backend'] = 'tkagg'
        fig = plt.figure(figsize=(11, 5), dpi = 150)
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

class Custom_FisherIndex(ctk.CTkToplevel):     #Still working on this page................................................................

    def __init__(self, master, exportPath:str = parent+fdel+'Macro_Chartist'+fdel+'SavedData'+fdel+'BEA'):
        super().__init__(master)
        self.default_font = ctk.CTkFont('Arial',13)
        self.title("Create custom Fisher Index from BEA Data")
        self.catz_loadPath = ctk.StringVar(self, value=parent+fdel+"Categories"+fdel+'PCE.json', name = 'category_loadPath' )
        self.CD_loadPath = ctk.StringVar(self, value=parent+fdel+"Datasets"+fdel+"Annual"+fdel+'U20405.xlsx', name = 'CurrentDollar_loadPath' )
        self.PI_loadPath = ctk.StringVar(self, value=parent+fdel+"Datasets"+fdel+"Annual"+fdel+'U20404.xlsx', name = 'PriceIndexes_loadPath' )
        print('Init of load paths: ', self.catz_loadPath, '\n', self.CD_loadPath, '\n', self.PI_loadPath)

        self.set_load_paths = ctk.CTkButton(self, text="Load Category Data",font=('Arial',14,'bold'),command=self.set_paths)
        self.set_load_paths.grid(column = 0, row = 0,padx=15,pady=15)

        self.run_calc = ctk.CTkButton(self, text="Calculate Fisher Index",font=('Arial',14,'bold'),command=self.calc_FI)
        self.run_calc.grid(column = 1, row = 0,padx=15,pady=15)

        catzPath_label = ctk.CTkLabel(self, text="Category heirarchy (.json)", font = ('Arial', 14))
        catzPath_label.grid(column = 1, row = 1, sticky = "e", padx=5,pady=3)
        catzPath = ctk.CTkEntry(self,textvariable=self.catz_loadPath,font=self.default_font,width=self.default_font.measure(self.catz_loadPath.get())+20)
        catzPath.grid(column = 0, row = 1,sticky = "s",padx=5,pady=5, columnspan = 2)
        cdPath_label = ctk.CTkLabel(self, text="Current dollar data, pq (.xlsx)", font = ('Arial', 14))
        cdPath_label.grid(column = 1, row = 2, sticky = "e", padx=5,pady=3) #sticky = "e"
        cdPath = ctk.CTkEntry(self,textvariable=self.CD_loadPath,font=self.default_font,width=self.default_font.measure(self.CD_loadPath.get())+20)
        cdPath.grid(column = 0, row = 2,padx=5, pady=5, sticky = "s",columnspan = 2)
        piPath_label = ctk.CTkLabel(self, text="Price index data, p (.xlsx)", font = ('Arial', 14))
        piPath_label.grid(column = 1, row = 3, sticky = "e", padx=5,pady=3)
        piPath = ctk.CTkEntry(self,textvariable=self.PI_loadPath,font=self.default_font,width=self.default_font.measure(self.PI_loadPath.get())+20)
        piPath.grid(column = 0, row = 3,padx=5,pady=5, sticky = "s",columnspan = 2)

        self.init_fi_obj()

    def set_paths(self):
        self.catz_loadPath.set(filedialog.askopenfilename(parent=self,initialdir=parent,title="Choose .json file that contains lists of the aggregates and categories to use for your Fisher Index"))
        self.CD_loadPath .set(filedialog.askopenfilename(parent=self,initialdir=parent,title="Choose .xlsx file that contains the current dollar estimates data downloaded from BEA."))
        self.PI_loadPath.set(filedialog.askopenfilename(parent=self,initialdir=parent,title="Choose .xlsx file that contains the price index data downloaded from BEA."))

        self.init_fi_obj()

    def init_fi_obj(self):
        self.FI_obj = custom_FI.BEA_FisherIndex(self.CD_loadPath.get(), self.PI_loadPath.get(), self.catz_loadPath.get())
        self.base_catz = ctk.StringVar(self, value = self.FI_obj.BaseCatz, name = 'agg_lvl_1')
        self.catzlvl2 =  ctk.StringVar(self, value = [list(cat.keys())[0] for cat in self.FI_obj.ReducedCatz.Aggregate_level_2], name = 'agg_lvl_2')
        try:
            self.catzlvl3 = ctk.StringVar(self, value = [list(cat.keys())[0] for cat in self.FI_obj.ReducedCatz.Aggregate_level_3], name = 'agg_lvl_3')
        except:
            self.catzlvl3 = ctk.StringVar(self, value = "", name = 'agg_lvl_3')

        self.toExclude = ctk.StringVar(self, value = "", name = 'excluded')
        self.exclude = []

        def ChooseASeries(event, ListBox: tk.Listbox, cat_level: int = 1):
            curs = ListBox.curselection()
            exclude_list = [self.FI_obj.BaseCatz, self.FI_obj.ReducedCatz.Aggregate_level_2, 
                            self.FI_obj.ReducedCatz.Aggregate_level_3]
            to_add = exclude_list[cat_level - 1][curs[0]]
            if isinstance(to_add, str):
                self.exclude.append(to_add)
            elif isinstance(to_add, dict):
                basCatz = custom_FI.extract_lowest_level_data(to_add)
                self.exclude.extend(basCatz)
            elif isinstance(to_add, list):
                self.exclude.extend(to_add)     
            else:
                self.exclude.append("WhazuFuzzleMuzzle??") 
            self.toExclude.set(self.exclude)
        cat_title_font = ('Arial', 14, 'bold')

        lvl3_label = ctk.CTkLabel(self, text="Level 3 Aggregates", font = cat_title_font)
        lvl3_label.grid(column=0,row=4, padx=10, pady=5)
        catz_lvl3 = tk.Listbox(self,listvariable = self.catzlvl3, width=0, font=('Arial', 12), foreground='black', background='white')
        catz_lvl3.grid(column=0,row=5, padx=10,pady=2,ipadx=15,ipady=10)
        catz_lvl3.bind('<Double-1>', lambda event: ChooseASeries(event, catz_lvl3, cat_level=3))

        lvl2_label = ctk.CTkLabel(self, text="Level 2 Aggregates", font = cat_title_font)
        lvl2_label.grid(column=1,row=4, padx=10, pady=5)
        catz_lvl2 = tk.Listbox(self,listvariable = self.catzlvl2, width=0, font=('Arial', 12), foreground='black', background='white')
        catz_lvl2.grid(column=1,row=5,padx=10, pady=2,ipadx=15,ipady=10)
        catz_lvl2.bind('<Double-1>', lambda event: ChooseASeries(event, catz_lvl2, cat_level=2))

        bcz_label = ctk.CTkLabel(self, text="Base Categories", font = cat_title_font)
        bcz_label.grid(column=0,row=6, padx=10, pady=5)
        catz_all = tk.Listbox(self,listvariable = self.base_catz, width=0, font=('Arial',12), foreground='black', background='white')
        catz_all.bind('<Double-1>', lambda event: ChooseASeries(event, catz_all))
        catz_all.grid(column=0,row=7,padx=30,pady=2,ipadx=15,ipady=10)

        ex_label = ctk.CTkLabel(self, text="Excluded Base Categories", font = cat_title_font)
        ex_label.grid(column=1,row=6, padx=10, pady=5)
        excluded = tk.Listbox(self, listvariable =  self.toExclude, width=0, font=('Arial',12), foreground='black', background='white')
        excluded.grid(column=1,row=7,padx=30,pady=2,ipadx=15,ipady=10)

    def calc_FI(self):
        print('Calculating Fisher index from the supplied current dollar and price index datasets.\n\
              Excluding base categories from the calculation: ', self.toExclude)
        
        self.FI_obj.Calculate_FI()
        self.plotTitle =  ctk.StringVar(self, value = "Plot title                                                        ", name = 'Plot title')
        self.indexName =  ctk.StringVar(self, value = "Manual index name                                                 ", name = 'Manual index name')
        self.refIndex =  ctk.StringVar(self, value = "Reference index name", name = 'Reference index name')

        self.plot_title = ctk.CTkEntry(self, textvariable = self.plotTitle,font = self.default_font, width = self.default_font.measure(self.plotTitle.get())+50)
        self.plot_title.grid(column=0, row=8, padx=30, pady=10)
        self.indexEntry = ctk.CTkEntry(self,textvariable = self.indexName, font = self.default_font, width = self.default_font.measure(self.indexName.get())+50)
        self.indexEntry.grid(column=1, row=8, padx=30, pady=10)
        self.chooseRef = ctk.CTkOptionMenu(self, values = self.FI_obj.PCE_Data.columns, variable = self.refIndex, font = self.default_font, width=0)
        self.chooseRef.grid(column=0, row=9, padx=30, pady=10)
        
        self.plotIt = ctk.CTkButton(self, text="Plot Fisher Index", font=('Arial',14,'bold'), command=self.plot_FI)
        self.plotIt.grid(column=1, row=9, padx=30, pady=10)

    def plot_FI(self): 
        self.FI_obj.LoadRefData()
        self.FI_obj.PlotIndexSet(title = self.plotTitle.get(), manual_metricName = self.indexName.get(), official_metricName = self.refIndex.get())
        plt.show()

######### OMG Why Am I doing this to myself?? Tkinter sucks nutz. I'm going to use PyQt5 for the next one. ##########################################
        
class CustomIndexWindow(ctk.CTkToplevel):

    def __init__(self, master, dataTable:dict, name: str = 'Dataset', exportPath:str = ancestor+fdel+'User_Data'+fdel+'BEA'):
        super().__init__(master)
        default_font = ctk.CTkFont('Arial',13)
        self.data = pd.DataFrame(dataTable['Series_Split'])
        print('Input data for left column: ', self.data)

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
        checkBoxLab = ctk.StringVar(self, value="Plot agg. index RHS?", name = 'RHS_plot')

        self.frame1 = ctk.CTkFrame(self); self.frame2 = ctk.CTkFrame(self); self.frame3 = ctk.CTkFrame(self); self.frame4 = ctk.CTkFrame(self)
        self.frame1.grid(column=0,row=0,pady=20,padx=20); self.frame2.grid(column=0,row=1,pady=20,padx=20); 
        self.frame3.grid(column=0,row=2,pady=20,padx=20); self.frame4.grid(column=0,row=3,pady=20,padx=20)
        self.ChoiceList = []
        self.choiceIndex = ctk.StringVar(self, value="", name = 'Choice_Index')
        self.choiceIndexList = []
        self.plotRHS = ctk.BooleanVar(self, value = False, name = "plotRHS")

        def ChooseSeries(event):
            data = self.data
            series = data.columns.to_list()
            curs = SeriesList.curselection()
            self.ChoiceList.append(series[curs[0]])
            self.choices.set(self.ChoiceList)
            self.choiceIndexList.append(len(self.ChoiceList)-1)
            self.choiceIndex.set(self.choiceIndexList)
        
        SeriesList = tk.Listbox(self.frame1,listvariable=self.components, width=0, font=('Arial',12), foreground='black', background='white')
        SeriesList.bind('<Double-1>',ChooseSeries)
        # label = ctk.CTkLabel(self, text="Columns in NIPA table", font = ('Arial', 12)); label.grid(column=0,row=0,sticky='n',padx=3,pady=3)
        SeriesList.grid(column=0,row=0,padx=30,pady=5,ipadx=15,ipady=10)
        ChosenSeries = tk.Listbox(self.frame1,listvariable=self.choices, width=0, font=('Arial',12), foreground='black', background='white')
        ChosenSeries.grid(column=1,row=0,padx=30,pady=30,ipadx=15,ipady=10)
        indexBox = tk.Listbox(self.frame1,listvariable=self.choiceIndex, width=0, font=('Arial',12),justify='center', foreground='black', background='white')
        indexBox.grid(column=2,row=0,padx=15,pady=30,ipadx=5,ipady=10)

        op_label = ctk.CTkLabel(self.frame2,text = 'Math operation to run on series: e.g (0+1)/(2-3)')
        op_label.grid(column=0,row=0,padx=5,pady=1)
        Operation = ctk.CTkEntry(self.frame2,textvariable=self.operationString,font=default_font,width=round(default_font.measure(self.ExportPath.get())/2))
        Operation.grid(column=0,row=1,padx=10,pady=2)
        plot = ctk.CTkButton(self.frame2, text="Show Index & components",font=('Arial',12,'bold'),text_color='gold',command=self.PlotButton)
        plot.grid(column=1,row=1,padx=10,pady=2)
        ShowC_Index = ctk.CTkCheckBox(self.frame2, textvariable=checkBoxLab, variable = self.plotRHS); 
        ShowC_Index.grid(column=2,row=1,padx=10,pady=2)

        self.frame3.columnconfigure(0,weight=1); self.frame3.columnconfigure(1,weight=1)
        self.frame3.columnconfigure(2,weight=1); self.frame3.columnconfigure(3,weight=1)

        name_label = ctk.CTkLabel(self.frame3,text = 'Name for custom index')
        name_label.grid(column=0,row=0,padx=5,pady=1)
        Index_Name = ctk.CTkEntry(self.frame3,textvariable = self.C_Index_name)
        Index_Name.grid(column=0,row=1,padx=5,pady=2)
        reset = ctk.CTkButton(self.frame3, text="RESET",font=('Arial',13,'bold'),text_color='tomato',command=self.ResetBox)
        reset.grid(column=1,row=1,padx=10, pady = 2)
        SetExport = ctk.CTkButton(self.frame3, text="Set export path",font=('Arial',14,'bold'),command=self.SetExpPath)
        SetExport.grid(column=2,row=1,padx=10, pady = 2)
        ExportC_Index = ctk.CTkButton(self.frame3,font=('Arial',14,'bold'),text='Export Index',text_color='lime',command=self.ExportIndex) 
        ExportC_Index.grid(column=3,row=1,padx=10, pady = 2)
        
        ExpPath = ctk.CTkEntry(self.frame4,textvariable=self.ExportPath,font=default_font,width=default_font.measure(self.ExportPath.get()+'                '))
        ExpPath.grid(row = 0, column = 0, padx=10,pady=10)
    
    def ExportIndex(self):   #Save the custom index series to disk. 
        name = self.C_Index_name.get()
        filename = self.ExportPath.get()+fdel+name+'.xlsx'
        print('Saving custom index series as: ',filename)
        self.C_Index.to_excel(filename,sheet_name='Closing_Price')
        with pd.ExcelWriter(filename, engine='openpyxl', mode='a') as writer:  
            self.SeriesInfo.to_excel(writer, sheet_name='SeriesInfo')
       
    def PlotIndex(self, C_Index:pd.Series, YScale:str='linear', title: str = None):     #Chart template.
        plt.rcParams['font.family'] = 'serif'
        plt.rcParams['figure.dpi'] = 200
        plt.rcParams['backend'] = 'tkagg'
        
        fig = plt.figure(figsize=(11, 5), dpi=150)
        fig.suptitle('U.S Bureau of Economic Analysis, custom Index', fontweight='bold')
        ax = fig.add_axes(rect=[0.07,0.06,0.85,0.84])
        plot_RHS = self.plotRHS.get()
        
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
        if plot_RHS:
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
    keyz = Utilities.api_keys(JSONpath=grampa+fdel+'SystemInfo')
    api_key = keyz.keys['bea']
    dataset = "NIPA"
    parameterName = "Tablename"
   
    filepath = wd+"/Datasets/BEAAPI_Info.xlsx"

    bilp = BureauEconomicAnalysisClient(api_key=api_key)
    data = bilp.national_income_and_product_accounts(table_name='T20600', year = ["2022", "2023"], frequency= ["M"])
    