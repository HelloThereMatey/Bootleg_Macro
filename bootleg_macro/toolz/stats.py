"""
Bootleg toolz — pairwise correlation and statistical analysis.

Ported from MacroBackend/stats.py.  Uses bootleg_datafeed auxiliary
for frequency handling instead of the legacy freqDetermination class.
"""

from __future__ import annotations

from typing import Literal

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from scipy import stats as scipy_stats
from statsmodels.tsa.stattools import adfuller, kpss

from bootleg_datafeed.auxiliary import (
    FrequencyConverter,
    convert_to_standard_series,
    infer_frequency,
)
from .utilities import (
    EqualSpacedTicks,
    format_func,
    Line2D,
    save_path_dialog,
)


# ---------------------------------------------------------------------------
# Standalone functions
# ---------------------------------------------------------------------------

def qd_corr(series1: pd.Series, series2: pd.Series) -> float:
    """Quant-Dare correlation (no demeaning — sensitive to level)."""
    sp = (series1 * series2).sum()
    ss1 = (series1 ** 2).sum()
    ss2 = (series2 ** 2).sum()
    return float(sp / np.sqrt(ss1 * ss2))


def rolling_qd(series1: pd.Series, series2: pd.Series, window: int = 1) -> pd.Series:
    """Rolling Quant-Dare correlation."""
    if len(series1) != len(series2):
        raise ValueError("Series must have the same length")
    vals = []
    for i in range(window - 1, len(series1)):
        w1 = series1.iloc[i - window + 1 : i + 1]
        w2 = series2.iloc[i - window + 1 : i + 1]
        vals.append(qd_corr(w1, w2))
    return pd.Series(vals, index=series1.index[window - 1 :])


def rolling_corr(
    series1: pd.Series, series2: pd.Series, window: int, method: str = "pearson"
) -> pd.Series:
    """Rolling correlation (Pearson / Spearman / Kendall)."""
    common = series1.index.intersection(series2.index)
    s1, s2 = series1.loc[common], series2.loc[common]
    data = [
        s1.iloc[i - window : i].corr(s2.iloc[i - window : i], method=method)
        if i >= window else np.nan
        for i in range(len(common))
    ]
    return pd.Series(data, index=common)


def check_stationarity(series):
    """ADF + KPSS stationarity tests."""
    adf = adfuller(series, regression="ct")
    kpss_res = kpss(series, regression="ct")
    return {
        "ADF": {
            "statistic": adf[0],
            "p-value": adf[1],
            "critical_values": adf[4],
        },
        "KPSS": {
            "statistic": kpss_res[0],
            "p-value": kpss_res[1],
            "critical_values": kpss_res[3],
        },
    }


# ---------------------------------------------------------------------------
# Pair_stats
# ---------------------------------------------------------------------------

class Pair_stats:
    """Pairwise correlation analysis between two time series.

    Parameters
    ----------
    series1, series2 : pd.Series
        Input time series.
    windows : list of int, default [30, 90, 180, 365]
        Rolling window lengths.
    corr_method : {"pearson", "spearman", "kendall"}
    ser1_title, ser2_title : str, optional
        Display names.
    watchlist_meta : pd.DataFrame, optional
        Metadata DataFrame for unit labels.
    downsample_to : str, optional
        Pandas frequency to resample both series to (e.g. "W", "M").
    """

    FREQ_REP = {"D": "Daily", "W": "Weekly", "M": "Monthly", "Q": "Quarterly", "Y": "Yearly"}

    def __init__(
        self,
        series1: pd.Series,
        series2: pd.Series,
        windows: list = None,
        corr_method: str = "pearson",
        ser1_title: str = "",
        ser2_title: str = "",
        watchlist_meta: pd.DataFrame = pd.DataFrame(),
        downsample_to: str = "",
    ):
        if windows is None:
            windows = [30, 90, 180, 365]

        self.series1 = series1.copy()
        self.series2 = series2.copy()
        self.corr_method = corr_method
        self.downsample_to = downsample_to
        self.windows = windows
        self.watchlist_meta = watchlist_meta if not watchlist_meta.empty else None

        self.ser1_title = ser1_title or (series1.name or "Series1")
        self.ser2_title = ser2_title or (series2.name or "Series2")
        self.series1.name = self.ser1_title
        self.series2.name = self.ser2_title

        self.frequency = ""
        self.per_in_year = 252  # fallback

        if self.check_input_series() is None:
            raise ValueError("Could not align input series.")

        self.name = f"{self.ser1_title} and {self.ser2_title}"
        self.data = self.returns_df()
        self.windows.append(min(len(self.series1), len(self.series2)) - 2)
        self.rolling_stats(corr_method=corr_method)


# ---------------------------------------------------------------------------
# Pair_stats
# ---------------------------------------------------------------------------

class Pair_stats:
    """Pairwise correlation analysis between two time series.

    Parameters
    ----------
    series1, series2 : pd.Series
        Input time series.
    windows : list of int, default [30, 90, 180, 365]
        Rolling window lengths.
    corr_method : {"pearson", "spearman", "kendall"}
    ser1_title, ser2_title : str, optional
        Display names.
    watchlist_meta : pd.DataFrame, optional
        Metadata DataFrame for unit labels.
    downsample_to : str, optional
        Pandas frequency to resample both series to (e.g. "W", "M").
    """

    FREQ_REP = {"D": "Daily", "W": "Weekly", "M": "Monthly", "Q": "Quarterly", "Y": "Yearly"}

    def __init__(
        self,
        series1: pd.Series,
        series2: pd.Series,
        windows: list = None,
        corr_method: str = "pearson",
        ser1_title: str = "",
        ser2_title: str = "",
        watchlist_meta: pd.DataFrame = pd.DataFrame(),
        downsample_to: str = "",
    ):
        if windows is None:
            windows = [30, 90, 180, 365]

        self.series1 = series1.copy()
        self.series2 = series2.copy()
        self.corr_method = corr_method
        self.downsample_to = downsample_to
        self.windows = windows
        self.watchlist_meta = watchlist_meta if not watchlist_meta.empty else None

        self.ser1_title = ser1_title or (series1.name or "Series1")
        self.ser2_title = ser2_title or (series2.name or "Series2")
        self.series1.name = self.ser1_title
        self.series2.name = self.ser2_title

        self.frequency = ""
        self.per_in_year = 252  # fallback

        if self.check_input_series() is None:
            raise ValueError("Could not align input series.")

        self.name = f"{self.ser1_title} and {self.ser2_title}"
        self.data = self.returns_df()
        self.windows.append(min(len(self.series1), len(self.series2)) - 2)
        self.rolling_stats(corr_method=corr_method)


    def check_input_series(self):
        """Align both series: ensure Series type, same frequency, same length."""
        s1 = convert_to_standard_series(self.series1)
        s2 = convert_to_standard_series(self.series2)

        f1 = infer_frequency(s1)
        f2 = infer_frequency(s2)

        if f1 is None and f2 is None:
            print("Could not infer frequency for either series.")
            return None

        std_map = {"D": 0, "W": 1, "M": 2, "Q": 3, "A": 4}
        # Use FrequencyConverter for standardisation
        f1_s = FrequencyConverter.standardize(f1 or "M")
        f2_s = FrequencyConverter.standardize(f2 or "M")

        if f1_s != f2_s:
            print(f"Frequency mismatch ({f1_s} vs {f2_s}), resampling...")
            r1, r2 = std_map.get(f1_s, 2), std_map.get(f2_s, 2)
            if r1 > r2:
                s2 = s2.resample(f1_s).last()
            else:
                s1 = s1.resample(f2_s).last()

        if self.downsample_to:
            ds = FrequencyConverter.standardize(self.downsample_to)
            s1 = s1.resample(ds).last()
            s2 = s2.resample(ds).last()

        # Trim to common date range
        common_start = max(s1.index.min(), s2.index.min())
        common_end = min(s1.index.max(), s2.index.max())
        self.series1 = s1.loc[common_start:common_end]
        self.series2 = s2.loc[common_start:common_end]

        if len(self.series1) < 3 or len(self.series2) < 3:
            print("Less than 3 observations after alignment.")
            return None

        self.frequency = FrequencyConverter.standardize(infer_frequency(self.series1) or "M")
        self.per_in_year = {"D": 252, "W": 52, "M": 12, "Q": 4, "A": 1}.get(self.frequency, 252)
        print(f"Series frequency: {self.frequency}, periods in year: {self.per_in_year}")
        return 1

    def returns_df(self):
        """Calculate log returns, YoY log returns, and percentage returns."""
        df = pd.concat([self.series1, self.series2], axis=1)
        print(
            f"Calculating returns: {self.ser1_title}, {self.ser2_title}, "
            f"freq={self.frequency}, periods/year={self.per_in_year}"
        )
        df["ret_" + self.ser1_title] = np.log(
            df[self.series1.name] / df[self.series1.name].shift(1)
        )
        df["ret_" + self.ser2_title] = np.log(
            df[self.series2.name] / df[self.series2.name].shift(1)
        )
        df["retYoY_" + self.ser1_title] = np.log(
            df[self.series1.name] / df[self.series1.name].shift(self.per_in_year)
        )
        df["retYoY_" + self.ser2_title] = np.log(
            df[self.series2.name] / df[self.series2.name].shift(self.per_in_year)
        )
        df["retPct_" + self.ser1_title] = df[self.series1.name].pct_change()
        df["retPct_" + self.ser2_title] = df[self.series2.name].pct_change()
        df.dropna(inplace=True)
        return df


    def check_input_series(self):
        """Align both series: ensure Series type, same frequency, same length."""
        s1 = convert_to_standard_series(self.series1)
        s2 = convert_to_standard_series(self.series2)

        f1 = infer_frequency(s1)
        f2 = infer_frequency(s2)

        if f1 is None and f2 is None:
            print("Could not infer frequency for either series.")
            return None

        std_map = {"D": 0, "W": 1, "M": 2, "Q": 3, "A": 4}
        # Use FrequencyConverter for standardisation
        f1_s = FrequencyConverter.standardize(f1 or "M")
        f2_s = FrequencyConverter.standardize(f2 or "M")

        if f1_s != f2_s:
            print(f"Frequency mismatch ({f1_s} vs {f2_s}), resampling...")
            r1, r2 = std_map.get(f1_s, 2), std_map.get(f2_s, 2)
            if r1 > r2:
                s2 = s2.resample(f1_s).last()
            else:
                s1 = s1.resample(f2_s).last()

        if self.downsample_to:
            ds = FrequencyConverter.standardize(self.downsample_to)
            s1 = s1.resample(ds).last()
            s2 = s2.resample(ds).last()

        # Trim to common date range
        common_start = max(s1.index.min(), s2.index.min())
        common_end = min(s1.index.max(), s2.index.max())
        self.series1 = s1.loc[common_start:common_end]
        self.series2 = s2.loc[common_start:common_end]

        if len(self.series1) < 3 or len(self.series2) < 3:
            print("Less than 3 observations after alignment.")
            return None

        self.frequency = FrequencyConverter.standardize(infer_frequency(self.series1) or "M")
        self.per_in_year = {"D": 252, "W": 52, "M": 12, "Q": 4, "A": 1}.get(self.frequency, 252)
        print(f"Series frequency: {self.frequency}, periods in year: {self.per_in_year}")
        return 1

    def returns_df(self):
        """Calculate log returns, YoY log returns, and percentage returns."""
        df = pd.concat([self.series1, self.series2], axis=1)
        print(
            f"Calculating returns: {self.ser1_title}, {self.ser2_title}, "
            f"freq={self.frequency}, periods/year={self.per_in_year}"
        )
        df["ret_" + self.ser1_title] = np.log(
            df[self.series1.name] / df[self.series1.name].shift(1)
        )
        df["ret_" + self.ser2_title] = np.log(
            df[self.series2.name] / df[self.series2.name].shift(1)
        )
        df["retYoY_" + self.ser1_title] = np.log(
            df[self.series1.name] / df[self.series1.name].shift(self.per_in_year)
        )
        df["retYoY_" + self.ser2_title] = np.log(
            df[self.series2.name] / df[self.series2.name].shift(self.per_in_year)
        )
        df["retPct_" + self.ser1_title] = df[self.series1.name].pct_change()
        df["retPct_" + self.ser2_title] = df[self.series2.name].pct_change()
        df.dropna(inplace=True)
        return df


    def rolling_stats(self, corr_method: str = "pearson"):
        """Calculate full-sample and rolling correlations, betas, alphas."""
        name = self.ser1_title + "_" + self.ser2_title
        d = self.data

        self.full_corr = d[self.series1.name].corr(d[self.series2.name], method=corr_method)
        self.full_RetCorr = d["ret_" + self.ser1_title].corr(d["ret_" + self.ser2_title], method=corr_method)
        self.full_YoYRetCorr = d["retYoY_" + self.ser1_title].corr(d["retYoY_" + self.ser2_title], method=corr_method)
        self.full_PctRetCorr = d["retPct_" + self.ser1_title].corr(d["retPct_" + self.ser2_title], method=corr_method)
        self.full_qdCorr = qd_corr(d["ret_" + self.ser1_title], d["ret_" + self.ser2_title])

        print(
            f"Full corrs — price:{self.full_corr:.4f}  ret:{self.full_RetCorr:.4f}  "
            f"YoY:{self.full_YoYRetCorr:.4f}  pct:{self.full_PctRetCorr:.4f}  "
            f"qd:{self.full_qdCorr:.4f}"
        )

        for w in self.windows:
            d[name + "_Corr_" + str(w)] = rolling_corr(
                d[self.series1.name], d[self.series2.name], w, method=corr_method
            )
            d[name + "_RetCorr_" + str(w)] = rolling_corr(
                d["ret_" + self.ser1_title], d["ret_" + self.ser2_title], w, method=corr_method
            )
            d[name + "_retYoY_" + str(w)] = rolling_corr(
                d["retYoY_" + self.ser1_title], d["retYoY_" + self.ser2_title], w, method=corr_method
            )
            d[name + "_PctRetCorr_" + str(w)] = rolling_corr(
                d["retPct_" + self.ser1_title], d["retPct_" + self.ser2_title], w, method=corr_method
            )
            try:
                d[name + "_qdCorr_" + str(w)] = rolling_qd(
                    d["ret_" + self.ser1_title], d["ret_" + self.ser2_title], w
                )
            except Exception as exc:
                print(f"qdCorr({w}) failed: {exc}")

            d[name + "_beta_" + str(w)] = d[name + "_Corr_" + str(w)] * (
                d["ret_" + self.ser1_title].rolling(window=w).std()
                / d["ret_" + self.ser2_title].rolling(window=w).std()
            )
            d[name + "_alpha_" + str(w)] = (
                d[self.series1.name].rolling(window=w).mean()
                - d[name + "_beta_" + str(w)] * d[self.series2.name].rolling(window=w).mean()
            )

    # ------------------------------------------------------------------
    # Plotting helpers
    # ------------------------------------------------------------------


    def rolling_stats(self, corr_method: str = "pearson"):
        """Calculate full-sample and rolling correlations, betas, alphas."""
        name = self.ser1_title + "_" + self.ser2_title
        d = self.data

        self.full_corr = d[self.series1.name].corr(d[self.series2.name], method=corr_method)
        self.full_RetCorr = d["ret_" + self.ser1_title].corr(d["ret_" + self.ser2_title], method=corr_method)
        self.full_YoYRetCorr = d["retYoY_" + self.ser1_title].corr(d["retYoY_" + self.ser2_title], method=corr_method)
        self.full_PctRetCorr = d["retPct_" + self.ser1_title].corr(d["retPct_" + self.ser2_title], method=corr_method)
        self.full_qdCorr = qd_corr(d["ret_" + self.ser1_title], d["ret_" + self.ser2_title])

        print(
            f"Full corrs — price:{self.full_corr:.4f}  ret:{self.full_RetCorr:.4f}  "
            f"YoY:{self.full_YoYRetCorr:.4f}  pct:{self.full_PctRetCorr:.4f}  "
            f"qd:{self.full_qdCorr:.4f}"
        )

        for w in self.windows:
            d[name + "_Corr_" + str(w)] = rolling_corr(
                d[self.series1.name], d[self.series2.name], w, method=corr_method
            )
            d[name + "_RetCorr_" + str(w)] = rolling_corr(
                d["ret_" + self.ser1_title], d["ret_" + self.ser2_title], w, method=corr_method
            )
            d[name + "_retYoY_" + str(w)] = rolling_corr(
                d["retYoY_" + self.ser1_title], d["retYoY_" + self.ser2_title], w, method=corr_method
            )
            d[name + "_PctRetCorr_" + str(w)] = rolling_corr(
                d["retPct_" + self.ser1_title], d["retPct_" + self.ser2_title], w, method=corr_method
            )
            try:
                d[name + "_qdCorr_" + str(w)] = rolling_qd(
                    d["ret_" + self.ser1_title], d["ret_" + self.ser2_title], w
                )
            except Exception as exc:
                print(f"qdCorr({w}) failed: {exc}")

            d[name + "_beta_" + str(w)] = d[name + "_Corr_" + str(w)] * (
                d["ret_" + self.ser1_title].rolling(window=w).std()
                / d["ret_" + self.ser2_title].rolling(window=w).std()
            )
            d[name + "_alpha_" + str(w)] = (
                d[self.series1.name].rolling(window=w).mean()
                - d[name + "_beta_" + str(w)] * d[self.series2.name].rolling(window=w).mean()
            )

    # ------------------------------------------------------------------
    # Plotting helpers
    # ------------------------------------------------------------------


    def plot_log_returns(self, downsample_to: str = ""):
        """Bar plot of log returns (single chart)."""
        cols = ["ret_" + self.ser1_title, "ret_" + self.ser2_title]
        two_series = self.data[cols]
        freq_str = self.frequency
        if downsample_to:
            two_series = two_series.resample(downsample_to).last()
            freq_str = self.FREQ_REP.get(downsample_to, downsample_to)

        fig, ax = plt.subplots(figsize=(14, 6))
        tdelta = two_series.index[1] - two_series.index[0]
        w = ax.get_window_extent().width / len(two_series) / 2
        ax.bar(two_series.index - tdelta / 4, two_series[cols[0]], width=w, label=self.ser1_title)
        ax.bar(two_series.index + tdelta / 4, two_series[cols[1]], width=w, label=self.ser2_title)
        ax.set_title("Log Returns: " + self.ser1_title + " vs " + self.ser2_title)
        ax.set_ylabel("Log Returns")
        ax.legend()
        ax.text(0.01, 1.02, "Data freq: " + self.frequency, transform=ax.transAxes)
        ax.margins(0.01, 0.03)
        self.returns_plot = fig
        return fig, ax

    def plot_log_returns_alt(
        self, downsample_to: str = "", color1: str = "b", color2: str = "r", YoY: bool = False
    ):
        """Bar plot of log returns (separate sub-panels)."""
        if YoY:
            cols = ["retYoY_" + self.ser1_title, "retYoY_" + self.ser2_title]
            title = "YoY Log Returns: " + self.ser1_title + " vs " + self.ser2_title
        else:
            cols = ["ret_" + self.ser1_title, "ret_" + self.ser2_title]
            title = "Log Returns: " + self.ser1_title + " vs " + self.ser2_title

        two_series = self.data[cols]
        freq_str = self.frequency
        if downsample_to:
            two_series = two_series.resample(downsample_to).last()
            freq_str = self.FREQ_REP.get(downsample_to, downsample_to)

        fig, axes = plt.subplots(2, 1, figsize=(14, 6))
        w = axes[0].get_window_extent().width / len(two_series) * 2
        axes[0].bar(two_series.index, two_series[cols[0]], width=w, label=self.ser1_title, color=color1)
        axes[1].bar(two_series.index, two_series[cols[1]], width=w, label=self.ser2_title, color=color2)
        axes[0].set_title(title)
        for ax in axes:
            ax.set_axisbelow(True)
            ax.legend(fontsize=11, frameon=True)
            ax.set_ylabel("Log Returns")
            ax.margins(0.01, 0.03)
        axes[0].text(0.01, 1.06, "Data freq: " + freq_str, transform=axes[0].transAxes)
        self.returns_plot = fig
        return fig, axes

    def plot_series(self, color1: str = "black", color2: str = "blue"):
        """Dual-axis plot of the two price series (inline twinx, no TwoAxisFig)."""
        fig, ax1 = plt.subplots(figsize=(14, 6))
        ax1.plot(self.series1.index, self.series1, color=color1, linewidth=2.25, label=self.ser1_title)
        ax1.set_yscale("log")
        ax1.set_ylabel(self.ser1_title)
        ax1.legend(loc="upper left")
        ax1.tick_params(axis="y", labelcolor=color1)

        ax2 = ax1.twinx()
        ax2.plot(self.series2.index, self.series2, color=color2, linewidth=2.25, label=self.ser2_title)
        ax2.set_yscale("log")
        ax2.set_ylabel(self.ser2_title)
        ax2.legend(loc="upper right")
        ax2.tick_params(axis="y", labelcolor=color2)

        fig.suptitle(self.name)
        self.fig1 = fig
        return fig, (ax1, ax2)


    def plot_log_returns(self, downsample_to: str = ""):
        """Bar plot of log returns (single chart)."""
        cols = ["ret_" + self.ser1_title, "ret_" + self.ser2_title]
        two_series = self.data[cols]
        freq_str = self.frequency
        if downsample_to:
            two_series = two_series.resample(downsample_to).last()
            freq_str = self.FREQ_REP.get(downsample_to, downsample_to)

        fig, ax = plt.subplots(figsize=(14, 6))
        tdelta = two_series.index[1] - two_series.index[0]
        w = ax.get_window_extent().width / len(two_series) / 2
        ax.bar(two_series.index - tdelta / 4, two_series[cols[0]], width=w, label=self.ser1_title)
        ax.bar(two_series.index + tdelta / 4, two_series[cols[1]], width=w, label=self.ser2_title)
        ax.set_title("Log Returns: " + self.ser1_title + " vs " + self.ser2_title)
        ax.set_ylabel("Log Returns")
        ax.legend()
        ax.text(0.01, 1.02, "Data freq: " + self.frequency, transform=ax.transAxes)
        ax.margins(0.01, 0.03)
        self.returns_plot = fig
        return fig, ax

    def plot_log_returns_alt(
        self, downsample_to: str = "", color1: str = "b", color2: str = "r", YoY: bool = False
    ):
        """Bar plot of log returns (separate sub-panels)."""
        if YoY:
            cols = ["retYoY_" + self.ser1_title, "retYoY_" + self.ser2_title]
            title = "YoY Log Returns: " + self.ser1_title + " vs " + self.ser2_title
        else:
            cols = ["ret_" + self.ser1_title, "ret_" + self.ser2_title]
            title = "Log Returns: " + self.ser1_title + " vs " + self.ser2_title

        two_series = self.data[cols]
        freq_str = self.frequency
        if downsample_to:
            two_series = two_series.resample(downsample_to).last()
            freq_str = self.FREQ_REP.get(downsample_to, downsample_to)

        fig, axes = plt.subplots(2, 1, figsize=(14, 6))
        w = axes[0].get_window_extent().width / len(two_series) * 2
        axes[0].bar(two_series.index, two_series[cols[0]], width=w, label=self.ser1_title, color=color1)
        axes[1].bar(two_series.index, two_series[cols[1]], width=w, label=self.ser2_title, color=color2)
        axes[0].set_title(title)
        for ax in axes:
            ax.set_axisbelow(True)
            ax.legend(fontsize=11, frameon=True)
            ax.set_ylabel("Log Returns")
            ax.margins(0.01, 0.03)
        axes[0].text(0.01, 1.06, "Data freq: " + freq_str, transform=axes[0].transAxes)
        self.returns_plot = fig
        return fig, axes

    def plot_series(self, color1: str = "black", color2: str = "blue"):
        """Dual-axis plot of the two price series (inline twinx, no TwoAxisFig)."""
        fig, ax1 = plt.subplots(figsize=(14, 6))
        ax1.plot(self.series1.index, self.series1, color=color1, linewidth=2.25, label=self.ser1_title)
        ax1.set_yscale("log")
        ax1.set_ylabel(self.ser1_title)
        ax1.legend(loc="upper left")
        ax1.tick_params(axis="y", labelcolor=color1)

        ax2 = ax1.twinx()
        ax2.plot(self.series2.index, self.series2, color=color2, linewidth=2.25, label=self.ser2_title)
        ax2.set_yscale("log")
        ax2.set_ylabel(self.ser2_title)
        ax2.legend(loc="upper right")
        ax2.tick_params(axis="y", labelcolor=color2)

        fig.suptitle(self.name)
        self.fig1 = fig
        return fig, (ax1, ax2)


    def plot_corrs(
        self,
        trim_windows: int = 0,
        plot_wrong_way: bool = True,
        percentage_ret_corr: bool = False,
        qd_corr: bool = False,
        YoY_retCorr: bool = False,
    ):
        """Plot rolling correlations for selected types."""
        name = self.ser1_title + "_" + self.ser2_title
        corr_types = [("RetCorr", name + "_RetCorr_")]
        if plot_wrong_way:
            corr_types.append(("Corr", name + "_Corr_"))
        if percentage_ret_corr:
            corr_types.append(("PctRetCorr", name + "_PctRetCorr_"))
        if qd_corr:
            corr_types.append(("qdCorr", name + "_qdCorr_"))
        if YoY_retCorr:
            corr_types.append(("retYoY", name + "_retYoY_"))

        fig, axes = plt.subplots(len(corr_types), 1, figsize=(14, 4 * len(corr_types)), squeeze=False)
        for ax, (ct, prefix) in zip(axes.flat, corr_types):
            full_key = "full_" + ct
            full_val = getattr(self, full_key, None)
            for w in self.windows:
                col = prefix + str(w)
                if col in self.data.columns:
                    label = str(w) + ("  (full={:.3f})".format(full_val) if full_val is not None else "")
                    ax.plot(self.data.index, self.data[col], label=label, linewidth=0.8)

            if full_val is not None:
                ax.axhline(y=full_val, color="red", linestyle="--", linewidth=0.8)
            ax.set_title(ct)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
        fig.tight_layout()
        self.corr_plot = fig
        return fig, axes

    def plot_lin_reg(self, yoy: bool = False, y_lim=None, x_lim=None):
        """Scatter plot with linear regression fit on returns."""
        if yoy:
            x = self.data["retYoY_" + self.ser1_title]
            y = self.data["retYoY_" + self.ser2_title]
        else:
            x = self.data["ret_" + self.ser1_title]
            y = self.data["ret_" + self.ser2_title]

        mask = x.notna() & y.notna()
        x, y = x[mask], y[mask]
        slope, intercept, r, p, _ = scipy_stats.linregress(x, y)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(x, y, alpha=0.6, s=10)
        x_line = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_line, slope * x_line + intercept, "r-", label=f"y={slope:.4f}x+{intercept:.4f}")
        ax.set_xlabel(self.ser1_title + (" YoY" if yoy else "") + " returns")
        ax.set_ylabel(self.ser2_title + (" YoY" if yoy else "") + " returns")
        ax.set_title(f"R² = {r**2:.4f},  p = {p:.4e}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        if y_lim:
            ax.set_ylim(y_lim)
        if x_lim:
            ax.set_xlim(x_lim)
        fig.tight_layout()
        self.lineRegPlot = fig
        return fig, ax


    def plot_corrs(
        self,
        trim_windows: int = 0,
        plot_wrong_way: bool = True,
        percentage_ret_corr: bool = False,
        qd_corr: bool = False,
        YoY_retCorr: bool = False,
    ):
        """Plot rolling correlations for selected types."""
        name = self.ser1_title + "_" + self.ser2_title
        corr_types = [("RetCorr", name + "_RetCorr_")]
        if plot_wrong_way:
            corr_types.append(("Corr", name + "_Corr_"))
        if percentage_ret_corr:
            corr_types.append(("PctRetCorr", name + "_PctRetCorr_"))
        if qd_corr:
            corr_types.append(("qdCorr", name + "_qdCorr_"))
        if YoY_retCorr:
            corr_types.append(("retYoY", name + "_retYoY_"))

        fig, axes = plt.subplots(len(corr_types), 1, figsize=(14, 4 * len(corr_types)), squeeze=False)
        for ax, (ct, prefix) in zip(axes.flat, corr_types):
            full_key = "full_" + ct
            full_val = getattr(self, full_key, None)
            for w in self.windows:
                col = prefix + str(w)
                if col in self.data.columns:
                    label = str(w) + ("  (full={:.3f})".format(full_val) if full_val is not None else "")
                    ax.plot(self.data.index, self.data[col], label=label, linewidth=0.8)

            if full_val is not None:
                ax.axhline(y=full_val, color="red", linestyle="--", linewidth=0.8)
            ax.set_title(ct)
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
        fig.tight_layout()
        self.corr_plot = fig
        return fig, axes

    def plot_lin_reg(self, yoy: bool = False, y_lim=None, x_lim=None):
        """Scatter plot with linear regression fit on returns."""
        if yoy:
            x = self.data["retYoY_" + self.ser1_title]
            y = self.data["retYoY_" + self.ser2_title]
        else:
            x = self.data["ret_" + self.ser1_title]
            y = self.data["ret_" + self.ser2_title]

        mask = x.notna() & y.notna()
        x, y = x[mask], y[mask]
        slope, intercept, r, p, _ = scipy_stats.linregress(x, y)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(x, y, alpha=0.6, s=10)
        x_line = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_line, slope * x_line + intercept, "r-", label=f"y={slope:.4f}x+{intercept:.4f}")
        ax.set_xlabel(self.ser1_title + (" YoY" if yoy else "") + " returns")
        ax.set_ylabel(self.ser2_title + (" YoY" if yoy else "") + " returns")
        ax.set_title(f"R² = {r**2:.4f},  p = {p:.4e}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        if y_lim:
            ax.set_ylim(y_lim)
        if x_lim:
            ax.set_xlim(x_lim)
        fig.tight_layout()
        self.lineRegPlot = fig
        return fig, ax


    def find_optimal_lag(self, n: int):
        """Brute-force lag search on raw prices (not recommended for financial data)."""
        best_lag, best_corr = 0, -1
        lag_series = []
        for lag in range(0, n + 1):
            s2_shifted = self.series2.shift(lag)
            common = pd.concat([self.series1, s2_shifted], axis=1).dropna()
            c = common.iloc[:, 0].corr(common.iloc[:, 1])
            lag_series.append((lag, c))
            if abs(c) > best_corr:
                best_corr, best_lag = abs(c), lag

        for lag in range(-n, 0):
            s1_shifted = self.series1.shift(-lag)
            common = pd.concat([s1_shifted, self.series2], axis=1).dropna()
            c = common.iloc[:, 0].corr(common.iloc[:, 1])
            lag_series.append((lag, c))
            if abs(c) > best_corr:
                best_corr, best_lag = abs(c), lag

        self.lag_test = pd.DataFrame(lag_series, columns=["lag", "corr"]).set_index("lag")
        return best_lag, best_corr

    def find_optimal_ret_lag(self, n: int, yoy: bool = False, increment: int = 1):
        """Lag search on returns with visualisation."""
        if yoy:
            r1 = np.log(self.series1 / self.series1.shift(self.per_in_year))
            r2 = np.log(self.series2 / self.series2.shift(self.per_in_year))
        else:
            r1 = np.log(self.series1 / self.series1.shift(1))
            r2 = np.log(self.series2 / self.series2.shift(1))

        r1, r2 = r1.dropna(), r2.dropna()
        min_len = min(len(r1), len(r2))
        r1, r2 = r1.iloc[-min_len:], r2.iloc[-min_len:]

        lags = list(range(-n, n + 1, increment))
        corrs = []
        shift_matrix = {}
        for lag in lags:
            if lag >= 0:
                shifted = r2.shift(lag)
            else:
                shifted = r2.shift(lag)
            common = pd.concat([r1, shifted], axis=1).dropna()
            shift_matrix[lag] = shifted
            corrs.append(common.iloc[:, 0].corr(common.iloc[:, 1]))

        opt_idx = max(range(len(corrs)), key=lambda i: abs(corrs[i]))
        opt_lag, opt_corr = lags[opt_idx], corrs[opt_idx]

        # Plot 1 — overlaid shifts
        fig1, ax1 = plt.subplots(figsize=(14, 4))
        for lag in [opt_lag, 0]:
            if lag in shift_matrix:
                s = shift_matrix[lag].dropna()
                ax1.plot(s.index, s / s.max(), label=f"lag={lag}", linewidth=0.8)
        r1_norm = r1 / r1.max()
        ax1.plot(r1_norm.index, r1_norm, label="series1 (no lag)", linewidth=1.2, color="black")
        ax1.legend()
        ax1.set_title(f"Optimal lag: {opt_lag}  (corr={opt_corr:.4f})")
        fig1.tight_layout()
        self.lag_plot = fig1

        # Plot 2 — corr vs lag
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.plot(lags, corrs, marker="o", linewidth=0.8, markersize=3)
        ax2.axvline(opt_lag, color="r", linestyle="--", linewidth=0.8)
        ax2.axhline(0, color="gray", linewidth=0.5)
        ax2.set_xlabel("Lag")
        ax2.set_ylabel("Correlation")
        ax2.set_title("Correlation vs lag shift")
        fig2.tight_layout()
        self.lag_plot2 = fig2

        self.ret_lag_test = pd.DataFrame(dict(lag=lags, corr=corrs)).set_index("lag")
        self.shiftmatrix = pd.DataFrame(shift_matrix)
        return opt_lag, opt_corr

    def bm_scatterMatrix(self, yoy: bool = False):
        """Scatter matrix with KDE on diagonal."""
        if yoy:
            df = self.data[["retYoY_" + self.ser1_title, "retYoY_" + self.ser2_title]].dropna()
        else:
            df = self.data[["ret_" + self.ser1_title, "ret_" + self.ser2_title]].dropna()

        from scipy.stats import gaussian_kde
        n = len(df.columns)
        fig, axes = plt.subplots(n, n, figsize=(10, 10))
        for i, col_i in enumerate(df.columns):
            for j, col_j in enumerate(df.columns):
                ax = axes[i, j]
                if i == j:
                    kde = gaussian_kde(df[col_i].dropna())
                    xs = np.linspace(df[col_i].min(), df[col_i].max(), 100)
                    ax.plot(xs, kde(xs), color="blue", linewidth=1.5)
                    peak = xs[np.argmax(kde(xs))]
                    ax.axvline(peak, color="r", linestyle="--", linewidth=0.8)
                else:
                    ax.scatter(df[col_j], df[col_i], alpha=0.5, s=10)
                if i == n - 1:
                    ax.set_xlabel(col_j, fontsize=9)
                if j == 0:
                    ax.set_ylabel(col_i, fontsize=9)
                ax.xaxis.set_major_formatter(FuncFormatter(format_func))
                if i == len(df.columns) - 1:
                    ax.xaxis.set_major_formatter(FuncFormatter(format_func))

        fig.suptitle("Scatter Matrix" + (" (YoY)" if yoy else ""), fontsize=12)
        fig.tight_layout()
        fig.subplots_adjust(top=0.92)
        self.scatMatPlot = fig
        return fig, axes

    def find_optimal_lag(self, n: int):
        """Brute-force lag search on raw prices (not recommended for financial data)."""
        best_lag, best_corr = 0, -1
        lag_series = []
        for lag in range(0, n + 1):
            s2_shifted = self.series2.shift(lag)
            common = pd.concat([self.series1, s2_shifted], axis=1).dropna()
            c = common.iloc[:, 0].corr(common.iloc[:, 1])
            lag_series.append((lag, c))
            if abs(c) > best_corr:
                best_corr, best_lag = abs(c), lag

        for lag in range(-n, 0):
            s1_shifted = self.series1.shift(-lag)
            common = pd.concat([s1_shifted, self.series2], axis=1).dropna()
            c = common.iloc[:, 0].corr(common.iloc[:, 1])
            lag_series.append((lag, c))
            if abs(c) > best_corr:
                best_corr, best_lag = abs(c), lag

        self.lag_test = pd.DataFrame(lag_series, columns=["lag", "corr"]).set_index("lag")
        return best_lag, best_corr

    def find_optimal_ret_lag(self, n: int, yoy: bool = False, increment: int = 1):
        """Lag search on returns with visualisation."""
        if yoy:
            r1 = np.log(self.series1 / self.series1.shift(self.per_in_year))
            r2 = np.log(self.series2 / self.series2.shift(self.per_in_year))
        else:
            r1 = np.log(self.series1 / self.series1.shift(1))
            r2 = np.log(self.series2 / self.series2.shift(1))

        r1, r2 = r1.dropna(), r2.dropna()
        min_len = min(len(r1), len(r2))
        r1, r2 = r1.iloc[-min_len:], r2.iloc[-min_len:]

        lags = list(range(-n, n + 1, increment))
        corrs = []
        shift_matrix = {}
        for lag in lags:
            if lag >= 0:
                shifted = r2.shift(lag)
            else:
                shifted = r2.shift(lag)
            common = pd.concat([r1, shifted], axis=1).dropna()
            shift_matrix[lag] = shifted
            corrs.append(common.iloc[:, 0].corr(common.iloc[:, 1]))

        opt_idx = max(range(len(corrs)), key=lambda i: abs(corrs[i]))
        opt_lag, opt_corr = lags[opt_idx], corrs[opt_idx]

        # Plot 1 — overlaid shifts
        fig1, ax1 = plt.subplots(figsize=(14, 4))
        for lag in [opt_lag, 0]:
            if lag in shift_matrix:
                s = shift_matrix[lag].dropna()
                ax1.plot(s.index, s / s.max(), label=f"lag={lag}", linewidth=0.8)
        r1_norm = r1 / r1.max()
        ax1.plot(r1_norm.index, r1_norm, label="series1 (no lag)", linewidth=1.2, color="black")
        ax1.legend()
        ax1.set_title(f"Optimal lag: {opt_lag}  (corr={opt_corr:.4f})")
        fig1.tight_layout()
        self.lag_plot = fig1

        # Plot 2 — corr vs lag
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.plot(lags, corrs, marker="o", linewidth=0.8, markersize=3)
        ax2.axvline(opt_lag, color="r", linestyle="--", linewidth=0.8)
        ax2.axhline(0, color="gray", linewidth=0.5)
        ax2.set_xlabel("Lag")
        ax2.set_ylabel("Correlation")
        ax2.set_title("Correlation vs lag shift")
        fig2.tight_layout()
        self.lag_plot2 = fig2

        self.ret_lag_test = pd.DataFrame(dict(lag=lags, corr=corrs)).set_index("lag")
        self.shiftmatrix = pd.DataFrame(shift_matrix)
        return opt_lag, opt_corr

    def bm_scatterMatrix(self, yoy: bool = False):
        """Scatter matrix with KDE on diagonal."""
        if yoy:
            df = self.data[["retYoY_" + self.ser1_title, "retYoY_" + self.ser2_title]].dropna()
        else:
            df = self.data[["ret_" + self.ser1_title, "ret_" + self.ser2_title]].dropna()

        from scipy.stats import gaussian_kde
        n = len(df.columns)
        fig, axes = plt.subplots(n, n, figsize=(10, 10))
        for i, col_i in enumerate(df.columns):
            for j, col_j in enumerate(df.columns):
                ax = axes[i, j]
                if i == j:
                    kde = gaussian_kde(df[col_i].dropna())
                    xs = np.linspace(df[col_i].min(), df[col_i].max(), 100)
                    ax.plot(xs, kde(xs), color="blue", linewidth=1.5)
                    peak = xs[np.argmax(kde(xs))]
                    ax.axvline(peak, color="r", linestyle="--", linewidth=0.8)
                else:
                    ax.scatter(df[col_j], df[col_i], alpha=0.5, s=10)
                if i == n - 1:
                    ax.set_xlabel(col_j, fontsize=9)
                if j == 0:
                    ax.set_ylabel(col_i, fontsize=9)
                ax.xaxis.set_major_formatter(FuncFormatter(format_func))
                if i == len(df.columns) - 1:
                    ax.xaxis.set_major_formatter(FuncFormatter(format_func))

        fig.suptitle("Scatter Matrix" + (" (YoY)" if yoy else ""), fontsize=12)
        fig.tight_layout()
        fig.subplots_adjust(top=0.92)
        self.scatMatPlot = fig
        return fig, axes

    def export_plots(self, savePath: str = "", dialog: str = "Tk", _format: str = "png"):
        """Save all generated plots to disk."""
        if not savePath:
            savePath = save_path_dialog() or "."

        figs = []
        for attr, suffix in [
            ("fig1", "_series"), ("returns_plot", "_ret"), ("lineRegPlot", "_reg"),
            ("corr_plot", "_corr"), ("scatMatPlot", "_scatMat"), ("lag_plot", "_lag"),
            ("lag_plot2", "_lagRes"),
        ]:
            if hasattr(self, attr):
                figs.append((getattr(self, attr), suffix))

        for fig, suffix in figs:
            path = os.path.join(savePath, f"{self.ser1_title}-{self.ser2_title}{suffix}.{_format}")
            fig.savefig(path, dpi=150, bbox_inches="tight")
            print(f"Saved: {path}")

    def assess_correlation_error(
        self, which_series: Literal["returns", "price", "yoy_returns", "pct_returns"] = "returns"
    ):
        """Statistical assessment of correlation reliability."""
        col_map = {
            "returns": ("ret_" + self.ser1_title, "ret_" + self.ser2_title),
            "price": (self.ser1_title, self.ser2_title),
            "yoy_returns": ("retYoY_" + self.ser1_title, "retYoY_" + self.ser2_title),
            "pct_returns": ("retPct_" + self.ser1_title, "retPct_" + self.ser2_title),
        }
        c1, c2 = col_map[which_series]
        s1, s2 = self.data[c1], self.data[c2]
        n = len(s1)

        r, p = scipy_stats.pearsonr(s1, s2)
        se_r = np.sqrt((1 - r**2) / (n - 2))

        # Normality
        shapiro1 = scipy_stats.shapiro(s1)
        shapiro2 = scipy_stats.shapiro(s2)

        # Stationarity
        stat1 = check_stationarity(s1)
        stat2 = check_stationarity(s2)

        result = {
            "data": which_series,
            "n": n,
            "pearson_r": r,
            "p_value": p,
            "std_error": se_r,
            "shapiro_series1": {"statistic": shapiro1[0], "p_value": shapiro1[1]},
            "shapiro_series2": {"statistic": shapiro2[0], "p_value": shapiro2[1]},
            "stationarity_series1": stat1,
            "stationarity_series2": stat2,
        }
        self.error_assessment_results = result
        return result

    def __repr__(self):
        return f"<Pair_stats: {self.ser1_title} vs {self.ser2_title}, {len(self.windows)} windows>"


    def export_plots(self, savePath: str = "", dialog: str = "Tk", _format: str = "png"):
        """Save all generated plots to disk."""
        if not savePath:
            savePath = save_path_dialog() or "."

        figs = []
        for attr, suffix in [
            ("fig1", "_series"), ("returns_plot", "_ret"), ("lineRegPlot", "_reg"),
            ("corr_plot", "_corr"), ("scatMatPlot", "_scatMat"), ("lag_plot", "_lag"),
            ("lag_plot2", "_lagRes"),
        ]:
            if hasattr(self, attr):
                figs.append((getattr(self, attr), suffix))

        for fig, suffix in figs:
            path = os.path.join(savePath, f"{self.ser1_title}-{self.ser2_title}{suffix}.{_format}")
            fig.savefig(path, dpi=150, bbox_inches="tight")
            print(f"Saved: {path}")

    def assess_correlation_error(
        self, which_series: Literal["returns", "price", "yoy_returns", "pct_returns"] = "returns"
    ):
        """Statistical assessment of correlation reliability."""
        col_map = {
            "returns": ("ret_" + self.ser1_title, "ret_" + self.ser2_title),
            "price": (self.ser1_title, self.ser2_title),
            "yoy_returns": ("retYoY_" + self.ser1_title, "retYoY_" + self.ser2_title),
            "pct_returns": ("retPct_" + self.ser1_title, "retPct_" + self.ser2_title),
        }
        c1, c2 = col_map[which_series]
        s1, s2 = self.data[c1], self.data[c2]
        n = len(s1)

        r, p = scipy_stats.pearsonr(s1, s2)
        se_r = np.sqrt((1 - r**2) / (n - 2))

        # Normality
        shapiro1 = scipy_stats.shapiro(s1)
        shapiro2 = scipy_stats.shapiro(s2)

        # Stationarity
        stat1 = check_stationarity(s1)
        stat2 = check_stationarity(s2)

        result = {
            "data": which_series,
            "n": n,
            "pearson_r": r,
            "p_value": p,
            "std_error": se_r,
            "shapiro_series1": {"statistic": shapiro1[0], "p_value": shapiro1[1]},
            "shapiro_series2": {"statistic": shapiro2[0], "p_value": shapiro2[1]},
            "stationarity_series1": stat1,
            "stationarity_series2": stat2,
        }
        self.error_assessment_results = result
        return result

    def __repr__(self):
        return f"<Pair_stats: {self.ser1_title} vs {self.ser2_title}, {len(self.windows)} windows>"


def results_to_markdown(results: dict) -> str:
    """Convert error-assessment dict to a markdown table string."""
    lines = ["# Correlation Error Assessment", f"Data: {results.get('data', '?')}", ""]
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Observations | {results.get('n', '?')} |")
    lines.append(f"| Pearson r | {results.get('pearson_r', '?'):.6f} |")
    lines.append(f"| p-value | {results.get('p_value', '?'):.4e} |")
    lines.append(f"| Std Error | {results.get('std_error', '?'):.6f} |")
    lines.append("")
    for k in ("shapiro_series1", "shapiro_series2"):
        v = results.get(k, {})
        lines.append(f"**{k}** — stat={v.get('statistic', '?'):.4f}, p={v.get('p_value', '?'):.4e}")
    lines.append("")
    lines.append("### Stationarity")
    for k in ("stationarity_series1", "stationarity_series2"):
        v = results.get(k, {})
        lines.append(f"**{k}**:")
        for t in ("ADF", "KPSS"):
            tv = v.get(t, {})
            lines.append(f"- {t}: stat={tv.get('statistic', '?'):.4f}, p={tv.get('p-value', '?'):.4e}")
    return "\n".join(lines)


def results_to_markdown(results: dict) -> str:
    """Convert error-assessment dict to a markdown table string."""
    lines = ["# Correlation Error Assessment", f"Data: {results.get('data', '?')}", ""]
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Observations | {results.get('n', '?')} |")
    lines.append(f"| Pearson r | {results.get('pearson_r', '?'):.6f} |")
    lines.append(f"| p-value | {results.get('p_value', '?'):.4e} |")
    lines.append(f"| Std Error | {results.get('std_error', '?'):.6f} |")
    lines.append("")
    for k in ("shapiro_series1", "shapiro_series2"):
        v = results.get(k, {})
        lines.append(f"**{k}** — stat={v.get('statistic', '?'):.4f}, p={v.get('p_value', '?'):.4e}")
    lines.append("")
    lines.append("### Stationarity")
    for k in ("stationarity_series1", "stationarity_series2"):
        v = results.get(k, {})
        lines.append(f"**{k}**:")
        for t in ("ADF", "KPSS"):
            tv = v.get(t, {})
            lines.append(f"- {t}: stat={tv.get('statistic', '?'):.4f}, p={tv.get('p-value', '?'):.4e}")
    return "\n".join(lines)
