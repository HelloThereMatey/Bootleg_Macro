# bootleg-toolz

Watchlist management, Plotly charting, and time series data processing utilities. Built on top of `bootleg-datafeed`.

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

### Optional

X-13ARIMA-SEATS seasonal adjustment requires the X-13 binary:

```bash
conda install -c conda-forge x13as
```

## Usage

### Watchlist — multi-series management

```python
from bootleg_toolz import Watchlist

# Create a new watchlist
wl = Watchlist(name="my_watchlist")

# Add series programmatically
from bootleg_datafeed.models import SeriesMetadata, StandardSeries
meta = SeriesMetadata(id="GDP", title="Gross Domestic Product", source="fred")
wl.append_series(StandardSeries(data={}, metadata=meta))

# View as DataFrame
df = wl.watchlist  # pandas DataFrame

# Remove a series
wl.drop_series("GDP")

# Save to Excel (creates .xlsx + .h5s sidecar)
wl.save_watchlist("my_watchlist.xlsx")

# Load from Excel
wl.load_watchlist("my_watchlist.xlsx")

# Save/Load CSV
wl.save_watchlist_csv("my_watchlist.csv")
wl.load_watchlist_csv("my_watchlist.csv")
```

### Charting — Plotly visualisations

```python
from bootleg_toolz import charting
import pandas as pd

# Create some series
series1 = pd.Series(...)
series2 = pd.Series(...)

# Single axis chart
fig = charting.create_chart(series1, title="My Chart")

# Dual axis chart (left + right y-axes)
fig = charting.create_dual_axis_chart(
    series1, series2,
    title="Comparison",
    left_label="Left Axis",
    right_label="Right Axis"
)

fig.show()
```

### Data Processing — seasonal adjustment

```python
from bootleg_toolz.data_processing import seasonal_adjust, x13_seasonal_adjust
import pandas as pd

# Load a monthly time series
series = pd.Series(
    ...,
    index=pd.date_range("2000-01-01", periods=120, freq="ME"),
    name="my_series"
)

# STL decomposition seasonal adjustment
adjusted = seasonal_adjust(series)
# period is auto-inferred (ME -> 12, QE -> 4, WE -> 52)

# With explicit period
adjusted = seasonal_adjust(series, period=12)

# X-13ARIMA-SEATS seasonal adjustment
x13_adjusted = x13_seasonal_adjust(series, freq=12)
# Falls back gracefully if X-13 binary is not installed

# Plot STL decomposition
from bootleg_toolz.data_processing import plot_decomposition
plot_decomposition(series)
```

## License

MIT
