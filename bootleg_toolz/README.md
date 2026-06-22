# bootleg-toolz

Watchlist management, Plotly charting, time-series statistics, distribution / trend fitting, and data utilities. Built on top of `bootleg-datafeed`.

## Installation

```bash
pip install bootleg-toolz
```

Or install from source in editable mode:

```bash
cd bootleg_toolz
pip install -e .
```

### Dependencies

- `bootleg-datafeed >= 0.1`
- `pandas >= 2.0`
- `plotly >= 5.0`
- `openpyxl >= 3.0`
- `tables >= 3.0`
- `statsmodels >= 0.14`
- `scipy >= 1.10`
- `matplotlib >= 3.7`
- `kaleido >= 0.1` (for PNG export — `pip install kaleido`)

### Optional

X-13ARIMA-SEATS seasonal adjustment requires the X-13 binary:

```bash
conda install -c conda-forge x13as
```

---

## 1. Charting — `bootleg_toolz.charting`

Plotly-based charting for time series with auto-layout, dual-axis support, and high-resolution PNG export (scale=3 by default).

### Single series

```python
from bootleg_toolz import charting
import pandas as pd

series = pd.Series(
    [100, 102, 101, 103, 105],
    index=pd.date_range("2024-01-01", periods=5, freq="ME"),
    name="GDP",
)

fig = charting.plot_series(series, title="GDP", yaxis_title="Index")

charting.show(fig)                       # Display (jupyter-compatible)
charting.save_png(fig, "gdp.png")        # ~300 DPI PNG
charting.save_html(fig, "gdp.html")      # Interactive HTML
```

### Multiple series (dual axis)

```python
primary = {"S&P 500": spx_series, "NASDAQ": ndx_series}
secondary = {"VIX": vix_series}

fig = charting.plot_multi(
    series_dict=primary,
    title="Equities vs Volatility",
    primary_yaxis_title="Price",
    secondary_series=secondary,
    secondary_yaxis_title="VIX",
    height=500,
)
charting.show(fig)
```

### Watchlist plotting

```python
fig = charting.plot_watchlist(
    left=[(meta1, series1), (meta2, series2)],
    right=[(meta3, series3)],
    plot_title="My Watchlist",
    primary_yaxis_title="Left Axis",
    secondary_yaxis_title="Right Axis",
)
```

---

## 2. Watchlist — `bootleg_toolz.Watchlist`

Multi-series management: define a watchlist by id + source, fetch all data at once, persist to Excel + HDF5, and plot.

```python
from bootleg_toolz import Watchlist

wl = Watchlist(name="my_watchlist")

# Fetch all series via Dataset.pull()
errors = wl.get_watchlist_data(
    start_date="2020-01-01",
    end_date="2024-12-31",
    extend_abs=True,  # splice cross-frequency ABS siblings for longer history
)

# Save as Excel (.xlsx) + HDF5 sidecar (.h5s)
wl.save_watchlist("my_watchlist.xlsx")
```

---

## 3. Statistics — `bootleg_toolz.stats`

Pairwise correlation analysis and stationarity testing. Ported from `MacroBackend/stats.py` with improved frequency handling.

### Pair_stats — full correlation toolkit

```python
from bootleg_toolz.stats import Pair_stats

ps = Pair_stats(series1, series2, windows=[30, 90, 180])

# Full-sample correlations (auto-computed)
ps.full_corr          # price correlation
ps.full_RetCorr       # log-return correlation
ps.full_YoYRetCorr    # YoY return correlation
ps.full_PctRetCorr    # percentage return correlation
ps.full_qdCorr        # Quant-Dare correlation

# Plotting
fig, ax = ps.plot_series()            # dual-axis price chart
fig, ax = ps.plot_log_returns()       # bar chart of log returns
fig, axes = ps.plot_corrs()           # rolling correlations
fig, ax = ps.plot_lin_reg()           # scatter + regression
fig, ax_mat = ps.bm_scatterMatrix()   # scatter matrix with KDE

# Lag analysis
lag, corr = ps.find_optimal_ret_lag(n=10)   # lag search on returns

# Statistical assessment
err = ps.assess_correlation_error("returns")
print(err["pearson_r"], err["p_value"], err["std_error"])
```

### Standalone functions

```python
from bootleg_toolz.stats import qd_corr, rolling_corr, rolling_qd, check_stationarity

# Quant-Dare correlation (no demeaning)
r = qd_corr(s1, s2)

# Rolling correlation
rc = rolling_corr(s1, s2, window=30, method="pearson")

# Stationarity tests (ADF + KPSS)
st = check_stationarity(s1)
# st["ADF"]["p-value"], st["KPSS"]["p-value"]
```

---

## 4. Distribution & Trend Fitting — `bootleg_toolz.fitting`

Ported from `MacroBackend/Fitting.py`.

### Distribution fitting

```python
from bootleg_toolz.fitting import stat_models_fit

sf = stat_models_fit(series)
sf.fit_gaussian()
sf.fit_lorentzian()
sf.fit_student_t()
sf.fit_gamma()   # bug fixed: now uses scipy.stats.gamma, not stats.t

# Plot histogram with all fits overlaid
sf.plot_histogram_with_fits(log=True)

# Q-Q plots for all four distributions
sf.qq_plots()
```

### Trend fitting

```python
from bootleg_toolz.fitting import FitTrend, FitFunction

ft = FitTrend(series)
ft.FitData(FitFunc="exponential", x1="1995-01-01", x2="2020-01-01")

# Plot data + trend + deviation + deviation histogram
fig, (ax1, ax2, ax3) = ft.ShowFit(yaxis="log", title="M2 Money Supply")
```

### Peak / trough detection

```python
from bootleg_toolz.fitting import identify_peaks_and_troughs
import datetime

peaks, troughs, raw_peaks, raw_troughs = identify_peaks_and_troughs(
    series, x_range=datetime.timedelta(weeks=156)
)
```

### Seasonal adjustment

```python
from bootleg_toolz.fitting import seasonal_adjust, plot_decomposition, x13_seasonal_adjust

# STL-based seasonal adjustment
adjusted = seasonal_adjust(series)

# X-13ARIMA-SEATS (requires x13as binary)
adjusted_x13 = x13_seasonal_adjust(series, freq=12)
```

### Normality tests

```python
from bootleg_toolz.fitting import normality_tests

results_df, qq_fig = normality_tests(series)
# Shapiro-Wilk, Anderson-Darling, K-S + Q-Q plot
```

---

## 5. Data Processing — `bootleg_toolz.data_processing`

STL decomposition and X-13 seasonal adjustment utilities.  Most functionality has been consolidated into `fitting.py` (see above); `data_processing` remains for backward compatibility.

```python
from bootleg_toolz.data_processing import seasonal_adjust, plot_decomposition, x13_seasonal_adjust
```

---

## 6. Utilities — `bootleg_toolz.utilities`

Low-level helpers used by `stats.py` and `fitting.py`. Also available for direct use.

```python
from bootleg_toolz.utilities import (
    EqualSpacedTicks,      # matplotlib log/linear tick generator
    GetClosestDateInIndex, # find closest date in DatetimeIndex
    find_closest_val,      # find closest value in Series
    Percent_OfBaseVal_Series,  # rebase series to 100
    SecondDerivative,      # second difference
    RoCYoY,                # rate of change of YoY growth
    save_path_dialog,      # Tkinter directory picker
    format_func,           # 2-decimal tick formatter
)
```

---

## Module reference

| Submodule | Key exports |
|-----------|-------------|
| `charting` | `plot_series()`, `plot_multi()`, `plot_watchlist()`, `save_png()`, `save_html()`, `show()` |
| `watchlist` | `Watchlist` class, `_parse_id()`, `_pull_series()`, `METADATA_INDEX` |
| `stats` | `Pair_stats`, `qd_corr()`, `rolling_corr()`, `rolling_qd()`, `check_stationarity()`, `results_to_markdown()` |
| `fitting` | `stat_models_fit`, `FitTrend`, `FitFunction`, `normality_tests()`, `identify_peaks_and_troughs()`, `seasonal_adjust()`, `x13_seasonal_adjust()` |
| `data_processing` | `seasonal_adjust()`, `plot_decomposition()`, `x13_seasonal_adjust()` |
| `utilities` | `EqualSpacedTicks`, `GetClosestDateInIndex`, `Percent_OfBaseVal_Series`, `save_path_dialog`, `format_func` |

## License

MIT
