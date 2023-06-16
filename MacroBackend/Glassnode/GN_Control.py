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
dir = os.path.dirname(wd); parent = os.path.dirname(dir)
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
savePath2 = parent+FDel+'Generic_Macro'+FDel+'SavedData'+FDel+'Glassnode'
plt.rcParams.update({'font.family':'serif'})   #Font family for the preview figure. 

def get_curr_screen_geometry():
    """
    Workaround to get the size of the current screen in a multi-screen setup.
    Returns:
        geometry (str): The standard Tk geometry string.
            [width]x[height]+[left]+[top]
    """
    root = tk.Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    geometry = root.winfo_geometry()
    root.destroy()
    return geometry

######### WINDOW DEFINTION ##############################
root = Tk()
root.title('Pull data from Glassnode widget')
root.config(bg='skyblue')
# Get the screen width and height
# Get the screen width and height
#sw = root.winfo_screenwidth();  print('Screen width: ',sw) #This doesn't work across different systems.
#sh = root.winfo_screenheight(); print('Screen height: ',sh)
screen = get_curr_screen_geometry()    #This figures out the screen size & geometry. Input manually instead
#to avoid the white flash at the start.
split = screen.split('+'); geo = split[0]
split2 = geo.split("x")
sw = int(split2[0]); sh = int(split2[1]) 
#sw = 1680; sh = 1050      #Set sw & sh manually in order to avoid the flash at the start.
fontMax = round((sw/1680)*16)
print('Screen display width x height (pixels): '+str(sw)+' x '+str(sh), 'fontMax = ',fontMax)

# Calculate the window size and position based on the desired aspect ratio
ww = int(0.5 * sw); wh = int(0.85 * sh)
print('Window width x height (pixels): '+str(ww)+' x '+str(wh))
root.geometry(f"{ww}x{wh}")
root.maxsize = (ww,wh)

########## Frames for parts of window #######################################################################################################
root.columnconfigure(0,weight=4); root.columnconfigure(1,weight=2)
root.rowconfigure(0,weight=2); root.rowconfigure(1,weight=4); root.rowconfigure(2,weight=4); root.rowconfigure(3,weight=2)

top_frame = Frame(root, width=ww,height=0.15*wh); top_frame.grid(row=0,column=0,padx=5,pady=5,sticky='w',columnspan=2); top_frame.grid_propagate(False)
top_frame.update(); TFw = top_frame.winfo_width(); TFh = top_frame.winfo_height()
print('Topframe geometry: ',top_frame.winfo_width(),top_frame.winfo_height())
mid_left = Frame(root, width=0.66*ww,height=0.375*wh); mid_right = Frame(root, width=0.35*ww,height=0.375*wh) 
mid_left.update(); mlFw = mid_left.winfo_width(); mlFh = mid_left.winfo_height(); mid_right.update(); mrFw = mid_right.winfo_width(); mrFh = mid_right.winfo_height()
mid_left.grid(row=1,column=0,padx=5,pady=2,sticky='w'); mid_right.grid(row=1,column=1,padx=5,pady=2,sticky='w'); mid_left.grid_propagate(False); mid_right.grid_propagate(False)
mid_left2 = Frame(root, width=0.66*ww,height=0.375*wh); mid_right2 = Frame(root, width=0.35*ww,height=0.375*wh)
mid_left2.grid(row=2,column=0,padx=5,pady=2,sticky='w'); mid_right2.grid(row=2,column=1,padx=5,pady=2,sticky='w'); mid_left2.grid_propagate(False); mid_right2.grid_propagate(False)
mid_left2.update(); ml2Fw = mid_left2.winfo_width(); ml2Fh = mid_left2.winfo_height(); mid_right2.update(); mr2Fw = mid_right2.winfo_width(); mr2Fh = mid_right2.winfo_height()
bot_frame = Frame(root, width=ww,height=0.1*wh); bot_frame.grid(row=3,column=0,padx=5,pady=5,sticky='w',columnspan=2); bot_frame.pack_propagate(False)
bot_frame.update(); BFw = bot_frame.winfo_width(); BFh = bot_frame.winfo_height()
print('Botframe geometry: ',bot_frame.winfo_width(),bot_frame.winfo_height())

######### WINDOW VARIABLES ##############################
path = StringVar(master=root,value=defPath,name='GNMetricList_Path')
save = StringVar(master=root,value=savePath2,name='DataSavePath')
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
add_BTC = BooleanVar(master=root,value=False,name='GraphBTC')

############ BUTTON FUNCTIONS ################################################################################################
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
    drop2 = OptionMenu(mid_right,assChoice,*assetsList); 
    drop3 = OptionMenu(mid_right,currChoice,*cuz)
    drop4 = OptionMenu(mid_right,resChoice,*rez)
    drop5 = OptionMenu(mid_right,formChoice,*forma)
    currencies.set(cuz); resolutions.set(rez); formats.set(forma)
    print(currChoice.get(),assChoice.get())

    TierBox.grid(column=0,row=0,sticky='w',padx=15)
    drop2.grid(column=1,row=0,padx=10,pady=15); 
    drop3.grid(column=2,row=0,padx=10,pady=20); 
    drop4.grid(column=1,row=1,padx=10,pady=20); 
    drop5.grid(column=2,row=1,padx=10,pady=20); 

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
            tree.column(col,width=75)
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
    plot_bitty = add_BTC.get()

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
    
    if plot_bitty:
        bitty = pd.read_excel(savePath2+FDel+'price_usd_close.xlsx')
        bitty.set_index('Date',inplace=True)
        bitty = pd.Series(bitty.squeeze(),name='BTC (USD)')
        axb = ax.twinx()
        axb.plot(bitty,color='orangered',label='BTC (USD)')
        axb.set_yscale(yScale)
        axb.set_ylabel('USD',fontweight='bold')
        DateRange = (data.index[len(data)-1]-data.index[0]).days
        ax.set_xlim(data.index[0]-datetime.timedelta(days=round(0.01*DateRange)),data.index[len(data)-1]+datetime.timedelta(days=round(0.01*DateRange)))
        print('BTC price will be added to plot preview. NOTE: You must manually update the BTC price by pulling and saving metric: "price_usd_close".')
    
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
# Top frame, setup grid first.
top_frame.columnconfigure(0, weight=1); top_frame.columnconfigure(1, weight=1); top_frame.columnconfigure(2, weight=1)
top_frame.rowconfigure(0, weight=1); top_frame.rowconfigure(1, weight=1); top_frame.rowconfigure(2, weight=1)

########### Load the excel file containing the dataframe with list of metrics from glassnode 
Title = Label(top_frame,text='Glassnode Studios data downloader',font=('Arial',fontMax,'bold')); Title.grid(column=1,row=0,padx=60,pady=5,sticky='w',columnspan=2)
btn=Button(top_frame, text="Load GN metrics list",fg='blue',command=LoadPathBtn,font=('Arial',round((14/16)*fontMax))); btn.grid(column=0,row=0,sticky='w',padx=10,pady=5)
upd=Button(top_frame, text="Update GN metrics list",fg='fuchsia',command=UpdateMetricList,font=('Arial',round((14/16)*fontMax))); upd.grid(column=3,row=0,padx=10,pady=5)
lb=Listbox(top_frame,listvariable=path, height=1, width=100); lb.grid(column=0,row=1,padx=10,pady=10,columnspan=4,sticky='ew')
######### Search term entry bar and search button. Search through the list of metrics. 
searchStr = StringVar(); searchStr.set("")
text_entry = Entry(top_frame); text_entry.grid(column=0,row=2,padx=15,pady=5)
update_button = Button(top_frame, text="Search metrics", command=SearchBtn,font=('Arial',round((14/16)*fontMax),'bold'),border=2); update_button.grid(column=1,row=2,padx=15,pady=5,sticky='w')
note = Label(top_frame,text='*Double click endpoint path to select metric.',font=('Arial',round((12/16)*fontMax))); note.grid(column=2,row=2,padx=15,pady=5)

############ Display results ##############################################################
res=Listbox(mid_left,listvariable=SearchDisplay, height=16, width=58); res.bind('<Double-1>', MakeChoice)
res.grid(column=0,row=1,sticky='w',padx=5)
getMetric = Button(mid_left, text="Get data for selected metric", command=getGNData, font=('Arial',round((11/16)*fontMax),'bold'))
getMetric.grid(column=0,row=2,sticky='ne',padx=1,pady=1)
note3 = Label(mid_left,text='Metrics/endpoints matching search criteria:',font=('Arial',round((10/16)*fontMax))); note3.grid(column=0,row=0,sticky='nw',padx=1,pady=1)

mid_right.columnconfigure(0,weight=1); mid_right.columnconfigure(1,weight=1) ; mid_right.columnconfigure(2,weight=1)
mid_right.rowconfigure(0,weight=1); mid_right.rowconfigure(1,weight=1) 

TierBox = Listbox(mid_right,listvariable=tier, height=1, width=3); TierBox.grid(column=0,row=0,sticky='w',padx=15)
note4 = Label(mid_right,text='Tier',font=('Arial',round((11/16)*fontMax),'bold')); note4.grid(column=0,row=0,sticky='nw',padx=15,pady=50)
drop2 = OptionMenu(mid_right,assChoice,value='Assets'); drop2.grid(column=1,row=0,padx=10,pady=15)
note5 = Label(mid_right,text='Assets',font=('Arial',round((11/16)*fontMax),'bold')); note5.grid(column=1,row=0,sticky='n',padx=10,pady=50)
drop3 = OptionMenu(mid_right,currChoice,value='Currencies'); drop3.grid(column=2,row=0,padx=10,pady=20)
note5 = Label(mid_right,text='Currencies',font=('Arial',round((11/16)*fontMax),'bold')); note5.grid(column=2,row=0,sticky='n',padx=5,pady=50)
drop4 = OptionMenu(mid_right,resChoice,'Resolutions'); drop4.grid(column=1,row=1,padx=10,pady=20)
note6 = Label(mid_right,text='Resolutions',font=('Arial',round((11/16)*fontMax),'bold')); note6.grid(column=1,row=1,sticky='n',padx=5,pady=30)
drop5 = OptionMenu(mid_right,formChoice,'Formats'); drop5.grid(column=2,row=1,padx=10,pady=20)
note7 = Label(mid_right,text='Formats',font=('Arial',round((11/16)*fontMax),'bold')); note7.grid(column=2,row=1,sticky='n',padx=5,pady=30)

text_entry2 = Entry(mid_right2,textvariable=StartDate); text_entry2.grid(column=0,row=0,padx=20,pady=45)
note8 = Label(mid_right2,text='Starting Date (YYYY-MM-DD), blank = max',font=('Arial',round((10/16)*fontMax))) ; note8.grid(column=0,row=0,sticky='n',padx=20,pady=20)
text_entry3 = Entry(mid_right2,textvariable=EndDate); text_entry3.grid(column=0,row=1,padx=20,pady=30)
note9 = Label(mid_right2,text='End Date (YYYY-MM-DD), blank = NOW',font=('Arial',round((10/16)*fontMax))); note9.grid(column=0,row=1,sticky='n',padx=20)

######### Display the data for the metric #####################
tree = Treeview(mid_left2,columns=['Date','Data'],show='headings',height=15)
tree.grid(column=0,row=0,sticky='nw',padx=5,pady=5)
YAxis = StringVar(mid_right2,value='linear',name="Yaxis_Scale")
options = ['linear','log']
drop = OptionMenu(mid_right2,YAxis, *options); drop.grid(column=0,row=2,sticky='w',padx=25,pady=60)
plot_button = Button(mid_right2, text="Preview metric",font=('Arial',round((11/16)*fontMax),'bold'), command=plotPreview); plot_button.grid(column=0,row=2,sticky='e',padx=10,pady=15)
note2 = Label(mid_right2,text='*Y-scaling of\npreview chart.',font=('Arial',round((11/16)*fontMax))); note2.grid(column=0,row=2,sticky='nw',padx=25,pady=15)
BTC_too = Checkbutton(mid_right2,text="Plot BTC price",variable=add_BTC); BTC_too.grid(column=0,row=2,sticky='ne',padx=10,pady=30)

lb2=Listbox(bot_frame,listvariable=save, height=1,width=round((0.9*BFw)/8.3)); lb2.pack(side='top',fill='x',expand=True,padx=15,pady=10)
#lb2.grid(row=0,sticky='ew',padx=10,pady=10,columnspan=2)
SetSavePath=Button(bot_frame, text="Set save path",fg='green',command=SetSavingPath); SetSavePath.pack(side='left',padx=5,pady=10)
#SetSavePath.grid(row=1,sticky='w',padx=30,pady=5)
SaveBtn=Button(bot_frame, text="Save data",fg='red',command=SaveData,font=('Arial',round((12/16)*fontMax),'bold')); SaveBtn.pack(side='right',padx=15,pady=10)
#SaveBtn.grid(row=1,sticky='e',padx=90,pady=5)

######## Run the main loop of the Tkinter window. #################################
root.mainloop()