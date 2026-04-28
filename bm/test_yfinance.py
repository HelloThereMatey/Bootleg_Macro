#!/usr/bin/env python
"""
Test script for yfinance source in bm.

Tests that we can download 3 time series from Yahoo Finance and that
they conform to the StandardSeries format.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bm import Dataset, StandardSeries


def test_yfinance_single_ticker():
    """Test pulling a single ticker."""
    ds = Dataset()

    print("=" * 60)
    print("Test 1: Pull AAPL (Apple) daily data")
    print("=" * 60)

    result = ds.pull_yfinance(
        ticker='AAPL',
        start_date='2023-01-01',
        end_date='2024-12-31',
        interval='1d',
    )

    assert isinstance(result, StandardSeries), f"Expected StandardSeries, got {type(result)}"
    assert isinstance(result.metadata.id, str), "Metadata id should be string"
    assert result.metadata.source == 'yfinance', f"Source should be 'yfinance', got {result.metadata.source}"
    assert result.metadata.start_date is not None, "Start date should be set"
    assert result.metadata.end_date is not None, "End date should be set"

    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Source: {result.metadata.source}")
    print(f"  Start: {result.metadata.start_date}")
    print(f"  End: {result.metadata.end_date}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Frequency: {result.metadata.frequency}")
    print(f"  Units: {result.metadata.units}")
    print(f"  Min: {result.metadata.min_value}")
    print(f"  Max: {result.metadata.max_value}")

    # Convert to pandas and check
    series = result.to_pandas()
    assert len(series) > 0, "Series should have data points"
    assert isinstance(series.index, type(series.index)), "Series should have index"

    print(f"\n  First 5 values:\n{series.head()}")
    print("\n  [PASS] Test 1 passed!\n")

    return result


def test_yfinance_index():
    """Test pulling an index."""
    ds = Dataset()

    print("=" * 60)
    print("Test 2: Pull ^GSPC (S&P 500) weekly data")
    print("=" * 60)

    result = ds.pull_yfinance(
        ticker='^GSPC',
        start_date='2020-01-01',
        end_date='2024-12-31',
        interval='1wk',
    )

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'yfinance'

    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Frequency: {result.metadata.frequency}")

    series = result.to_pandas()
    print(f"\n  First 5 values:\n{series.head()}")
    print("\n  [PASS] Test 2 passed!\n")

    return result


def test_yfinance_crypto():
    """Test pulling crypto data."""
    ds = Dataset()

    print("=" * 60)
    print("Test 3: Pull BTC-USD (Bitcoin) daily data")
    print("=" * 60)

    result = ds.pull_yfinance(
        ticker='BTC-USD',
        start_date='2023-01-01',
        end_date='2024-12-31',
        interval='1d',
    )

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'yfinance'
    assert result.metadata.id == 'BTC-USD'

    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Frequency: {result.metadata.frequency}")
    print(f"  Min value: {result.metadata.min_value}")
    print(f"  Max value: {result.metadata.max_value}")

    series = result.to_pandas()
    print(f"\n  First 5 values:\n{series.head()}")
    print("\n  [PASS] Test 3 passed!\n")

    return result


def test_generic_pull():
    """Test the generic pull method."""
    ds = Dataset()

    print("=" * 60)
    print("Test 4: Test generic pull() method")
    print("=" * 60)

    result = ds.pull(
        source='yfinance',
        ticker='MSFT',
        start_date='2024-01-01',
        end_date='2024-12-31',
    )

    assert isinstance(result, StandardSeries)
    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print("\n  [PASS] Test 4 passed!\n")

    return result


def main():
    print("\n" + "=" * 60)
    print("bm yfinance source tests")
    print("=" * 60 + "\n")

    try:
        test_yfinance_single_ticker()
        test_yfinance_index()
        test_yfinance_crypto()
        test_generic_pull()

        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
