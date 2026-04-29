#!/usr/bin/env python
"""
Test script for coingecko source in bm.

Tests that we can download 3 cryptocurrencies from CoinGecko and that
they conform to the StandardSeries format.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bm import Dataset, StandardSeries


def test_coingecko_bitcoin():
    """Test pulling Bitcoin data."""
    ds = Dataset()

    print("=" * 60)
    print("Test 1: Pull Bitcoin (BTC) from CoinGecko")
    print("=" * 60)

    result = ds.pull_coingecko(
        coin_id='bitcoin',
        days=365,
    )

    assert isinstance(result, StandardSeries), f"Expected StandardSeries, got {type(result)}"
    assert result.metadata.source == 'coingecko', f"Source should be 'coingecko', got {result.metadata.source}"
    assert result.metadata.id == 'bitcoin', f"ID should be 'bitcoin', got {result.metadata.id}"
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

    series = result.to_pandas()
    assert len(series) > 0, "Series should have data points"

    print(f"\n  First 5 values:\n{series.head()}")
    print("\n  [PASS] Test 1 passed!\n")

    return result


def test_coingecko_ethereum():
    """Test pulling Ethereum data."""
    ds = Dataset()

    print("=" * 60)
    print("Test 2: Pull Ethereum (ETH) from CoinGecko")
    print("=" * 60)

    result = ds.pull_coingecko(
        coin_id='ethereum',
        days=180,
    )

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'coingecko'
    assert result.metadata.id == 'ethereum'

    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Units: {result.metadata.units}")

    series = result.to_pandas()
    print(f"\n  First 5 values:\n{series.head()}")
    print("\n  [PASS] Test 2 passed!\n")

    return result


def test_coingecko_dogecoin():
    """Test pulling Dogecoin data."""
    ds = Dataset()

    print("=" * 60)
    print("Test 3: Pull Dogecoin (DOGE) from CoinGecko")
    print("=" * 60)

    result = ds.pull_coingecko(
        coin_id='dogecoin',
        days=90,
    )

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'coingecko'
    assert result.metadata.id == 'dogecoin'

    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")

    series = result.to_pandas()
    print(f"\n  First 5 values:\n{series.head()}")
    print("\n  [PASS] Test 3 passed!\n")

    return result


def main():
    print("\n" + "=" * 60)
    print("bm CoinGecko source tests")
    print("=" * 60 + "\n")

    try:
        test_coingecko_bitcoin()
        test_coingecko_ethereum()
        test_coingecko_dogecoin()

        print("=" * 60)
        print("ALL COINGECKO TESTS PASSED!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
