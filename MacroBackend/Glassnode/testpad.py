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

screen = get_curr_screen_geometry()

#screen = os.system("xrandr  | grep \* | cut -d' ' -f4")

print(screen)
quit()
######### WINDOW DEFINTION ##############################
root = Tk()
root.title('Pull data from Glassnode widget')
root.config(bg='skyblue')
# Get the screen width and height
# Get the screen width and height
sw = root.winfo_screenwidth();  print('Screen width: ',sw)
sh = root.winfo_screenheight(); print('Screen height: ',sh)

# Calculate the window size and position based on the desired aspect ratio
ww = int(0.5 * sw); print('Screen width: ',sw)
wh = int(0.9 * sh); print('Screen height: ',sw)
print('Window width x height (pixels): '+str(ww)+' x '+str(wh))
root.geometry(f"{ww}x{wh}")
root.maxsize = (ww,wh)

########## Frames for parts of window #######################################################################################################
root.columnconfigure(0,weight=4); root.columnconfigure(1,weight=2)
root.rowconfigure(0,weight=2); root.rowconfigure(1,weight=4); root.rowconfigure(2,weight=4); root.rowconfigure(3,weight=2)

top_frame = Frame(root, width=ww,height=0.15*wh); top_frame.grid(row=0,column=0,padx=5,pady=5,sticky='w',columnspan=2)
mid_left = Frame(root, width=0.66*ww,height=0.35*wh); mid_right = Frame(root, width=0.35*ww,height=0.35*wh)
mid_left.grid(row=1,column=0,padx=5,pady=5,sticky='w'); mid_right.grid(row=1,column=1,padx=5,pady=5,sticky='w')
mid_left2 = Frame(root, width=0.66*ww,height=0.35*wh); mid_right2 = Frame(root, width=0.35*ww,height=0.35*wh)
mid_left2.grid(row=2,column=0,padx=5,pady=5,sticky='w'); mid_right2.grid(row=2,column=1,padx=5,pady=5,sticky='w')
bot_frame = Frame(root, width=ww,height=0.15*wh); bot_frame.grid(row=3,column=0,padx=5,pady=5,sticky='w',columnspan=2)







######## Run the main loop of the Tkinter window. #################################
root.mainloop()