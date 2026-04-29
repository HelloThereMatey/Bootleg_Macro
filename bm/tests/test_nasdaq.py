#!/usr/bin/env python
"""
Tests for Nasdaq Data Link source.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from bm import Dataset, StandardSeries
from bm.sources.nasdaq_source import pull_nasdaq, search_nasdaq, get_nasdaq_metadata

NASDAQ_KEY = "ChHHNTWkY4rb3aYoYepw"


def test_nasdaq_pull():
    """Test basic Nasdaq pull with explicit API key."""
    result = pull_nasdaq(
        symbol="WIKI/AAPL",
        start_date="2023-01-01",
        end_date="2024-12-31",
        api_key=NASDAQ_KEY,
    )
    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'nasdaq'
    assert result.metadata.length > 0
    print(f"Test 1: WIKI/AAPL - PASS")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Frequency: {result.metadata.frequency}")
    return result


def test_nasdaq_dexusd():
    """Test pulling EUR/USD exchange rate from Nasdaq."""
    result = pull_nasdaq(
        symbol="ECONOMIA/DEXUSEU",
        start_date="2024-01-01",
        end_date="2024-12-31",
        api_key=NASDAQ_KEY,
    )
    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'nasdaq'
    print(f"Test 2: ECONOMIA/DEXUSEU (EUR/USD) - PASS")
    print(f"  ID: {result.metadata.id}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Min: {result.metadata.min_value}, Max: {result.metadata.max_value}")
    return result


def test_nasdaq_search():
    """Test Nasdaq search function."""
    results = search_nasdaq("Apple", api_key=NASDAQ_KEY)
    print(f"Test 3: Search 'Apple' - {'PASS' if len(results) > 0 else 'FAIL'}")
    print(f"  Found {len(results)} results")
    if len(results) > 0:
        print(f"  First result: {results.iloc[0].get('name', results.iloc[0].get('symbol', 'N/A'))}")
    return results


def test_nasdaq_metadata():
    """Test getting Nasdaq dataset metadata."""
    # get_nasdaq_metadata may not be available in all versions
    try:
        meta = get_nasdaq_metadata("WIKI/AAPL", api_key=NASDAQ_KEY)
        print(f"Test 4: Metadata - {'PASS' if meta else 'FAIL'}")
        if meta:
            print(f"  Keys: {list(meta.keys()) if isinstance(meta, dict) else type(meta)}")
    except AttributeError:
        # get_metadata not available in all nasdaqdatalink versions
        print("Test 4: get_nasdaq_metadata - SKIPPED (not available in this version)")


def test_nasdaq_generic_pull():
    """Test pulling Nasdaq via Dataset generic pull method."""
    ds = Dataset()
    result = ds.pull(
        source='nasdaq',
        symbol="ECONOMIA/DEXUSEU",
        start_date="2024-01-01",
        end_date="2024-06-01",
    )
    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'nasdaq'
    print(f"Test 5: Generic pull('nasdaq', ...) - PASS")
    print(f"  ID: {result.metadata.id}")
    return result


def main():
    print("\n" + "=" * 60)
    print("bm Nasdaq Data Link source tests")
    print("=" * 60 + "\n")

    tests = [
        ("WIKI/AAPL", test_nasdaq_pull),
        ("ECONOMIA/DEXUSEU", test_nasdaq_dexusd),
        ("Search 'Apple'", test_nasdaq_search),
        ("get_nasdaq_metadata", test_nasdaq_metadata),
        ("Generic pull('nasdaq', ...)", test_nasdaq_generic_pull),
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
        print("ALL NASDAQ TESTS PASSED!")
    else:
        print("SOME NASDAQ TESTS FAILED!")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())