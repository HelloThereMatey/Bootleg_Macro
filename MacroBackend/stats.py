from typing import Literal
import pandas as pd
import numpy as np
import Utilities, Charting
#import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import seaborn as sns
from scipy import stats
from statsmodels.tsa.stattools import adfuller, kpss

import sys
import os
#######  Add the parent directory to the path so that the MacroBackend module can be imported.  #######
wd = os.path.dirname(__file__); parent = os.path.dirname(wd)
fdel = os.path.sep
sys.path.append(parent)

#### Standalone functions......

def qd_corr(series1: pd.Series, series2: pd.Series) -> float:
    """
    Calculates the correlation between two pandas Series using the Quant-Dare method.

    :param series1: The first pandas Series. When calculating rolling correlations, this will be a slice over the window of the series. 
    :param series2: The second pandas Series. When calculating rolling correlations, this will be a slice over the window of the series.

    :return: The Quant-Dare correlation between the two Series.
    """

    # Calculate the sum of the products of the deviations from the mean
    sum_products = (series1 * series2).sum()

    # Calculate the sum of the squares of the deviations from the mean
    sum_squares1 = (series1 ** 2).sum()
    sum_squares2 = (series2 ** 2).sum()

    # Calculate the Quandt-Dichotomous correlation
    qd_corr = sum_products / np.sqrt(sum_squares1 * sum_squares2)

    return qd_corr

def rolling_qd(series1: pd.Series, series2: pd.Series, window: int = 1) -> pd.Series:
    """
    Calculates the rolling Quant-Dare correlation between two pandas Series.

    :param series1: The first pandas Series.
    :param series2: The second pandas Series.
    :param window: The size of the rolling window.

    :return: A pandas Series containing the rolling Quant-Dare correlation values.
    """

    if len(series1) != len(series2):
        raise ValueError("Series must have the same length")
    
    rolling_corrs = []
    for i in range(window - 1, len(series1)):
        window_series1 = series1[i - (window - 1):i + 1]
        window_series2 = series2[i - (window - 1):i + 1]
        corr = qd_corr(window_series1, window_series2)
        rolling_corrs.append(corr)
    
    return pd.Series(rolling_corrs, index=series1.index[window - 1:])

def rolling_corr(series1: pd.Series, series2: pd.Series, window: int, method: str = "pearson") -> pd.Series:
    """Calculate rolling correlation between two time series"""
    # Ensure both series are aligned to same index
    common_idx = series1.index.intersection(series2.index)
    s1 = series1.loc[common_idx]
    s2 = series2.loc[common_idx]
    
    # Calculate rolling correlation directly
    rolling_corr = pd.Series(
        index=common_idx,
        data=[s1.iloc[i-window:i].corr(s2.iloc[i-window:i], method=method) 
              if i >= window else np.nan 
              for i in range(len(common_idx))]
    )
    
    return rolling_corr

def check_stationarity(series):
    # Augmented Dickey-Fuller test
    # H0: Series has unit root (non-stationary)
    adf_result = adfuller(series, regression='ct')
    
    # KPSS test
    # H0: Series is trend stationary
    kpss_result = kpss(series, regression='ct')
    
    return {
        'ADF': {
            'statistic': adf_result[0],
            'p-value': adf_result[1],
            'critical_values': adf_result[4]
        },
        'KPSS': {
            'statistic': kpss_result[0],
            'p-value': kpss_result[1],
            'critical_values': kpss_result[3]
        }
    }

####### My Pair stats class for looking at correlation between a pair of assets in great detail....
class Pair_stats(object):
    """"
    Class to calculate stats between two series for a number of different window lengths. 
    Stats such as correlation.
    Determines frequency and downsamples a series to match the other if necessary..
    
    Parameters (__init__):
    - series1 (pd.Series): The first input series.
    - series2 (pd.Series): The second input series.
    - windows (list): A list of window lengths for which to calculate the rolling correlation.

    Key Attributes:
    - self (pd.DataFrame inherited): A DataFrame containing the original series and their log and pcercent returns, as well as the rolling correlations.
    - This is just a dataframe but it has a self.name attribute. 
    - self.full_corr (float): The full correlation between the two series over the whole length. 
    """

    def __init__(self, series1: pd.Series, series2: pd.Series, windows: list = [30, 90, 180, 365], corr_method: str = "pearson",
                 ser1_title: str = "", ser2_title: str = "", watchlist_meta: pd.DataFrame = pd.DataFrame(),
                 downsample_to: str = ""):
        super().__init__()
  
        self.series1 = series1
        self.series2 = series2
        self.corr_method = corr_method

        self.downsample_to = downsample_to  #Use pandas frequency strings to resample both series and decrease the frequency. e.g "W", "M", "MS"
        self.freq_rep_dict = {'D': "Daily", "W": "Weekly", "M": "Monthly", "Q": "Quarterly", "Y": "Yearly"}

        if len(ser1_title) == 0:
            self.ser1_title = self.series1.name
        else:
            self.ser1_title = ser1_title
        if len(ser2_title) == 0:
            self.ser2_title = ser2_title = self.series2.name
        else:
            self.ser2_title = ser2_title

        if self.series1.name != self.ser1_title or self.series2.name != self.ser2_title:
            print("Renaming series to match titles....")
            series1.rename(self.ser1_title, inplace=True)
            series2.rename(self.ser2_title, inplace=True)

        if watchlist_meta.empty:
            self.watchlist_meta = None
        else:
            self.watchlist_meta = watchlist_meta

        print("Series names: series1:",self.series1.name, "series2:", self.series2.name)
        self.frequency = ""
        self.windows = windows 
        
        if self.check_input_series() is None:
            return
        self.name = f'{self.ser1_title} and {self.ser2_title}'
        self.data = self.returns_df()
        print("Windows: ", self.windows)
        self.windows.append(min(len(self.series1), len(self.series2))-2)

        self.rolling_stats(corr_method = corr_method)

    def check_input_series(self):
        """ Check the input series and ensure they are of the same frequency and length. 
        Force them into to that state if not."""

            #Ensure that both are series first:
        try:
            series1 = Utilities.ensure_series(self.series1)
            series2 = Utilities.ensure_series(self.series2)
            print("Input series object types: ", type(series1), type(series2))
        except ValueError as e:
            print(e)
            print("Input series object types: ", type(series1), type(series2), "only pd.Series objects are currentl supported. Convert them to Series first.")
            return None
        
            ## Ensure that the two series are of the same frequency and length. 
        self.freq1 = Utilities.freqDetermination(series1); self.freq1.DetermineSeries_Frequency()
        freq2 = Utilities.freqDetermination(series2); freq2.DetermineSeries_Frequency()
        print(self.freq1.frequency, freq2.frequency)
        self.series1 = self.freq1.series; self.series2 = freq2.series
        self.freq_rep_dict = self.freq1.frequency_dict
        
        if self.freq1.frequency != freq2.frequency:
            print("Frequency of series do not match, downsampling the higher freq series to match...")
            try:
                s1_rank = self.freq1.freq_list[self.freq1.freq_list == self.freq1.frequency].index.to_list()[0]
                s2_rank = freq2.freq_list[freq2.freq_list == freq2.frequency].index.to_list()[0]
            except Exception as e:
                print('Error getting frequency rank for resampling, ', e)
                return None
            
            if s1_rank > s2_rank:
                print('Resampling series 2 to match series 1...')
                series2 = series2.resample(self.freq1.freq).last()
                self.series2 = series2
                self.frequency = self.freq1.frequency
                print(self.freq1.frequency, self.frequency)
            elif s1_rank < s2_rank:
                print('Resampling series 1 to match series 2...')
                series1 = series1.resample(freq2.freq).last()
                self.series1 = series1
                self.frequency = freq2.frequency
                print(freq2.frequency, self.frequency)
            else:
                print("Are the two series of the same frequency?...")
                return None
        else:
            self.frequency = self.freq1.frequency

        if len(self.downsample_to) > 0: 
            self.series1 = series1.resample(self.downsample_to).last() #Must use a lower frequency than original freq, e.g "W"from "D"..
            self.series2 = series2.resample(self.downsample_to).last()
            freqCheck = Utilities.freqDetermination(self.series1)
            freqCheck.DetermineSeries_Frequency();  self.frequency = freqCheck.frequency
        
        # Make sure series are the same lengths after first having made them the same frequency:
        self.series1, self.series2 = Utilities.match_series_lengths(self.series1, self.series2)
        self.per_in_year = round(self.freq1.periods_in_day[self.frequency]*365.25)
        print("Series frequencies (common to both): ", self.frequency, "periods in year: ", self.per_in_year)
        return 1
    
    def returns_df(self):
        """ Calculate the log returns for the two series and return a DataFrame with the returns. 
        The DataFrame will contain the original series, the log returns, and the percentage returns.
        - This is stored in the self.data attribute."""
            # # Let's calulate some returns innit...
        df = pd.concat([self.series1, self.series2], axis = 1)
        print("Calculating returns for series: ", self.series1.name, self.series2.name,
              ", with frequency: ", self.frequency, ", periods in 1 year: ", self.per_in_year)

        df["ret_"+self.ser1_title] = np.log(df[self.series1.name]/df[self.series1.name].shift(1))
        df["ret_"+self.ser2_title] = np.log(df[self.series2.name]/df[self.series2.name].shift(1))
        df["retYoY_"+self.ser1_title] = np.log(df[self.series1.name]/df[self.series1.name].shift(self.per_in_year))
        df["retYoY_"+self.ser2_title] = np.log(df[self.series2.name]/df[self.series2.name].shift(self.per_in_year))
        df["retPct_"+self.ser1_title] = df[self.series1.name].pct_change(fill_method=None)
        df["retPct_"+self.ser2_title] = df[self.series2.name].pct_change(fill_method=None)
        df.dropna(inplace=True)
        return df

    def rolling_stats(self, corr_method: str = 'pearson'):
        """ Calculate the rolling correlation between the two series for different window lengths.

        **Parameters:**

        - yoy (bool): Flag indicating whether to calculate the rolling correlation on a year-over-year basis using YoY log returns.
        - corr_method (str): The correlation method to use (e.g., 'pearson', 'spearman', 'kendall').

        **Returns:**

        - The results are stored in the self.data DataFrame. 
        - The full correlation is stored in the self.full_corr attribute.
        """

        ## Now for correlations...
        self.full_corr = self.data[self.series1.name].corr(self.data[self.series2.name], method = corr_method)
        print("Whole time correlation, "+self.ser1_title+" vs "+self.ser2_title, ":", self.full_corr)
        self.full_RetCorr = self.data["ret_"+self.ser1_title].corr(self.data["ret_"+self.ser2_title], method = corr_method)
        print("Whole time correlation between log returns, "+self.ser1_title+" vs "+self.ser2_title+":", self.full_RetCorr)
        self.full_YoYRetCorr = self.data["retYoY_"+self.ser1_title].corr(self.data["retYoY_"+self.ser2_title], method = corr_method)
        print("Whole time correlation between log YoY returns, "+self.ser1_title+" vs "+self.ser2_title+":", self.full_YoYRetCorr)
        self.full_PctRetCorr = self.data["retPct_"+self.ser1_title].corr(self.data["retPct_"+self.ser2_title], method = corr_method)
        print("Whole time correlation between percentage returns,"+self.ser1_title+" vs "+self.ser2_title+":", self.full_PctRetCorr)
        self.full_qdCorr = qd_corr(self.data["ret_"+self.ser1_title], self.data["ret_"+self.ser2_title])
        print("Whole time qd correlation between log returns,"+self.ser1_title+" vs "+self.ser2_title+":", self.full_qdCorr)
        print("Rolling stats Windows: ", self.windows)
        names = self.ser1_title+"_"+self.ser2_title
        for window in self.windows:
            # For price series
            self.data[names + "_Corr_" + str(window)] = rolling_corr(self.data[self.series1.name], self.data[self.series2.name], 
                window, method=corr_method)
            
            # For log returns
            self.data[names + "_RetCorr_" + str(window)] = rolling_corr(self.data["ret_" + self.ser1_title], self.data["ret_" + self.ser2_title], 
                window, method=corr_method)
            
            # For YoY returns
            self.data[names + "_retYoY_" + str(window)] = rolling_corr(self.data["retYoY_" + self.ser1_title], self.data["retYoY_" + self.ser2_title], 
                window, method=corr_method)
            
            # For percentage returns
            self.data[names + "_PctRetCorr_" + str(window)] = rolling_corr(
                self.data["retPct_" + self.ser1_title], self.data["retPct_" + self.ser2_title], window, 
                method=corr_method)
            try:
                self.data[names + "_qdCorr_" + str(window)] = rolling_qd(self.data["ret_" + self.ser1_title], self.data["ret_" + self.ser2_title], window)
            except Exception as ahshitfckdup:
                print("Could not calculate the corr using the quant dare formula, for this pair, ", self.ser1_title, "&", self.ser2_title, "\nError message: ", ahshitfckdup)
            self.data[names + "_beta_" + str(window)] = self.data[names + "_Corr_" + str(window)] * (self.data["ret_" + self.ser1_title].rolling(window=window).std() / self.data["ret_" + self.ser2_title].rolling(window=window).std())
            self.data[names + "_alpha_" + str(window)] = self.data[self.series1.name].rolling(window=window).mean() - self.data[names + "_beta_" + str(window)] * self.data[self.series2.name].rolling(window=window).mean()

    def plot_log_returns(self, downsample_to: str = ""):
        """ Plot the log returns of the two series on the same chart.
        Results may vary with this method, use plot_log_returns_alt for more reliable results."""
        # Extract the relevant data
        two_series_only = self.data[["ret_" + self.ser1_title, "ret_" + self.ser2_title]]
        freq_str = self.frequency
        if downsample_to:
            two_series_only = two_series_only.resample(downsample_to).last()
            freq_str = self.freq_rep_dict[downsample_to] if downsample_to in self.freq_rep_dict.keys() else downsample_to

        # Plot using matplotlib directly
        fig, ax = plt.subplots(figsize=(14, 6)) 
        
        # Create bar plots for each series
        #width = 0.4  # Width of the bars
        plot_width = ax.get_window_extent().width # Convert from pixels to inches
        width =  (plot_width/ len(two_series_only)) / 2 # Width of each bar
        print("Plot width: ", plot_width, "bar width: ", width) 

        # Calculate the time delta for offsetting the bars
        tDelta = (two_series_only.index[1] - two_series_only.index[0])
        print("Time delta: ", tDelta, tDelta /2)
        ax.bar(two_series_only.index - tDelta/4, two_series_only["ret_" + self.ser1_title], width = width, label=self.ser1_title)
        ax.bar(two_series_only.index + tDelta/4, two_series_only["ret_" + self.ser2_title], width = width, label=self.ser2_title)

        # Set the title and labels
        ax.set_title('Log Returns: ' + self.ser1_title + ' vs ' + self.ser2_title)
        #ax.set_xlabel('Date')
        ax.set_ylabel('Log Returns')
        ax.legend()
        ax.text(0.01, 1.02, "Data frequency: "+self.frequency, horizontalalignment='left', transform=ax.transAxes)
        ax.margins(0.01, 0.03)
        self.returns_plot = fig
        return fig, ax

    def plot_log_returns_alt(self, downsample_to: str = "", color1: str = "b", color2: str = "r", YoY : bool = False):
        """ Plot the log returns of the two series as subplots."""
        if YoY:
            two_series_only = self.data[["retYoY_" + self.ser1_title, "retYoY_" + self.ser2_title]]
            plot_title = 'YoY Log Returns: ' + self.ser1_title + ' vs ' + self.ser2_title
        else:
            two_series_only = self.data[["ret_" + self.ser1_title, "ret_" + self.ser2_title]]
            plot_title = 'Log Returns: ' + self.ser1_title + ' vs ' + self.ser2_title
        freq_str = self.frequency
        if downsample_to:
            two_series_only = two_series_only.resample(downsample_to).last()
            freq_str = self.freq_rep_dict[downsample_to] if downsample_to in self.freq_rep_dict.keys() else downsample_to

        fig, axes = plt.subplots(2, 1, figsize=(14, 6))
        plot_width = axes[0].get_window_extent().width # Convert from pixels to inches
        width =  (plot_width/ len(two_series_only)) # Width of each bar
        print("Plot width: ", plot_width, "bar width: ", width) 
        # Plot the log returns
        axes[0].bar(two_series_only.index, two_series_only[two_series_only.columns[0]], width = width*2, label=self.ser1_title, color = color1)
        axes[1].bar(two_series_only.index, two_series_only[two_series_only.columns[1]], width = width*2, label=self.ser2_title, color = color2)
        axes[1].legend()
        # Set the title and labels
        axes[0].set_title(plot_title)
        for ax in axes:
            ax.set_axisbelow(True)
            ax.legend(fontsize = 11, frameon = True)
            ax.set_ylabel('Log Returns')
            ax.margins(0.01, 0.03)

        axes[0].text(0.01, 1.06, 'Data frequency: '+freq_str, ha='left', va='center', transform=axes[0].transAxes)
        self.returns_plot = fig
        return fig, axes

    def plot_series(self, color1: str = "black", color2: str = "blue"):
    
        leftTraces = {self.ser1_title: (self.series1, color1, 2.25)}
        rightTraces = {self.ser2_title: (self.series2, color2, 2.25)}
        
        try:
            lylabel = self.watchlist_meta.loc["units", self.series1.name] if not pd.isna(self.watchlist_meta.loc["units", self.series1.name]) else "USD"
        except:
            lylabel = "USD"
        try:
            rylabel = self.watchlist_meta.loc["units", self.series2.name] if not pd.isna(self.watchlist_meta.loc["units", self.series2.name]) else "USD"
        except:
            rylabel = "USD"

        ytr = Utilities.EqualSpacedTicks(10, self.series1, "log"); print("Left ticks: ", ytr) 
        ytr2 = Utilities.EqualSpacedTicks(10, self.series2, "log")

        self.fig1 = Charting.TwoAxisFig(leftTraces, "log", lylabel, title=self.name,
            RightTraces=rightTraces, RightScale="log", RYLabel=rylabel, LeftTicks=ytr, RightTicks=ytr2)
        
        return self.fig1, self.fig1.axes[0]

    def plot_corrs(self, trim_windows: int = 0, plot_wrong_way: bool = True, percentage_ret_corr: bool = False, qd_corr: bool = False,
                   YoY_retCorr: bool = False):
        """
        Plot rolling Pearson correlations between your two series for the different window lengths.
        *** Parameters: ***
        - trim_windows: int = 0, (optional). The number of windows to trim from the beginning of the list.
        - plot_wrong_way: bool = True, (optional). Whether to plot the rolling correlation traces calculated using the actual series
        values instead of the log or percentage returns. This is not recommended for financial data yet is often done by Rookies and 
        it can be useful to also plot this to show the contrast between the two methods.
        - percentage_ret_corr: Whether to plot the percentage returns correlation.
        - qd_corr: Whether to plot the QuantDare returns correlation. This is an alternative formula to Pearson correlation where the means
        are removed from the formula.
        """
        # Determine the number of plots
        plot_types = [
            ('RetCorr', True),  # Always plot RetCorr
            ('Corr', plot_wrong_way),
            ('PctRetCorr', percentage_ret_corr),
            ('qdCorr', qd_corr),
            ('retYoY',YoY_retCorr)
        ]
        num_plots = sum([pt[1] for pt in plot_types])

        # Step 1: Create subplots
        if num_plots == 1:
            fig, ax = plt.subplots(num_plots, 1, figsize=(12, 2.5 + (1.75 * num_plots)), sharex=True)  # Adjust figsize as needed
            axes = [ax]
        else:
            fig, axes = plt.subplots(num_plots, 1, figsize=(12, 2.5 + (1.75 * num_plots)), sharex=True)  # Adjust figsize as needed

        # Step 2: Plot data
        # Assuming self.data is a DataFrame with the necessary columns
        current_ax = 0
        for plot_type, should_plot in plot_types:
            if should_plot:
                for i in range(trim_windows, len(self.windows), 1):
                    col_name = f"{self.ser1_title}_{self.ser2_title}_{plot_type}_{self.windows[i]}"
                    if col_name in self.data.columns:
                        axes[current_ax].plot(self.data.index, self.data[col_name], label=f"{self.windows[i]} periods")
                current_ax += 1

        fig.subplots_adjust(left=0.08, bottom=0.06, right=0.97, top=0.95, hspace=0.11)  # Adjust the right margin to fit the legend

        # Step 3: Style (mimicking pandas.plot)
        for ax in axes:
            ax.set_ylabel('Correlation', fontweight='bold', fontsize=10)

        plotTypeinfo = {
                    'RetCorr': {"title": f"Correlation: {self.ser1_title} vs {self.ser2_title}: Log returns correlation.", "full_corr": self.full_RetCorr},
                    'retYoY': {"title": f"Correlation: {self.ser1_title} vs {self.ser2_title}: YoY returns correlation.", "full_corr": self.full_YoYRetCorr},
                    'Corr': {"title": f"Correlation: {self.ser1_title} vs {self.ser2_title} (wrong way)", "full_corr": self.full_corr},
                    'PctRetCorr': {"title": "Percentage returns correlation.", "full_corr": self.full_PctRetCorr},
                    'qdCorr': {"title": "QuantDare returns correlation.", "full_corr": self.full_qdCorr}
                }
        
        current_ax = 0
        for plot_type, should_plot in plot_types:
            if should_plot:
                ax = axes[current_ax]
                ax.axhline(plotTypeinfo[plot_type]["full_corr"], color="r", linestyle="--", lw=1)
                ax.tick_params(axis='x', labelsize=0, length=0, width=0)
                if current_ax == len(axes) - 1:
                    ax.tick_params(axis='x', labelsize=11, length=3)
                current_ax += 1

        print("Frequency of the pair: ", self.frequency)
        # Optional: Titles, labels, etc.
        current_ax = 0
        for plot_type, should_plot in plot_types:
            if should_plot:
                title = plotTypeinfo[plot_type]["title"]
                axes[current_ax].set_title(title, fontsize=11, pad=3.5)
                current_ax += 1
 
        line_handle = Utilities.Line2D([0], [0], color="r", linestyle="--", lw=1, label="Correlation\nfull length")
        handles, labels = axes[0].get_legend_handles_labels()
        handles_combined = handles + [line_handle]
        labels_combined = labels + ["Correlation\nfull length"]
        axes[num_plots - 1].legend(handles=handles_combined, labels=labels_combined, fontsize=10, bbox_to_anchor=(0.75, -0.1), ncol=6)
        fig.text(0.865, 0.97, 'Data frequency: ' + self.frequency, ha='center', va='center')
        fig.text(0.1, 0.97, 'Correlation method: ' + self.corr_method, ha='center', va='center')

        self.corr_plot = fig
        
    def plot_lin_reg(self, yoy: bool = False, y_lim: tuple = None, x_lim: tuple = None):
        """ Plot a scatter plot of the returns of the two series, along with a linear regression line.
        The plot will also display the R² value.
        """

        if yoy:
            print("Plotting linear regression using YoY returns rather than single period returns...")
            rets = self.data[["retYoY_"+self.ser1_title, "retYoY_"+self.ser2_title]]
        else:
            rets = self.data[["ret_"+self.ser1_title, "ret_"+self.ser2_title]]

        reg = np.polyfit(rets[rets.columns[1]], rets[rets.columns[0]], deg = 1, full = False)
   
        vals = np.polyval(reg, rets[rets.columns[1]])
        # Calculate the R² value
        residuals = rets[rets.columns[0]] - vals
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((rets[rets.columns[0]] - np.mean(rets[rets.columns[0]]))**2)
        r_squared = 1 - (ss_res / ss_tot)
        ax = rets.plot(kind="scatter", x = rets.columns[1], y = rets.columns[0], alpha = 0.6, figsize = (13, 5), edgecolor='none')
        ax.plot(rets[rets.columns[1]], vals , 'r', lw = 1.5)

        # Add a text box with the R² value
        textstr = f'$R^2 = {r_squared:.2f}$'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=12,
                verticalalignment='top', bbox=props)
        
        if y_lim:
            ax.set_ylim(y_lim)
        if x_lim:
            ax.set_xlim(x_lim)
        self.lineRegPlot = ax.get_figure()

    def find_optimal_lag(self, n):
        """ Find the optimal lag-time that yields the highest correlation between the two series.
        Note that this does not use log returns of series1 and series2 and is therefore not recommended for financial data
        or any other series that deviate significantly from stationarity and normality."""

        correlations = []; backcorrs = []
        for i in range(n+1):
            shifted_series2 = self.series2.shift(i)
            correlation = self.series1.corr(shifted_series2, method=self.corr_method)
            correlations.append(correlation)
        for i in range(n+1):
            shifted_series1 = self.series1.shift(i)
            backcorr = self.series2.corr(shifted_series1, method=self.corr_method)
            backcorrs.append(backcorr)

        print("Correlations for shifted series2: ", correlations)
        optimal_lag = correlations.index(max(correlations))
        highest_correlation = max(correlations)
        backcorr_ser = pd.Series(backcorrs[::-1], index=range(-(n+1), 0))
        self.lag_test = pd.concat([backcorr_ser, pd.Series(correlations, index=range(n+1))], axis=0)
        
        return optimal_lag, highest_correlation
    
    def find_optimal_ret_lag(self, n, yoy: bool = False, increment: int = 1):
        """ Find the optimal lag-time that yields the highest correlation between the returns of the two series. 
        parameter n: int, the maximum number of lags to test. The function will test lags from 0 to n and -n to 0.
        concatenating the results into a series. The lags are periods of the datetime index of the series."""

        if yoy:
            print("Using YoY log returns for the cross-correlation analysis, periods in a year, ", self.per_in_year)
            ser1 = self.data["retYoY_"+self.ser1_title]
        else:
            ser1 = self.data["ret_"+self.ser1_title]
        ser2 = self.data[self.ser2_title]

        ## Shift series and calculate correlations
        shifted = {}; correlations = {}
        output_data = pd.DataFrame([ser1])
        # Shift series 1 forward, corresponding to series 2 being shifted back...
        for i in range(-n, n+1, increment): 
            shifted_series2 = ser2.shift(i)
            if yoy:
                shifted_series2_rets = np.log(shifted_series2/shifted_series2.shift(self.per_in_year))
            else:
                shifted_series2_rets = np.log(shifted_series2/shifted_series2.shift(1))
            shifted[i] = shifted_series2_rets
            correlation = ser1.corr(shifted_series2_rets, method=self.corr_method)
            correlations[i] = correlation
            output_data = pd.concat([output_data, shifted_series2_rets], axis=1)
    
        ### Plot the shifted series for inspection, normalize plotted series to between 0 & 1 and offset in Y for easy viewing.
        fig1, ax1 = plt.subplots(1, 1, figsize=(12, 5))
        ax1.set_title("Full period correlation for "+self.ser1_title+" (static) and "+self.ser2_title+" (shifted over range: -"+str(n)+" to "+str(n)+")")
        for i in range(-n, n+1, increment*5):
            norm_series = (shifted[i]-shifted[i].min())/shifted[i].max()
            ax1.plot(norm_series+(0.05*i), label=f"Shifted series {i}",lw=0.5)
        norm_ser1 = (ser1-ser1.min())/ser1.max()
        ax1.plot(norm_ser1, label=self.ser1_title, lw=1.5, color = 'black', alpha = 0.7)
    
        self.ret_lag_test = pd.Series(correlations, name = "Corr_shift_"+self.ser1_title+"_"+self.ser2_title)

       # Find the key with the maximum value
        optimal_lag = max(correlations, key=correlations.get)
        highest_correlation = correlations[optimal_lag]  # Find the maximum value

        print(f"Optimal lag: {optimal_lag}", f"Highest correlation: {highest_correlation}")
        
        ###### Plot de cunt....
        fig2, ax2 = plt.subplots(figsize=(12, 5))
        ax2.set_title("Lag-test for "+self.ser1_title+" and "+self.ser2_title+". Correlation as function of series time-shift.")
        ax2.plot(self.ret_lag_test, label = "", color = 'green')
        ax2.text(0, -0.1, "Data frequency: "+self.frequency, horizontalalignment='left', transform=ax2.transAxes)
        ax2.set_xlabel("Time shift of "+self.ser2_title+" (number of periods)")
        ax2.set_ylabel("Correlation (Pearson)")
        
        self.shiftmatrix = output_data
        self.lag_plot = fig1
        self.lag_plot2 = fig2
        return optimal_lag, highest_correlation

    def bm_scatterMatrix(self, yoy: bool = False):
        """ Custom scatter matrix plot. Incudes kernel density approximations and line for the max of each kde.
        """
        if yoy:
            print("Plotting scatter matrix using YoY returns rather than one period returns...")
            rets = self.data[["retYoY_"+self.ser1_title, "retYoY_"+self.ser2_title]]
        else:
            rets = self.data[["ret_"+self.ser1_title, "ret_"+self.ser2_title]]

        # Create a scatter matrix
        scatter_matrix = pd.plotting.scatter_matrix(rets, diagonal="kde", figsize=(13, 7))

        # Add red dotted lines at the peak points of the KDE plots
        for i, ax in enumerate(scatter_matrix.diagonal()):
            # Extract the data for the current diagonal plot
            data = rets.iloc[:, i]
            
            # Calculate the KDE
            kde = sns.kdeplot(data, ax=ax, color='blue')
            
            # Find the peak of the KDE
            kde_lines = kde.get_lines()[0]
            x_data = kde_lines.get_xdata()
            y_data = kde_lines.get_ydata()
            peak_x = x_data[np.argmax(y_data)]
            
            # Add a red dotted line at the peak point
            ax.axvline(peak_x, color='red', linestyle='--', lw = 1)
            
            # Set the y-axis formatter
            ax.yaxis.set_major_formatter(FuncFormatter(Utilities.format_func))
            # Add a text box with the x value of the peak
            textstr = f'Peak x = {peak_x:.2f}'
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=12,
                    verticalalignment='top', bbox=props)
        
        # Extract the figure from the scatter matrix
        fig = scatter_matrix[0][0].get_figure()
        self.scatMatPlot = fig
        return scatter_matrix

    def export_plots(self, savePath: str = "", dialog: str = "Tk", format: str = "png"):
        """ 
        Save the plot figures created by the other methods here to disk.

        **Parameters:**
        - savePath (str): The path to save the figures to. If not provided, a dialog will be shown.
        - dialog (str): The dialog to use for saving the files. Options are 'Tk' (default) or 'Qt'.
        - format (str): The format to save the figures in. Default is 'png'.
        """

        savename = self.ser1_title + "-" + self.ser2_title; savename = savename.replace(" ", "_")
        if not savePath:
            if dialog == "Qt":
                savePath = Utilities.save_path_dialog()
            else:
                savePath = Utilities.save_path_dialog(qt=False)

        save_options = {
            'format': format,
            'bbox_inches': 'tight',
            'pad_inches': 0.1  # Adjust padding as needed
        }

        if hasattr(self, "fig1"):
            self.fig1.savefig(savePath + fdel + savename + '_series.' + format, **save_options)
            print("Saved figure 1 to: ", savePath + fdel + savename + '_series.' + format)
        if hasattr(self, "returns_plot"):
            self.returns_plot.savefig(savePath + fdel + savename + '_ret.' + format, **save_options)
            print("Saved returns_plot to: ", savePath + fdel + savename + '_ret.' + format)
        if hasattr(self, "lineRegPlot"):
            self.lineRegPlot.savefig(savePath + fdel + savename + '_reg.' + format, **save_options)
            print("Saved linear regression scatter plot to: ", savePath + fdel + savename + '_reg.' + format)
        if hasattr(self, "corr_plot"):
            self.corr_plot.savefig(savePath + fdel + savename + '_corr.' + format, **save_options)
            print("Saved correlation plot figure to: ", savePath + fdel + savename + '_corr.' + format)
        if hasattr(self, "scatMatPlot"):
            self.scatMatPlot.savefig(savePath + fdel + savename + '_scatMat.' + format, **save_options)
            print("Saved scatter matrix plot figure to: ", savePath + fdel + savename + '_scatMat.' + format)
        if hasattr(self, "lag_plot"):
            self.lag_plot.savefig(savePath + fdel + savename + '_lag.' + format, **save_options)
            print("Saved lag plot figure to: ", savePath + fdel + savename + '_lag.' + format)
        if hasattr(self, "lag_plot2"):
            self.lag_plot2.savefig(savePath + fdel + savename + '_lagRes.' + format, **save_options)
            print("Saved lag plot figure to: ", savePath + fdel + savename + '_lagRes.' + format)

    def assess_correlation_error(self, which_series: Literal["returns", "price", "yoy_returns", "pct_returns"] = "returns"):
        """ Assess the correlation between the two series and the error involved,
        including normality and stationarity tests.

        **Parameters:**
        which_series: One of:

            - "returns": Use log returns
            - "price": Use raw price series
            - "yoy_returns": Use year-over-year returns
            - "pct_returns": Use percentage returns
        """
        
         # Map literal values to data columns
        series_map = {
            "returns": (f"ret_{self.ser1_title}", f"ret_{self.ser2_title}"),
            "price": (self.ser1_title, self.ser2_title),
            "yoy_returns": (f"retYoY_{self.ser1_title}", f"retYoY_{self.ser2_title}"),
            "pct_returns": (f"retPct_{self.ser1_title}", f"retPct_{self.ser2_title}")
        }
        
        if which_series not in series_map:
            raise ValueError(f"which_series must be one of {list(series_map.keys())}")
        
        s1_col, s2_col = series_map[which_series]
        ds1 = self.data[s1_col]
        ds2 = self.data[s2_col]

        n = len(ds1)
        if n < 3:
            raise ValueError("Not enough data points to calculate correlation.")
        # Compute Pearson correlation
        r, pval = stats.pearsonr(ds1, ds2)
        # Standard error
        se_r = np.sqrt((1 - r**2) / (n - 2))
        # Normality tests
        shapiro_p1 = stats.shapiro(ds1)
        shapiro_p2 = stats.shapiro(ds2)
        # Stationarity tests
        adf_p1 = check_stationarity(ds1)
        adf_p2 = check_stationarity(ds2)

        # Results
        ser1res = self.ser1_title + "_"+ which_series
        ser2res = self.ser2_title + "_"+ which_series

        results = {
            'correlation_coefficient': r,
            'p_value_non_corr': pval,
            'standard_error': se_r,
            'normality_tests': {
                ser1res: shapiro_p1,
                ser2res: shapiro_p2
            },
            'stationarity_tests': {
                ser1res: adf_p1,
                ser2res: adf_p2
            }
        }
        self.error_assessment_results = results
        return results
    
# def results_to_markdown(results: dict) -> str:
#     """Convert statistical results to markdown via DataFrame"""
#     import pandas as pd
    
#     def build_data(results):
#         # Build multi-level data structure
#         data = {
#             ('Correlation', 'Value'): [
#                 results['correlation_coefficient'],
#                 results['p_value_non_corr'],
#                 results['standard_error']
#             ],
#             ('Correlation', 'Conclusion'): [
#                 f"{'Strong' if abs(results['correlation_coefficient']) > 0.7 else 'Moderate' if abs(results['correlation_coefficient']) > 0.3 else 'Weak'} correlation",
#                 f"{'Reject' if results['p_value_non_corr'] < 0.05 else 'Fail to reject'} H₀: no correlation",
#                 "Precision measure"
#             ]
#         }
        
#         # Add normality test results
#         for series, result in results['normality_tests'].items():
#             data[(f'Normality ({series})', 'Value')] = [
#                 result.statistic,
#                 result.pvalue,
#                 None
#             ]
#             data[(f'Normality ({series})', 'Conclusion')] = [
#                 'Shapiro-Wilk statistic',
#                 f"{'Reject' if result.pvalue < 0.05 else 'Fail to reject'} H₀: normal",
#                 None
#             ]
        
#         # Add stationarity test results
#         for series, tests in results['stationarity_tests'].items():
#             for test in ['ADF', 'KPSS']:
#                 test_results = tests[test]
#                 data[(f'Stationarity-{test} ({series})', 'Value')] = [
#                     test_results['statistic'],
#                     test_results['p-value'],
#                     None
#                 ]
#                 h0 = "non-stationary" if test == 'ADF' else "stationary"
#                 data[(f'Stationarity-{test} ({series})', 'Conclusion')] = [
#                     f"{test} statistic",
#                     f"{'Reject' if test_results['p-value'] < 0.05 else 'Fail to reject'} H₀: {h0}",
#                     None
#                 ]
        
#         return data
    
#     # Create DataFrame with MultiIndex for results
#     data = build_data(results)
#     index = ['Statistic', 'P-value', 'Std Error']
#     df = pd.DataFrame(data, index=index).T
    
#     return df.to_markdown(floatfmt=".4g")

def results_to_markdown(results: dict) -> str:
    """Convert statistical results to markdown via DataFrame"""
    import pandas as pd
    
    def build_data(results):
        # Build multi-level data structure
        data = {
            ('Correlation', 'Value'): [
                results['correlation_coefficient'],
                results['p_value_non_corr'],
                None
            ],
            ('Correlation', 'Conclusion'): [
                f"{'Strong' if abs(results['correlation_coefficient']) > 0.7 else 'Moderate' if abs(results['correlation_coefficient']) > 0.3 else 'Weak'} correlation",
                f"{'Reject' if results['p_value_non_corr'] < 0.05 else 'Fail to reject'} H₀: no correlation",
                f"Std Error: {results['standard_error']:.4g}"
            ]
        }
        
        # Add normality test results
        for series, result in results['normality_tests'].items():
            data[(f'Normality ({series})', 'Value')] = [
                result.statistic,
                result.pvalue,
                None
            ]
            data[(f'Normality ({series})', 'Conclusion')] = [
                'Shapiro-Wilk statistic',
                f"{'Reject' if result.pvalue < 0.05 else 'Fail to reject'} H₀: normal",
                None
            ]
        
        # Add stationarity test results
        for series, tests in results['stationarity_tests'].items():
            for test in ['ADF', 'KPSS']:
                test_results = tests[test]
                data[(f'Stationarity-{test} ({series})', 'Value')] = [
                    test_results['statistic'],
                    test_results['p-value'],
                    None
                ]
                h0 = "non-stationary" if test == 'ADF' else "stationary"
                data[(f'Stationarity-{test} ({series})', 'Conclusion')] = [
                    f"{test} statistic",
                    f"{'Reject' if test_results['p-value'] < 0.05 else 'Fail to reject'} H₀: {h0}",
                    None
                ]
        
        return data
    
    # Create DataFrame with MultiIndex for results
    data = build_data(results)
    index = ['Statistic', 'P-value', 'Conclusion']
    df = pd.DataFrame(data, index=index).T
    
    # Flatten the MultiIndex
    flattened_data = {}
    for (test, subindex), values in df.iterrows():
        if subindex == 'Value':
            flattened_data[test] = values
        elif subindex == 'Conclusion':
            if test in flattened_data:
                flattened_data[test]['Conclusion'] = ' '.join(values.dropna().astype(str))
            else:
                flattened_data[test] = pd.Series([None, None, ' '.join(values.dropna().astype(str))], index=['Statistic', 'P-value', 'Conclusion'])
    
    # Create new DataFrame with flattened structure
    flattened_df = pd.DataFrame(flattened_data).T
    flattened_df.index.name = 'Test'
    
    return flattened_df.to_markdown(floatfmt=".4g")