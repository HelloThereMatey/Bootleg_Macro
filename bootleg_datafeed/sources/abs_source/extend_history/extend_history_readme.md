# extend_history — Cross-frequency ABS time series extension

Extends an ABS time series or whole catalogue backwards or forwards by splicing it with data from a sibling series at a different frequency. For example, a monthly CPI index starting in 2017 gets extended back to 1972 using the quarterly series for the same concept.

Works in both directions:
- **Monthly → Quarterly** (forward): pass a monthly series ID, extend backwards with quarterly data
- **Quarterly → Monthly** (reverse): pass a quarterly series ID, extend forwards with monthly data

- For most series and catalogues, the returns will be the same as `read_abs_series()` and `read_abs_cat()` respectively. Only series with a valid sibling at another frequency will be extended.

## API

### `extend_series(series_id, cat=None, **kwargs)`

Returns `(series: Series, meta: DataFrame)` — a single extended time series and its metadata.

```python
from readabs.extend_history import extend_series

# Auto-resolve catalogue, extend backwards
s, meta = extend_series("A130392586J")
# 226 obs, 1972-07-01 to 2026-04-01

# Reverse: quarterly → monthly
s, meta = extend_series("A2326391L")
# 246 obs, 1948-07-01 to 2026-04-01
```

| Argument | Default | Description |
|---|---|---|
| `series_id` | required | ABS series ID (any frequency) |
| `cat` | `None` | Catalogue number. Auto-looked up if omitted. |
| `**kwargs` | | Passed to `read_abs_series()`. Supports `verbose`, `single_excel_only`, `cache_only`, etc. |

### `extend_catalogue(cat, **kwargs)`

Extend every series in a catalogue that has a sibling at another frequency.

```python
from readabs.extend_history import extend_catalogue

data_dict, meta = extend_catalogue("6401.0")
```

Returns `(data_dict, meta)` — same format as `read_abs_cat()`.

### `find_cat_for_series(series_id)`

```python
from readabs.extend_history import find_cat_for_series

find_cat_for_series("A130392586J")  # → "6401.0"
```

## How it works

1. **Look up** the series in the master index (`abs_series_map.csv.gz`, 108k rows)
2. **Find sibling** — finds series with the same description at a different frequency
3. **Resolve roles** — the higher-frequency series (whichever it is) is fetched from the current catalogue; the lower-frequency series comes from the historical release
4. **Calculate release date** — determines which historical ABS publication to download (quarter-end before the higher-freq series started)
5. **Fetch historical data** — downloads the catalogue as it stood at that date (Excel-only, 404s suppressed)
6. **Rebase & concatenate** — the lower-freq series is re-scaled so its last value matches the higher-freq series' first value, then concatenated

## Caching

- **Master index**: cached in memory via `functools.cache`
- **Historical catalogues**: cached in a module-level dict keyed by `(cat, history)`
- **ABS HTTP cache**: uses the standard `READABS_CACHE_DIR` (default `./.readabs_cache/`)
- **Single-table download**: when the master index has a clean table identifier, `extend_series` automatically downloads only that table from the current catalogue

## Limitations

- Sibling discovery relies on exact description text match — if the ABS rewords the description between frequencies, the match won't work
- Not all catalogues have a monthly/quarterly split
- Older ABS releases may have different table layouts; not every sibling is guaranteed to be found
