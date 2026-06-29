"""
Bootleg toolz — shared utilities for matplotlib-based charting and data helpers.

Ported from MacroBackend/Utilities.py with superseded code removed.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog
from typing import Optional, Union

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


# ---------------------------------------------------------------------------
# Tick / label helpers
# ---------------------------------------------------------------------------

def count_zeros_after_decimal(median_value: float) -> int:
    """Count digits after decimal up to the first non-zero (for tick precision)."""
    if 0 < median_value < 1:
        str_val = str(median_value).split(".")[1]
        return len(str_val) - len(str_val.lstrip("0")) + 1
    return 1


def EqualSpacedTicks(
    numTicks: int,
    data: Union[pd.Series, pd.DataFrame] = None,
    LogOrLin: str = "linear",
    LabOffset: float = None,
    labPrefix: str = None,
    labSuffix: str = None,
    Ymin: float = None,
    Ymax: float = None,
):
    """Generate evenly spaced tick positions and string labels.

    Parameters
    ----------
    numTicks : int
        Number of ticks to generate.
    data : pd.Series | pd.DataFrame, optional
        Data used to infer Ymin/Ymax when not given explicitly.
    LogOrLin : {'linear', 'log'}
        Scale type.
    LabOffset, labPrefix, labSuffix : optional
        Adjust displayed labels.
    Ymin, Ymax : float, optional
        Explicit axis bounds.

    Returns
    -------
    ticks : list[float]
    tick_labels : list[str]
    """
    if data is not None:
        if Ymin is None:
            Ymin = data.min().min() if isinstance(data, pd.DataFrame) else data.min()
        if Ymax is None:
            Ymax = data.max().max() if isinstance(data, pd.DataFrame) else data.max()

    decimals = count_zeros_after_decimal((Ymax - Ymin) / 2)

    if LogOrLin == "log":
        ticks = np.logspace(np.log10(Ymin), np.log10(Ymax), numTicks, base=10)
    else:
        ticks = np.linspace(Ymin, Ymax, numTicks)

    tick_labs = ticks.copy()
    if LabOffset is not None:
        tick_labs += LabOffset

    tick_labs = tick_labs.round(decimals).astype(str).tolist()
    ticks = ticks.astype(float).tolist()

    if labPrefix is not None:
        tick_labs = [labPrefix + s for s in tick_labs]
    if labSuffix is not None:
        tick_labs = [s + labSuffix for s in tick_labs]
    return ticks, tick_labs


def format_func(value, tick_number):
    """Matplotlib formatter — 2 decimal places."""
    return f"{value:.2f}"


# ---------------------------------------------------------------------------
# Date / index lookups
# ---------------------------------------------------------------------------

def GetClosestDateInIndex(
    df_index: Union[pd.DataFrame, pd.Series, pd.DatetimeIndex],
    searchDate: str = "2012-01-01",
):
    """Find the index entry closest to *searchDate* (YYYY-MM-DD).

    Returns (closest_date, integer_position).
    """
    if isinstance(df_index, pd.DatetimeIndex):
        index = df_index
    elif isinstance(df_index, (pd.DataFrame, pd.Series)):
        index = df_index.index
    else:
        raise TypeError("Input must have/be a DatetimeIndex.")

    date_ts = pd.to_datetime(searchDate)
    index = pd.to_datetime(index)
    closest_date = min(index, key=lambda x: abs((x - date_ts).total_seconds()))
    return closest_date, index.get_loc(closest_date)


def find_closest_val(series: pd.Series, target_value: float):
    """Find the value in *series* closest to *target_value*.

    Returns (closest_value, index_label).
    """
    idx = (series - target_value).abs().idxmin()
    return series.loc[idx], idx


# ---------------------------------------------------------------------------
# Series maths
# ---------------------------------------------------------------------------

def Percent_OfBaseVal_Series(
    series: pd.Series,
    ZeroDate: str = None,
    median: bool = False,
    mean: bool = False,
    start: bool = False,
) -> pd.Series:
    """Rebase *series* so a reference point = 100.

    Reference: *ZeroDate* (closest date), *median*, *mean*, or *start*.
    Defaults to first value if no option given.
    """
    if ZeroDate is not None:
        ZeroIndex = GetClosestDateInIndex(series, searchDate=ZeroDate)[1]
    elif median:
        val = series.median()
        _, idx = find_closest_val(series, val)
        ZeroIndex = series.index.get_loc(idx)
    elif mean:
        val = series.mean()
        _, idx = find_closest_val(series, val)
        ZeroIndex = series.index.get_loc(idx)
    elif start:
        ZeroIndex = 0
    else:
        ZeroIndex = 0

    base_val = series.iloc[ZeroIndex]
    return (series / base_val) * 100


# ---------------------------------------------------------------------------
# Derivatives / momentum
# ---------------------------------------------------------------------------

def SecondDerivative(input: pd.Series, periods: int) -> pd.Series:
    """Second difference (rate-of-change of rate-of-change)."""
    fd = input.pct_change(periods=periods) * 100 + 100
    return fd.pct_change(periods=periods) * 100


def RoCYoY(input: pd.Series) -> pd.Series:
    """Rate of change of YoY growth."""
    yoy = input.pct_change(periods=12) * 100 + 100
    return yoy.pct_change(periods=1) * 100


def RoCofRoC(input: pd.Series, periods: int = 1) -> pd.Series:
    """Second difference (simple diff)."""
    roc = input.diff(periods=periods)
    return roc.diff(periods=periods)


# ---------------------------------------------------------------------------
# Matplotlib axis helpers
# ---------------------------------------------------------------------------

def GetAxesDims(fig, ax):
    """Return dict of axes dimensions in inches / points / cm."""
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    xm, ym = ax.margins()
    w_in = bbox.width
    h_in = bbox.height
    return {
        "width_inches_total": w_in,
        "width_inches": w_in - xm * w_in,
        "width_points_total": w_in * 72,
        "width_points": (w_in - xm * w_in) * 72,
        "width_cm_total": w_in * 2.54,
        "width_cm": (w_in - xm * w_in) * 2.54,
        "height_inches_total": h_in,
        "height_inches": h_in - ym * h_in,
        "height_points_total": h_in * 72,
        "height_points": (h_in - ym * h_in) * 72,
        "height_cm_total": h_in * 2.54,
        "height_cm": (h_in - ym * h_in) * 2.54,
    }


def get_global_min_max(ax):
    """Global min / max across all lines on an axes."""
    vals = []
    for line in ax.get_lines():
        vals.extend(line.get_ydata())
    return min(vals), max(vals)


# ---------------------------------------------------------------------------
# File dialogs
# ---------------------------------------------------------------------------

def save_path_dialog(initialdir: str = None, title: str = "Choose your save destination...", qt: bool = False):
    """Open a directory-chooser dialog (Tkinter fallback, Qt optional)."""
    if qt:
        try:
            from PyQt6.QtWidgets import QApplication, QFileDialog
            import sys

            app = QApplication(sys.argv)
            path = QFileDialog.getExistingDirectory(None, title, initialdir or "", options=QFileDialog.Option.DontUseNativeDialog)
            app.exit()
            return path
        except ImportError:
            pass

    root = tk.Tk()
    root.withdraw()
    path = filedialog.askdirectory(initialdir=initialdir or "", mustexist=True, title=title)
    root.withdraw()
    return path
