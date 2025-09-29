import sys
import os
wd = os.path.dirname(__file__); parent = os.path.dirname(wd)
sys.path.append(parent)
fdel = os.path.sep

import numpy as np
from scipy.signal import argrelextrema
from scipy.optimize import curve_fit
import scipy.stats as stats
from statsmodels.tsa.seasonal import STL

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates
from MacroBackend import Utilities
import datetime 

def calc_chart_xlims(index: pd.DatetimeIndex, xmin: str = None, xmax: str = None, 
                     margin_left: float = 0.05, margin_right: float = 0.05) -> tuple:
    """
    Sets the x-axis limits with a buffer on a matplotlib chart.

    Parameters:
    ax (matplotlib.axes.Axes): The axes object of the plot.
    index (pd.DatetimeIndex,): The datetime index of a pd.Series of the main trace on a given chart
    margin_left (float), margin_right (float): The left margin, right margin.
    xmin, xmax: can specify dates to restrict your axis range. 
    """
    if not isinstance(index, pd.DatetimeIndex):
        raise TypeError("Input index must be of type pd.DatetimeIndex")

    if xmin is not None and xmax is not None:
        min_date = Utilities.GetClosestDateInIndex(index, xmin)[0]
        max_date = Utilities.GetClosestDateInIndex(index, xmax)[0]
        print(xmin, xmax, min_date, max_date)
    else:
        min_date, max_date = index.min(), index.max() 
    # Extract min and max dates from the series index

    # Calculate the buffer in terms of days
    date_range = max_date - min_date
    left_buffer = datetime.timedelta(days=date_range.days * margin_left)
    right_buffer = datetime.timedelta(days=date_range.days * margin_right)

    # Apply the buffer
    xlim_lower = min_date - left_buffer
    xlim_upper = max_date + right_buffer

    return (xlim_lower, xlim_upper)

def identify_peaks_and_troughs(data: pd.Series, x_range: datetime.timedelta):
    # Convert x_range to number of points
    x_range_points = round(x_range.total_seconds() / (data.index[1] - data.index[0]).total_seconds())
    print("X-range points: ", x_range_points)

    # Find all peaks and troughs
    peaks = argrelextrema(data.values, np.greater_equal, order=x_range_points)[0]
    troughs = argrelextrema(-data.values, np.less_equal, order=x_range_points)[0]
    print(peaks)

    def filter_peaks(peak_indices, x_range):
        peak_indices.sort()
        final_peak_indices = []
        for peak_index in peak_indices:
            if not final_peak_indices or peak_index - final_peak_indices[-1] > x_range:
                final_peak_indices.append(peak_index)
            elif data[peak_index] > data[final_peak_indices[-1]]:
                final_peak_indices[-1] = peak_index
        return final_peak_indices
   
    # Find the most significant peaks and troughs
    significant_peaks = filter_peaks(peaks, x_range_points)
    significant_troughs = filter_peaks(troughs, x_range_points)

    # Combine and sort

    ThePeaksRaw = pd.Series(data.index[peaks], index = peaks, name = "Peaks_in_data")
    TroffzRaw = pd.Series(data.index[troughs], index = troughs, name = "Troughs_in_data")
    ThePeaks = pd.Series(data.index[significant_peaks], index = significant_peaks, name = "Peaks_in_data_filtered")
    Troffz = pd.Series(data.index[significant_troughs], index = significant_troughs, name = "Troughs_in_data_filtered")

    return ThePeaks, Troffz, ThePeaksRaw, TroffzRaw

def normality_tests(data: pd.Series):
    """
    Perform normality tests on the dataset. These tests include the Shapiro-Wilk test, the Anderson-Darling test, and the Kolmogorov-Smirnov test.
    These tests quantify how well the data fits a normal distribution.

    *Parameters:*
    - data (pd.Series): The dataset to be tested. Must be a pandas Series.

    *Returns:*
    - results (pd.DataFrame): A DataFrame containing the results of the normality tests.
    """

    # Ensure the data is a numpy array
    data = data.dropna().values

    # Shapiro-Wilk test
    shapiro_stat, shapiro_p = stats.shapiro(data)

    # Anderson-Darling test
    anderson_result = stats.anderson(data, dist='norm')
    anderson_stat = anderson_result.statistic
    anderson_critical_values = anderson_result.critical_values
    anderson_significance_levels = anderson_result.significance_level

    # Kolmogorov-Smirnov test
    ks_stat, ks_p = stats.kstest(data, 'norm', args=(np.mean(data), np.std(data)))

    # Create a DataFrame to store the results
    results = pd.DataFrame({
        'Test': ['Shapiro-Wilk', 'Anderson-Darling', 'Kolmogorov-Smirnov'],
        'Statistic': [shapiro_stat, anderson_stat, ks_stat],
        'p-value': [shapiro_p, np.nan, ks_p],
        'Critical Values': [np.nan, anderson_critical_values, np.nan],
        'Significance Levels': [np.nan, anderson_significance_levels, np.nan]
    })

    # Q-Q plot and R² calculation
    fig, ax = plt.subplots(figsize=(6, 6))
    (osm, osr), (slope, intercept, r) = stats.probplot(data, dist="norm", fit=True, plot=ax)
    
    # Calculate R² manually
    y_pred = slope * osm + intercept
    ss_res = np.sum((osr - y_pred) ** 2)
    ss_tot = np.sum((osr - np.mean(osr)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    
    ax.text(0.05, 0.95, f'R² = {r2:.4f}', fontsize=10, transform=ax.transAxes, 
            bbox=dict(facecolor='beige', edgecolor='black', boxstyle='round,pad=0.5'))
    plt.show()

    return results, fig

def ks_test_distribution(data: pd.Series, distribution: str):
    """
    Perform the Kolmogorov-Smirnov test on the dataset to check how well it fits a specified distribution.
    Generate a Q-Q plot for visual inspection.

    *Parameters:*
    - data (pd.Series): The dataset to be tested. Must be a pandas Series.
    - distribution (str): The distribution type to test against (e.g., 'norm' for normal, 'cauchy' for Lorentzian).

    *Returns:*
    - results (pd.DataFrame): A DataFrame containing the results of the Kolmogorov-Smirnov test.
    """

    # Ensure the data is a numpy array
    data = data.dropna().values
    stats.norm
    # Kolmogorov-Smirnov test
    if distribution == 'norm':
        ks_stat, ks_p = stats.kstest(data, stats.norm.cdf, args=(np.mean(data), np.std(data)))
    elif distribution == 'cauchy':
        ks_stat, ks_p = stats.kstest(data, stats.cauchy.cdf, args=(np.median(data), stats.iqr(data)))
    else:
        ks_stat, ks_p = stats.kstest(data, distribution)

    # Create a DataFrame to store the results
    results_dict = {
        'Test': ['Kolmogorov-Smirnov'],
        'Statistic': [ks_stat],
        'p-value': [ks_p]
    }
    results = pd.DataFrame(results_dict)

    # Q-Q plot
    fig, ax = plt.subplots(figsize=(6, 6))
    stats.probplot(data, dist=distribution, plot=ax)
    ax.set_title(f'Q-Q Plot for {distribution} Distribution')
    plt.show()

    return results   

# Define Gaussian function
def gaussian(x, amp, cen, wid):
    return amp * np.exp(-(x-cen)**2 / (2*wid**2))

# Define Lorentzian function
def lorentzian(x, amp, cen, wid):
    return amp * wid**2 / ((x-cen)**2 + wid**2)

# Define Student's t-distribution function
def student_t(x, amp, cen, df, scale):
    return amp * stats.t.pdf(x, df, loc=cen, scale=scale)

class stat_models_fit(object):
    def __init__(self, data: pd.Series):
        self.data = data.copy()
        self.name = data.name

         # Create histogram data
        self.hist, self.bin_edges = np.histogram(self.data, bins=len(self.data), density=True)
        self.bin_centers = (self.bin_edges[:-1] + self.bin_edges[1:]) / 2
        # Plot Gaussian fit
        self.x_fit = np.linspace(self.bin_edges[0], self.bin_edges[-1], len(self.data))

    def fit_gaussian(self, method: str = 'MLE'):
        """Fit method optons are 'MLE' for maximum likelihood estimation and 'MM' for moment matching."""
        try:
            gauss_fit = stats.norm.fit(self.data, method=method)
            self.norm = stats.norm(*gauss_fit)
            fit_series = self.norm.pdf(self.x_fit)
            self.gaussian = pd.Series(fit_series, index = self.x_fit, name = self.name + " Gauss fit")
            self.gaussian_params = gauss_fit
            return gauss_fit
        except Exception as e:
            print(f"Gaussian fit failed: {e}")
            return None

    def fit_lorentzian(self, method: str = 'MLE'):
        """Fit method optons are 'MLE' for maximum likelihood estimation and 'MM' for moment matching."""
        try:
            cauchy_fit = stats.cauchy.fit(self.data, method=method)
            self.cauchy = stats.cauchy(*cauchy_fit)
            fit_series = self.cauchy.pdf(self.x_fit)
            self.lorentzian = pd.Series(fit_series, index = self.x_fit, name = self.name + " Lorentzian fit")
            self.lorentzian_params = cauchy_fit
            return cauchy_fit
        except Exception as e:
            print(f"Lorentzian fit failed: {e}")
            return None

    def fit_student_t(self, method: str = 'MLE'):
        """Fit method optons are 'MLE' for maximum likelihood estimation and 'MM' for moment matching."""
        try:
            t_fit = stats.t.fit(self.data, method=method)
            self.t_dist = stats.t(*t_fit)
            fit_series = self.t_dist.pdf(self.x_fit)
            self.t = pd.Series(fit_series, index = self.x_fit, name = self.name + " Student T fit")
            self.t_params = t_fit
            return t_fit
        except Exception as e:
            print(f"Student T fit failed: {e}")
            return None
    
    def fit_gamma(self, method: str = 'MLE'):
        """Fit method optons are 'MLE' for maximum likelihood estimation and 'MM' for moment matching."""
        try:
            gamma_fit = stats.gamma.fit(self.data, method=method)
            self.gam_dist = stats.t(*gamma_fit)
            fit_series = self.gam_dist.pdf(self.x_fit)
            self.gamma = pd.Series(fit_series, index = self.x_fit, name = self.name + " Gamma dist. fit")
            self.gamma_params = gamma_fit
            return gamma_fit
        except Exception as e:
            print(f"Gamma fit failed bruh: {e}")
            return None

    def plot_histogram_with_fits(self, log: bool = False, title: str = 'Histogram with Gaussian, Lorentzian, Student\'s t and Gamma dist. fits'):
        """
        Plot a histogram of your data and show how it compares to fitted distributions...
        """
        # Plot histogram
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.hist(self.data, bins=1000, color='blue', alpha=0.85, label=self.name + " hist", density=True)

        if hasattr(self, 'gaussian'):
            ax.plot(self.gaussian, color='red', label='Gaussian Fit')
        if hasattr(self, 'lorentzian'):
            ax.plot(self.lorentzian, color='green', label='Lorentzian Fit')
        if hasattr(self, 't'):
            ax.plot(self.t, color='purple', label=f'T-Dist. Fit (df={self.t_params[0]:.2f})')
        if hasattr(self, 'gamma'):
            ax.plot(self.gamma, color='fuchsia', label='Gamma Fit')
        if hasattr(self, 'data_filtered'):
            ax.hist(self.data_filtered, bins=1000, color='red', alpha=0.6, label=self.name + " filtered", density=True)
        if hasattr(self, 'lower_threshold') and hasattr(self, 'upper_threshold'):
            ax.axvline(self.upper_threshold, color='blue', linestyle='--', lw = 1, label='Upper cut-off')
            ax.axvline(self.lower_threshold, color='black', linestyle='--', lw = 1, label='Lower cut-off')

        ax.legend(loc="upper left", fontsize=10)
        ax.set_xlabel('Value')
        ax.set_ylabel('Density')
        ax.set_title(title, fontsize = 11)
        if log:
            ax.set_yscale('log')
            ax.set_ylim(10**(-2), self.hist.max())

        self.hist_fig = fig

    def qq_plots(self, data: pd.Series = None):
        """
        Generate Q-Q plots for four distributions, the Cauchy (Lorentzian) distribution, Normal (Gaussian) distribution,
        Student's T distribution, and the Gamma distribution against the input series data.

        *Parameters:*
        - data (pd.Series): The dataset to be tested. Must be a pandas Series.

        """
        if data is not None:
            data = data.copy().dropna().values
        else:
            # Ensure the data is a numpy array
            data = self.data.copy().dropna().values

        # Q-Q plot for Normal distribution
        fig, ax = plt.subplots(2, 2, figsize=(12, 12))

        # Function to calculate R² and set transparency
        def plot_with_r2(ax, data, dist, sparams, title):
            (osm, osr), (slope, intercept, r) = stats.probplot(data, dist=dist, sparams=sparams, fit=True, plot=ax)
            y_pred = slope * osm + intercept
            ss_res = np.sum((osr - y_pred) ** 2)
            ss_tot = np.sum((osr - np.mean(osr)) ** 2)
            r2 = 1 - (ss_res / ss_tot)
            ax.set_title(f'{title} (R² = {r2:.4f})', fontsize=11)
            for line in ax.get_lines():
                if line.get_linestyle() == 'None':  # This identifies the markers
                    line.set_alpha(0.5)
                    line.set_markeredgewidth(0)  # Remove the line around the marker perimeter

        # Q-Q plot for Normal distribution using fitted parameters
        if hasattr(self, 'gaussian_params'):
            plot_with_r2(ax[0][0], data, "norm", self.gaussian_params, 'Q-Q Plot for Normal Distribution')

        # Q-Q plot for Cauchy distribution using fitted parameters
        if hasattr(self, 'lorentzian_params'):
            plot_with_r2(ax[0][1], data, "cauchy", self.lorentzian_params, 'Q-Q Plot for Cauchy Distribution')

        # Q-Q plot for Student's T distribution using fitted parameters
        if hasattr(self, 't_params'):
            plot_with_r2(ax[1][0], data, "t", self.t_params, "Q-Q Plot for Student's T Distribution")

        # Q-Q plot for Gamma distribution using fitted parameters
        if hasattr(self, 'gamma_params'):
            plot_with_r2(ax[1][1], data, "gamma", self.gamma_params, "Q-Q Plot for Gamma Distribution")

        plt.tight_layout()
        plt.show()
        self.qq_fig = fig

    def remove_outliers(self, distribution: str, cutoff_threshold: float = 5):
        """
        Remove outliers that fall outside of the given fitted distribution from the self.data time series.

        Parameters:
            distribution (str): The name of the distribution to use for filtering ('gaussian', 'lorentzian', 'student_t', 'gamma').
            cutoff_threshold (float): The percentile threshold for removing outliers. In percentage. 

        Returns:
            pandas.DataFrame: DataFrame containing original data, outlier mask, and filtered data
        """
        # Get the appropriate distribution object
        if distribution == 'gaussian' and hasattr(self, 'gaussian'):
            dist = self.norm
        elif distribution == 'lorentzian' and hasattr(self, 'lorentzian'):
            dist = self.cauchy
        elif distribution == 't' and hasattr(self, 't'):
            dist = self.t_dist
        elif distribution == 'gamma' and hasattr(self, 'gamma'):
            dist = self.gam_dist
        else:
            raise ValueError(f"Distribution '{distribution}' not fitted or not recognized.")

        # Convert percentiles to proportions (e.g., 5% -> 0.05)
        lower_prop = cutoff_threshold / 100
        upper_prop = 1 - lower_prop

        # Get the theoretical quantiles from the fitted distribution
        self.lower_threshold = dist.ppf(lower_prop)
        self.upper_threshold = dist.ppf(upper_prop)

        # Create a boolean mask for outliers using the theoretical thresholds
        outliers_mask = (self.data < self.lower_threshold) | (self.data > self.upper_threshold)
        # Ensure the mask has the same index as the original data
        outliers_mask = pd.Series(outliers_mask, index=self.data.index)
        
        # Create output DataFrame
        dataout = pd.DataFrame({
            "Data_at_start": self.data.copy(),
            "Is_outlier": outliers_mask
        })

        # Set points that fall outside of the distribution to NaN
        self.data_filtered = self.data.copy()
        self.data_filtered[outliers_mask] = np.nan
        
        print(f"Outliers removed using {distribution} distribution.")
        print(f"Theoretical thresholds: lower={self.lower_threshold:.3f}, upper={self.upper_threshold:.3f}")
        print(f"Number of outliers removed: {outliers_mask.sum()}")
        
        # Add filtered data to output DataFrame
        dataout["Data_filtered"] = self.data_filtered

        return dataout

#### Distibution fits and plot convenience function..........
def fit_dists_plot(series: pd.Series, log: bool = False, figsize: tuple = (6, 5)):
    """_summary_

    Args:
        series (pd.Series): Your data series to fit dists to and plot.
        log (bool, optional): Log axis on dists plot. Defaults to False.

    Returns:
        Fitting.stat_models_fit: Object defined above. 
    """
    fitobj = stat_models_fit(series)
    fitobj.fit_gaussian()
    fitobj.fit_gamma()
    fitobj.fit_lorentzian()
    fitobj.fit_student_t()
    fitobj.plot_histogram_with_fits(log=log, title = f"{series.name}: Histogram with fitted distributions")
    fitobj.hist_fig.set_size_inches(figsize[0], figsize[1])
    return fitobj
        
#### Traces are input as dict of tuples e.g {"TraceName": (data,color,linewidth)}
def TwoAxisFig(LeftTraces:dict,LeftScale:str,LYLabel:str,title:str,XTicks=None,RightTraces:dict=None,RightScale:str=None,RYLabel:str=None,\
            LeftTicks:tuple=None,RightTicks:tuple=None,RightMinTicks:tuple=None,text1:str=None):
    """
    Create a figure with two y-axes.

    Parameters:
    LeftTraces (dict): A dictionary containing the left y-axis traces. The keys are the trace names and the values are lists containing the trace data, color, and line width.
    LeftScale (str): The scale of the left y-axis. Can be 'linear' or 'log'.
    LYLabel (str): The label for the left y-axis.
    title (str): The title of the figure.
    XTicks (list or None): The tick positions for the x-axis. If None, the default ticks will be used.
    RightTraces (dict or None): A dictionary containing the right y-axis traces. The keys are the trace names and the values are lists containing the trace data, color, and line width. If None, only the left y-axis will be plotted.
    RightScale (str or None): The scale of the right y-axis. Can be 'linear' or 'log'. If None, the right y-axis will have the same scale as the left y-axis.
    RYLabel (str or None): The label for the right y-axis. If None, no label will be displayed.
    LeftTicks (tuple or None): The tick positions and labels for the left y-axis. Must be input as a tuple of lists or np.arrays. With format (Tick positions list, tick labels list). If None, the default ticks will be used.
    RightTicks (tuple or None): The tick positions and labels for the right y-axis. Must be input as a tuple of lists or np.arrays. With format (Tick positions list, tick labels list). If None, the default ticks will be used.
    RightMinTicks (tuple or None): The tick positions and labels for the minor ticks of the right y-axis. Must be input as a tuple of lists or np.arrays. With format (Tick positions list, tick labels list). If None, no minor ticks will be displayed.
    text1 (str or None): Additional text to be displayed on the figure. If None, no additional text will be displayed.

    Returns:
    fig (matplotlib.figure.Figure): The created figure.
    """
    fig = plt.figure(num=title,figsize=(13,6.5), tight_layout=True)
    gs1 = GridSpec(1, 1, top = 0.95, bottom=0.11 ,left=0.06,right=0.92)
    ax1 = fig.add_subplot(gs1[0])
    ax1 = fig.axes[0]
    ax1.set_title(title,fontweight='bold')

    for trace in LeftTraces.keys():
        ax1.plot(LeftTraces[trace][0],label = trace,color=LeftTraces[trace][1],lw=LeftTraces[trace][2])
    if LeftTicks is not None:    ### Ticks must be input as a tuple of lists or np.arrays. WIth format (Tick positions list, tick labels list)
            ax1.tick_params(axis='y',which='both',length=0,labelsize=0)
            ax1.set_yticks(LeftTicks[0]); ax1.set_yticklabels(LeftTicks[1])
            ax1.tick_params(axis='y',which='major',length=3,labelsize=9)
    if RightTraces is not None:
        ax1b = ax1.twinx()
        ax1b.margins(0.02,0.03)
        for axis in ['top','bottom','left','right']:
            ax1b.spines[axis].set_linewidth(1.5) 
        for trace in RightTraces.keys():
            ax1b.plot(RightTraces[trace][0],label = trace,color=RightTraces[trace][1],lw=RightTraces[trace][2])
        ax1b.legend(loc=4, fontsize=9)
        if RightScale == 'log':    
            ax1b.set_yscale('log')
        if RYLabel is not None:
            ax1b.set_ylabel(RYLabel,fontweight='bold',labelpad=15,fontsize=11)
        if RightTicks is not None:    
            ax1b.tick_params(axis='y',which='both',length=0,labelsize=0)
            ax1b.set_yticks(RightTicks[0]); ax1b.set_yticklabels(RightTicks[1])
            ax1b.tick_params(axis='y',which='major',length=4,labelsize=10)
            if RightMinTicks is not None:
                ax1b.set_yticks(RightMinTicks[0],minor=True); 
                ax1b.set_yticklabels(RightMinTicks[1],minor=True)
                ax1b.tick_params(axis='y',which='minor',length=2,labelsize=7)

    if LeftScale == 'log':
        ax1.set_yscale('log')
    if XTicks is not None:
        ax1.xaxis.set_ticks(XTicks) 
        ax1.tick_params(axis='x',length=3,labelsize='small',labelrotation=45)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%y-%b'))
        ax1.set_xlim(XTicks[0],XTicks[len(XTicks)-1])
        ax1.set_xlabel('Date (year-month)',fontweight='bold',fontsize=11)
    
    ax1.legend(loc=2,fontsize=9)
    ax1.set_ylabel(LYLabel,fontweight='bold',fontsize=11)
    for axis in ['top','bottom','left','right']:
            ax1.spines[axis].set_linewidth(1.5)
    if text1 is not None:
        ax1.text(0.25, -0.12, text1, fontweight = 'bold', transform = ax1.transAxes)
    return fig

class FitFunction():
    def __init__(self):
        ### Define function formula as a function below, and define tuple in self.functions with (callable function, Yscale of data display).. 
        self.functions = {"Linear": (self.FitLine, 'linear'),
                        'Exp_Base10':(self.Exp_Base10, 'log'), 
                        "Exponential": (None,'log'),
                        "ExpLog": (self.expLog, 'log'),
                        "LinExpLog": (self.expLog, 'linear'),
                        "Logistic": (self.logistic_func, 'log')}
        print("Data fitting engine, fit function options are: ",list(self.functions.keys()))

    ## Mathematical functions to fit to data.
    def FitLine(self, x, m, b):
        self.funcName = "Linear"
        return (m*x) + b
    
    def Exp_Base10(self, x, a, b):
        self.funcName = "Exp_Base10"
        return 10**(a*x+b)

    def expLog(self, x, a, b):  # Define expLog function
        self.funcName = "ExpLog"
        return 10**(a*np.log(x)-b)
        #return np.exp((a*np.log(x)-b))

    # def logistic_func(self, x, K, A, r):  # Define logistic function
    #     self.funcName = "Logistic"
    #     return K / (1 + A * np.exp(-r * x))
    # # Fit logistic function to data

    def logistic_func(self, x, K, A, r):  # Define logistic function
        self.funcName = "Logistic"
        # Scale x for stability
        x_scaled = x / 1000  # Adjust the scaling factor as needed
        return K / (1 + A * np.exp(-r * x_scaled))
    
class FitTrend():

    def __init__(self, data: pd.Series) -> None:
        self.name = data.name
        self.original_data = data.copy()
        self.original_data_BU = data.copy()
        self.data_max = self.original_data.max()
        
        freq = Utilities.freqDetermination(self.original_data_BU)
        freq.DetermineSeries_Frequency()
        self.Series_freq  = freq.frequency
        self.freq = freq.frequency
        print(self.original_data_BU.name, "series frequency: ", self.freq)

    def fitExpTrend(self, x, y):

        fit = np.polyfit(x, np.log(y), 1)
        print('Exponential fit to: ',self.original_data.name, ', x, np.log(y), intercept, slope a,b = ',fit)
        a = fit[0]; b = fit[1]
        
        return a,b

    def FitData(self, FitFunc: str = "ExpLog", x1 = None, x2 = None):  #Fit trend to data. 
        full_index = self.original_data.index
        if x1 is not None and x2 is not None:
            if isinstance(self.original_data.index , pd.DatetimeIndex):
                ex1 = Utilities.GetClosestDateInIndex(self.original_data, x1)
                ex2 = Utilities.GetClosestDateInIndex(self.original_data, x2)
                subset_start_index = ex1[1]; subset_end_index = ex2[1]
                
                self.original_data = self.original_data[ex1[0]:ex2[0]]
            else:
                self.original_data = self.original_data[x1:x2] 
                subset_start_index = self.original_data_BU.index.get_loc(x1)
                subset_end_index = self.original_data_BU.index.get_loc(x2)
        else:
            subset_start_index = 0      

        index = self.original_data.index.to_numpy()
        func = FitFunction()
        right_ext_num = round(0.03*len(full_index))
        # Calculate the offset of the subset's start relative to the full dataset
 
        x = np.linspace(subset_start_index,subset_end_index,len(index), dtype=int); y = self.original_data.to_numpy(); yLog = np.log(y)
        ext_left = np.linspace(0,subset_start_index-1, subset_start_index, dtype=int)
        ext_right = np.linspace(subset_end_index, len(full_index) + right_ext_num, len(full_index) - subset_end_index + right_ext_num - 2, dtype=int)
        full_x = np.concatenate([ext_left, x, ext_right], axis = 0)
        right_ext_index = pd.date_range(start = self.original_data_BU.index[-1], freq = self.freq[2], periods = right_ext_num)
        ext_index = self.original_data_BU.index.union(right_ext_index).unique().sort_values()

        f = func.functions[FitFunc][0]; funcName = FitFunc
        LogOrLin = func.functions[FitFunc][1]
        print(f, funcName, LogOrLin)

        if funcName == "Exponential":
            a, b = self.fitExpTrend(x, y)
            fit = [np.exp(b+a*ex) for ex in x]
            full_fit = [np.exp(b+a*ex) for ex in full_x]
            popt = (a, b); pcov = "?"
            print(a, b)
        elif funcName != "Exponential" and LogOrLin == 'linear':
            try:
                popt, pcov = curve_fit(f,x,y)
                fit = f(x,*popt)
                full_fit = f(full_x,*popt)
            except Exception as error:    
                print('Devo, fit failed bro.. error message: ',error,'\n',"Trying run fit again with LogOrLin set to 'log'") 
                popt, pcov = curve_fit(f,x,yLog)
                fit = f(x,*popt)
                full_fit = f(full_x,*popt)
        elif funcName != "Exponential" and LogOrLin == 'log':
            try:
                popt, pcov = curve_fit(f,x,yLog)
                fit = np.exp(f(x,*popt))
                full_fit = f(full_x,*popt)
            except Exception as error:    
                print('Devo, fit failed bro.. error message: ',error,'\n',"Trying run fit again with LogOrLin set to 'linear'") 
                popt, pcov = curve_fit(f,x,y)
                fit = f(x,*popt)
                full_fit = f(full_x,*popt)
        else: 
            raise Exception("Fit function not found. Check spelling and try again.")        
        print("Fitted, ", self.original_data.name, funcName, 'fit coefficients: ', popt)

        Fit = pd.Series(fit, index=self.original_data.index, name=self.original_data.name+" "+funcName+" fit")  
 
        Full_Fit = pd.Series(full_fit, index = ext_index, name = self.original_data_BU.name+" "+funcName+" ext_fit")

        print('Trendline fitted to data: ',self.original_data.name,' ',funcName,' function used, optimized fitting parameters: ',popt)  
        self.fit = Fit
        self.ext_fit = Full_Fit

        self.calc_fit_quality_params()

        self.Fit_Info = {"Fit function":funcName,
                        "p_opt": popt,
                        "p_cov": pcov,
                        "R_Squared": self.r2}
        if funcName == "ExpLog":
            self.fit[0:round(0.02*len(self.fit))] = np.nan   ##This is here to remove the first 2% of the curve where it flies upwards.
            self.TrendDev[0:round(0.02*len(self.TrendDev))] = np.nan
        elif funcName == "Exp_Base10":
            print("Note: 'Exp_Base10 fit was not working last timme I checked. Use 'Exponential' instead.")    
    
    def StdDevBands(self, multiples:int, periods:int):
        stdDev = self.fit.rolling(window=periods).std()
        numstd_l = multiples/np.e
        self.std_u = self.fit + multiples*stdDev; self.std_u.rename('Upper std. dev. band',inplace=True)
        self.std_l = self.fit - numstd_l*stdDev; self.std_l.rename('Lower std. dev. band',inplace=True)

    def calc_fit_quality_params(self):

        self.fit_res = ((self.original_data - self.fit)**2).sum(); print("Residual squared: ", self.fit_res)
        self.ss_tot = ((self.original_data - self.original_data.mean())**2).sum(); print("Total sum of squares: ", self.ss_tot)
        self.r2 = round(1 - (self.fit_res / self.ss_tot),3); print("R squared value from fit: ",self.r2)
        self.TrendDev = ((self.original_data - self.fit)/self.fit)*100; print('Dev from trend max, min: ',self.TrendDev.max(),self.TrendDev.min())
        self.TrendDev.rename('Percentage_dev_from_fit',inplace=True) 

        self.ffit_res = ((self.original_data_BU - self.ext_fit)**2).sum(); print("Residual squared (ext fit): ", self.ffit_res)
        self.fss_tot = ((self.original_data_BU - self.original_data_BU.mean())**2).sum(); print("Total sum of squares (ext fit): ", self.fss_tot)
        self.fr2 = round(1 - (self.ffit_res/ self.fss_tot),3); print("R squared value from fit: ", self.fr2)
        self.fTrendDev = ((self.original_data_BU- self.ext_fit)/self.ext_fit)*100; print('Dev from trend max, min: (ext fit) ', self.fTrendDev.max(), self.fTrendDev.min())
        self.fTrendDev.rename('Percentage_dev_from_ext_fit',inplace=True)  

    def PCBands(self, PC_Offset:float):
        self.pcu = self.fit*((100+PC_Offset)/100); self.pcu.rename('Upper '+str(PC_Offset)+'% band',inplace=True)
        self.pcl = self.fit/((100+PC_Offset)/100); self.pcu.rename('Lower '+str(PC_Offset)+'% band',inplace=True)

    def ShowFit(self, yaxis: str = "linear", YLabel: str = "Price (USD)", title: str = None,
                xmin_date: str = None, xmax_date: str = None, y_margins: float = 0.03):
        if self.fit is None:
            print('Run fitting function first before trying to plot the fit.')    
            return
        
        else:
            fig = plt.figure(figsize=(13,6.5), tight_layout=True)
            gs1 = GridSpec(1, 1, top = 0.95, bottom=0.07, left=0.08, right=0.92)
            ax1 = fig.add_subplot(gs1[0]); axb = ax1.twinx()
            if title is None:
                title = self.fit.name + ", fit quality assessment chart."
            ax1.set_title(title,fontweight='bold')

            if yaxis == 'log':
                ax1.set_yscale('log'); axb.set_yscale('log')
                lTicks, lTickLabs = Utilities.EqualSpacedTicks(10, self.original_data_BU, LogOrLin='log')
                self.fTrendDev += 100
                rTicks, rTickLabs = Utilities.EqualSpacedTicks(10, self.fTrendDev, LogOrLin='log',LabOffset=-100,labSuffix="%")
                ax1.tick_params(axis='y',which='both',length=0,width=0,right=False,labelright=False,labelsize=0)  
                ax1.set_yticks(lTicks); ax1.set_yticklabels(lTickLabs)
                ax1.tick_params(axis='y',which='major',width=1,length=3,labelsize=8,left=True,labelleft=True)
                axb.tick_params(axis='y',which='both',length=0,width=0,right=False,labelright=False,labelsize=0) 
                axb.set_yticks(rTicks); axb.set_yticklabels(rTickLabs)
                axb.tick_params(axis='y',which='major',width=1,length=3,labelsize=8,right=True,labelright=True)

            ax1.plot(self.original_data_BU, label = self.original_data_BU.name, color = "black", lw = 2.5)
            ax1.plot(self.ext_fit, label = self.ext_fit.name, color = "blue", ls = "dashed", lw=1)
            ax1.plot(self.fit,label = self.fit.name, color = "red", ls = "dashed", lw=1.5)
            axb.plot(self.fTrendDev, label = self.TrendDev.name, color = "green", lw = 1.25)
            axb.set_ylabel('% deviation from fitted trend', fontsize = 10, fontweight = 'bold')
            ax1.set_ylabel(YLabel, fontsize = 10, fontweight = 'bold')

            ax1.legend(loc=2, fontsize = 'small'); axb.legend(loc=2, bbox_to_anchor=(0,0.89), fontsize = 'small')
            ax1.grid(visible=True,axis='both',which='major',lw=0.75,ls=":",color='gray')
            ax1.grid(visible=True,axis='x',which='both',lw=0.75,ls=":",color='gray')
            ax1.minorticks_on()
            # ax1.set_ylim((self.original_data_BU.min()-0.075*self.original_data_BU.min()),(self.original_data_BU.max()+0.075*self.original_data_BU.max()))
            printr2 = "R-squared value from fitted subset: "+str(self.Fit_Info['R_Squared'])
            ax1.text(x=0.37, y = 0.97, s= printr2,horizontalalignment='left',verticalalignment='center', transform=ax1.transAxes)

            if xmin_date is not None and xmax_date is not None:
                left, right = calc_chart_xlims(self.original_data_BU.index, xmin=xmin_date, xmax=xmax_date, margin_left=0.01, margin_right=0.05)
            else:
                left, right = calc_chart_xlims(self.original_data_BU.index, margin_left=0.01, margin_right=0.05)
            ax1.set_xlim(left, right)

            for axis in ['top','bottom','left','right']:
                ax1.spines[axis].set_linewidth(1.5) 
            return fig
        
####### A funcion for finding the peak locations in a time series. Optionally brings up a plot where yu can add
### additional peak locations manually. 
def get_peak_locs(data_series: pd.Series, yscale: str = 'log', ylabel: str = "Bil. of U.S $", 
                  title: str = "M2 monetary Aggregate USA", mode: str = "automan")-> pd.Series:
    """
    mode: string, options: ["auto", "manual", "automan"]...
    """
    if mode == "manual":
        peaks = []
    else:
        peaks = identify_peaks_and_troughs(data_series, x_range=datetime.timedelta(weeks=156))[0]

    def final_locs(data: pd.Series, x_locs: list) -> pd.Series:
        print(" X locs: ", x_locs)
        vals = []; index = []
        for loc in x_locs:
            date_loc = Utilities.GetClosestDateInIndex(data.index, searchDate = loc.strftime('%Y-%m-%d'))
            #sub_range = data.iloc[date_loc_index-5: date_loc_index+5]
            #all_locs.append(argrelextrema(sub_range.values, np.greater_equal, order=len(sub_range))[0])
            vals.append(date_loc[0])
            index.append(date_loc[1]) 
        
        return pd.Series(vals, index = index, name = "Peak locations, "+data.name).sort_index()

    if mode == "auto":
        peak_locs = peaks
    else:
        text_note = "Left-click at peak location to add red vertical line.Right-click to remove last red line. \n\
            Peak locations will be exported to a Series."
        # Initial plot
        LeftTraces = {data_series.name: (data_series,"blue",1.5)}
        fig = TwoAxisFig(LeftTraces, yscale, ylabel, title, text1=text_note)
        x_locs = peaks.to_list(); lines = []
        ax = fig.axes[0]

        for date in peaks:
            ax.axvline(x=date, color='black', linestyle='--', lw=1)

        # Event handler for mouse clicks
        def onclick(event):
            # Right click removes the last line
            if event.button == 3 and lines:
                line = lines.pop()
                line.remove()
            # Left click adds a vertical line
            elif event.button == 1:
                line = ax.axvline(x=event.xdata, color='r', ls = "--", lw = 1)
                lines.append(line)
                x_locs.append(mdates.num2date(event.xdata))
                print(x_locs)
            # Redraw the figure
            fig.canvas.draw()
            # Print the corresponding dates        

        # Connect the event handler
        fig.canvas.mpl_connect('button_press_event', onclick)
        plt.show()
        peak_locs = final_locs(data_series, x_locs)

    return peak_locs

## Seasonal adjustment function using STL decomposition from statsmodels...
def seasonal_adjust(series: pd.Series, period: int = None, robust: bool = True) -> pd.Series:
    """
    Returns a seasonally adjusted version of the input time series using STL decomposition.

    Parameters:
        series (pd.Series): The time series to adjust.
        period (int, optional): The number of periods in a seasonal cycle (e.g., 12 for monthly data).
        robust (bool): Use robust fitting to handle outliers.

    Returns:
        pd.Series: Seasonally adjusted series (trend + residual).
    """
    if period is None:
        # Try to infer period from frequency
        inferred = pd.infer_freq(series.index)
        if inferred == 'M':
            period = 12
        elif inferred == 'Q':
            period = 4
        elif inferred == 'W':
            period = 52
        else:
            raise ValueError("Please specify the seasonal period for your data.")
    stl = STL(series, period=period, robust=robust)
    res = stl.fit()
    return res.trend + res.resid  # Seasonally adjusted series

def plot_decomposition(series: pd.Series, period: int = None, robust: bool = True):
    """Quick plot of STL decomposition components."""
    import matplotlib.pyplot as plt
    stl = STL(series, period=period, robust=robust)
    res = stl.fit()
    res.plot()
    plt.show()

def x13_seasonal_adjust(series: pd.Series, freq: int = None) -> pd.Series:
    """
    Seasonally adjust a time series using X-13ARIMA-SEATS only.
    
    Parameters:
    -----------
    series : pd.Series
        Time series data with datetime index to seasonally adjust
    freq : int, optional  
        Seasonal frequency (4 for quarterly, 12 for monthly). If None, attempts to infer from index
    
    Returns:
    --------
    pd.Series
        Seasonally adjusted time series with same index as input, or original series if X-13 fails
    
    Notes:
    ------
    Requires X-13ARIMA-SEATS binary installed and on PATH.
    Install via: conda install -c conda-forge x13as
    """
    
    # Validate input
    if not isinstance(series.index, pd.DatetimeIndex):
        try:
            series.index = pd.to_datetime(series.index)
        except Exception:
            print("Warning: Series must have a datetime-like index for seasonal adjustment. Returning original series.")
            return series
    
    # Infer frequency if not provided
    if freq is None:
        print("No frequency provided, attempting to infer frequency of time-series...")
        inferred_freq = pd.infer_freq(series.index)
        if inferred_freq:
            if 'M' in inferred_freq:
                freq = 12  # Monthly
            elif 'Q' in inferred_freq:  
                freq = 4   # Quarterly
            elif 'W' in inferred_freq:
                freq = 52  # Weekly

        if freq is not None:
            print(f"Frequency inferred, will use: {freq}")
        # Fallback frequency detection
        if freq is None:
            freq = 12 if len(series) > 24 else 4
            print(f"Could not infer frequency, using default: {freq}")
    
    # Check X-13 availability
    try:
        from statsmodels.tsa.x13 import x13_arima_analysis
    except ImportError:
        print("X-13 not available. Install statsmodels and X-13 binary (conda install -c conda-forge x13as). Returning original series.")
        return series
    
    # Attempt X-13 seasonal adjustment
    try:
        print(f"Attempting X-13ARIMA-SEATS seasonal adjustment (freq={freq})...")
        result = x13_arima_analysis(series, freq=freq)
        
        # Extract seasonally adjusted series
        if hasattr(result, 'seasadj'):
            sa_series = result.seasadj
        elif hasattr(result, 'series'):
            sa_series = result.series  
        else:
            raise AttributeError("X-13 result missing expected seasonally adjusted series")
        
        # Ensure proper Series formatting
        if not isinstance(sa_series, pd.Series):
            sa_series = pd.Series(sa_series, index=series.index)
        
        sa_series = sa_series.rename(f"{series.name}_x13_seasadj" if series.name else "x13_seasadj")
        print("X-13 seasonal adjustment completed successfully")
        return sa_series
        
    except Exception as e:
        print(f"X-13 seasonal adjustment failed: {e}. Returning original series.")
        return series

if __name__ == '__main__':
    data = pd.Series(pd.read_excel(parent+fdel+'Macro_Chartist/SavedData/CPIAUCSL.xlsx', sheet_name="Closing_Price", index_col=0).squeeze())
    # xmin_date="1990-01-01"; xmax_date=datetime.datetime.today().strftime("%Y-%m-%d")
    # data = data[xmin_date:xmax_date]

    fit = FitTrend(data)
    fit.FitData(FitFunc='Exponential', x1="1995-01-01", x2 = "2020-01-01")
    print(fit.fit, fit.original_data_BU, fit.TrendDev, fit.fTrendDev, fit.Fit_Info)

    figure = fit.ShowFit(yaxis='log', YLabel="Billions of U.S $", title="M2 Money Supply U.S")

    data_YoY = Utilities.MonthPeriodAnnGrowth2(data, months = 12)
    peaks = identify_peaks_and_troughs(data_YoY, x_range=datetime.timedelta(weeks=156))[0]

    # Assuming 'data2' is your second pd.Series
    fig, ax1 = plt.subplots()

    color = 'tab:blue'
    ax1.set_ylabel('data_YoY', color=color)  # we already handled the x-label with ax1
    ax1.plot(data, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:red'
    # we already handled the x-label with ax1
    ax2.set_ylabel('data2', color=color)  
    ax2.plot(data_YoY, color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    
    for date in peaks:
        ax1.axvline(x=date, color='black', linestyle='--', lw=1)  # adds a vertical line at the given date

    fig.tight_layout()  # otherwise the right y-label is slightly clipped

    plt.show()