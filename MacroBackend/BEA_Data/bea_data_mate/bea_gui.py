import os
wd = os.path.dirname(__file__)  ## This gets the working directory which is the folder where you have placed this .py file. 
parent = os.path.dirname(wd); grandpa = os.path.dirname(parent); ancestor = os.path.dirname(grandpa)
print('Working directory: ',wd,'\n, parent folder',parent, '\nlevel above that: ', grandpa, '\nnext one up: ',ancestor)
import sys;
sys.path.append(parent); sys.path.append(ancestor)
from MacroBackend import Utilities ## Don't worry if your IDE shows that this module can't be found, it should stil work. 

import customtkinter as ctk
ctk.set_appearance_mode("light")
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkFont
from tkinter import filedialog, messagebox
import tkinter.tix as tix
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("QtAgg")

import json
import datetime
from bea_data_mate import BEA_API_backend

###### Determine what OS this is running on and get appropriate path delimiter. #########
fdel = os.path.sep
print("Operating system: ",sys.platform, "Path separator character: ", fdel)

######### Set default font and fontsize ##################### Make this automatic and hide in utility files later on. 
No_ScreenSettings = False; OldSesh = None
try:
    ScreenSetFile = open(grandpa+fdel+'SystemInfo'+fdel+'ScreenData.json')
    ScreenSettings = dict(json.load(ScreenSetFile))
    OldSesh = {'OS': ScreenSettings['OS'], 'USER': ScreenSettings['USER']}
except: 
    No_ScreenSettings = True    

####### GET OS AND PLATFORM INFORMATION ########################################
if sys.platform == 'win32':
    username = os.environ['USERNAME']
else: 
    username = os.environ['USER']
SessionCheck = {'OS': sys.platform, 'USER': username}

if OldSesh is None or SessionCheck != OldSesh or No_ScreenSettings:
    SingleDisplay = messagebox.askyesno(title='GUI sizing steup',message='Script has detected that this is the first time this script has been run on this system.\
        Script will now measure screen size to correctly size GUI. You must run this process with only a single display running on the system. \
            Make sure that you set system to single display mode first and then run script. You can go back to multiple screens after running the script once.\
                Is system set to single display mode?')
    if SingleDisplay is True:
        tkVars = Utilities.TkinterSizingVars()
        tkVars.SetScreenInfoFile()
        tkVars.ExportVars()
        ScreenSettings = tkVars.ScreenData

defCharWid = ScreenSettings['Def_font']['char_width (pixels)']; ###Width of an average character for tkinter widgets. 
defCharH = ScreenSettings['Def_font']['char_height (pixels)']
screen_width = ScreenSettings['Screen_width']; screen_height = ScreenSettings['Screen_height']
win_widthT = round(0.6*screen_width); win_heightT = round(0.5*screen_height)
win_widChars = round(win_widthT/defCharWid); win_HChars = round(win_heightT/defCharH)

print(ScreenSettings,win_widthT,win_heightT,win_widChars,win_HChars)

# Initalize the new BEA client.
keyz = Utilities.api_keys()
api_key= keyz.keys['bea']
defPath = parent+fdel+'Datasets'+fdel+'BEAAPI_Info.xlsx' ## This deafult path should lead to an excel file that has info on BEAAPI.
bea = BEA_API_backend.BEA_Data(api_key=api_key,BEA_Info_filePath=defPath)

######## Tkinter initialization #########################################
root = ctk.CTk()
default_font = tkFont.nametofont("TkDefaultFont")
root.title('Bureau of Economic Analysis Data Downloader')

## Arrange the sections on the GUI as grid. 
root.columnconfigure(0,weight=1,minsize=win_widthT)
root.rowconfigure(0,weight=3); root.rowconfigure(1,weight=4); root.rowconfigure(2,weight=3)
root.rowconfigure(3,weight=3); root.rowconfigure(4,weight=3)

## Define the sections on the GUI as grid. 
top = ctk.CTkFrame(root,width=win_widthT); top.grid(column=0,row=0,padx=10,pady=5)
middle = ctk.CTkFrame(root,width=win_widthT); middle.grid(column=0,row=1,padx=10,pady=5)
bottom = ctk.CTkFrame(root,width=win_widthT); bottom.grid(column=0,row=2,padx=10,pady=5)
bottom2 = ctk.CTkFrame(root,width=win_widthT); bottom2.grid(column=0,row=3,padx=10,pady=5)
bottom3 = ctk.CTkFrame(root,width=win_widthT); bottom3.grid(column=0,row=4,padx=10,pady=5)

def SearchBtn():   #Search through a dataframe containing data that can be pulled from BEA API.
    loadPath = path.get(); term = searchTerm.get()
    print("Search term original: ",term)
    TheDataSet = DataSet.get()

    ridEm = {"(":"",")":"","'":"","'":"",",":""}
    for char in ridEm.keys():
        # term = term.replace(char,ridEm[char])
        loadPath = loadPath.replace(char,ridEm[char])
    print("Search term butchered: ",term)    
    print('Will search for ',term,', amoungst dataset: ',TheDataSet,'\n',loadPath)
    DS_Name = TheDataSet+'_Tables'
    df = bea.BEAAPI_InfoTables[DS_Name]
    results = SearchMetrics(df,term)
    
    result = results['Description'].to_list(); finRes = []
    TCodes = results.index.to_list()
    for res in result:
        finRes.append(res+"!")
    SearchResults.set(finRes)
    TableNames.set(TCodes)

def SearchMetrics(MetricsList, SearchString:str): 
    if type(MetricsList) == str:  
        df = pd.read_excel(MetricsList,sheet_name='NIPA_Tables')  #Load the GNMetrics list as pandas dataframe. 
        df.set_index(df.columns[0],inplace=True); df.index.rename('Index',inplace=True) 
    elif str(type(MetricsList) == "<class 'pandas.core.frame.DataFrame'>"):
        df = MetricsList
    else:
        print('List must be supplied as a dataframe or as a str containing a path to an excel file to load the dataframe from.')    
        quit()

    #Set your serach term here. Wildcard characters (*) not needed. Will list all partial matches. Case insensitive. 
    matchDF = Utilities.Search_DF(df, SearchString)  #search 
    return matchDF

def MakeChoice(event):
    cs = result_box.curselection()
    SearchList = SearchResults.get()
    TableNameList = str(TableNames.get()).split(",")
    lisT = SearchList.split("!")
    chosen = str(lisT[cs[0]]); chosen = chosen[4:len(chosen)]
    TheTable = str(TableNameList[cs[0]]).replace("'","").replace("(","").replace(")","").replace(" ","")
    choice.set(chosen)
    TableName.set(TheTable)
    print(TheTable, chosen)
    frequencies = []; TableDescList = chosen.split(" ")
    for fre in ["(A)","(Q)","(M)"]:
        if fre in TableDescList:
            frequencies.append(fre[1:2])      
    freqs.configure(values=frequencies)
    freq.set(frequencies[0])

def PullBEASeries():
    TheDataSet = DataSet.get(); print('Looking for data from the ', TheDataSet, ' dataset from BEA.')
    tCode = str(TableName.get()).replace("'","").replace("(","").replace(")","").replace(" ","")
    TableDesc = str(choice.get()).replace("'","")
    
    data = None
    SeriesFreq = freq.get(); year = []
    startY = StartDate.get(); endY = EndDate.get()
    if len(startY) == 0:
        year = "ALL"
    if len(endY) == 0:    
        endY = datetime.date.today().year
    if type(year) == list:
        for i in range(int(startY),int(endY)+1,1):
            year.append(str(i))    
    
    bea.Get_BEA_Data(dataset=TheDataSet,tCode=tCode,frequency=SeriesFreq,year=year)
    if bea.Data is not None:
        data = bea.Data
    else:
        print('Data pull failed, check error message from BEA API above.')
        return     
   
    if data is not None:
        table = pd.DataFrame(data['Series_Split'])
        dates = pd.DatetimeIndex(table.index); dateIndex = pd.Index(dates.date)
        datelist = dateIndex.to_list()
        print('Preview of the table pulled form BEA: ',table)

        ######### Display the data for the metric #####################
        new_win = tk.Toplevel(root)
        tree = ttk.Treeview(new_win,columns=[],show='headings',height=35)
        tree.grid(column=0,row=0,sticky='nw',padx=5,pady=5)
        allCols = table.columns.to_list(); allCols.insert(0,'Date')
        Data.set(table.to_json()); Date.set(datelist)
        cols.set(allCols) 
        tree["columns"] = allCols
        for col in tree['columns']:
            tree.column(col,width=round((0.9*screen_width)/len(allCols)))
            tree.heading(col,text=col)
        for i in range(len(table)):
            values = table.iloc[i].tolist(); values.insert(0,dates[i])
            tree.insert('',tk.END,values=values)  
    else:
        print('No data..')        
        return None

######## Plot preview ###################################
def plotPreview():
    dateStr = Date.get(); dataStr = Data.get()
    ep = choice.get(); split = ep.split('/'); name = split[len(split)-1]
    ridEm = {"(":"",")":"","'":"","'":""}
    for char in ridEm.keys():
        dateStr = dateStr.replace(char,ridEm[char]) 
    dateList = dateStr.split(',')
    dates = pd.DatetimeIndex(dateList)
    dataStr = dict(json.loads(dataStr))
    yScale = YAxis.get()
    figure = bea.BEAPreviewPlot(YScale=yScale)
    plt.show()       

def SetSavingPath():
    folder_selected = filedialog.askdirectory(initialdir=savePath)
    save.set(folder_selected)     

def SaveData():
    folder = save.get()
    if bea.Data is not None:
        name = bea.Data_tCode
    bea.Export_BEA_Data([name],saveLoc=folder+fdel)
    
def CustomExport():
    if bea.Data is not None:
        exportWindow = BEA_API_backend.CustomIndexWindow(root, bea.Data, name=bea.Data_name)
    else:
        print('Load data first.....')    

def custom_fi():
    FI_window = BEA_API_backend.Custom_FisherIndex(root)

def open_info_window(title: str, info_text: str):
    info_window = Utilities.InfoWindow(root, title, info_text)
    info_window.open()  

######## Define and arange the features on the GUI window 
path = ctk.StringVar(master=root,value=defPath,name='Data folder path.')
searchTerm = ctk.StringVar(master=root,value="",name='SearchTerm')
SearchResults = ctk.StringVar(master=root,value="",name='SearchResults')
TableNames = ctk.StringVar(master=root,value="",name='TableNamesList')
TableName = ctk.StringVar(master=root,value="",name='TableName')
choice = ctk.StringVar(master=root,value="",name='Table choice')
freq = ctk.StringVar(master=root,value="",name='Series frequency')
DataSet = ctk.StringVar(master=root,value="NIPA",name='DataSet')

StartDate = ctk.StringVar(master=root,value="",name='StartDate')
EndDate = ctk.StringVar(master=root,value="",name='EndDate')

############## Variables for plotting data...
Date = ctk.StringVar(master=root,value="",name='DataDateColumn')
Data = ctk.StringVar(master=root,value="",name='DataColumn')
cols = ctk.StringVar(master=root,value="",name='DataColumns')
YAxis = ctk.StringVar(master=root,value='linear',name="Yaxis_Scale")
savePath = parent+fdel+'Datasets'; export = ancestor+fdel+'User_Data'+fdel+'BEA'

save = ctk.StringVar(master=root,value=savePath,name='DataSavePath')
ExportPath = ctk.StringVar(master=root,value=export,name='Export_Path')
components = ctk.StringVar(master=root,value="",name='IndexComponents')
choices = ctk.StringVar(master=root,value="",name='Chosen_series')
C_Index = ctk.StringVar(master=root,value="",name='Custom_index_name')

########### Search bar and tings.
pathBar = ctk.CTkEntry(top,width=round(0.95*win_widthT),textvariable=path); pathBar.grid(column=0,row=0,columnspan=5,padx=10,pady=5)
dsLabel = ctk.CTkLabel(top, text = 'DATASET', font=('Arial', 12, 'bold')); dsLabel.grid(column=0,row=1,padx=5)
choose_ds = ctk.CTkOptionMenu(top, values = bea.DSTables, variable=DataSet); choose_ds.grid(column=0,row=2,padx=5,pady=2)
choose_ds = ctk.CTkOptionMenu(top, values = bea.DSTables, variable=DataSet); choose_ds.grid(column=0,row=2,padx=5,pady=2)
DatasetInfo = "BEA API has some 13 or so different datasets that you can choose to pull data from.\n Currently only the NIPA, NIPA details and Fixed Asset\
    datasets are supported. These are: \n NIPA: National Income and Product Accounts. \n This is the most important dataset available at BEA, containing data tables \n\
such as GDP and components and PCE. \n NIPA_Details: This has the same NIPA data in more detail. \n Fixed__Assets: \nThis has fixed investment data such as manufacturing construction."

helpBtn = ctk.CTkButton(top, width = round(defCharWid*2), height = round(defCharWid*3), text = "?", 
                        command = lambda: open_info_window("Choose BEA Dataset", DatasetInfo)); helpBtn.grid(column=0, sticky = 'e', row=2,padx=2,pady=2)
searchLabel = ctk.CTkLabel(top, text = 'Enter search term/s separated by ","', font=('Arial', 11)); searchLabel.grid(column=1,row=1,padx=5)
searchTerm = ctk.CTkEntry(top); searchTerm.grid(column=1,row=2,padx=5,pady=2)
searchTerm = ctk.CTkEntry(top); searchTerm.grid(column=1,row=2,padx=5,pady=2)
btn=ctk.CTkButton(top, text="Search for data",text_color='black',command=SearchBtn,font=('Arial',12, 'bold'),border_width=1)
btn.grid(column=2,row=2,padx=5,pady=2)
btn_hover = Utilities.HoverInfo(btn, text = "Search through the BEA data \ntables in the current DATASET.")
flabel = ctk.CTkLabel(top,text='Data frequency',font=('Arial',12,'bold')) ; flabel.grid(column=4,row=1)
freqs = ctk.CTkOptionMenu(top,values=[""],variable=freq); freqs.grid(column=4,row=2,padx=30,pady=2)

# Create a text box to display the results
result_box = tk.Listbox(middle,listvariable=SearchResults, font = default_font, height=round(250/defCharH), width=round(win_widChars*0.93), background="white", foreground="black")
result_box.bind('<Double-1>', MakeChoice)
print(result_box.config)
result_box.pack(padx=30,pady=15)

# ########### Start and end dates #################################
bottom.columnconfigure(0,weight=1,minsize=np.floor(win_widthT/4)*0.97); bottom.columnconfigure(1,weight=1,minsize=np.floor(win_widthT/4)*0.97)
bottom.columnconfigure(2,weight=1,minsize=np.floor(win_widthT/4)*0.97); bottom.columnconfigure(3,weight=1,minsize=np.floor(win_widthT/4)*0.97)
GetDataBtn = ctk.CTkButton(bottom, text="Get data", text_color='black',command=PullBEASeries,font=('Arial',13,'bold'),border_width=1); GetDataBtn.grid(column=2,row=0,pady=5)
hovInfo = Utilities.HoverInfo(GetDataBtn, text = "Get selected data table from BEA API")

start = ctk.CTkEntry(bottom,textvariable=StartDate); start.grid(column=0,row=0,sticky='w',pady=5,padx=15)
sLabel = ctk.CTkLabel(bottom,text='Start year\nblank = "All years"',font=('Arial',10)) ; sLabel.grid(column=0,row=0,sticky='e',pady=35)
end = ctk.CTkEntry(bottom,textvariable=EndDate); end.grid(column=1,row=0,sticky='w',pady=5,padx=15)
eLabel = ctk.CTkLabel(bottom,text='End year\nblank = latest data',font=('Arial',10)); eLabel.grid(column=1,row=0,sticky='e',pady=35)
SaveBtn=ctk.CTkButton(bottom, text="Export data",text_color='black', command=SaveData,font=('Arial',13,'bold'),border_width=1); SaveBtn.grid(column=3,row=0,pady=10)

options = ['linear','log']
bottom2.columnconfigure(0,weight=1,minsize=np.floor(win_widthT/4)*0.97); bottom2.columnconfigure(1,weight=1,minsize=np.floor(win_widthT/4)*0.97)
bottom2.columnconfigure(2,weight=1,minsize=np.floor(win_widthT/4)*0.97); bottom2.columnconfigure(3,weight=1,minsize=np.floor(win_widthT/4)*0.97)
drop = ctk.CTkOptionMenu(bottom2,variable=YAxis,values=options); drop.grid(column=0,sticky='w',row=0,padx=20,pady=10)
dLabel = ctk.CTkLabel(bottom2,text='Chart Y-scale.',font=('Arial',11)); dLabel.grid(column=0,row=0,sticky='e')
plot_button = ctk.CTkButton(bottom2, text="Preview data", text_color='yellow', font=('Arial',13,'bold'),command=plotPreview,border_width=1)
plot_button.grid(column=1,row=0,pady=10)
CustomIndex=ctk.CTkButton(bottom2, text="Individual Series Analysis",text_color='orange',command=CustomExport,font=('Arial',14,'bold'),border_width=1)
CustomIndex.grid(column=2,row=0,pady=10)
Custom_FI = ctk.CTkButton(bottom2, text="Custom Fisher index",command=custom_fi, text_color='tomato', font=('Arial',14,'bold'),border_width=1) 
Custom_FI.grid(column=3,row=0,pady=10)

savePathDisplay =ctk.CTkEntry(bottom3,textvariable=save,width=round(0.79*win_widthT)); savePathDisplay.grid(column=0,row=0,columnspan=3,padx=10,pady=5)
SetSavePath = ctk.CTkButton(bottom3, text="Set save path",text_color='white', font=('Arial',13,'bold'), command=SetSavingPath,border_width=1)
SetSavePath.grid(column=3,row=0,padx=10,pady=5)

##Put this into a functin so that the GUI won't run until fuunction called.
def Run_BEA_GUI(window: ctk.CTk):
## Run the loop that brings up the GUI and keeps it there.
    window.mainloop()

if __name__ == "__main__":
    Run_BEA_GUI(root)