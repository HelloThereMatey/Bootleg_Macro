import tkinter as tk
from tkinter import *
from tkinter.ttk import Treeview
from tkinter import filedialog
import pandas as pd
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
import GlassNode_API 
import datetime
import time
import os
from sys import platform

wd = os.path.dirname(os.path.realpath(__file__))
dir = os.path.dirname(wd)
if platform == "linux" or platform == "linux2":
    FDel = '/' # linux
elif platform == "darwin":
    FDel = '/' # OS X#
elif platform == "win32":
    FDel = '\\' #Windows...

# Insert your glassnode API key here
API_KEY = GlassNode_API.API_KEY
defPath = wd+FDel+'Saved_Data'+FDel+'GN_MetricsList.xlsx'
savePath = wd+FDel+'Saved_Data'
plt.rcParams.update({'font.family':'serif'})   #Font family for the preview figure. 

root = Tk()
root.title('Pull data from Glassnode widget')
# Get the screen width and height
sw = root.winfo_screenwidth(); print('Screen width: ',sw)
sh = root.winfo_screenheight(); print('Screen height: ',sh)
ww = 0.47*sw; wh = 0.7*sh; print('Window width x height (pixels): '+str(ww)+' x '+str(wh))
frame = tk.Frame(root,width=ww,height=wh,background='white')
frame.pack(fill=tk.BOTH, expand=1)
frame.pack_propagate(0) #Prevent auto adjustment of windowframe. 
path = StringVar(master=root,value=defPath,name='GNMetricList_Path')
save = StringVar(master=root,value=savePath,name='DataSavePath')
SearchResults = StringVar(master=root,value="",name='SearchResults')
choice = StringVar(master=root,value="",name='Choice')
Date = StringVar(master=root,value="",name='DataDateColumn')
Data = StringVar(master=root,value="",name='DataColumn')
cols = StringVar(master=root,value="",name='DataColumns')
tier = StringVar(master=root,value="",name='Tier')
assets = StringVar(master=root,value="",name='Assets')
assChoice = StringVar(master=root,value="Asset",name='ChosenAsset')
currencies = StringVar(master=root,value="",name='Currencies')
currChoice = StringVar(master=root,value="Currency",name='CurrencyChoice')
resolutions = StringVar(master=root,value="",name='Resolutions')
resChoice = StringVar(master=root,value="Resolution",name='ResolutionChoice')
formats = StringVar(master=root,value="",name='Formats')
formChoice = StringVar(master=root,value="Data format",name='ChosenFormat')
SearchDisplay = StringVar(master=root,value="",name='SearchDisplay')
StartDate = StringVar(master=root,value="",name='StartDate')
EndDate = StringVar(master=root,value="",name='EndDate')
dataForm =  IntVar(master=root,value=0,name='Pandas data format')

def LoadPathBtn():
    file_selected = filedialog.askopenfilename()
    path.set(file_selected)
    print(file_selected)
    df = pd.read_excel(file_selected)
    df.set_index(df.columns[0],inplace=True); df.index.rename('Index',inplace=True) 
    print(df.tail(50))
    return file_selected

def update_text():
    searchStr.set(text_entry.get())

def SetSavingPath():
    folder_selected = filedialog.askdirectory()
    save.set(folder_selected)

def UpdateMetricList():
    Loc = root.getvar(name='GNMetricList_Path'); loc = Loc[0]
    olDF = pd.read_excel(loc); olLength = len(olDF)
    df = pd.DataFrame(GlassNode_API.UpdateGNMetrics(API_KEY))
    print('Metrics list updated, old length: ',olLength,'new length: ',len(df))
    df.to_excel(loc)

def SearchBtn():
    update_text()
    loadPath = path.get(); term = searchStr.get()
    print(loadPath)
    ridEm = {"(":"",")":"","'":"","'":"",",":""}
    for char in ridEm.keys():
        term = term.replace(char,ridEm[char])
        loadPath = loadPath.replace(char,ridEm[char])
    print(term,loadPath)
    results = GlassNode_API.SearchMetrics(loadPath,term)
    result = results['path'].to_list(); finRes = []
    for res in result:
        rez = str(res); split = rez.split('/'); temp = split[len(split)-1]
        finRes.append(temp)
    SearchResults.set(result); SearchDisplay.set(finRes)
    print(result)
    
def MakeChoice(event):
    cs = res.curselection()
    loadPath = path.get(); term = searchStr.get()
    ridEm = {"(":"",")":"","'":"","'":"",",":""}
    for char in ridEm.keys():
        term = term.replace(char,ridEm[char])
        loadPath = loadPath.replace(char,ridEm[char])

    result = pd.DataFrame(GlassNode_API.SearchMetrics(loadPath,term))
    ResultsList = result['path'].to_list()
    asses = str(result.iloc[cs[0]].at['assets']); cuz = str(result.iloc[cs[0]].at['currencies'])
    rez = str(result.iloc[cs[0]].at['resolutions']); forma = str(result.iloc[cs[0]].at['formats'])
    ridEm = {" ":"", "'":'"'}; #"'":"","[":"","]":"","'":"","'":""
    for char in ridEm.keys():
        asses = asses.replace(char,ridEm[char]); cuz = cuz.replace(char,ridEm[char])
        rez = rez.replace(char,ridEm[char]); forma = forma.replace(char,ridEm[char])
    assers = json.loads(asses); print('Assets, json str: ',assers,type(assers),assers[0],type(assers[0]))
    assetsList = [ass["symbol"] for ass in assers]

    ridEm = {" ":"","'":"","'":"","[":"","]":"","'":""}
    for char in ridEm.keys():
        cuz = cuz.replace(char,ridEm[char]); rez = rez.replace(char,ridEm[char]); forma = forma.replace(char,ridEm[char])
    cuz = cuz.split(','); rez = rez.split(','); forma = forma.split(','); print(cuz,rez,forma)
    cuz = [st[1:len(st)-1] for st in cuz]; rez = [st[1:len(st)-1] for st in rez]; forma = [st[1:len(st)-1] for st in forma]
    print("Selection: ",cs[0],' ',ResultsList[cs[0]])
    print("Tier: ",result.iloc[cs[0]].at['tier'])
    print("Assets: ",assetsList); print("Currencies: ",cuz)
    print("Resolutions: ",rez); print("Formats: ",forma)
    choice.set(ResultsList[cs[0]])
    tier.set(result.iloc[cs[0]].at['tier']); assets.set(assetsList)
    assChoice.set(assetsList[0]); currChoice.set(cuz[0]); resChoice.set('24h');formChoice.set(forma[0])
    drop2 = OptionMenu(frame,assChoice,*assetsList); drop2.place(x=(570/ww)*ww, y=(135/wh)*wh)
    drop3 = OptionMenu(frame,currChoice,*cuz); drop3.place(x=(690/ww)*ww, y=(135/wh)*wh)
    drop4 = OptionMenu(frame,resChoice,*rez); drop4.place(x=(550/ww)*ww, y=(200/wh)*wh)
    drop5 = OptionMenu(frame,formChoice,*forma); drop5.place(x=(670/ww)*ww, y=(200/wh)*wh)
    currencies.set(cuz); resolutions.set(rez); formats.set(forma)
    print(currChoice.get(),assChoice.get())

def getGNData():
    ep = choice.get(); split = ep.split('/'); name = split[len(split)-1]
    ridEm = {"(":"",")":"","''":"","'":"","'":""," ":""}
    for char in ridEm.keys():
        ep = ep.replace(char,ridEm[char])
    params = {'a':assChoice.get(),'i':resChoice.get(),'f':formChoice.get(),'api_key': API_KEY} 
    start = StartDate.get(); end = EndDate.get(); 
    if len(start) > 1:
      startD = datetime.datetime.strptime(start,"%Y-%m-%d")
      stDate  = int(time.mktime(startD.timetuple()))
      params['s'] = stDate
      print('Using start date: ',startD,stDate)
    else:
        print('Start date will be the maximum distance into past for the metric.')  
    if len(end) > 1:    
        endD = datetime.datetime.strptime(end,"%Y-%m-%d")
        EDate  = int(time.mktime(endD.timetuple()))
        params['u'] = EDate
        print('Using end date: ',endD,EDate)
    else:
        print('End date will be now.')      
    
    series = pd.Series(GlassNode_API.GetMetric(ep,API_KEY,params=params),name=name)
    print(type(series))
    
    try:
        series = series.astype(float)
        SerOrDF = 'series'
    except Exception as err:
        print(err,series.dtype,type(series.iloc[0]))    
        if str(type(series.iloc[0])) == "<class 'dict'>":
            print("That's a big dict. Let's break it up"); 
            df = pd.DataFrame(series.tolist(),index=series.index)
            SerOrDF = 'df'
            print(df)    
        else: 
            print("dtype of series is not dict, need to figure out how to deal with this type. Pulling out....")
            print(series,type(series),series.dtype,type(series.iloc[0]))
            quit()        
    dates = pd.DatetimeIndex(series.index); dates.rename('date',inplace=True)
    dateColumn = dates.to_list(); Date.set(dateColumn)
    tree.delete(*tree.get_children())
    if SerOrDF == "series":
        dataForm.set(0); dataColumn = series.to_list()
        series = pd.Series(dataColumn,index=dates,name=name)
        Data.set(series.to_json())
        cols.set(['Date',series.name])
        tree["columns"] = ['Date',series.name]
        for col in tree['columns']:
            tree.column(col,width=150)
            tree.heading(col,text=col)
        for i in range(len(dataColumn)):
            values = [dateColumn[i],dataColumn[i]]
            tree.insert('',tk.END,values=values)   
    else:
        dataForm.set(1)
        allCols = df.columns.to_list(); allCols.insert(0,'Date')
        Data.set(df.to_json())
        print(allCols)
        cols.set(allCols) 
        tree["columns"] = allCols
        for col in tree['columns']:
            tree.column(col,width=100)
            tree.heading(col,text=col)
        for i in range(len(df)):
            values = df.iloc[i].tolist(); values.insert(0,dates[i])
            tree.insert('',tk.END,values=values)    
    print('Is data a series or a dataframe?',SerOrDF)
######## Plot preview ###################################
def plotPreview():
    dateStr = Date.get(); dataStr = Data.get(); DForm = dataForm.get()
    ep = choice.get(); split = ep.split('/'); name = split[len(split)-1]
    ridEm = {"(":"",")":"","'":"","'":""}
    for char in ridEm.keys():
        dateStr = dateStr.replace(char,ridEm[char]) 
    dateList = dateStr.split(','); #dataList = dataStr.split(',')
    dates = pd.DatetimeIndex(dateList)
    dataStr = dict(json.loads(dataStr))

    fig = plt.figure(figsize=(8, 4), dpi=150)
    ax = fig.add_subplot(111)

    if DForm == 0:
        data = pd.Series(dataStr.values(),index=dates,name=name)
        data = data.astype(float)
        ax.plot(data,color='black',label=name)
    else:
        data = pd.DataFrame.from_dict(dataStr)
        dateSer = pd.Series(dates,index=data.index,name='Date')
        data = pd.concat([dateSer,data],axis=1)
        data.set_index('Date',inplace=True)
        data = data.astype(float)
        for col in data.columns:
            ax.plot(data[col],label=col)    
    ax.legend(fontsize=9)
    yScale = YAxis.get()
    ax.set_yscale(yScale); ax.set_title(name,fontweight='bold')
    ax.tick_params(axis='both',labelsize=9); ax.minorticks_on(); ax.margins(x=0.02,y=0.02)
    ax.grid(visible=True,axis='both',which='major',lw=0.5,color='gray',ls=':')
    plt.show()        

def SaveData():
    dateStr = Date.get(); dataStr = Data.get(); DForm = dataForm.get(); print('Data is series or dataframe: ',DForm)
    ep = choice.get(); split = ep.split('/'); name = split[len(split)-1]; Save = save.get()
    ridEm = {"(":"",")":"","'":"","'":""}
    for char in ridEm.keys():
        dateStr = dateStr.replace(char,ridEm[char]) 
        Save = Save.replace(char,ridEm[char])
    Save = Save.replace(",","") 
    dateList = dateStr.split(','); #dataList = dataStr.split(',')
    dates = pd.DatetimeIndex(dateList)
    dataStr = dict(json.loads(dataStr))
    if DForm == 0:
        data = pd.Series(dataStr.values(),index=dates,name=name)
        data = data.astype(float)
        data.rename(name,inplace=True) 
    else:
        data = pd.DataFrame.from_dict(dataStr)
        dateSer = pd.Series(dates,index=data.index,name='Date')
        data = pd.concat([dateSer,data],axis=1)
        data.set_index('Date',inplace=True)
        data = data.astype(float)

    saveName = Save+FDel+name+'.xlsx'
    print(data,saveName)
    data.index.rename('Date',inplace=True)
    data.to_excel(saveName)      

#def GetBTCUSD():    

######### FEATURES WITHIN THE WINDOW #################################################################
########### Load the excel file containing the dataframe with list of metrics from glassnode 
btn=Button(frame, text="Load GN metrics list",fg='blue',command=LoadPathBtn)
upd=Button(frame, text="Update GN metrics list",fg='fuchsia',command=UpdateMetricList)
lb=Listbox(frame,listvariable=path, height=1, width=83)
######### Search term entry bar and search button. Search through the list of metrics. 
searchStr = StringVar(); searchStr.set("")
text_entry = Entry(frame)
update_button = Button(frame, text="Search metrics", command=SearchBtn)
note = Label(frame,text='*Double click endpoint \npath to select metric.',font=('Arial',10))
############ Display results #########################################
getMetric = Button(frame, text="Get data for selected metric", command=getGNData)
res=Listbox(frame,listvariable=SearchDisplay, height=15, width=50)
res.bind('<Double-1>', MakeChoice)
TierBox = Listbox(frame,listvariable=tier, height=1, width=3)
drop2 = OptionMenu(frame,assChoice,value='Assets')
note3 = Label(frame,text='Metrics/endpoints matching search criteria:',font=('Arial',10))
note4 = Label(frame,text='Tier',font=('Arial',10))
note5 = Label(frame,text='Assets',font=('Arial',10))
drop3 = OptionMenu(frame,currChoice,value='Currencies')
note5 = Label(frame,text='Currencies',font=('Arial',10))
drop4 = OptionMenu(frame,resChoice,'Resolutions')
note6 = Label(frame,text='Resolutions',font=('Arial',10))
drop5 = OptionMenu(frame,formChoice,'Formats')
note7 = Label(frame,text='Formats',font=('Arial',10))
text_entry2 = Entry(frame,textvariable=StartDate)
note8 = Label(frame,text='Starting Date (YYYY-MM-DD), blank = max',font=('Arial',10))
text_entry3 = Entry(frame,textvariable=EndDate)
note9 = Label(frame,text='End Date (YYYY-MM-DD), blank = NOW',font=('Arial',10))
# BTC_too = Checkbutton(frame)

######### Display the data for the metric #####################
tree = Treeview(frame,columns=['Date','Data'],show='headings',height=round((11/wh)*wh))

YAxis = StringVar(frame,value='linear',name="Yaxis_Scale")
options = ['linear','log']
drop = OptionMenu(frame,YAxis, *options)
plot_button = Button(frame, text="Preview metric", command=plotPreview)
note2 = Label(frame,text='*Y-scaling of\npreview chart.',font=('Arial',10))

SetSavePath=Button(frame, text="Set save path",fg='green',command=SetSavingPath)
SaveBtn=Button(frame, text="Save data",fg='red',command=SaveData)
lb2=Listbox(frame,listvariable=save, height=1, width=83)

################ Arange all the features ############################################################
btn.place(x=(20/ww)*ww, y=(10/wh)*wh) #Load GN metrics file.
upd.place(x=(600/ww)*ww, y=(10/wh)*wh)    #Update GN metrcs button
lb.place(x=0.02*ww, y=0.062*wh)      #GN metrics path.
text_entry.place(x=(20/ww)*ww, y=(80/wh)*wh)       #Search bar. 
update_button.place(x=(225/ww)*ww,y=(85/wh)*wh)      ###Search button.
note.place(x=(350/ww)*ww,y=(80/wh)*wh)       ##Double click note.
getMetric.place(x=(290/ww)*ww,y=(405/wh)*wh)       #Get GN metric data button.
res.place(x=(20/ww)*ww, y=(140/wh)*wh); note3.place(x=(15/ww)*ww,y=(120/wh)*wh)   #Listbox showing results of search.
TierBox.place(x=(490/ww)*ww, y=(140/wh)*wh); note4.place(x=(492/ww)*ww,y=(115/wh)*wh)  #Tier
drop2.place(x=(570/ww)*ww, y=(135/wh)*wh); note5.place(x=(580/ww)*ww,y=(110/wh)*wh) #Assets
drop3.place(x=(690/ww)*ww, y=(135/wh)*wh); note5.place(x=(690/ww)*ww,y=(115/wh)*wh)   #Currencies
drop4.place(x=(550/ww)*ww, y=(200/wh)*wh); note6.place(x=(555/ww)*ww,y=(180/wh)*wh)  #Resolutions
drop5.place(x=(670/ww)*ww, y=(200/wh)*wh); note7.place(x=(680/ww)*ww,y=(180/wh)*wh) #Formats
text_entry2.place(x=(550/ww)*ww, y=(270/wh)*wh); note8.place(x=(550/ww)*ww,y=(250/wh)*wh) #StartDate
text_entry3.place(x=(550/ww)*ww, y=(350/wh)*wh); note9.place(x=(550/ww)*ww,y=(330/wh)*wh)  #EndDate
tree.place(x=(20/ww)*ww,y=(435/wh)*wh,width=600)  #Dataframe display tree. 
drop.place(x=(660/ww)*ww,y=(520/wh)*wh); note2.place(x=660,y=(550/wh)*wh) #Plot preview Y-axis
plot_button.place(x=(640/ww)*ww,y=(440/wh)*wh)   #Plot preview button.
SetSavePath.place(x=(20/ww)*ww, y=(670/wh)*wh) #SavePath button.
SaveBtn.place(x=(670/ww)*ww, y=(670/wh)*wh)  #Save button. 
lb2.place(x=(15/ww)*ww, y=(700/wh)*wh) #SavePath

######## Run the main loop of the Tkinter window. #################################
root.mainloop()