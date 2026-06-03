#!/usr/bin/env python
"""
Dedicated tests for tedata (Trading Economics) source.

Tests search and pull with detailed logging, retry behavior,
and sufficient timeouts (60s default, 120s for slow connections).
Shows all messages and logs for debugging.
"""

import sys
import logging
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging to show all messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-25s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bm.tedata")
logger.setLevel(logging.DEBUG)

# Also set tedata package logger to DEBUG
logging.getLogger("tedata").setLevel(logging.INFO)

import pandas as pd
from bootleg_datafeed import Dataset
from bootleg_toolz import WatchlistSearch, Watchlist
from bootleg_datafeed.sources.tedata_source import (
    pull_tedata,
    search_tedata,
    get_tedata_url,
)


CHARTS_DIR = Path(__file__).parent / "source_charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)


def _save_series_png(series, filename: str, dpi: int = 150) -> Path:
    """Save a series as PNG chart."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    s = series.copy() if hasattr(series, 'copy') else series
    if hasattr(s, 'index') and hasattr(s.index, 'tz') and s.index.tz is not None:
        s.index = s.index.tz_convert('UTC').tz_localize(None)

    title = filename.replace('_', ' ').title()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(s.index, s.values, linewidth=1.2, color='steelblue')
    ax.set_title(title, fontsize=12)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    path = CHARTS_DIR / f"{filename}.png"
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"  Chart saved: {path.name} ({path.stat().st_size // 1024} KB)")
    return path


# =============================================================================
# URL construction test
# =============================================================================

def test_url_construction():
    """Test URL construction from series ID."""
    logger.info("=" * 60)
    logger.info("TEST: URL construction")
    logger.info("=" * 60)

    cases = [
        ("https://tradingeconomics.com/commodity/crude-oil",
         "https://tradingeconomics.com/commodity/crude-oil"),
        ("commodity/crude-oil",
         "https://tradingeconomics.com/commodity/crude-oil"),
        ("/united-states/ism-manufacturing-new-orders",
         "https://tradingeconomics.com/united-states/ism-manufacturing-new-orders"),
    ]

    for input_id, expected in cases:
        result = get_tedata_url(input_id)
        status = "PASS" if result == expected else "FAIL"
        logger.info(f"  [{status}] get_tedata_url({input_id!r})")
        logger.info(f"         = {result!r}")
        if result != expected:
            logger.error(f"         expected: {expected!r}")
            return False

    return True


# =============================================================================
# Search tests
# =============================================================================

def test_search_crud_oil(timeout: int = 60):
    """Search for 'crude oil'."""
    logger.info("=" * 60)
    logger.info("TEST: search_tedata('crude oil')")
    logger.info("=" * 60)
    logger.info(f"  timeout={timeout}s")

    t0 = time.time()
    try:
        results = search_tedata("crude oil", timeout=timeout)
        elapsed = time.time() - t0
        logger.info(f"  Completed in {elapsed:.1f}s")
        logger.info(f"  Results: {len(results)} rows")

        if not results.empty:
            logger.info(f"  Columns: {results.columns.tolist()}")
            for _, row in results.iterrows():
                logger.info(f"    - {row.get('metric', '?')} ({row.get('country', '?')}): {row.get('url', '?')}")
        else:
            logger.warning("  No results returned (may indicate a problem)")

        print(f"\nSearch results DataFrame:\n{results.to_string()}\n")

    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"  Failed after {elapsed:.1f}s: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

    return results


def test_search_gold(timeout: int = 60):
    """Search for 'gold'."""
    logger.info("=" * 60)
    logger.info("TEST: search_tedata('gold')")
    logger.info("=" * 60)
    logger.info(f"  timeout={timeout}s")

    t0 = time.time()
    try:
        results = search_tedata("gold", timeout=timeout)
        elapsed = time.time() - t0
        logger.info(f"  Completed in {elapsed:.1f}s")
        logger.info(f"  Results: {len(results)} rows")
        if not results.empty:
            for _, row in results.iterrows():
                logger.info(f"    - {row.get('metric', '?')} ({row.get('country', '?')})")
        print(f"\nSearch results DataFrame:\n{results.to_string()}\n")
    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"  Failed after {elapsed:.1f}s: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

    return results


# =============================================================================
# Pull tests
# =============================================================================

def test_pull_crud_oil(timeout: int = 90):
    """Pull WTI Crude Oil (daily data)."""
    logger.info("=" * 60)
    logger.info("TEST: pull_tedata(crude oil) — WTI Crude Oil")
    logger.info("=" * 60)
    logger.info(f"  URL: https://tradingeconomics.com/commodity/crude-oil")
    logger.info(f"  timeout={timeout}s")

    t0 = time.time()
    try:
        result = pull_tedata(
            url="https://tradingeconomics.com/commodity/crude-oil",
            start_date="2023-01-01",
            end_date="2024-12-31",
            timeout=timeout,
        )
        elapsed = time.time() - t0

        logger.info(f"  Success in {elapsed:.1f}s!")
        logger.info(f"  ID: {result.metadata.id}")
        logger.info(f"  Title: {result.metadata.title}")
        logger.info(f"  Source: {result.metadata.source}")
        logger.info(f"  Original source: {result.metadata.original_source}")
        logger.info(f"  Frequency: {result.metadata.frequency}")
        logger.info(f"  Units: {result.metadata.units}")
        logger.info(f"  Length: {result.metadata.length}")
        logger.info(f"  Start: {result.metadata.start_date}")
        logger.info(f"  End: {result.metadata.end_date}")
        logger.info(f"  Min: {result.metadata.min_value:.4f}")
        logger.info(f"  Max: {result.metadata.max_value:.4f}")

        series = result.to_pandas()
        logger.info(f"  Series points: {len(series)}")
        logger.info(f"  Date range: {series.index[0].date()} to {series.index[-1].date()}")
        logger.info(f"  Last value: {series.iloc[-1]:.4f} {result.metadata.units}")

        # Save chart
        path = _save_series_png(series, 'tedata_crude_oil')
        print(f"\nChart: {path}\n")

        return result

    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"  Failed after {elapsed:.1f}s: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def test_pull_brent(timeout: int = 90):
    """Pull Brent Crude Oil."""
    logger.info("=" * 60)
    logger.info("TEST: pull_tedata(brent crude oil) — Brent Crude")
    logger.info("=" * 60)
    logger.info(f"  URL: https://tradingeconomics.com/commodity/brent-crude-oil")
    logger.info(f"  timeout={timeout}s")

    t0 = time.time()
    try:
        result = pull_tedata(
            url="https://tradingeconomics.com/commodity/brent-crude-oil",
            start_date="2023-01-01",
            end_date="2024-12-31",
            timeout=timeout,
        )
        elapsed = time.time() - t0

        logger.info(f"  Success in {elapsed:.1f}s!")
        logger.info(f"  ID: {result.metadata.id}")
        logger.info(f"  Title: {result.metadata.title}")
        logger.info(f"  Length: {result.metadata.length}")
        logger.info(f"  Frequency: {result.metadata.frequency}")
        logger.info(f"  Units: {result.metadata.units}")

        series = result.to_pandas()
        logger.info(f"  Series points: {len(series)}")
        logger.info(f"  Date range: {series.index[0].date()} to {series.index[-1].date()}")
        logger.info(f"  Last value: {series.iloc[-1]:.4f} {result.metadata.units}")

        path = _save_series_png(series, 'tedata_brent_crude')
        print(f"\nChart: {path}\n")

        return result

    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"  Failed after {elapsed:.1f}s: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def test_pull_ism_manufacturing(timeout: int = 90):
    """Pull US ISM Manufacturing (monthly indicator)."""
    logger.info("=" * 60)
    logger.info("TEST: pull_tedata(ISM Manufacturing) — US ISM Mfg Index")
    logger.info("=" * 60)
    logger.info(f"  URL: https://tradingeconomics.com/united-states/ism-manufacturing-new-orders")
    logger.info(f"  timeout={timeout}s")

    t0 = time.time()
    try:
        result = pull_tedata(
            url="https://tradingeconomics.com/united-states/ism-manufacturing-new-orders",
            timeout=timeout,
        )
        elapsed = time.time() - t0

        logger.info(f"  Success in {elapsed:.1f}s!")
        logger.info(f"  ID: {result.metadata.id}")
        logger.info(f"  Title: {result.metadata.title}")
        logger.info(f"  Length: {result.metadata.length}")
        logger.info(f"  Frequency: {result.metadata.frequency}")
        logger.info(f"  Units: {result.metadata.units}")

        series = result.to_pandas()
        logger.info(f"  Series points: {len(series)}")
        logger.info(f"  Date range: {series.index[0].date()} to {series.index[-1].date()}")
        logger.info(f"  Last value: {series.iloc[-1]:.4f}")

        path = _save_series_png(series, 'tedata_ism_manufacturing')
        print(f"\nChart: {path}\n")

        return result

    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"  Failed after {elapsed:.1f}s: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def test_pull_gold(timeout: int = 90):
    """Pull Gold price (daily)."""
    logger.info("=" * 60)
    logger.info("TEST: pull_tedata(gold) — Gold Price")
    logger.info("=" * 60)
    logger.info(f"  URL: https://tradingeconomics.com/commodity/gold")
    logger.info(f"  timeout={timeout}s")

    t0 = time.time()
    try:
        result = pull_tedata(
            url="https://tradingeconomics.com/commodity/gold",
            start_date="2023-01-01",
            end_date="2024-12-31",
            timeout=timeout,
        )
        elapsed = time.time() - t0

        logger.info(f"  Success in {elapsed:.1f}s!")
        logger.info(f"  ID: {result.metadata.id}")
        logger.info(f"  Title: {result.metadata.title}")
        logger.info(f"  Length: {result.metadata.length}")
        logger.info(f"  Frequency: {result.metadata.frequency}")
        logger.info(f"  Units: {result.metadata.units}")

        series = result.to_pandas()
        logger.info(f"  Series points: {len(series)}")
        logger.info(f"  Date range: {series.index[0].date()} to {series.index[-1].date()}")
        logger.info(f"  Last value: {series.iloc[-1]:.4f} {result.metadata.units}")

        path = _save_series_png(series, 'tedata_gold')
        print(f"\nChart: {path}\n")

        return result

    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"  Failed after {elapsed:.1f}s: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


# =============================================================================
# Watchlist test
# =============================================================================

def test_watchlist_with_tedata(timeout: int = 90):
    """Build a watchlist combining tedata series with search + manual entries."""
    logger.info("=" * 60)
    logger.info("TEST: Watchlist with tedata series")
    logger.info("=" * 60)

    ws = WatchlistSearch()
    wl = Watchlist(name='tedata_watchlist_test')

    # Add from search
    try:
        results = ws.search('tedata', 'natural gas')
        if len(results) > 0:
            first = results.iloc[0]
            wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
                'id': first['id'],
                'source': 'tedata',
                'title': first['title']
            }])], ignore_index=True)
            logger.info(f"  Added from search: {first['title']}")
    except Exception as e:
        logger.warning(f"  Search error: {e}")

    # Add known entries manually
    for url, title in [
        ("https://tradingeconomics.com/commodity/copper", "Copper"),
        ("https://tradingeconomics.com/united-states/consumer-confidence", "US Consumer Confidence"),
    ]:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': url, 'source': 'tedata', 'title': title
        }])], ignore_index=True)
        logger.info(f"  Added manually: {title}")

    logger.info(f"  Watchlist entries: {len(wl.watchlist)}")
    logger.info(f"\n  Watchlist:\n{wl.watchlist.to_string()}\n")

    # Pull all
    t0 = time.time()
    errors = wl.get_watchlist_data(start_date='2023-01-01', end_date='2024-12-31')
    elapsed = time.time() - t0

    logger.info(f"  Pull completed in {elapsed:.1f}s")
    logger.info(f"  Errors: {errors}")
    logger.info(f"  Datasets: {list(wl.datasets.keys())}")

    for sid, series in wl.datasets.items():
        s = series.to_pandas() if hasattr(series, 'to_pandas') else series
        safe_name = f"wl_{sid.replace('https://tradingeconomics.com/', '').replace('/', '_')}"
        path = _save_series_png(s, safe_name)

    return wl


# =============================================================================
# Dataset and generic pull tests
# =============================================================================

def test_dataset_pull_tedata(timeout: int = 90):
    """Test pull via Dataset.pull_tedata()."""
    logger.info("=" * 60)
    logger.info("TEST: Dataset.pull_tedata()")
    logger.info("=" * 60)

    ds = Dataset()
    t0 = time.time()
    try:
        result = ds.pull_tedata(
            url="https://tradingeconomics.com/commodity/silver",
            start_date="2023-01-01",
            end_date="2024-12-31",
            timeout=timeout,
        )
        elapsed = time.time() - t0
        logger.info(f"  Success in {elapsed:.1f}s!")
        logger.info(f"  Title: {result.metadata.title}, Length: {result.metadata.length}")

        series = result.to_pandas()
        path = _save_series_png(series, 'tedata_silver')
        print(f"\nChart: {path}\n")

        return result
    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"  Failed after {elapsed:.1f}s: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def test_generic_pull(timeout: int = 90):
    """Test generic Dataset.pull('tedata', ...)."""
    logger.info("=" * 60)
    logger.info("TEST: Dataset.pull('tedata', ...)")
    logger.info("=" * 60)

    ds = Dataset()
    t0 = time.time()
    try:
        result = ds.pull(
            'tedata',
            url="united-states/corporate Profits",
            timeout=timeout,
        )
        elapsed = time.time() - t0
        logger.info(f"  Success in {elapsed:.1f}s!")
        logger.info(f"  Title: {result.metadata.title}, Length: {result.metadata.length}")

        series = result.to_pandas()
        path = _save_series_png(series, 'tedata_corporate_profits')
        print(f"\nChart: {path}\n")

        return result
    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"  Failed after {elapsed:.1f}s: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "=" * 70)
    print(" bm tedata Source Tests")
    print(" Logging: DEBUG level (all messages shown)")
    print(f" Output: {CHARTS_DIR}")
    print("=" * 70 + "\n")

    tests = [
        ("URL construction", test_url_construction),
        ("Search crude oil", lambda: test_search_crud_oil(timeout=90)),
        ("Search gold", lambda: test_search_gold(timeout=90)),
        ("Pull crude oil (WTI)", lambda: test_pull_crud_oil(timeout=120)),
        ("Pull brent crude", lambda: test_pull_brent(timeout=120)),
        ("Pull ISM manufacturing", lambda: test_pull_ism_manufacturing(timeout=120)),
        ("Pull gold", lambda: test_pull_gold(timeout=120)),
        ("Pull silver (via Dataset)", lambda: test_dataset_pull_tedata(timeout=120)),
        ("Pull corporate profits (generic)", lambda: test_generic_pull(timeout=120)),
        ("Watchlist with tedata", lambda: test_watchlist_with_tedata(timeout=120)),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n{'='*70}")
        print(f"Running: {name}")
        print(f"{'='*70}\n")
        try:
            test_func()
            passed += 1
            print(f"\n[✓] {name} — PASSED")
        except Exception as e:
            failed += 1
            print(f"\n[✗] {name} — FAILED: {e}")

    print(f"\n{'='*70}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*70}")

    charts = sorted(CHARTS_DIR.glob("tedata_*.png"))
    print(f"\nSaved {len(charts)} tedata charts:")
    for c in charts:
        size_kb = c.stat().st_size // 1024
        print(f"  {c.name} ({size_kb} KB)")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())