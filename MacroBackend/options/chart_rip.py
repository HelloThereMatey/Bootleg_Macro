import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams["backend"] = "QtAgg"
from PyQt6 import QtWidgets
import sys
import os
wd = os.path.abspath(os.path.dirname(__file__))
fdel = os.path.sep

def qt_load_file_dialog(dialog_title: str = "Choose a file", initial_dir: str = wd, 
                        file_types: str = "All Files (*);;Text Files (*.txt);;Excel Files (*.xlsx)"):
    app = QtWidgets.QApplication.instance()  # Check if an instance already exists
    if not app:  # If not, create a new instance
        app = QtWidgets.QApplication(sys.argv)

    file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, dialog_title, initial_dir, file_types, options=QtWidgets.QFileDialog.Option.DontUseNativeDialog)

    return file_path

class plot_rippa(object): 
    def __init__(self, imagePath: str = "", x0: float = 0, x1: float = 1, y0: float = 1, 
                 y1: float = 1, xscale: str = "linear", yscale: str = "linear", title: str = "Chart image",
                 chart_data_frequency: str = ""):
        #Reading the .png self.image into a multi-dimensional ndarray
        super().__init__()
        self.x0 = x0; self.x1 = x1; self.y0 = y0; self.y1 = y1
        self.xscale = xscale; self.yscale = yscale; self.title = title
        self.frequency = chart_data_frequency

        if len(imagePath) > 0:
            self.imagePath = imagePath
        else:
            self.imagePath = qt_load_file_dialog(file_types = "Image Files (*.png *.jpeg *.jpg *.bmp *.tiff *.tif *.gif *.svg *.webp *.heic *.pdf *.ico)")
        self.image = plt.imread(self.imagePath)
        print("Loaded self.image of shape (R, G, B, A)", self.image.shape)
        
        sl = self.image[:,:,0:0]
        self.image_ar = sl.shape[1]/sl.shape[0]
        print("Image aspect ratio: ", self.image_ar, "width, height (pixels): ", sl.shape[1], sl.shape[0])    
        # Display the self.image
        self.fig, self.ax = plt.subplots(figsize = (8*self.image_ar, 8))
        self.ax.imshow(self.image)

        # Initialize an empty dictionary to store RGB values
        self.trace_colors = {"left": {}, "right": {}}   #Dictionary to store the RGB values of the traces. One key for left axis traces, one for right.
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
                    trace_key = f"Trace{len(self.trace_colors['left']) + len(self.trace_colors['right']) + 1}"
                    # Store the RGB values and pixel locations in the dictionary
                    if event.key == 'shift':  # Check if Shift key is pressed
                        # Perform the alternative action for Shift+Double-Click
                        print("Shift+Double-Click detected at position:", event.xdata, event.ydata)
                        self.trace_colors["right"][trace_key] = {'RGB': rgb_values, 'Locations': pixel_locations}
                    else:
                        self.trace_colors["left"][trace_key] = {'RGB': rgb_values, 'Locations': pixel_locations}
                    print(f"{trace_key}: RGB values at ({x}, {y}): {rgb_values}, Number of matching pixels: {len(pixel_locations)}")
                    print("Trace data added, data thus far: ", self.trace_colors)

        if provide_trace_colors:
            self.trace_colors = provide_trace_colors
            for axis in self.trace_colors.keys():
                for trace_name in self.trace_colors[axis].keys():
                    rgb_values = self.trace_colors[axis][trace_name]["RGB"]
                    matching_pixels = np.where((self.image[:, :, 0] == rgb_values[0]) & 
                                                    (self.image[:, :, 1] == rgb_values[1]) & 
                                                    (self.image[:, :, 2] == rgb_values[2]))
                            # Convert indices to pixel locations
                    pixel_locations = list(zip(matching_pixels[0], matching_pixels[1]))
                    self.trace_colors[axis][trace_name]["Locations"] = pixel_locations
        else:
            self.fig.canvas.mpl_connect('button_press_event', onclick)
            plt.show()
        
    def display_trace_locations(self):
        blank_image = np.zeros_like(self.image[:,:,0])  # For grayscale
        # blank_image = np.zeros_like(self.image)  # For RGB

        # Iterate through each trace and mark the positions
        for axis in self.trace_colors.keys():
            for trace_key, trace_info in self.trace_colors[axis].items():
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
        # Assuming 'trace_dataframes' is your dictionary of DataFrames
        self.data_series = {"left": {}, "right": {}}  # Dictionary to store the final data series

        for axis in self.trace_colors.keys():
            for trace_name, locs in self.trace_colors[axis].items():
                print(f"Axis: {axis}, Trace: {trace_name}")  # Debugging print
                if locs:  # Check if locs is not empty
                    # Create a DataFrame from locations with two columns: 'Y' and 'X'
                    df = pd.DataFrame(locs["Locations"], columns=[trace_name+'_y', trace_name+'_x'])
                else:
                    df = pd.DataFrame(columns=[trace_name+'_y', trace_name+'_x'])  # Empty DataFrame with column names
                # Store the DataFrame in the new dictionary

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
                self.trace_colors[axis][trace_name]['idx_max_px'] = norm_index.max()  #Normalised index, proportion of max number of pixels.
                self.trace_colors[axis][trace_name]['idx_min_px'] = norm_index.min() 
                norm_series = series / self.max_y; 
                self.trace_colors[axis][trace_name]['max_px'] = norm_series.max()
                self.trace_colors[axis][trace_name]['min_px'] = norm_series.min()
                index = norm_index*(self.x1 - self.x0) + self.x0
                series = norm_series*(self.y1 - self.y0) + self.y0
                series = pd.Series(series.to_list(), index = index, name = trace_name)

                #Lets make the x index, datetime. 
                if start_date is not None and end_date is not None:
                    dtindex = pd.date_range(start = start_date, end = end_date, periods = len(series))
                    series = pd.Series(series.to_list(), index = dtindex, name = trace_name)

                if self.frequency:
                    """Resample the series to the specified frequency"""
                    print("Resampling the series to", self.frequency)
                    series = series.resample(self.frequency).last()

                self.data_series[axis][trace_name] = series  # Save dat bad boy...

            if yr0 is not None and yr1 is not None:
                for trace in self.data_series["right"].keys():
                    self.rescale_trace(trace, yr0, yr1)


    def rescale_trace(self, trace_name, y0, y1):
        for axis in self.data_series.keys():
            if trace_name in self.data_series[axis].keys():
                the_ax = axis
        if self.data_series is None:
            print("Run trace_locs_to_values method first to set the data series dict.")
            return
        else:
            series = pd.Series(self.data_series[the_ax][trace_name])
            series = (series - series.min())/(series.max() - series.min()) # back to a normalised series yet fraction of max value of series here, not pixel value.
            #Next line makes it normed to a fraction of the pixel range of the chart. 
            series = self.trace_colors[the_ax][trace_name]["min_px"] + series * (self.trace_colors[the_ax][trace_name]["max_px"] - self.trace_colors[the_ax][trace_name]["min_px"])
            series = series*(y1 - y0) + y0
            self.data_series[the_ax][trace_name] = series

    def plot_first_two(self, label_left: str, label_right: str, ylabel_left: str, ylabel_right: str):

        self.fig, ax = plt.subplots() 
        ax.plot(self.data_series['Trace1'], c = 'orangered', label = label_left)
        ax.set_ylabel(ylabel_left)
        axb = ax.twinx()
        axb.plot(self.data_series['Trace1'], 'b', label = label_right)
        axb.set_ylabel(ylabel_right)
        ax.legend(fontsize = "small", loc = 2); axb.legend(fontsize = "small", loc = 1)

##### Convenience function to run a rip..........

def rip_chart(imagePath: str = "", trace_colors: dict = {} , x0: float = 0, x1: float = 1, y0: float = 0, y1: float = 1, yr0: float = None, yr1: float = None,
              title: str = "Plot Rippa", start_date: str = None, end_date: str = None, resample_to_freq: str = ""):
    
    if imagePath:
        plot = plot_rippa(imagePath=imagePath, x0=x0, x1=x1, y0=y0, y1=y1, title=title, chart_data_frequency=resample_to_freq)
    else:
        plot = plot_rippa(x0=x0, x1=x1, y0=y0, y1=y1, title=title)
    if trace_colors:
        plot.active_chart(provide_trace_colors=trace_colors)
    else:
        plot.active_chart()
    plot.display_trace_locations()
    plot.trace_locs_to_values(yr0=yr0, yr1=yr1, start_date = start_date, end_date = end_date)
    return plot
    

if __name__ == "__main__":
    image_path = '/Users/jamesbishop/Downloads/fknScamercnt.png'
    # trace_colors_given = {"left": {"Trace1": {"RGB": np.array([0, 0, 0, 1])}},
    #                       "right": {"Trace2": {"RGB": np.array([0.92941177, 0.49019608, 0.19215687, 1.0])}}}
    # ##Will want to modify the above to add te axis for the trace and change the modification that the trace_colors flag does...
    # x0, x1, y0, y1 = 0, 1, 116000, 124000
    # yr0, yr1 = 38000, 100000
    # title = "Plot Rippa"
    # plot = plot_rippa(imagePath=image_path, x0=x0, x1=x1, y0=y0, y1=y1, title=title, chart_data_frequency='D') #imagePath=image_path, 
    # plot.active_chart()
    # plot.display_trace_locations()
    # plot.trace_locs_to_values(yr0=yr0, yr1=yr1, start_date = "2023-12-01", end_date = "2024-12-31")
    # ax = pd.Series(plot.data_series["left"]["Trace1"]).plot()
    # pd.Series(plot.data_series["right"]["Trace2"]).plot(ax = ax, secondary_y=True)
    # plt.show()
    # print(plot.data_series, pd.Series(plot.data_series["left"]["Trace1"]).index.has_duplicates,
    #        pd.Series(plot.data_series["right"]["Trace2"]).index.has_duplicates)

    plot = rip_chart(imagePath='/Users/jamesbishop/Downloads/cw_gli.png', y0 = 1000, y1 = 2600,
                             yr0=80, yr1=220, start_date="2010-01-01", end_date="2024-08-20", resample_to_freq="W")
    export = pd.HDFStore('/Users/jamesbishop/Documents/Python/Bootleg_Macro/User_Data/SavedData/gli_cw.h5s')
    export['cwgli'] = plot.data_series['right']['Trace2'].rename('Global_Liquidity_Index_CW')
    export.close()