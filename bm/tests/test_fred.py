#!/usr/bin/env python
"""
Tests for FRED source.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bm import Dataset, StandardSeries
from bm.sources.fred_source import pull_fred, search_fred


FRED_KEY = "f632119c4e0599a3229fec5a9ac83b1c"


def test_fred_gdp():
    """Test pulling GDP data from FRED."""
    result = pull_fred(
        series_id='GDP',
        api_key=FRED_KEY,
        start_date='2023-01-01',
        end_date='2024-12-31',
    )

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'fred'
    assert result.metadata.id == 'GDP'
    assert result.metadata.length > 0

    print(f"Test 1: GDP - PASS")
    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Frequency: {result.metadata.frequency}")
    print(f"  Units: {result.metadata.units}")
    print(f"  Start: {result.metadata.start_date}")
    print(f"  End: {result.metadata.end_date}")
    return result


def test_fred_unemployment():
    """Test pulling unemployment rate from FRED."""
    result = pull_fred(
        series_id='UNRATE',
        api_key=FRED_KEY,
        start_date='2024-01-01',
        end_date='2024-12-31',
    )

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'fred'
    print(f"Test 2: UNRATE (Unemployment) - PASS")
    print(f"  ID: {result.metadata.id}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Min: {result.metadata.min_value}, Max: {result.metadata.max_value}")
    return result


def test_fred_federal_funds():
    """Test pulling Federal Funds Rate."""
    result = pull_fred(
        series_id='FEDFUNDS',
        api_key=FRED_KEY,
    )

    assert isinstance(result, StandardSeries)
    print(f"Test 3: FEDFUNDS (Fed Funds Rate) - PASS")
    print(f"  ID: {result.metadata.id}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Min: {result.metadata.min_value}, Max: {result.metadata.max_value}")
    return result


def test_fred_search():
    """Test FRED search function."""
    results = search_fred('inflation', api_key=FRED_KEY)
    print(f"Test 4: Search 'inflation' - {'PASS' if len(results) > 0 else 'FAIL'}")
    print(f"  Found {len(results)} series")
    if len(results) > 0:
        print(f"  First: {results.iloc[0].get('series_id', 'N/A')} - {results.iloc[0].get('title', 'N/A')[:50]}")
    return results


def test_fred_via_dataset():
    """Test pulling FRED via Dataset class."""
    ds = Dataset()
    result = ds.pull_fred(series_id='GDP', start_date='2024-01-01', end_date='2024-06-01')

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'fred'
    assert result.metadata.length > 0
    print(f"Test 5: Dataset.pull_fred('GDP') - PASS")
    print(f"  Length: {result.metadata.length}")
    return result


def test_fred_generic_pull():
    """Test pulling FRED via generic pull() method."""
    ds = Dataset()
    result = ds.pull(source='fred', series_id='DGS10', start_date='2024-01-01', end_date='2024-12-31')

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'fred'
    assert result.metadata.id == 'DGS10'
    print(f"Test 6: Generic pull('fred', ...) - PASS")
    print(f"  ID: {result.metadata.id}, Title: {result.metadata.title[:40]}")
    return result


def main():
    print("\n" + "=" * 60)
    print("bm FRED source tests")
    print("=" * 60 + "\n")

    tests = [
        ("GDP", test_fred_gdp),
        ("UNRATE", test_fred_unemployment),
        ("FEDFUNDS", test_fred_federal_funds),
        ("Search 'inflation'", test_fred_search),
        ("Dataset.pull_fred()", test_fred_via_dataset),
        ("Generic pull('fred', ...)", test_fred_generic_pull),
    ]

    all_passed = True
    for name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL FRED TESTS PASSED!")
    else:
        print("SOME FRED TESTS FAILED!")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())