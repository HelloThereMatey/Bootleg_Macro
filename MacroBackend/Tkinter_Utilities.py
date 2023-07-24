import tkinter as tk
import tkinter.font as tkFont
import os
import sys
import json

class TkinterSizingVars():

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.allCharsStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "
        #'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*=-,.|()?+[]\/~1234567890 ><"";'
        self.FDel = os.path.sep
        
    def SetScreenInfoFile(self):
        ###### Determine what OS this is running on and get appropriate path delimiter. #########
        print("Operating system: ",sys.platform, "Path separator character: ", self.FDel)
        if sys.platform == 'win32':
            username = os.environ['USERNAME']
        else:
            username = os.environ['USER']

        self.ScreenData = {'OS': sys.platform,
                    "USER": username}

        # Get screen size
        self.root.update_idletasks()
        self.root.attributes('-fullscreen', True)
        self.root.state('iconic')
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        print(f'Screen size: {screen_width}x{screen_height}')
        self.ScreenData['Screen_width'] = screen_width
        self.ScreenData['Screen_height'] = screen_height

        # Get character size
        label = tk.Label(self.root, text="M")
        label.pack()
        self.root.update_idletasks()
        char_width = label.winfo_width()
        char_height = label.winfo_height()
        print(f'Character size: {char_width}x{char_height}')
        self.ScreenData['Char_width'] = char_width
        self.ScreenData['Char_height'] = char_height
        self.ScreenData['Def_font'] =  self.get_def_FontInfo()

        self.root.destroy()

    def get_def_FontInfo(self):
        print("Measuring default font... all characters: ","\n", self.allCharsStr,len(self.allCharsStr))
        default_font = tkFont.nametofont("TkDefaultFont")
        lengthAll = default_font.measure(self.allCharsStr)
        defFontInfo = {'name': default_font.name ,
                    'family': default_font.actual('family'),
                    'size': default_font.actual('size'),
                    'char_width (pixels)': default_font.measure('C'),
                    #'char_width (pixels)': round(lengthAll/len(self.allCharsStr)),
                    'char_height (pixels)': default_font.metrics("linespace")}
        return defFontInfo
    
    def ExportVars(self,folder:str):
        filePath = folder+self.FDel+"ScreenData.json"
        with open(filePath, 'w') as f:
            json.dump(self.ScreenData, f, indent=4)


if __name__ == "__main__":
    root = tk.Tk()
    wd = os.path.dirname(os.path.realpath(__file__))
    FDel = os.path.sep
    InfoFolder = wd+FDel+'SystemInfo'
    tkVars = TkinterSizingVars()
    tkVars.SetScreenInfoFile()
    tkVars.ExportVars(InfoFolder)
    print(tkVars.ScreenData)