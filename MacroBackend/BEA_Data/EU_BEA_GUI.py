import customtkinter as ctk
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import datetime
import os
import sys
wd = os.path.dirname(__file__)
from BEA_API_backend import BEA_Data
import BEA_API_backend
from fontTools.ttLib import TTFont

######### Set default font and fontsize ##################### Make this automatic and hide in utility files later on. 
font = TTFont('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
DefaultFontSize = 12

cmap = font['cmap']
t = cmap.getcmap(3,1).cmap
s = font.getGlyphSet()
units_per_em = font['head'].unitsPerEm

def getTextWidth(text,pointSize):  #Width of a displayed string in points.
    total = 0
    for c in text:
        if ord(c) in t and t[ord(c)] in s:
            total += s[t[ord(c)]].width
        else:
            total += s['.notdef'].width
    total = total*float(pointSize)/units_per_em
    return total

string = 'abcdefghijklmnopqrstuvwxyz'; text = string+string.upper()
width = getTextWidth(text,DefaultFontSize); defCharWid = round(width/len(text))
# print('Text: "%s"' % text)
# print('Number of characters ',len(text))
# print('Width in points: %f' % width)
# print('Average character width in points:',defCharWid)

###### Determine what OS this is running on and get appropriate path delimiter. #########
FDel = os.path.sep
print("Operating system: ",sys.platform, "Path separator character: ", FDel)
wd = os.path.dirname(os.path.realpath(__file__))    #Get working directory.
dir = os.path.dirname(wd); parent = os.path.dirname(dir)

# Initalize the new BEA client.
api_key='779F26DA-1DB0-4CC2-94DD-2AE3492DA4FC'
defPath = wd+FDel+'Datasets'+FDel+'BEAAPI_Info.xlsx'
bea = BEA_Data(api_key=api_key,BEA_Info_filePath=defPath)

######## Tkinter initialization #########################################
root = ctk.CTk()
root.title('Bureau of Economic Analysis Data Downloader')
WindowWidthTarget = 800 #points
defCharWid_window = round(WindowWidthTarget/defCharWid); print(defCharWid_window)

def SearchBtn():
    loadPath = path.get(); term = searchTerm.get()
    print(loadPath)
    ridEm = {"(":"",")":"","'":"","'":"",",":""}
    for char in ridEm.keys():
        term = term.replace(char,ridEm[char])
        loadPath = loadPath.replace(char,ridEm[char])
    print(term,loadPath)
    results = SearchMetrics(loadPath,term)
    print(results)
    result = results['Description'].to_list(); finRes = []
    TCodes = results['TableName'].to_list()
    for res in result:
        finRes.append(res+"!")
    SearchResults.set(finRes)
    TableNames.set(TCodes)

def SearchMetrics(MetricsList, SearchString:str): 
    if type(MetricsList) == str:  
        df = pd.read_excel(MetricsList,sheet_name='NIPA_TableNames')  #Load the GNMetrics list as pandas dataframe. 
        df.set_index(df.columns[0],inplace=True); df.index.rename('Index',inplace=True) 
        print(df.head(50))
    elif str(type(MetricsList) == "<class 'pandas.core.frame.DataFrame'>"):
        pass
    else:
        print('List must be supplied as a dataframe or as a str containing a path to an excel file to load the dataframe from.')    
        quit()

    #Set your serach term here. Wildcard characters (*) not needed. Will list all partial matches. Case insensitive. 
    matches, match_indices, match_col, matchDF = BEA_API_backend.Search_df(df, SearchString)  #search 
    return matchDF

def MakeChoice(event):
    cs = result_box.curselection()
    SearchList = SearchResults.get()
    TableNameList = str(TableNames.get()).split(",")
    #ridEm = {"(":"",")":"","'":"","'":""}
    # for char in ridEm.keys():
    #     SearchList = SearchList.replace(char,ridEm[char])
    lisT = SearchList.split("!")
    chosen = str(lisT[cs[0]]); chosen = chosen[4:len(chosen)]
    TheTable = TableNameList[cs[0]]
    print(TheTable, chosen)
    choice.set(chosen)
    TableName.set(TheTable)
    frequencies = []; TableDescList = chosen.split(" ")
    for fre in ["(A)","(Q)","(M)"]:
        if fre in TableDescList:
            frequencies.append(fre[1:2])
    print(frequencies)        
    freqs.configure(values=frequencies)
    freq.set(frequencies[0])

def PullBEASeries():
    tCode = str(TableName.get()).replace("'","")
    tCode = tCode.replace(" ","")
    TableDesc = str(choice.get()).replace("'","")
    
    SeriesFreq = freq.get(); year = []
    startY = StartDate.get(); endY = EndDate.get()
    if len(startY) == 0:
        year = "ALL"
    if len(endY) == 0:    
        endY = datetime.date.today().year
    if type(year) == list:
        for i in range(int(startY),int(endY)+1,1):
            year.append(str(i))    

    bea.Get_NIPA_Data(tCode,frequency=SeriesFreq,tDesc=TableDesc,year=year)
    data = bea.NIPA_Data
   
    if data is not None:
        table = pd.DataFrame(data['Series_Split'])
        dates = pd.DatetimeIndex(table.index); dates.rename('TimePeriod',inplace=True)
        datelist = dates.to_list()
        print('Preview of the table pulled form BEA: ',table)

        ######### Display the data for the metric #####################
        new_win = tk.Toplevel(root)
        tree = ttk.Treeview(new_win,columns=[],show='headings',height=35)
        tree.grid(column=0,row=0,sticky='nw',padx=5,pady=5)
        allCols = table.columns.to_list(); allCols.insert(0,'Date')
        Data.set(table.to_json()); Date.set(datelist)
        print(allCols)
        cols.set(allCols) 
        tree["columns"] = allCols
        for col in tree['columns']:
            tree.column(col,width=round((1000/defCharWid)))
            tree.heading(col,text=col)
        for i in range(len(table)):
            values = table.iloc[i].tolist(); values.insert(0,dates[i])
            tree.insert('',tk.END,values=values)  

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
    figure = bea.BEAPreviewPlot(yScale)

    plt.show()       

def SetSavingPath():
    folder_selected = filedialog.askdirectory(initialdir=savePath)
    save.set(folder_selected)     

def SaveData():
    folder = save.get()
    if bea.NIPA_Data is not None:
        name = bea.NIPA_Data_tCode
    bea.Export_BEA_Data([name],saveLoc=folder+FDel)

path = ctk.StringVar(master=root,value=defPath,name='Data folder path.')
searchTerm = ctk.StringVar(master=root,value="",name='SearchTerm')
SearchResults = ctk.StringVar(master=root,value="",name='SearchResults')
TableNames = ctk.StringVar(master=root,value="",name='TableNamesList')
TableName = ctk.StringVar(master=root,value="",name='TableName')
choice = ctk.StringVar(master=root,value="",name='Table choice')
freq = ctk.StringVar(master=root,value="",name='Series frequency')
StartDate = ctk.StringVar(master=root,value="",name='StartDate')
EndDate = ctk.StringVar(master=root,value="",name='EndDate')

############## Variables for plotting data...
Date = ctk.StringVar(master=root,value="",name='DataDateColumn')
Data = ctk.StringVar(master=root,value="",name='DataColumn')
cols = ctk.StringVar(master=root,value="",name='DataColumns')
YAxis = ctk.StringVar(master=root,value='linear',name="Yaxis_Scale")

savePath = wd+FDel+'Datasets'
save = ctk.StringVar(master=root,value=savePath,name='DataSavePath')

########### Load the excel file containing the dataframe with list of metrics from glassnode 
pathBar = ctk.CTkEntry(root,width=600,textvariable=path); pathBar.grid(column=0,row=0,sticky='nsew',padx=10,pady=10)
searchTerm = ctk.CTkEntry(root); searchTerm.grid(column=0,row=1,sticky='w',padx=10,pady=5)
btn=ctk.CTkButton(root, text="Search for data",command=SearchBtn,font=('Arial',12)); btn.grid(column=0,row=1,padx=10,pady=5)
freqs = ctk.CTkOptionMenu(root,values=[""],variable=freq); freqs.grid(column=0,row=1,sticky='e',padx=20,pady=5)
flabel = ctk.CTkLabel(root,text='Data frequency',font=('Arial',11,'bold')) ; flabel.grid(column=0,row=1,sticky='e',padx=170,pady=5)

# Create a text box to display the results
result_box = tk.Listbox(root,listvariable=SearchResults, height=round(140/defCharWid), width=defCharWid_window); result_box.bind('<Double-1>', MakeChoice)
result_box.grid(column=0,row=2,padx=10,pady=10)
GetDataBtn = ctk.CTkButton(root, text="Get data series",command=PullBEASeries,font=('Arial',12))
GetDataBtn.grid(column=0,row=3,sticky='sw',padx=10,pady=30)

########### Start and end dates #################################
start = ctk.CTkEntry(root,textvariable=StartDate); start.grid(column=0,row=4,sticky='sw',padx=10,pady=30)
sLabel = ctk.CTkLabel(root,text='Starting year, blank = "All years"',font=('Arial',10)) ; sLabel.grid(column=0,row=4,sticky='nw',padx=10)
end = ctk.CTkEntry(root,textvariable=EndDate); end.grid(column=0,row=4,sticky='s',padx=200,pady=30)
eLabel = ctk.CTkLabel(root,text='End year, blank = latest data',font=('Arial',10)); eLabel.grid(column=0,row=4,sticky='n',padx=5)

options = ['linear','log']
drop = ctk.CTkOptionMenu(root,variable=YAxis,values=options); drop.grid(column=0,row=3,sticky='se',padx=10,pady=30)
dLabel = ctk.CTkLabel(root,text='Y-scaling for chart.',font=('Arial',12)); dLabel.grid(column=0,row=3,sticky='ne',padx=40,pady=0)
plot_button = ctk.CTkButton(root, text="Preview data",font=('Arial',12,'bold'), command=plotPreview); plot_button.grid(column=0,row=4,sticky='e',padx=10,pady=15)

SaveBtn=ctk.CTkButton(root, text="Export data",command=SaveData,font=('Arial',14,'bold')); SaveBtn.grid(column=0,row=3,padx=30,pady=5)
savePathDisplay =ctk.CTkEntry(root,textvariable=save,width=700); savePathDisplay.grid(column=0,row=6,sticky='w',padx=10,pady=5)
SetSavePath = ctk.CTkButton(root, text="Set save path",font=('Arial',12,'bold'),command=SetSavingPath); SetSavePath.grid(column=0,row=6,sticky='e',padx=20,pady=5)

#lb=ctk.CTkComboBox(top_frame,listvariable=path, height=1, width=100); lb.grid(column=0,row=1,padx=10,pady=10,columnspan=4,sticky='ew')
######### Search term entry bar and search Button. Search through the list of metrics. 

root.mainloop()