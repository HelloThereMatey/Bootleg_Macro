#!/usr/bin/env python
"""
Comprehensive test script for bm data sources.

Tests all implemented sources and verifies placeholder behavior
for sources requiring API keys or external dependencies.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bm import Dataset, StandardSeries, SOURCES


def test_yfinance():
    """Test yfinance source - should work without API key."""
    ds = Dataset()

    print("=" * 60)
    print("Test: yfinance source")
    print("=" * 60)

    result = ds.pull_yfinance(
        ticker='AAPL',
        start_date='2024-01-01',
        end_date='2024-12-31',
    )

    assert isinstance(result, StandardSeries), f"Expected StandardSeries, got {type(result)}"
    assert result.metadata.source == 'yfinance'
    assert result.metadata.id == 'AAPL'
    assert result.metadata.length > 0

    print(f"  ID: {result.metadata.id}, Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}, Frequency: {result.metadata.frequency}")
    print("  [PASS] yfinance works!\n")

    return result


def test_coingecko():
    """Test CoinGecko source - should work without API key."""
    ds = Dataset()

    print("=" * 60)
    print("Test: CoinGecko source")
    print("=" * 60)

    result = ds.pull_coingecko(
        coin_id='bitcoin',
        days=90,
    )

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'coingecko'
    assert result.metadata.id == 'bitcoin'
    assert result.metadata.length > 0

    print(f"  ID: {result.metadata.id}, Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}, Units: {result.metadata.units}")
    print("  [PASS] CoinGecko works!\n")

    return result


def test_fred_missing_key():
    """Test FRED source - should raise error without API key."""
    ds = Dataset()

    print("=" * 60)
    print("Test: FRED source (no API key)")
    print("=" * 60)

    try:
        ds.pull_fred(series_id='GDP', start_date='2024-01-01')
        print("  [FAIL] Should have raised ValueError")
        return False
    except ValueError as e:
        if "API key required" in str(e):
            print(f"  Correctly raised: {e}")
            print("  [PASS] FRED placeholder works!\n")
            return True
        else:
            print(f"  [FAIL] Wrong error: {e}")
            return False
    except Exception as e:
        print(f"  [FAIL] Unexpected error: {e}")
        return False


def test_bea_missing_key():
    """Test BEA source - should be placeholder."""
    ds = Dataset()

    print("=" * 60)
    print("Test: BEA source (not implemented)")
    print("=" * 60)

    try:
        ds.pull_bea(dataset='NIPA', table_code='T10101')
        print("  [FAIL] Should have raised NotImplementedError")
        return False
    except NotImplementedError as e:
        print(f"  Correctly raised: {e}")
        print("  [PASS] BEA placeholder works!\n")
        return True
    except Exception as e:
        print(f"  [FAIL] Unexpected error: {e}")
        return False


def test_generic_pull():
    """Test the generic pull() method."""
    ds = Dataset()

    print("=" * 60)
    print("Test: Generic pull() method")
    print("=" * 60)

    # Test routing to yfinance
    result = ds.pull(source='yfinance', ticker='MSFT', start_date='2024-01-01')
    assert result.metadata.id == 'MSFT'
    print(f"  Routed to yfinance for {result.metadata.id}")

    # Test routing to coingecko
    result = ds.pull(source='coingecko', coin_id='ethereum', days=30)
    assert result.metadata.id == 'ethereum'
    print(f"  Routed to coingecko for {result.metadata.id}")

    print("  [PASS] Generic pull works!\n")
    return True


def test_sources_list():
    """Verify SOURCES list is properly defined."""
    print("=" * 60)
    print("Test: SOURCES list")
    print("=" * 60)

    expected_sources = [
        'yfinance', 'fred', 'bea', 'coingecko', 'nasdaq',
        'glassnode', 'abs', 'rba', 'tradingview', 'tedata'
    ]

    for source in expected_sources:
        if source in SOURCES:
            print(f"  ✓ {source}")
        else:
            print(f"  ✗ {source} MISSING")
            return False

    print("  [PASS] All expected sources in SOURCES list!\n")
    return True


def main():
    print("\n" + "=" * 60)
    print("bm comprehensive source tests")
    print("=" * 60 + "\n")

    all_passed = True
    tests = [
        ("Sources list", test_sources_list),
        ("yfinance", test_yfinance),
        ("CoinGecko", test_coingecko),
        ("FRED placeholder", test_fred_missing_key),
        ("BEA placeholder", test_bea_missing_key),
        ("Generic pull", test_generic_pull),
    ]

    for name, test_func in tests:
        try:
            result = test_func()
            if result is False:
                all_passed = False
        except Exception as e:
            print(f"  [FAIL] {name} raised unexpected error: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
