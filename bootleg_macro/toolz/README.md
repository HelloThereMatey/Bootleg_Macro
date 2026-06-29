# bootleg-macro.toolz

Watchlist management, Plotly charting, time-series statistics, distribution / trend fitting, and data utilities. Built on top of `bootleg-datafeed`.

**Note**: This is now a subdirectory within the `bootleg-macro` meta-package. Install via `bootleg-macro`.

## Installation

```bash
# Install bootleg-macro (includes toolz + indexes by default)
pip install -e ./bootleg_macro

# Or with GUI support
pip install -e "./bootleg_macro[gui]"
```

The toolz module is always installed when you install `bootleg-macro`.

---

## 1. Charting — `bootleg_macro.toolz.charting`

Plotly-based charting for time series with auto-layout, dual-axis support, and high-resolution PNG export (scale=3 by default).

### Single series

```python
from bootleg_macro import charting
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
from bootleg_macro import Watchlist

wl = Watchlist(name="my_list")
wl.get_watchlist_data(start_date="2020-01-01")

fig = charting.plot_watchlist(
    left=[("GDP", wl.datasets["GDP"]), ("UNRATE", wl.datasets["UNRATE"])],
    right=[("VIX", wl.datasets["VIX"])],
    plot_title="Economic Indicators",
)
charting.show(fig)
```

---

## 2. Watchlist — `bootleg_macro.toolz.Watchlist`

Multi-series management: define a watchlist by id + source, fetch all data at once, persist to Excel + HDF5, and plot.

```python
from bootleg_macro import Watchlist

wl = Watchlist(name="my_watchlist")

# Add series (from search results or manually)
from bootleg_datafeed.models import SeriesMetadata
meta = SeriesMetadata(id="GDP", title="Gross Domestic Product", source="fred")
wl.append_series(meta, series_data)

# Fetch all data via Dataset
errors = wl.get_watchlist_data(
    start_date="2020-01-01",
    end_date="2024-12-31",
)

# Save as Excel (.xlsx) + HDF5 sidecar (.h5s)
wl.save_watchlist("my_watchlist.xlsx")
```

---

## 3. Statistics — `bootleg_macro.toolz.stats`

Pairwise correlation analysis and stationarity testing.

```python
from bootleg_macro.toolz.stats import Pair_stats

ps = Pair_stats(series1, series2, windows=[30, 90, 180])

# Full-sample correlations
ps.full_corr          # price correlation
ps.full_RetCorr       # log-return correlation
ps.full_YoYRetCorr    # YoY return correlation

# Plotting
fig, ax = ps.plot_series()            # dual-axis price chart
fig, axes = ps.plot_corrs()           # rolling correlations
fig, ax = ps.plot_lin_reg()           # scatter + regression
```

### Standalone functions

```python
from bootleg_macro.toolz.stats import qd_corr, rolling_corr, check_stationarity

# Quant-Dare correlation (no demeaning)
r = qd_corr(s1, s2)

# Rolling correlation
rc = rolling_corr(s1, s2, window=30, method="pearson")

# Stationarity tests (ADF + KPSS)
st = check_stationarity(s1)
```

---

## 4. Distribution & Trend Fitting — `bootleg_macro.toolz.fitting`

Distribution fitting, trend fitting, seasonal adjustment, and peak/trough detection.

```python
from bootleg_macro.toolz.fitting import stat_models_fit, FitTrend

# Distribution fitting
sf = stat_models_fit(series)
sf.fit_gaussian()
sf.fit_lorentzian()
sf.fit_student_t()
sf.fit_gamma()

# Plot histogram with all fits overlaid
sf.plot_histogram_with_fits(log=True)

# Trend fitting
ft = FitTrend(series)
ft.FitData(FitFunc="exponential", x1="1995-01-01", x2="2020-01-01")
fig, (ax1, ax2, ax3) = ft.ShowFit(yaxis="log", title="M2 Money Supply")
```

---

## 5. Utilities — `bootleg_macro.toolz.utilities`

Low-level helpers:

```python
from bootleg_macro.toolz.utilities import (
    EqualSpacedTicks,      # matplotlib log/linear tick generator
    GetClosestDateInIndex, # find closest date in DatetimeIndex
    Percent_OfBaseVal_Series,  # rebase series to 100
    SecondDerivative,      # second difference
)
```

---

## Dependencies

Part of `bootleg-macro`. Requires:
- `bootleg-datafeed >= 0.1`
- `pandas >= 2.0`
- `plotly >= 5.0`
- `openpyxl >= 3.0`
- `tables >= 3.0`
- `statsmodels >= 0.14`
- `scipy >= 1.10`
- `matplotlib >= 3.7`

## License

MIT
