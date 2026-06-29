"""
Bootleg toolz — trend fitting, distribution fitting, and statistical models.

Ported from MacroBackend/Fitting.py.  Uses bootleg_datafeed auxiliary
for frequency inference instead of the legacy freqDetermination class.
"""

from __future__ import annotations

import datetime
from typing import Optional

import matplotlib as mpl
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
from scipy import stats as scipy_stats
from scipy.optimize import curve_fit
from scipy.signal import argrelextrema
from statsmodels.tsa.seasonal import STL

from bootleg_datafeed.auxiliary import FrequencyConverter, infer_frequency
from .utilities import EqualSpacedTicks, GetClosestDateInIndex


# ---------------------------------------------------------------------------
# X-axis helpers
# ---------------------------------------------------------------------------

def calc_chart_xlims(
    index: pd.DatetimeIndex,
    xmin: str = None,
    xmax: str = None,
    margin_left: float = 0.05,
    margin_right: float = 0.05,
) -> tuple:
    """Calculate x-axis limits with margins around a DatetimeIndex."""
    if not isinstance(index, pd.DatetimeIndex):
        raise TypeError("index must be DatetimeIndex")

    if xmin is not None and xmax is not None:
        min_date = GetClosestDateInIndex(index, xmin)[0]
        max_date = GetClosestDateInIndex(index, xmax)[0]
    else:
        min_date, max_date = index.min(), index.max()

    date_range = max_date - min_date
    left_buffer = datetime.timedelta(days=date_range.days * margin_left)
    right_buffer = datetime.timedelta(days=date_range.days * margin_right)
    return (min_date - left_buffer, max_date + right_buffer)


# ---------------------------------------------------------------------------
# Peak / trough detection
# ---------------------------------------------------------------------------

def identify_peaks_and_troughs(
    data: pd.Series, x_range: datetime.timedelta
):
    """Find local extrema in a time series."""
    dsec = (data.index[1] - data.index[0]).total_seconds()
    x_range_points = round(x_range.total_seconds() / dsec)
    peaks = argrelextrema(data.values, np.greater_equal, order=x_range_points)[0]
    troughs = argrelextrema(-data.values, np.less_equal, order=x_range_points)[0]

    def filter_extrema(indices, order):
        indices = sorted(indices)
        out = []
        for idx in indices:
            if not out or idx - out[-1] > order:
                out.append(idx)
            elif data[idx] > data[out[-1]]:
                out[-1] = idx
        return out

    sig_peaks = filter_extrema(peaks, x_range_points)
    sig_troughs = filter_extrema(troughs, x_range_points)

    ThePeaksRaw = pd.Series(data.index[peaks], index=peaks, name="Peaks")
    TroffzRaw = pd.Series(data.index[troughs], index=troughs, name="Troughs")
    ThePeaks = pd.Series(data.index[sig_peaks], index=sig_peaks, name="Peaks_filtered")
    Troffz = pd.Series(data.index[sig_troughs], index=sig_troughs, name="Troughs_filtered")
    return ThePeaks, Troffz, ThePeaksRaw, TroffzRaw


# ---------------------------------------------------------------------------
# Distribution functions for curve_fit
# ---------------------------------------------------------------------------

def gaussian(x, amp, cen, wid):
    return amp * np.exp(-((x - cen) ** 2) / (2 * wid ** 2))


def lorentzian(x, amp, cen, wid):
    return amp * wid ** 2 / ((x - cen) ** 2 + wid ** 2)


def student_t(x, amp, cen, df, scale):
    return amp * scipy_stats.t.pdf(x, df, loc=cen, scale=scale)

# ---------------------------------------------------------------------------
# Normality tests
# ---------------------------------------------------------------------------

def normality_tests(data: pd.Series):
    """Shapiro-Wilk, Anderson-Darling, K-S tests with Q-Q plot."""
    data = data.dropna().values
    shapiro_stat, shapiro_p = scipy_stats.shapiro(data)
    anderson_result = scipy_stats.anderson(data, dist="norm")
    ks_stat, ks_p = scipy_stats.kstest(data, "norm", args=(np.mean(data), np.std(data)))

    results = pd.DataFrame(
        {
            "Test": ["Shapiro-Wilk", "Anderson-Darling", "Kolmogorov-Smirnov"],
            "Statistic": [shapiro_stat, anderson_result.statistic, ks_stat],
            "p-value": [shapiro_p, np.nan, ks_p],
            "Critical Values": [np.nan, anderson_result.critical_values, np.nan],
            "Significance Levels": [np.nan, anderson_result.significance_level, np.nan],
        }
    )

    fig, ax = plt.subplots(figsize=(6, 6))
    (osm, osr), (slope, intercept, r) = scipy_stats.probplot(data, dist="norm", fit=True, plot=ax)
    y_pred = slope * osm + intercept
    ss_res = np.sum((osr - y_pred) ** 2)
    ss_tot = np.sum((osr - np.mean(osr)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    ax.text(
        0.05, 0.95, f"R\u00b2 = {r2:.4f}", fontsize=10, transform=ax.transAxes,
        bbox=dict(facecolor="beige", edgecolor="black", boxstyle="round,pad=0.5"),
    )
    fig.tight_layout()
    return results, fig


def ks_test_distribution(data: pd.Series, distribution: str):
    """K-S test against a named distribution with Q-Q plot."""
    data = data.dropna().values
    if distribution == "norm":
        ks_stat, ks_p = scipy_stats.kstest(
            data, scipy_stats.norm.cdf, args=(np.mean(data), np.std(data))
        )
    elif distribution == "cauchy":
        ks_stat, ks_p = scipy_stats.kstest(
            data, scipy_stats.cauchy.cdf, args=(np.median(data), scipy_stats.iqr(data))
        )
    else:
        ks_stat, ks_p = scipy_stats.kstest(data, distribution)

    results = pd.DataFrame({"Test": ["K-S"], "Statistic": [ks_stat], "p-value": [ks_p]})
    fig, ax = plt.subplots(figsize=(6, 6))
    scipy_stats.probplot(data, dist=distribution, plot=ax)
    ax.set_title(f"Q-Q Plot for {distribution} Distribution")
    fig.tight_layout()
    return results, fig

# ---------------------------------------------------------------------------
# Normality tests
# ---------------------------------------------------------------------------

def normality_tests(data: pd.Series):
    """Shapiro-Wilk, Anderson-Darling, K-S tests with Q-Q plot."""
    data = data.dropna().values
    shapiro_stat, shapiro_p = scipy_stats.shapiro(data)
    anderson_result = scipy_stats.anderson(data, dist="norm")
    ks_stat, ks_p = scipy_stats.kstest(data, "norm", args=(np.mean(data), np.std(data)))

    results = pd.DataFrame(
        {
            "Test": ["Shapiro-Wilk", "Anderson-Darling", "Kolmogorov-Smirnov"],
            "Statistic": [shapiro_stat, anderson_result.statistic, ks_stat],
            "p-value": [shapiro_p, np.nan, ks_p],
            "Critical Values": [np.nan, anderson_result.critical_values, np.nan],
            "Significance Levels": [np.nan, anderson_result.significance_level, np.nan],
        }
    )

    fig, ax = plt.subplots(figsize=(6, 6))
    (osm, osr), (slope, intercept, r) = scipy_stats.probplot(data, dist="norm", fit=True, plot=ax)
    y_pred = slope * osm + intercept
    ss_res = np.sum((osr - y_pred) ** 2)
    ss_tot = np.sum((osr - np.mean(osr)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    ax.text(
        0.05, 0.95, f"R\u00b2 = {r2:.4f}", fontsize=10, transform=ax.transAxes,
        bbox=dict(facecolor="beige", edgecolor="black", boxstyle="round,pad=0.5"),
    )
    fig.tight_layout()
    return results, fig


def ks_test_distribution(data: pd.Series, distribution: str):
    """K-S test against a named distribution with Q-Q plot."""
    data = data.dropna().values
    if distribution == "norm":
        ks_stat, ks_p = scipy_stats.kstest(
            data, scipy_stats.norm.cdf, args=(np.mean(data), np.std(data))
        )
    elif distribution == "cauchy":
        ks_stat, ks_p = scipy_stats.kstest(
            data, scipy_stats.cauchy.cdf, args=(np.median(data), scipy_stats.iqr(data))
        )
    else:
        ks_stat, ks_p = scipy_stats.kstest(data, distribution)

    results = pd.DataFrame({"Test": ["K-S"], "Statistic": [ks_stat], "p-value": [ks_p]})
    fig, ax = plt.subplots(figsize=(6, 6))
    scipy_stats.probplot(data, dist=distribution, plot=ax)
    ax.set_title(f"Q-Q Plot for {distribution} Distribution")
    fig.tight_layout()
    return results, fig

# ---------------------------------------------------------------------------
# stat_models_fit — distribution fitting
# ---------------------------------------------------------------------------

class stat_models_fit:
    """Fit Gaussian, Lorentzian, Student-t, and Gamma distributions to data."""

    def __init__(self, data: pd.Series):
        self.data = data.copy()
        self.name = data.name or "data"
        self.hist, self.bin_edges = np.histogram(self.data, bins=len(self.data), density=True)
        self.bin_centers = (self.bin_edges[:-1] + self.bin_edges[1:]) / 2
        self.x_fit = np.linspace(self.bin_edges[0], self.bin_edges[-1], len(self.data))

    def fit_gaussian(self, method: str = "MLE"):
        try:
            fit = scipy_stats.norm.fit(self.data, method=method)
            self.norm = scipy_stats.norm(*fit)
            fit_series = self.norm.pdf(self.x_fit)
            self.gaussian = pd.Series(fit_series, index=self.x_fit, name=self.name + " Gauss fit")
            self.gaussian_params = fit
            return fit
        except Exception as e:
            print(f"Gaussian fit failed: {e}")
            return None

    def fit_lorentzian(self, method: str = "MLE"):
        try:
            fit = scipy_stats.cauchy.fit(self.data, method=method)
            self.cauchy = scipy_stats.cauchy(*fit)
            fit_series = self.cauchy.pdf(self.x_fit)
            self.lorentzian = pd.Series(fit_series, index=self.x_fit, name=self.name + " Lorentzian fit")
            self.lorentzian_params = fit
            return fit
        except Exception as e:
            print(f"Lorentzian fit failed: {e}")
            return None

    def fit_student_t(self, method: str = "MLE"):
        try:
            fit = scipy_stats.t.fit(self.data, method=method)
            self.t_dist = scipy_stats.t(*fit)
            fit_series = self.t_dist.pdf(self.x_fit)
            self.t = pd.Series(fit_series, index=self.x_fit, name=self.name + " Student T fit")
            self.t_params = fit
            return fit
        except Exception as e:
            print(f"Student T fit failed: {e}")
            return None

    def fit_gamma(self, method: str = "MLE"):
        """BUGFIX: was using stats.t() instead of stats.gamma() for the result."""
        try:
            fit = scipy_stats.gamma.fit(self.data, method=method)
            self.gam_dist = scipy_stats.gamma(*fit)
            fit_series = self.gam_dist.pdf(self.x_fit)
            self.gamma = pd.Series(fit_series, index=self.x_fit, name=self.name + " Gamma fit")
            self.gamma_params = fit
            return fit
        except Exception as e:
            print(f"Gamma fit failed: {e}")
            return None

    def plot_histogram_with_fits(
        self, log: bool = False,
        title: str = "Histogram with Gaussian, Lorentzian, Student\'s t and Gamma fits"
    ):
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.hist(self.data, bins=1000, color="blue", alpha=0.85, label=self.name, density=True)
        if hasattr(self, "gaussian"):
            ax.plot(self.gaussian, color="red", label="Gaussian Fit")
        if hasattr(self, "lorentzian"):
            ax.plot(self.lorentzian, color="green", label="Lorentzian Fit")
        if hasattr(self, "t"):
            ax.plot(self.t, color="purple", label=f"T-Dist (df={self.t_params[0]:.2f})")
        if hasattr(self, "gamma"):
            ax.plot(self.gamma, color="fuchsia", label="Gamma Fit")
        if hasattr(self, "data_filtered"):
            ax.hist(self.data_filtered, bins=1000, color="red", alpha=0.6, label=f"{self.name} filtered", density=True)
        if hasattr(self, "lower_threshold"):
            ax.axvline(self.lower_threshold, color="black", linestyle="--", lw=1, label="Lower cut-off")
        if hasattr(self, "upper_threshold"):
            ax.axvline(self.upper_threshold, color="blue", linestyle="--", lw=1, label="Upper cut-off")
        ax.legend(loc="upper left", fontsize=10)
        ax.set_xlabel("Value")
        ax.set_ylabel("Density")
        ax.set_title(title, fontsize=11)
        if log:
            ax.set_yscale("log")
            ax.set_ylim(10**-2, self.hist.max())
        self.hist_fig = fig
        return fig, ax

    def qq_plots(self, data: pd.Series = None):
        """Q-Q plots for Normal, Cauchy, Student-t, and Gamma."""
        if data is not None:
            d = data.copy().dropna().values
        else:
            d = self.data.copy().dropna().values

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        dists = [
            ("Normal", scipy_stats.norm),
            ("Cauchy", scipy_stats.cauchy),
            ("Student-t", scipy_stats.t),
            ("Gamma", scipy_stats.gamma),
        ]
        for ax, (name, dist) in zip(axes.flat, dists):
            scipy_stats.probplot(d, dist=dist, plot=ax)
            ax.set_title(f"{name} Q-Q Plot")
        fig.tight_layout()
        self.qq_figs = fig
        return fig, axes

# ---------------------------------------------------------------------------
# stat_models_fit — distribution fitting
# ---------------------------------------------------------------------------

class stat_models_fit:
    """Fit Gaussian, Lorentzian, Student-t, and Gamma distributions to data."""

    def __init__(self, data: pd.Series):
        self.data = data.copy()
        self.name = data.name or "data"
        self.hist, self.bin_edges = np.histogram(self.data, bins=len(self.data), density=True)
        self.bin_centers = (self.bin_edges[:-1] + self.bin_edges[1:]) / 2
        self.x_fit = np.linspace(self.bin_edges[0], self.bin_edges[-1], len(self.data))

    def fit_gaussian(self, method: str = "MLE"):
        try:
            fit = scipy_stats.norm.fit(self.data, method=method)
            self.norm = scipy_stats.norm(*fit)
            fit_series = self.norm.pdf(self.x_fit)
            self.gaussian = pd.Series(fit_series, index=self.x_fit, name=self.name + " Gauss fit")
            self.gaussian_params = fit
            return fit
        except Exception as e:
            print(f"Gaussian fit failed: {e}")
            return None

    def fit_lorentzian(self, method: str = "MLE"):
        try:
            fit = scipy_stats.cauchy.fit(self.data, method=method)
            self.cauchy = scipy_stats.cauchy(*fit)
            fit_series = self.cauchy.pdf(self.x_fit)
            self.lorentzian = pd.Series(fit_series, index=self.x_fit, name=self.name + " Lorentzian fit")
            self.lorentzian_params = fit
            return fit
        except Exception as e:
            print(f"Lorentzian fit failed: {e}")
            return None

    def fit_student_t(self, method: str = "MLE"):
        try:
            fit = scipy_stats.t.fit(self.data, method=method)
            self.t_dist = scipy_stats.t(*fit)
            fit_series = self.t_dist.pdf(self.x_fit)
            self.t = pd.Series(fit_series, index=self.x_fit, name=self.name + " Student T fit")
            self.t_params = fit
            return fit
        except Exception as e:
            print(f"Student T fit failed: {e}")
            return None

    def fit_gamma(self, method: str = "MLE"):
        """BUGFIX: was using stats.t() instead of stats.gamma() for the result."""
        try:
            fit = scipy_stats.gamma.fit(self.data, method=method)
            self.gam_dist = scipy_stats.gamma(*fit)
            fit_series = self.gam_dist.pdf(self.x_fit)
            self.gamma = pd.Series(fit_series, index=self.x_fit, name=self.name + " Gamma fit")
            self.gamma_params = fit
            return fit
        except Exception as e:
            print(f"Gamma fit failed: {e}")
            return None

    def plot_histogram_with_fits(
        self, log: bool = False,
        title: str = "Histogram with Gaussian, Lorentzian, Student\'s t and Gamma fits"
    ):
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.hist(self.data, bins=1000, color="blue", alpha=0.85, label=self.name, density=True)
        if hasattr(self, "gaussian"):
            ax.plot(self.gaussian, color="red", label="Gaussian Fit")
        if hasattr(self, "lorentzian"):
            ax.plot(self.lorentzian, color="green", label="Lorentzian Fit")
        if hasattr(self, "t"):
            ax.plot(self.t, color="purple", label=f"T-Dist (df={self.t_params[0]:.2f})")
        if hasattr(self, "gamma"):
            ax.plot(self.gamma, color="fuchsia", label="Gamma Fit")
        if hasattr(self, "data_filtered"):
            ax.hist(self.data_filtered, bins=1000, color="red", alpha=0.6, label=f"{self.name} filtered", density=True)
        if hasattr(self, "lower_threshold"):
            ax.axvline(self.lower_threshold, color="black", linestyle="--", lw=1, label="Lower cut-off")
        if hasattr(self, "upper_threshold"):
            ax.axvline(self.upper_threshold, color="blue", linestyle="--", lw=1, label="Upper cut-off")
        ax.legend(loc="upper left", fontsize=10)
        ax.set_xlabel("Value")
        ax.set_ylabel("Density")
        ax.set_title(title, fontsize=11)
        if log:
            ax.set_yscale("log")
            ax.set_ylim(10**-2, self.hist.max())
        self.hist_fig = fig
        return fig, ax

    def qq_plots(self, data: pd.Series = None):
        """Q-Q plots for Normal, Cauchy, Student-t, and Gamma."""
        if data is not None:
            d = data.copy().dropna().values
        else:
            d = self.data.copy().dropna().values

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        dists = [
            ("Normal", scipy_stats.norm),
            ("Cauchy", scipy_stats.cauchy),
            ("Student-t", scipy_stats.t),
            ("Gamma", scipy_stats.gamma),
        ]
        for ax, (name, dist) in zip(axes.flat, dists):
            scipy_stats.probplot(d, dist=dist, plot=ax)
            ax.set_title(f"{name} Q-Q Plot")
        fig.tight_layout()
        self.qq_figs = fig
        return fig, axes

# ---------------------------------------------------------------------------
# FitFunction — math function library for trend fitting
# ---------------------------------------------------------------------------

class FitFunction:
    """Library of math functions for trend line fitting."""

    @staticmethod
    def linear(x, a, b):
        return a * x + b

    @staticmethod
    def exponential(x, a, b, c):
        return a * np.exp(b * (x - c))

    @staticmethod
    def exp_log(x, a, b, c, d):
        """Exponential-logistic (sigmoid-type)."""
        return a + (b - a) / (1 + np.exp(c * (x - d)))

    @staticmethod
    def logistic(x, a, b, c, d):
        """Generalised logistic."""
        return a + (b - a) / (1 + np.exp(c * (x - d)))

    @staticmethod
    def power_law(x, a, b, c):
        return a * (x - c) ** b

    @staticmethod
    def quadratic(x, a, b, c):
        return a * x ** 2 + b * x + c

    @staticmethod
    def cubic(x, a, b, c, d):
        return a * x ** 3 + b * x ** 2 + c * x + d

    @staticmethod
    def polynom(x, a, b, c, d, e):
        return a * x ** 4 + b * x ** 3 + c * x ** 2 + d * x + e

    FUNC_MAP = {
        "linear": (linear, 2),
        "exponential": (exponential, 3),
        "exp_log": (exp_log, 4),
        "logistic": (logistic, 4),
        "power_law": (power_law, 3),
        "quadratic": (quadratic, 3),
        "cubic": (cubic, 4),
        "polynom": (polynom, 5),
    }

    @classmethod
    def get(cls, name: str):
        """Get (function, n_params) for a named fit function."""
        if name not in cls.FUNC_MAP:
            raise ValueError(f"Unknown fit function: {name}. Options: {list(cls.FUNC_MAP)}")
        return cls.FUNC_MAP[name]


# ---------------------------------------------------------------------------
# FitTrend — trend line fitting for time series
# ---------------------------------------------------------------------------

class FitTrend:
    """Fit a trend line (linear, exponential, etc.) to a time series."""

    def __init__(
        self,
        series: pd.Series,
        line_style: str = "solid",
        line_color: str = "black",
        name: str = "Trend",
    ):
        self.original_data = series.copy().dropna()
        self.line_style = line_style
        self.line_color = line_color
        self.name = name
        self.fit = None
        self.fTrendDev = None
        self.TrendDev = None
        self.original_data_BU = None
        self.Fit_Info = {}
        self.fit_params = None
        self.fit_freq = 12

        # Infer frequency for period labelling
        freq = infer_frequency(self.original_data)
        if freq:
            self.fit_freq = {"D": 252, "W": 52, "M": 12, "Q": 4, "A": 1}.get(freq, 12)

    def FitData(
        self,
        FitFunc: str = "exponential",
        x1: str = None,
        x2: str = None,
        disp: bool = False,
    ):
        """Fit a trend line over date range [x1, x2]."""
        data = self.original_data.copy()
        if x1 is not None:
            d = GetClosestDateInIndex(data, x1)
            data = data.loc[d[0]:]
        if x2 is not None:
            d = GetClosestDateInIndex(data, x2)
            data = data.loc[:d[0]]

        x_vals = np.arange(len(data)).astype(float)
        y_vals = data.values.astype(float)
        fn, n_params = FitFunction.get(FitFunc)

        # Generate initial guesses
        p0 = [1.0] * n_params
        if FitFunc == "linear":
            p0 = [y_vals[-1] / x_vals[-1] if x_vals[-1] != 0 else 1, y_vals[0]]
        elif FitFunc in ("exponential", "power_law"):
            p0 = [1.0, 0.01, y_vals[0]]

        try:
            popt, _ = curve_fit(fn, x_vals, y_vals, p0=p0, maxfev=10000)
        except Exception as e:
            print(f"Fit failed for {FitFunc}: {e}")
            return None

        self.fit_params = popt
        self.fit = fn(x_vals, *popt)
        self.original_data_BU = data

        # Trend deviation
        trend_series = pd.Series(self.fit, index=data.index, name="Fitted_trend")
        dev = ((data / trend_series) - 1) * 100
        self.TrendDev = dev
        self.fTrendDev = trend_series

        self.Fit_Info = {
            "function": FitFunc,
            "params": popt,
            "range": (data.index[0], data.index[-1]),
        }

        if disp:
            self.ShowFit()
        return popt

    def ShowFit(
        self,
        yaxis: str = "linear",
        YLabel: str = "Value",
        title: str = "Trend Fit",
    ):
        """Plot original data with fitted trend, deviation panel, and bands."""
        if self.fit is None:
            raise ValueError("Run FitData() first.")

        fig = plt.figure(figsize=(14, 8))
        gs = GridSpec(3, 1, height_ratios=[2, 1, 1], hspace=0.15)

        # --- Top panel: data + trend ---
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(self.original_data.index, self.original_data, color="blue", linewidth=1.5, label="Data")
        ax1.plot(self.fTrendDev.index, self.fTrendDev, color="red", linewidth=1.5, label="Trend")
        ax1.set_yscale(yaxis)
        ax1.set_ylabel(YLabel)
        ax1.set_title(title)
        ax1.legend(loc="upper left", fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(calc_chart_xlims(self.fTrendDev.index))

        # ticks
        ytr, ytr_labs = EqualSpacedTicks(6, data=self.original_data, LogOrLin=yaxis)
        ax1.set_yticks(ytr)
        ax1.set_yticklabels(ytr_labs)

        # --- Middle: deviation ---
        ax2 = fig.add_subplot(gs[1])
        ax2.plot(self.TrendDev.index, self.TrendDev, color="purple", linewidth=1, label="Deviation (%)")
        ax2.axhline(0, color="gray", linewidth=0.5)
        ax2.set_ylabel("Dev %")
        ax2.legend(loc="upper left", fontsize=9)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(ax1.get_xlim())

        # --- Bottom: frequency of deviations ---
        ax3 = fig.add_subplot(gs[2])
        ax3.hist(self.TrendDev.dropna(), bins=50, color="gray", alpha=0.7, edgecolor="black")
        ax3.axvline(0, color="red", linestyle="--", linewidth=1)
        ax3.set_xlabel("Deviation (%)")
        ax3.set_ylabel("Frequency")
        ax3.grid(True, alpha=0.3)

        fig.tight_layout()
        self.fig_trend = fig
        return fig, (ax1, ax2, ax3)

# ---------------------------------------------------------------------------
# FitFunction — math function library for trend fitting
# ---------------------------------------------------------------------------

class FitFunction:
    """Library of math functions for trend line fitting."""

    @staticmethod
    def linear(x, a, b):
        return a * x + b

    @staticmethod
    def exponential(x, a, b, c):
        return a * np.exp(b * (x - c))

    @staticmethod
    def exp_log(x, a, b, c, d):
        """Exponential-logistic (sigmoid-type)."""
        return a + (b - a) / (1 + np.exp(c * (x - d)))

    @staticmethod
    def logistic(x, a, b, c, d):
        """Generalised logistic."""
        return a + (b - a) / (1 + np.exp(c * (x - d)))

    @staticmethod
    def power_law(x, a, b, c):
        return a * (x - c) ** b

    @staticmethod
    def quadratic(x, a, b, c):
        return a * x ** 2 + b * x + c

    @staticmethod
    def cubic(x, a, b, c, d):
        return a * x ** 3 + b * x ** 2 + c * x + d

    @staticmethod
    def polynom(x, a, b, c, d, e):
        return a * x ** 4 + b * x ** 3 + c * x ** 2 + d * x + e

    FUNC_MAP = {
        "linear": (linear, 2),
        "exponential": (exponential, 3),
        "exp_log": (exp_log, 4),
        "logistic": (logistic, 4),
        "power_law": (power_law, 3),
        "quadratic": (quadratic, 3),
        "cubic": (cubic, 4),
        "polynom": (polynom, 5),
    }

    @classmethod
    def get(cls, name: str):
        """Get (function, n_params) for a named fit function."""
        if name not in cls.FUNC_MAP:
            raise ValueError(f"Unknown fit function: {name}. Options: {list(cls.FUNC_MAP)}")
        return cls.FUNC_MAP[name]


# ---------------------------------------------------------------------------
# FitTrend — trend line fitting for time series
# ---------------------------------------------------------------------------

class FitTrend:
    """Fit a trend line (linear, exponential, etc.) to a time series."""

    def __init__(
        self,
        series: pd.Series,
        line_style: str = "solid",
        line_color: str = "black",
        name: str = "Trend",
    ):
        self.original_data = series.copy().dropna()
        self.line_style = line_style
        self.line_color = line_color
        self.name = name
        self.fit = None
        self.fTrendDev = None
        self.TrendDev = None
        self.original_data_BU = None
        self.Fit_Info = {}
        self.fit_params = None
        self.fit_freq = 12

        # Infer frequency for period labelling
        freq = infer_frequency(self.original_data)
        if freq:
            self.fit_freq = {"D": 252, "W": 52, "M": 12, "Q": 4, "A": 1}.get(freq, 12)

    def FitData(
        self,
        FitFunc: str = "exponential",
        x1: str = None,
        x2: str = None,
        disp: bool = False,
    ):
        """Fit a trend line over date range [x1, x2]."""
        data = self.original_data.copy()
        if x1 is not None:
            d = GetClosestDateInIndex(data, x1)
            data = data.loc[d[0]:]
        if x2 is not None:
            d = GetClosestDateInIndex(data, x2)
            data = data.loc[:d[0]]

        x_vals = np.arange(len(data)).astype(float)
        y_vals = data.values.astype(float)
        fn, n_params = FitFunction.get(FitFunc)

        # Generate initial guesses
        p0 = [1.0] * n_params
        if FitFunc == "linear":
            p0 = [y_vals[-1] / x_vals[-1] if x_vals[-1] != 0 else 1, y_vals[0]]
        elif FitFunc in ("exponential", "power_law"):
            p0 = [1.0, 0.01, y_vals[0]]

        try:
            popt, _ = curve_fit(fn, x_vals, y_vals, p0=p0, maxfev=10000)
        except Exception as e:
            print(f"Fit failed for {FitFunc}: {e}")
            return None

        self.fit_params = popt
        self.fit = fn(x_vals, *popt)
        self.original_data_BU = data

        # Trend deviation
        trend_series = pd.Series(self.fit, index=data.index, name="Fitted_trend")
        dev = ((data / trend_series) - 1) * 100
        self.TrendDev = dev
        self.fTrendDev = trend_series

        self.Fit_Info = {
            "function": FitFunc,
            "params": popt,
            "range": (data.index[0], data.index[-1]),
        }

        if disp:
            self.ShowFit()
        return popt

    def ShowFit(
        self,
        yaxis: str = "linear",
        YLabel: str = "Value",
        title: str = "Trend Fit",
    ):
        """Plot original data with fitted trend, deviation panel, and bands."""
        if self.fit is None:
            raise ValueError("Run FitData() first.")

        fig = plt.figure(figsize=(14, 8))
        gs = GridSpec(3, 1, height_ratios=[2, 1, 1], hspace=0.15)

        # --- Top panel: data + trend ---
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(self.original_data.index, self.original_data, color="blue", linewidth=1.5, label="Data")
        ax1.plot(self.fTrendDev.index, self.fTrendDev, color="red", linewidth=1.5, label="Trend")
        ax1.set_yscale(yaxis)
        ax1.set_ylabel(YLabel)
        ax1.set_title(title)
        ax1.legend(loc="upper left", fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(calc_chart_xlims(self.fTrendDev.index))

        # ticks
        ytr, ytr_labs = EqualSpacedTicks(6, data=self.original_data, LogOrLin=yaxis)
        ax1.set_yticks(ytr)
        ax1.set_yticklabels(ytr_labs)

        # --- Middle: deviation ---
        ax2 = fig.add_subplot(gs[1])
        ax2.plot(self.TrendDev.index, self.TrendDev, color="purple", linewidth=1, label="Deviation (%)")
        ax2.axhline(0, color="gray", linewidth=0.5)
        ax2.set_ylabel("Dev %")
        ax2.legend(loc="upper left", fontsize=9)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(ax1.get_xlim())

        # --- Bottom: frequency of deviations ---
        ax3 = fig.add_subplot(gs[2])
        ax3.hist(self.TrendDev.dropna(), bins=50, color="gray", alpha=0.7, edgecolor="black")
        ax3.axvline(0, color="red", linestyle="--", linewidth=1)
        ax3.set_xlabel("Deviation (%)")
        ax3.set_ylabel("Frequency")
        ax3.grid(True, alpha=0.3)

        fig.tight_layout()
        self.fig_trend = fig
        return fig, (ax1, ax2, ax3)

# ---------------------------------------------------------------------------
# Peak location finder (interactive)
# ---------------------------------------------------------------------------

def get_peak_locs(
    data_series: pd.Series,
    yscale: str = "log",
    ylabel: str = "Bil. of U.S $",
    title: str = "M2 Monetary Aggregate USA",
    mode: str = "automan",
) -> pd.Series:
    """Identify peak locations. Modes: 'auto', 'manual', 'automan'."""
    if mode == "manual":
        peaks = []
    else:
        peaks = identify_peaks_and_troughs(data_series, x_range=datetime.timedelta(weeks=156))[0]

    def final_locs(data, x_locs):
        vals, index = [], []
        for loc in x_locs:
            d = GetClosestDateInIndex(data.index, searchDate=loc.strftime("%Y-%m-%d"))
            vals.append(d[0]), index.append(d[1])
        return pd.Series(vals, index=index, name="Peak locs, " + data.name).sort_index()

    if mode == "auto":
        peak_locs = peaks
    else:
        fig, ax1 = plt.subplots(figsize=(14, 6))
        ax1.plot(data_series.index, data_series, color="blue", linewidth=1.5, label=data_series.name)
        ax1.set_yscale(yscale)
        ax1.set_ylabel(ylabel)
        ax1.set_title(title)
        x_locs = peaks.to_list() if len(peaks) else []
        lines = []
        for date in peaks:
            l = ax1.axvline(x=date, color="black", linestyle="--", lw=1)
            lines.append(l)

        def onclick(event):
            nonlocal lines, x_locs
            if event.button == 3 and lines:
                lines.pop().remove()
            elif event.button == 1:
                l = ax1.axvline(x=event.xdata, color="r", ls="--", lw=1)
                lines.append(l)
                x_locs.append(mdates.num2date(event.xdata))
            fig.canvas.draw()

        fig.canvas.mpl_connect("button_press_event", onclick)
        plt.show()
        peak_locs = final_locs(data_series, x_locs)

    return peak_locs


# ---------------------------------------------------------------------------
# Seasonal adjustment wrappers
# ---------------------------------------------------------------------------

def seasonal_adjust(series: pd.Series, period: int = None, robust: bool = True) -> pd.Series:
    """STL-based seasonal adjustment."""
    if period is None:
        inferred = pd.infer_freq(series.index)
        period = {"M": 12, "Q": 4, "W": 52}.get(inferred, 12)
    stl = STL(series, period=period, robust=robust)
    res = stl.fit()
    return res.trend + res.resid


def plot_decomposition(series: pd.Series, period: int = None, robust: bool = True):
    """Plot STL decomposition."""
    stl = STL(series, period=period or 12, robust=robust)
    res = stl.fit()
    res.plot()
    plt.show()


def x13_seasonal_adjust(series: pd.Series, freq: int = None) -> pd.Series:
    """X-13ARIMA-SEATS seasonal adjustment (requires x13as binary)."""
    if freq is None:
        inferred = pd.infer_freq(series.index)
        freq = {"M": 12, "Q": 4, "W": 52}.get(inferred, 12)
    try:
        from statsmodels.tsa.x13 import x13_arima_analysis
        result = x13_arima_analysis(series, freq=freq)
        sa = result.seasadj if hasattr(result, "seasadj") else result.series
        sa = pd.Series(sa, index=series.index).rename(f"{series.name}_x13_seasadj")
        return sa
    except Exception as e:
        print(f"X-13 failed: {e}. Returning original series.")
        return series

# ---------------------------------------------------------------------------
# Peak location finder (interactive)
# ---------------------------------------------------------------------------

def get_peak_locs(
    data_series: pd.Series,
    yscale: str = "log",
    ylabel: str = "Bil. of U.S $",
    title: str = "M2 Monetary Aggregate USA",
    mode: str = "automan",
) -> pd.Series:
    """Identify peak locations. Modes: 'auto', 'manual', 'automan'."""
    if mode == "manual":
        peaks = []
    else:
        peaks = identify_peaks_and_troughs(data_series, x_range=datetime.timedelta(weeks=156))[0]

    def final_locs(data, x_locs):
        vals, index = [], []
        for loc in x_locs:
            d = GetClosestDateInIndex(data.index, searchDate=loc.strftime("%Y-%m-%d"))
            vals.append(d[0]), index.append(d[1])
        return pd.Series(vals, index=index, name="Peak locs, " + data.name).sort_index()

    if mode == "auto":
        peak_locs = peaks
    else:
        fig, ax1 = plt.subplots(figsize=(14, 6))
        ax1.plot(data_series.index, data_series, color="blue", linewidth=1.5, label=data_series.name)
        ax1.set_yscale(yscale)
        ax1.set_ylabel(ylabel)
        ax1.set_title(title)
        x_locs = peaks.to_list() if len(peaks) else []
        lines = []
        for date in peaks:
            l = ax1.axvline(x=date, color="black", linestyle="--", lw=1)
            lines.append(l)

        def onclick(event):
            nonlocal lines, x_locs
            if event.button == 3 and lines:
                lines.pop().remove()
            elif event.button == 1:
                l = ax1.axvline(x=event.xdata, color="r", ls="--", lw=1)
                lines.append(l)
                x_locs.append(mdates.num2date(event.xdata))
            fig.canvas.draw()

        fig.canvas.mpl_connect("button_press_event", onclick)
        plt.show()
        peak_locs = final_locs(data_series, x_locs)

    return peak_locs


# ---------------------------------------------------------------------------
# Seasonal adjustment wrappers
# ---------------------------------------------------------------------------

def seasonal_adjust(series: pd.Series, period: int = None, robust: bool = True) -> pd.Series:
    """STL-based seasonal adjustment."""
    if period is None:
        inferred = pd.infer_freq(series.index)
        period = {"M": 12, "Q": 4, "W": 52}.get(inferred, 12)
    stl = STL(series, period=period, robust=robust)
    res = stl.fit()
    return res.trend + res.resid


def plot_decomposition(series: pd.Series, period: int = None, robust: bool = True):
    """Plot STL decomposition."""
    stl = STL(series, period=period or 12, robust=robust)
    res = stl.fit()
    res.plot()
    plt.show()


def x13_seasonal_adjust(series: pd.Series, freq: int = None) -> pd.Series:
    """X-13ARIMA-SEATS seasonal adjustment (requires x13as binary)."""
    if freq is None:
        inferred = pd.infer_freq(series.index)
        freq = {"M": 12, "Q": 4, "W": 52}.get(inferred, 12)
    try:
        from statsmodels.tsa.x13 import x13_arima_analysis
        result = x13_arima_analysis(series, freq=freq)
        sa = result.seasadj if hasattr(result, "seasadj") else result.series
        sa = pd.Series(sa, index=series.index).rename(f"{series.name}_x13_seasadj")
        return sa
    except Exception as e:
        print(f"X-13 failed: {e}. Returning original series.")
        return series
