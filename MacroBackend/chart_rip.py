import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams["backend"] = "QtAgg"
import tkinter as tk
from tkinter import filedialog

import os
wd = os.path.abspath(os.path.dirname(__file__))
fdel = os.path.sep

def basic_load_dialog():
    window = tk.Tk()
    window.withdraw()
    file_path = filedialog.askopenfilename(defaultextension = '.png', 
                                           filetypes=(('Image files', '*.png *.bmp *.jpg *.jpeg *.pdf *.svg *.tiff *.tif'),
                                                  ('All files', '*.*')),
                                           initialdir=wd, parent=window, title='Choose a chart image file to load.')
    window.withdraw()
    return file_path

class plot_rippa(object): 
    def __init__(self, imagePath: str = "", x0: float = 0, x1: float = 1, y0: float = 1, 
                 y1: float = 1, xscale: str = "linear", yscale: str = "linear", title: str = "Chart image"):
        #Reading the .png self.image into a multi-dimensional ndarray
        super().__init__()
        self.x0 = x0; self.x1 = x1; self.y0 = y0; self.y1 = y1
        self.xscale = xscale; self.yscale = yscale; self.title = title

        if len(imagePath) > 0:
            self.imagePath = imagePath
        else:
            self.imagePath = basic_load_dialog()

        self.image = plt.imread(self.imagePath)
        print("Loaded self.image of shape (R, G, B, A)", self.image.shape)
        
        sl = self.image[:,:,0:0]
        self.image_ar = sl.shape[1]/sl.shape[0]
        print("Image aspect ratio: ", self.image_ar, "width, height (pixels): ", sl.shape[1], sl.shape[0])    
        # Display the self.image
        self.fig, self.ax = plt.subplots(figsize = (8*self.image_ar, 8))
        self.ax.imshow(self.image)

        # Initialize an empty dictionary to store RGB values
        self.trace_colors = {}
        self.data_series = None

    def active_chart(self):

        def onclick( event):
            if event.dblclick:  # Check if the event is a double-click
                if event.xdata is not None and event.ydata is not None:
                    x, y = int(event.xdata), int(event.ydata)
                    rgb_values = self.image[y, x]
                    # Find all pixels with the same RGB values
                    matching_pixels = np.where((self.image[:, :, 0] == rgb_values[0]) & 
                                            (self.image[:, :, 1] == rgb_values[1]) & 
                                            (self.image[:, :, 2] == rgb_values[2]))
                    # Convert indices to pixel locations
                    pixel_locations = list(zip(matching_pixels[0], matching_pixels[1]))
                    # Generate the next trace key
                    trace_key = f"Trace{len(self.trace_colors) + 1}"
                    # Store the RGB values and pixel locations in the dictionary
                    self.trace_colors[trace_key] = {'RGB': rgb_values, 'Locations': pixel_locations}
                    print(f"{trace_key}: RGB values at ({x}, {y}): {rgb_values}, Number of matching pixels: {len(pixel_locations)}")

        self.fig.canvas.mpl_connect('button_press_event', onclick)

        plt.show()
        
    def display_trace_locations(self):
        blank_image = np.zeros_like(self.image[:,:,0])  # For grayscale
        # blank_image = np.zeros_like(self.image)  # For RGB

        # Iterate through each trace and mark the positions
        for trace_key, trace_info in self.trace_colors.items():
            for (y, x) in trace_info['Locations']:  # Assuming 'Locations' stores (y, x) tuples
                blank_image[y, x] = 255  # Mark as white for grayscale
                # For RGB, you might want to set a specific color per trace
                # blank_image[y, x, :] = [255, 0, 0]  # Example: Mark as red

        # Display the marked image
        plt.imshow(blank_image, cmap='gray')  # Use 'cmap' only for grayscale images
        plt.title('Marked Positions from Traces')
        plt.show()
    
    def trace_locs_to_values(self):
        self.max_x = self.image.shape[1]
        self.max_y = self.image.shape[0]
        print("Max x, y: ", self.max_x, self.max_y)
        self.trace_dataframes = {}
        for trace_name, locs in self.trace_colors.items():
            print(f"Trace: {trace_name}, Locations: {locs}")  # Debugging print
            if locs:  # Check if locs is not empty
                # Create a DataFrame from locations with two columns: 'Y' and 'X'
                df = pd.DataFrame(locs["Locations"], columns=[trace_name+'_y', trace_name+'_x'])
            else:
                df = pd.DataFrame(columns=[trace_name+'_y', trace_name+'_x'])  # Empty DataFrame with column names
            # Store the DataFrame in the new dictionary
            self.trace_dataframes[trace_name] = df
        
        # Assuming 'trace_dataframes' is your dictionary of DataFrames
        self.median_trace_dataframes = {}  # Dictionary to store the DataFrames with median values
        self.data_series = {}

        for trace_name, df in self.trace_dataframes.items():
            median_df = df.groupby(trace_name + '_x')[trace_name + '_y'].median().reset_index()
            #median_df = median_df.iloc[::-1].reset_index()   
            median_df.columns = [trace_name + '_x', trace_name + '_y']
            #median_df[trace_name + '_x'] = self.max_x - median_df[trace_name + '_x']
            median_df[trace_name + '_y'] = self.max_y - median_df[trace_name + '_y']
            #median_df = pd.concat([median_df[trace_name + '_x'][::-1].reset_index(drop=True), median_df[trace_name + '_y'].reset_index(drop=True)], axis = 1)
            median_df.set_index(trace_name + '_x', inplace=True, drop = True)
        
            series = median_df[trace_name + '_y']
    
            # Normalize 'x' and 'y' values as fraction of the number of pixels in that direction
            # Then multiply by the range of the plot in that direction and add min axis value. 
            index = (series.index / self.max_x)*(self.x1 - self.x0) + self.x0
            series = (series / self.max_y)*(self.y1 - self.y0) + self.y0
            series = pd.Series(series.to_list(), index = index, name = trace_name)
            self.data_series[trace_name] = series
            self.median_trace_dataframes[trace_name] = median_df

    def rescale_trace(self, trace_name, y0, y1):
        if self.data_series is None:
            print("Run trace_locs_to_values method first to set the data series dict.")
            return
        else:
            series = self.data_series[trace_name]
            series /= series.max()
            series = series*(y1 - y0) + y0
            self.data_series[trace_name] = series
        
    def plot_first_two(self, label_left: str, label_right: str, ylabel_left: str, ylabel_right: str):

        self.fig, ax = plt.subplots() 
        ax.plot(self.data_series['Trace1'], c = 'orangered', label = label_left)
        ax.set_ylabel(ylabel_left)
        axb = ax.twinx()
        axb.plot(self.data_series['Trace1'], 'b', label = label_right)
        axb.set_ylabel(ylabel_right)
        ax.legend(fontsize = "small", loc = 2); axb.legend(fontsize = "small", loc = 1)

if __name__ == "__main__":
    x0, x1, y0, y1 = 0, 0, 0, 0
    xscale, yscale = 1, 1
    title = "Plot Rippa"
    plot = plot_rippa(x0=x0, x1=x1, y0=y0, y1=y1, xscale=xscale, yscale=yscale, title=title)
    plot.active_chart()
    plot.display_trace_locations()
    plot.trace_locs_to_values()
