import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams["backend"] = "QtAgg"
from PyQt6 import QtWidgets
import sys
import os
import json
import pickle

wd = os.path.abspath(os.path.dirname(__file__))
fdel = os.path.sep

def qt_load_file_dialog(dialog_title: str = "Choose a file", initial_dir: str = wd, 
                        file_types: str = "All Files (*);;Text Files (*.txt);;Excel Files (*.xlsx)"):
    app = QtWidgets.QApplication.instance()  # Check if an instance already exists
    if not app:  # If not, create a new instance
        app = QtWidgets.QApplication(sys.argv)

    file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, dialog_title, initial_dir, file_types, options=QtWidgets.QFileDialog.Option.DontUseNativeDialog)

    return file_path

def qt_save_file_dialog(dialog_title: str = "Save file as", initial_dir: str = wd, 
                       file_types: str = "All Files (*);;Text Files (*.txt);;Excel Files (*.xlsx)"):
    app = QtWidgets.QApplication.instance()  # Check if an instance already exists
    if not app:  # If not, create a new instance
        app = QtWidgets.QApplication(sys.argv)

    file_path, _ = QtWidgets.QFileDialog.getSaveFileName(None, dialog_title, initial_dir, file_types, options=QtWidgets.QFileDialog.Option.DontUseNativeDialog)

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
        self.imdir = os.path.dirname(imagePath); print("Directory image loaded from: ", self.imdir)

        if len(imagePath) > 0:
            self.imagePath = imagePath
        else:
            self.imagePath = qt_load_file_dialog(initial_dir=wd, file_types = "Image Files (*.png *.jpeg *.jpg *.bmp *.tiff *.tif *.gif *.svg *.webp *.heic *.pdf *.ico)")
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

    def load_image(self, imagePath: str = ""):
        """Load a new image into the plot. This will replace the current image."""
        if len(imagePath) > 0:
            self.imagePath = imagePath
        else:
            self.imagePath = qt_load_file_dialog(initial_dir=wd, file_types = "Image Files (*.png *.jpeg *.jpg *.bmp *.tiff *.tif *.gif *.svg *.webp *.heic *.pdf *.ico)")
        self.image = plt.imread(self.imagePath)
        print("Loaded self.image of shape (R, G, B, A)", self.image.shape)
        
        sl = self.image[:,:,0:0]
        self.image_ar = sl.shape[1]/sl.shape[0]
        print("Image aspect ratio: ", self.image_ar, "width, height (pixels): ", sl.shape[1], sl.shape[0])    

    def active_chart(self, provide_trace_colors: dict = {}, color_tolerance: float = 0.1, message: str = "Double-click on a pixel to select its color as a trace.\
                Hold shift and double-click to specify that the trace is plotted vs right axis rather than left."):
        """ **Parameter**: provide_trace_colors must in format {"trace_name": {"RGB": [R, G, B, A]}},
        where R,G,B,A are the red, blue, green & alpha values that define the color for that trace (float between 0 and 1).
        Double-click on a pixel that is within a trace to select that color as the trace color. Hold shift and dbl-click to
        specify that the trace is plotted vs right axis rather than left..
        **Parameter**: color_tolerance: Maximum allowed distance (Euclidean in RGB) for a pixel color to be considered a match.
                       Adjust based on image compression/artifacts. Value is relative to max distance (sqrt(3) for normalized RGB).
        **Parameter**: message: A message to display on the chart, e.g. "Click on a pixel to select its color as a trace.".
        This method will display the chart image and allow the user to double-click on pixels to select
        """

        def onclick(event):
            if event.dblclick:
                if event.xdata is not None and event.ydata is not None:
                    x, y = int(event.xdata), int(event.ydata)
                    clicked_rgb = self.image[y, x, :3] # Get RGB, ignore alpha if present

                    # Calculate the squared Euclidean distance between the clicked color and all pixel colors
                    # We use RGB channels (0, 1, 2). Assuming image values are floats [0, 1].
                    # If they are uint8 [0, 255], divide by 255.0 first or adjust tolerance.
                    # Ensure image is float for calculation
                    img_float = self.image[:, :, :3].astype(np.float32)
                    if np.max(img_float) > 1.0: # Check if image is likely 0-255
                        img_float /= 255.0
                        clicked_rgb = clicked_rgb.astype(np.float32) / 255.0


                    # Calculate squared distance (faster than sqrt)
                    distances_sq = np.sum((img_float - clicked_rgb)**2, axis=2)

                    # Define squared tolerance (avoids sqrt calculation)
                    tolerance_sq = color_tolerance**2 # Adjust this tolerance value as needed

                    # Find pixels within the squared tolerance
                    matching_pixels = np.where(distances_sq <= tolerance_sq)

                    # Convert indices to pixel locations (y, x)
                    pixel_locations = list(zip(matching_pixels[0], matching_pixels[1]))

                    # Generate the next trace key
                    trace_key = f"Trace{len(self.trace_colors['left']) + len(self.trace_colors['right']) + 1}"

                    # Store the RGB values (use the originally clicked color) and pixel locations
                    if event.key == 'shift':
                        print("Shift+Double-Click detected at position:", event.xdata, event.ydata)
                        self.trace_colors["right"][trace_key] = {'RGB': self.image[y, x], 'Locations': pixel_locations} # Store original clicked RGBA
                    else:
                        self.trace_colors["left"][trace_key] = {'RGB': self.image[y, x], 'Locations': pixel_locations} # Store original clicked RGBA

                    print(f"{trace_key}: Clicked RGB at ({x}, {y}): {self.image[y, x]}, Number of matching pixels: {len(pixel_locations)}")
                    #print("Trace data added, data thus far: ", self.trace_colors)

        if provide_trace_colors:
            self.trace_colors = provide_trace_colors
            for axis in self.trace_colors.keys():
                for trace_name in self.trace_colors[axis].keys():
                    target_rgb = np.array(self.trace_colors[axis][trace_name]["RGB"][:3]) # Use provided RGB

                    # --- Repeat the distance calculation logic from onclick ---
                    img_float = self.image[:, :, :3].astype(np.float32)
                    if np.max(img_float) > 1.0:
                        img_float /= 255.0
                        target_rgb = target_rgb.astype(np.float32) / 255.0

                    distances_sq = np.sum((img_float - target_rgb)**2, axis=2)
                    tolerance_sq = color_tolerance**2
                    matching_pixels = np.where(distances_sq <= tolerance_sq)
                    # ----------------------------------------------------------

                    pixel_locations = list(zip(matching_pixels[0], matching_pixels[1]))
                    self.trace_colors[axis][trace_name]["Locations"] = pixel_locations
                    print(f"Provided {trace_name}: Target RGB: {self.trace_colors[axis][trace_name]['RGB']}, Found {len(pixel_locations)} matching pixels.")
        else:
            self.fig.canvas.mpl_connect('button_press_event', onclick)
            # Display message if provided
            if message:
                self.ax.text(0.02, 0.98, message, transform=self.ax.transAxes, 
                            fontsize=12, verticalalignment='top', horizontalalignment='left',
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
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

    def display_colored_traces(self, color_map=None):
        """
        Display each trace in a different color on a blank image with same dimensions as original.
        
        Parameters:
        -----------
        color_map : dict, optional
            Dictionary mapping trace names to RGB color values. 
            Format: {'Trace1': [R, G, B], 'Trace2': [R, G, B], ...}
            If not provided, default colors will be assigned.
        """
        # Create a blank RGB image with same dimensions as original - initialize with white (255) pixels
        blank_image = np.ones((self.image.shape[0], self.image.shape[1], 3), dtype=np.uint8) * 255
        
        # Default colors if not provided (RGB format)
        default_colors = {
            'Trace1': [0, 255, 0],    # Green
            'Trace2': [255, 255, 0],  # Yellow
            'Trace3': [255, 0, 0],    # Red
            'Trace4': [0, 0, 255],    # Blue
            'Trace5': [255, 0, 255],  # Magenta
            'Trace6': [0, 255, 255],  # Cyan
        }
        
        # Use provided color map or default
        colors = color_map if color_map else default_colors
        
        # Iterate through each trace in left and right axes
        for axis in self.trace_colors.keys():
            for trace_key, trace_info in self.trace_colors[axis].items():
                if 'Locations' in trace_info:
                    # Get color for this trace
                    trace_color = colors.get(trace_key, [255, 255, 255])  # Default to white if not in map
                    
                    # Plot each pixel from the trace
                    for (y, x) in trace_info['Locations']:
                        blank_image[y, x] = trace_color
        
        # Display the marked image
        plt.figure(figsize=(10, 10*self.image.shape[0]/self.image.shape[1]))  # Maintain aspect ratio
        plt.imshow(blank_image)
        
        # Add a legend
        legend_handles = []
        for axis in self.trace_colors.keys():
            for trace_key in self.trace_colors[axis].keys():
                if trace_key in colors:
                    color = np.array(colors[trace_key]) / 255.0  # Normalize to 0-1 for matplotlib
                    legend_handles.append(plt.Line2D([0], [0], color=color, lw=4, label=f"{axis}: {trace_key}"))
        
        if legend_handles:
            plt.legend(handles=legend_handles, loc='best')
        
        plt.title('Colored Traces')
        plt.axis('off')  # Hide axes
        plt.tight_layout()
        plt.show()

    def create_x_indexes(self, y: int = 50, start_date: str = None, end_date: str = None, frequency: str = "D"):
        """Create x indexes for the data found in the trace_colors dict. These will aply for when one is extracting
        colored regions from an image of a chart that specify different regimes/ active buy/sell signals. 

        **Parameters:**
        -----------
        - y : int - The y-coordinate of the line of pixels to be used for the x-axis.
        - start_date : str - Start date for the x-axis in 'YYYY-MM-DD' format.
        - end_date : str - End date for the x-axis in 'YYYY-MM-DD' format.
        frequency : str - Frequency for resampling the x-axis data. Default is 'D' (daily).
        """
        if start_date is None or end_date is None:
            print("Please provide both start_date and end_date.")
            return
        
        # Dictionary to store boolean series
        self.boolean_series = {"left": {}, "right": {}}

        # Create a date range based on the provided start and end dates
        for axis in self.trace_colors.keys():
            for trace_name in self.trace_colors[axis].keys():
                trace_info = self.trace_colors[axis][trace_name]
                if "Locations" not in trace_info.keys():
                    print(f"No location data found for {axis}:{trace_name}")
                    continue
                pixlocs = trace_info["Locations"]
                # Create a date range based on the provided start and end dates
                date_range = pd.date_range(start=start_date, end=end_date, periods=self.image.shape[1])
                # Create a new DataFrame with the date range as the index
                ser = pd.Series()
                 # Initialize boolean array with False for all x positions
                bool_array = np.zeros(self.image.shape[1], dtype=bool)
                
                # Set True for x coordinates where this trace color is found
                x_coords = [x for y, x in trace_info["Locations"]]
                bool_array[x_coords] = True
                
                # Create a pandas Series with the date range as index
                bool_series = pd.Series(bool_array, index=date_range, name=f"{axis}_{trace_name}")
                
                # Resample if frequency is provided and different from the date range frequency
                if frequency:
                    # Resample and fill with method that makes sense for boolean data
                    # For boolean data, we'll consider it True if any value in the period is True
                    bool_series = bool_series.resample(frequency).last()
            
                # Store the series
                self.boolean_series[axis][trace_name] = bool_series
                print(f"Created boolean series for {axis}:{trace_name} with {bool_series.sum()} True values")


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

    def export_raw_pixlocs(self, savepath: str = None):
        if savepath is None:
            savepath = qt_save_file_dialog(dialog_title="Choose name & location to save your .pkl", initial_dir=self.imdir, file_types="pickle files (*.pkl)")

        # json_for = json.dumps(self.trace_colors)
        # with open(savepath, 'w') as file:
        #     file.write(json_for)
        with open(savepath, 'wb') as file:
            pickle.dump(self.trace_colors, file)

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

def vams_42_macro_chart_rip(start_date: str, end_date: str, frequency: str = "D", image_path: str = None, export_pixlocs:bool = False,
                            color_names: dict = {'left_Trace1': "green", 'left_Trace2': 'yellow', 'left_Trace3': 'red'}, chart_message:str = None,
                            initial_dir: str = None) -> tuple[pd.DataFrame, plot_rippa]:
    """Function to rip a 42 macro VAMS chart as screenshotted from a 42Macro slidedeck. ill extract green, orange & red regions and 
    return a pandas datetime index Dataframe with main column "signal" with the signal color as a function of date.

    **Parameters:**
    -----------
    - start_date : str - Start date for the x-axis in 'YYYY-MM-DD' format.
    - end_date : str - End date for the x-axis in 'YYYY-MM-DD' format.
    - frequency : str - Frequency for resampling the x-axis data. Default is 'D' (daily).
    - image_path : str - Path to the chart image. If not provided, a file dialog will open to choose an image.
    - export_pixlocs : bool - If True, export the raw pixel locations of the traces to a .pkl file.
    - color_names : dict - Dictionary mapping trace names to their colors. Default is {'left_Trace1': "green", 'left_Trace2': 'yellow', 'left_Trace3': 'red'}.
    - chart_message : str - Message to display on the chart, e.g. "Double click on green, yellow and then red regions in that order.".
    - initial_dir : str - Initial directory for the file dialog to choose the chart image.  
    """

    if initial_dir is None:
        initial_dir = wd  # Use the current working directory if not provided

    if image_path is None:
        image_path = qt_load_file_dialog(dialog_title="Choose a chart image that you have cropped to chart area only.", 
                                     initial_dir=initial_dir, file_types="Image Files (*.png *.jpeg *.jpg *.bmp *.tiff *.tif *.gif *.svg *.webp *.heic *.pdf *.ico)")
        

    plot = plot_rippa(imagePath=image_path)
    if chart_message is not None:
        plot.active_chart(message=chart_message)
    else:
        plot.active_chart()
    if export_pixlocs:
        plot.export_raw_pixlocs()
    
    plot.create_x_indexes(start_date = start_date, end_date = end_date, frequency = frequency)
    df = pd.concat([plot.boolean_series['left'][key] for key in plot.boolean_series['left'].keys()], axis=1).ffill(axis=0).rename(columns = color_names)

    # Create a signal column that identifies the active trace
    df['signal'] = pd.NA  # Start with NA values

    # Use boolean indexing
    df.loc[df[color_names["left_Trace3"]] == 1, 'signal'] = color_names["left_Trace3"]     # Apply Red first (highest priority)
    df.loc[df[color_names["left_Trace2"]] == 1, 'signal'] = color_names["left_Trace2"]  # Then Yellow
    df.loc[df[color_names["left_Trace1"]] == 1, 'signal'] = color_names["left_Trace1"]  # Then Green

    # Fill any remaining NAs with "None" or another default value
    df['signal'] = df['signal'].fillna('None')

    return df, plot # Return the signal series

def plot_signal_colored_timeseries(
    data: pd.DataFrame,
    price_col: str,
    signal_col: str,
    signal_colors=None,
    figsize=(12, 6),
    title="Signal Colored Time Series",
    use_log_scale=True,
    date_format='%Y-%m',
    date_interval=None,
    legend_loc='upper left'
):
    """
    Create a time series plot with colored backgrounds based on signal values.
    
    Parameters:
    -----------
    data : pd.DataFrame
        DataFrame with DatetimeIndex containing price and signal data
    price_col : str
        Column name for the price data to be plotted
    signal_col : str
        Column name for the signal data that determines background colors
    signal_colors : dict, optional
        Dictionary mapping signal values to colors (RGBA or color names)
        Default: {'green': (0, 0.5, 0, 0.5), 'yellow': (1, 0.84, 0, 0.5), 'red': (1, 0, 0, 0.5)}
    figsize : tuple, optional
        Figure size as (width, height) in inches
    title : str, optional
        Plot title
    use_log_scale : bool, optional
        Whether to use logarithmic scale for price axis
    date_format : str, optional
        Format string for date labels on x-axis
    date_interval : int, optional
        Interval in months between date ticks
    legend_loc : str, optional
        Location of the legend
        
    Returns:
    --------
    fig, ax : matplotlib figure and axes objects
    """
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.colors import to_rgba
    from matplotlib.patches import Patch
    import pandas as pd
    import numpy as np
    
    # Make a copy of the data to avoid modifying the original
    data_copy = data.copy()
    
    # Fill NaN values with 'None' string
    data_copy[signal_col] = data_copy[signal_col].fillna('None')
    
    # Default signal colors if none provided
    if signal_colors is None:
        signal_colors = {
            'green': to_rgba('green', 0.5),
            'yellow': to_rgba('gold', 0.5),
            'red': to_rgba('red', 0.5),
            'None': to_rgba('white', 1)  # Transparent for "None"
        }
    else:
        # Convert any string colors to rgba
        for key, value in signal_colors.items():
            if isinstance(value, str):
                signal_colors[key] = to_rgba(value, 0.5)
    
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Find where the signal changes
    signal_changes = data_copy[signal_col] != data_copy[signal_col].shift(1)
    change_indices = data_copy.index[signal_changes].tolist()
    
    # Ensure the first and last dates are included
    if data_copy.index[0] not in change_indices:
        change_indices.insert(0, data_copy.index[0])
    if data_copy.index[-1] not in change_indices:
        change_indices.append(data_copy.index[-1])
    
    # Add colored vertical spans (backgrounds)
    used_signals = set()
    
    for i in range(len(change_indices) - 1):
        start_date = change_indices[i]
        end_date = change_indices[i+1]
        
        # Get signal value for this period and convert to string
        signal_value = data_copy.loc[start_date, signal_col]
        signal_key = str(signal_value)
        
        # Get color (default to white if not found)
        color = signal_colors.get(signal_key, to_rgba('white', 0.5))
        
        # Add the vertical span
        ax.axvspan(start_date, end_date, facecolor=color, alpha=0.5, zorder=0)
        
        # Track used signals for legend
        used_signals.add(signal_key)
    
    # Convert the index to datetime64 and the price column to numeric values
    x_values = data_copy.index.to_numpy()
    y_values = pd.to_numeric(data_copy[price_col], errors='coerce').to_numpy()
    
    # Plot the price data directly with numpy arrays to avoid category converter issues
    price_line, = ax.plot(
        x_values,
        y_values,
        color='black',
        label=price_col,
        linewidth=1.5,
        zorder=5  # Ensure line is above background
    )
    
    # Set up logarithmic scale if requested
    if use_log_scale:
        ax.set_yscale('log')
    
    # Format the x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    if date_interval is None:
        date_interval = round(((data.index[-1] - data.index[0])).days // 30) // 20 # Default to approximately 20 ticks
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=date_interval))
    
    # Rotate date labels
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Set labels and title
    ax.set_ylabel(f'{price_col}', color='black', fontsize=12)
    ax.set_title(title, fontsize=14)
    
    # Create legend elements for used signals
    legend_elements = [Patch(facecolor=signal_colors[s], label=s) for s in used_signals if s in signal_colors]
    legend_elements.append(price_line)
    
    # Add the legend
    ax.legend(handles=legend_elements, loc=legend_loc)
    
    # Add grid lines
    ax.grid(True, axis='y', linestyle='--', alpha=0.6)
    ax.margins(x=0.01, y=0.03)  # Add margins to avoid cutting off data
    # Adjust layout
    plt.tight_layout()
    
    return fig, ax 


if __name__ == "__main__":
    #image_path = ''

    # miplot = None
    # if miplot is None:
    #     miplot = qt_load_file_dialog(dialog_title="Choose a chart image that you have cropped to chart area only.", 
    #                                  initial_dir=wd, file_types="Image Files (*.png *.jpeg *.jpg *.bmp *.tiff *.tif *.gif *.svg *.webp *.heic *.pdf *.ico)")
    # plot = plot_rippa(imagePath=miplot)
    # plot.active_chart()
    # plot.export_raw_pixlocs()
    path = '/Users/jamesbishop/Documents/Financial/Investment/MACRO_STUDIES/Proper_Studies/42Macro/SPX_Gold_Bondz'

    signal, plot = vams_42_macro_chart_rip(start_date="1998-01-01", end_date="2025-03-05", frequency="W", 
                                           chart_message="Double click on green, yellow and then red regions in that order.",
                                           initial_dir= path)
    signal.to_excel(qt_save_file_dialog(dialog_title="Save the signal series as an Excel file", initial_dir=plot.imdir, file_types="Excel Files (*.xlsx)"))
    print("Signal series saved to Excel file.")
    print(signal)

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

    # plot = rip_chart(imagePath='/Users/jamesbishop/Downloads/cw_gli.png', y0 = 1000, y1 = 2600,
    #                          yr0=80, yr1=220, start_date="2010-01-01", end_date="2024-08-20", resample_to_freq="W")
    # export = pd.HDFStore('/Users/jamesbishop/Documents/Python/Bootleg_Macro/User_Data/SavedData/gli_cw.h5s')
    # export['cwgli'] = plot.data_series['right']['Trace2'].rename('Global_Liquidity_Index_CW')
    # export.close()