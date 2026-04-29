#!/usr/bin/env python
"""
Test script for ABS source in bm.

Tests that we can download 3 time series from the Australian Bureau of Statistics
and that they conform to the StandardSeries format.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bm import Dataset, StandardSeries


def test_abs_unemployment():
    """Test pulling unemployment rate from ABS."""
    ds = Dataset()

    print("=" * 60)
    print("Test 1: Pull ABS Unemployment Rate (Labour Force Survey)")
    print("=" * 60)

    # A84423050A is unemployment rate in 6202.0 (Labour Force Survey)
    result = ds.pull_abs(
        series_id='A84423050A',
        catalog_num='6202.0',
    )

    assert isinstance(result, StandardSeries), f"Expected StandardSeries, got {type(result)}"
    assert result.metadata.source == 'abs'
    assert result.metadata.start_date is not None
    assert result.metadata.end_date is not None

    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Source: {result.metadata.source}")
    print(f"  Start: {result.metadata.start_date}")
    print(f"  End: {result.metadata.end_date}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Frequency: {result.metadata.frequency}")
    if result.metadata.units:
        print(f"  Units: {result.metadata.units}")

    series = result.to_pandas()
    print(f"\n  First 5 values:\n{series.head()}")
    print("\n  [PASS] Test 1 passed!\n")

    return result


def test_abs_employed_total():
    """Test pulling total employment from ABS."""
    ds = Dataset()

    print("=" * 60)
    print("Test 2: Pull ABS Total Employment")
    print("=" * 60)

    # A85255398K is Employed total, Persons in 6202.0 (Labour Force Survey)
    result = ds.pull_abs(
        series_id='A85255398K',
        catalog_num='6202.0',
    )

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'abs'

    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")

    series = result.to_pandas()
    print(f"\n  First 5 values:\n{series.head()}")
    print("\n  [PASS] Test 2 passed!\n")

    return result


def test_abs_employed_females():
    """Test pulling female employment from ABS."""
    ds = Dataset()

    print("=" * 60)
    print("Test 3: Pull ABS Female Employment")
    print("=" * 60)

    # A85255158X is Employed total, Females in 6202.0 (Labour Force Survey)
    result = ds.pull_abs(
        series_id='A85255158X',
        catalog_num='6202.0',
    )

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'abs'

    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")

    series = result.to_pandas()
    print(f"\n  First 5 values:\n{series.head()}")
    print("\n  [PASS] Test 3 passed!\n")

    return result


def main():
    print("\n" + "=" * 60)
    print("bm ABS source tests")
    print("=" * 60 + "\n")

    try:
        test_abs_unemployment()
        test_abs_employed_total()
        test_abs_employed_females()

        print("=" * 60)
        print("ALL ABS TESTS PASSED!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
