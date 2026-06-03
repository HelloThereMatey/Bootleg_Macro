"""
Time series data processing utilities for bootleg_toolz.

Provides seasonal adjustment methods for financial and economic time series:
    - seasonal_adjust: STL decomposition-based seasonal adjustment
    - plot_decomposition: STL decomposition visualization
    - x13_seasonal_adjust: X-13ARIMA-SEATS seasonal adjustment

All functions operate on pd.Series objects with datetime-like indices.
"""

from __future__ import annotations

import pandas as pd
from statsmodels.tsa.seasonal import STL


def seasonal_adjust(series: pd.Series, period: int = None, robust: bool = True) -> pd.Series:
    """
    Returns a seasonally adjusted version of the input time series using STL decomposition.

    Parameters
    ----------
    series : pd.Series
        The time series to adjust. Must have a datetime-like index.
    period : int, optional
        The number of periods in a seasonal cycle (e.g., 12 for monthly data).
        If None, inferred from the series frequency.
    robust : bool, default True
        Use robust fitting to handle outliers.

    Returns
    -------
    pd.Series
        Seasonally adjusted series (trend + residual).
    """
    if period is None:
        inferred = pd.infer_freq(series.index)
        if inferred:
            upper = inferred.upper()
            if "M" in upper:
                period = 12
            elif "Q" in upper:
                period = 4
            elif "W" in upper:
                period = 52
        if period is None:
            raise ValueError(
                "Please specify the seasonal period for your data. "
                f"Could not infer from frequency {inferred!r}."
            )
    stl = STL(series, period=period, robust=robust)
    res = stl.fit()
    return res.trend + res.resid  # Seasonally adjusted series


def plot_decomposition(series: pd.Series, period: int = None, robust: bool = True):
    """
    Quick plot of STL decomposition components (observed, trend, seasonal, residual).

    Parameters
    ----------
    series : pd.Series
        The time series to decompose.
    period : int, optional
        The number of periods in a seasonal cycle. Inferred if None.
    robust : bool, default True
        Use robust fitting to handle outliers.
    """
    import matplotlib.pyplot as plt

    stl = STL(series, period=period, robust=robust)
    res = stl.fit()
    res.plot()
    plt.show()


def x13_seasonal_adjust(series: pd.Series, freq: int = None) -> pd.Series:
    """
    Seasonally adjust a time series using X-13ARIMA-SEATS only.

    Parameters
    ----------
    series : pd.Series
        Time series data with datetime index to seasonally adjust.
    freq : int, optional
        Seasonal frequency (4 for quarterly, 12 for monthly). If None, attempts
        to infer from index.

    Returns
    -------
    pd.Series
        Seasonally adjusted time series with same index as input, or original
        series if X-13 fails.

    Notes
    -----
    Requires X-13ARIMA-SEATS binary installed and on PATH.
    Install via: conda install -c conda-forge x13as
    """
    # Validate input
    if not isinstance(series.index, pd.DatetimeIndex):
        try:
            series.index = pd.to_datetime(series.index)
        except Exception:
            print(
                "Warning: Series must have a datetime-like index for seasonal "
                "adjustment. Returning original series."
            )
            return series

    # Infer frequency if not provided
    if freq is None:
        print("No frequency provided, attempting to infer frequency of time-series...")
        inferred_freq = pd.infer_freq(series.index)
        if inferred_freq:
            if "M" in inferred_freq:
                freq = 12  # Monthly
            elif "Q" in inferred_freq:
                freq = 4  # Quarterly
            elif "W" in inferred_freq:
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
        print(
            "X-13 not available. Install statsmodels and X-13 binary "
            "(conda install -c conda-forge x13as). Returning original series."
        )
        return series

    # Attempt X-13 seasonal adjustment
    try:
        print(f"Attempting X-13ARIMA-SEATS seasonal adjustment (freq={freq})...")
        result = x13_arima_analysis(series, freq=freq)

        # Extract seasonally adjusted series
        if hasattr(result, "seasadj"):
            sa_series = result.seasadj
        elif hasattr(result, "series"):
            sa_series = result.series
        else:
            raise AttributeError(
                "X-13 result missing expected seasonally adjusted series"
            )

        # Ensure proper Series formatting
        if not isinstance(sa_series, pd.Series):
            sa_series = pd.Series(sa_series, index=series.index)

        sa_series = sa_series.rename(
            f"{series.name}_x13_seasadj" if series.name else "x13_seasadj"
        )
        print("X-13 seasonal adjustment completed successfully")
        return sa_series

    except Exception as e:
        print(f"X-13 seasonal adjustment failed: {e}. Returning original series.")
        return series
