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

    def active_chart(self, provide_trace_colors: dict = {}):
        """ **Parameter**: provide_trace_colors must in format {"trace_name": {"RGB": [R, G, B, A]}}, 
        where R,G,B,A are the red, blue, green & alpha values that define the color for that trace (float between 0 and 1). 
        Double-click on a pixel that is within a trace to select that color as the trace color. Hold shift and dbl-click to
        specify that the trace is plotted vs right axis rather than left.."""

        def onclick(event):
            if event.dblclick:  
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
                    if event.key == 'shift':  # Check if Shift key is pressed
                        # Perform the alternative action for Shift+Double-Click
                        print("Shift+Double-Click detected at position:", event.xdata, event.ydata)
                        self.trace_colors[trace_key] = {'RGB': rgb_values, "axis": "right", 'Locations': pixel_locations}
                    else:
                        self.trace_colors[trace_key] = {'RGB': rgb_values, "axis": "left", 'Locations': pixel_locations}
                    print(f"{trace_key}: RGB values at ({x}, {y}): {rgb_values}, Number of matching pixels: {len(pixel_locations)}")
                    print(trace_key, self.trace_colors[trace_key]['RGB'], type(self.trace_colors[trace_key]['RGB']))

        if provide_trace_colors:
            self.trace_colors = provide_trace_colors
            for trace_name in self.trace_colors.keys():
                rgb_values = self.trace_colors[trace_name]["RGB"]
                matching_pixels = np.where((self.image[:, :, 0] == rgb_values[0]) & 
                                                (self.image[:, :, 1] == rgb_values[1]) & 
                                                (self.image[:, :, 2] == rgb_values[2]))
                        # Convert indices to pixel locations
                pixel_locations = list(zip(matching_pixels[0], matching_pixels[1]))
                self.trace_colors[trace_name]["Locations"] = pixel_locations
        else:
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
    
    def trace_locs_to_values(self, yr0: float = None, yr1: float = None, start_date: str = None, end_date: str = None):
        """Parameters:
        * yr0, yr1: if a right axis is present on the chart as well as left axis, min and max values of the right axis. 
        * start_date, end_date: start and end dates for the x - axis ('YYYY-MM-DD'), will make a datetime index. """

        self.max_x = self.image.shape[1]  #These are the max number of pixels in each direction for the chart. 
        self.max_y = self.image.shape[0]
        print("Max x, y: ", self.max_x, self.max_y)
        self.trace_dataframes = {}
        for trace_name, locs in self.trace_colors.items():
            #print(f"Trace: {trace_name}, Locations: {locs}")  # Debugging print
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
            norm_index = series.index / self.max_x
            #These save the position of the max of the data series on the chart as fraction of max no. pixels.
            self.trace_colors[trace_name]['idx_max_px'] = norm_index.max()  #Normalised index, proportion of max number of pixels.
            self.trace_colors[trace_name]['idx_min_px'] = norm_index.min() 
            norm_series = series / self.max_y; 
            self.trace_colors[trace_name]['max_px'] = norm_series.max()
            self.trace_colors[trace_name]['min_px'] = norm_series.min()
            index = norm_index*(self.x1 - self.x0) + self.x0
            series = norm_series*(self.y1 - self.y0) + self.y0
            series = pd.Series(series.to_list(), index = index, name = trace_name)

            #Lets make the x index, datetime. 
            if start_date is not None and end_date is not None:
                dtindex = pd.date_range(start = start_date, end = end_date, periods = len(series))
                series = pd.Series(series.to_list(), index = dtindex, name = trace_name)

            self.data_series[trace_name] = series
            self.median_trace_dataframes[trace_name] = median_df

        if yr0 is not None and yr1 is not None:
            for trace in self.data_series.keys():
                if self.trace_colors[trace]["axis"] == 'right':
                    self.rescale_trace(trace, yr0, yr1)


    def rescale_trace(self, trace_name, y0, y1):
        if self.data_series is None:
            print("Run trace_locs_to_values method first to set the data series dict.")
            return
        else:
            series = pd.Series(self.data_series[trace_name])
            series = (series - series.min())/(series.max() - series.min()) # back to a normalised series yet fraction of max value of series here, not pixel value.
            #Next line makes it normed to a fraction of the pixel range of the chart. 
            series = self.trace_colors[trace_name]["min_px"] + series * (self.trace_colors[trace_name]["max_px"] - self.trace_colors[trace_name]["min_px"])
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
    image_path = '/Users/jamesbishop/Pictures/CHartPics_ToDIgitize/CapWars_GLvsXAU-cc.png'
    trace_colors_given = {"Trace1": {"RGB": np.array([0, 0, 0, 1]), "axis": "left"},
                          "Trace2": {"RGB": np.array([0.92941177, 0.49019608, 0.19215687, 1.0]), "axis": "right"}}
    ##Will want to modify the above to add te axis for the trace and change the modification that the trace_colors flag does...
    x0, x1, y0, y1 = 0, 1, 1000, 2600
    yr0, yr1 = 80, 220
    xscale, yscale = 1, 1
    title = "Plot Rippa"
    plot = plot_rippa(imagePath=image_path, x0=x0, x1=x1, y0=y0, y1=y1, xscale=xscale, yscale=yscale, title=title)
    plot.active_chart(provide_trace_colors=trace_colors_given)
    plot.display_trace_locations()
    plot.trace_locs_to_values(yr0=yr0, yr1=yr1, start_date = "2010-01-01", end_date = "2024-07-07")
    ax = pd.Series(plot.data_series["Trace1"]).plot()
    pd.Series(plot.data_series["Trace2"]).plot(ax = ax, secondary_y=True)
    plt.show()
    print(plot.data_series, pd.Series(plot.data_series["Trace1"]).index.has_duplicates,
           pd.Series(plot.data_series["Trace2"]).index.has_duplicates)
    print(plot.trace_colors["Trace1"]["axis"], plot.trace_colors["Trace2"]["axis"])
