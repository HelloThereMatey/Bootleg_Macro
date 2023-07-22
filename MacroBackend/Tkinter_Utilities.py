import tkinter as tk
import os
import sys
import json

def SetScreenInfoFile(InfoFolder:str):
    root = tk.Tk()
    ###### Determine what OS this is running on and get appropriate path delimiter. #########
    FDel = os.path.sep
    print("Operating system: ",sys.platform, "Path separator character: ", FDel)
    if sys.platform == 'win32':
        username = os.environ['USERNAME']
    else:
        username = os.environ['USER']

    ScreenData = {'OS': sys.platform,
                  "USER": username}

    # Get screen size
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    print(f'Screen size: {screen_width}x{screen_height}')
    ScreenData['Screen_width'] = screen_width
    ScreenData['Screen_height'] = screen_height

    # Get character size
    label = tk.Label(root, text="M")
    label.pack()
    root.update_idletasks()
    char_width = label.winfo_width()
    char_height = label.winfo_height()
    print(f'Character size: {char_width}x{char_height}')
    ScreenData['Char_width'] = char_width
    ScreenData['Char_height'] = char_height

    filePath = InfoFolder+FDel+"ScreenData.json"
    with open(filePath, 'w') as f:
        json.dump(ScreenData, f, indent=4)

    root.destroy()

def get_char_dimensions(root):
    default_font = tkFont.nametofont("TkDefaultFont")
    char_width = default_font.measure('M')
    char_height = default_font.metrics("linespace")
    return char_width, char_height

if __name__ == "__main__":
    wd = os.path.dirname(os.path.realpath(__file__))
    FDel = os.path.sep
    InfoFolder = wd+FDel+'SystemInfo'
    SetScreenInfoFile(InfoFolder)
