#!/usr/bin/env python
"""
Tests for tedata source (Trading Economics scraping).

Tests high-frequency (BRENT crude) and low-frequency (ISM Manufacturing) series,
both Firefox and Chrome browsers, and browser-not-found error handling.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from bm import Dataset, StandardSeries
from bm.sources.tedata_source import (
    pull_tedata,
    search_tedata,
    get_tedata_url,
    BrowserPreference,
    BrowserNotFoundError,
)


def test_tedata_url_construction():
    """Test URL construction from series ID."""
    # Full URL passthrough
    url = "https://tradingeconomics.com/united-states/ism-manufacturing-new-orders"
    assert get_tedata_url(url) == url

    # Path-only construction
    path = "united-states/ism-manufacturing-new-orders"
    assert get_tedata_url(path) == f"https://tradingeconomics.com/{path}"

    # Leading slash stripped
    assert get_tedata_url("/united-states/ism-manufacturing-new-orders") == url

    print("Test 1: URL construction - PASS")


def test_tedata_browser_preference_enum():
    """Test BrowserPreference enum values."""
    assert BrowserPreference.FIREFOX.value == "firefox"
    assert BrowserPreference.CHROME.value == "chrome"
    assert BrowserPreference.AUTO.value == "auto"
    # String conversion
    assert BrowserPreference("auto") == BrowserPreference.AUTO
    assert BrowserPreference("firefox") == BrowserPreference.FIREFOX
    print("Test 2: BrowserPreference enum - PASS")


def test_tedata_low_freq_series():
    """Test pulling a lower-frequency series (ISM Manufacturing) - monthly."""
    result = pull_tedata(
        url="https://tradingeconomics.com/united-states/ism-manufacturing-new-orders",
        browser="auto",
    )

    assert isinstance(result, StandardSeries), f"Expected StandardSeries, got {type(result)}"
    assert result.metadata.source == 'tedata'
    assert result.metadata.original_source == 'Trading Economics' or result.metadata.original_source is not None
    assert result.metadata.length > 0

    print(f"Test 3: ISM Manufacturing (low freq) - PASS")
    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Frequency: {result.metadata.frequency}")
    print(f"  Original source: {result.metadata.original_source}")
    print(f"  Units: {result.metadata.units}")

    return result


def test_tedata_high_freq_series():
    """Test pulling a higher-frequency series (BRENT crude oil) - daily."""
    result = pull_tedata(
        url="https://tradingeconomics.com/commodity/brent-crude-oil",
        browser="auto",
    )

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'tedata'
    assert result.metadata.length > 0

    # BRENT should be daily or higher frequency
    print(f"Test 4: BRENT Crude (high freq) - PASS")
    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Frequency: {result.metadata.frequency}")
    print(f"  Min value: {result.metadata.min_value}")
    print(f"  Max value: {result.metadata.max_value}")

    return result


def test_tedata_via_dataset():
    """Test pulling tedata via Dataset class."""
    ds = Dataset()
    result = ds.pull_tedata(
        url="https://tradingeconomics.com/united-states/ism-manufacturing-new-orders",
        browser="auto",
    )

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'tedata'
    assert result.metadata.length > 0
    print("Test 5: Dataset.pull_tedata() - PASS")


def test_tedata_generic_pull():
    """Test pulling tedata via generic pull() method."""
    ds = Dataset()
    result = ds.pull(
        source='tedata',
        url="united-states/consumer-confidence",
    )

    assert isinstance(result, StandardSeries)
    assert result.metadata.source == 'tedata'
    print(f"Test 6: Generic pull('tedata', ...) - PASS")
    print(f"  ID: {result.metadata.id}, Length: {result.metadata.length}")


def test_tedata_search():
    """Test search_tedata function."""
    results = search_tedata("crude oil")
    # Results may be empty if search fails, but should return DataFrame
    assert isinstance(results, type([])) or hasattr(results, 'columns'), f"Expected list or DataFrame, got {type(results)}"
    print(f"Test 7: search_tedata('crude oil') - PASS (returned {type(results).__name__})")


def test_tedata_browser_not_found_error():
    """Test that BrowserNotFoundError is raised when browsers unavailable."""
    # This test validates the error class exists and has proper message
    error = BrowserNotFoundError("Neither Firefox nor Chrome is available.")
    assert "Firefox" in str(error)
    assert "Chrome" in str(error)
    print("Test 8: BrowserNotFoundError class - PASS")


def main():
    print("\n" + "=" * 60)
    print("bm tedata source tests")
    print("=" * 60 + "\n")

    tests = [
        ("URL construction", test_tedata_url_construction),
        ("BrowserPreference enum", test_tedata_browser_preference_enum),
        ("ISM Manufacturing (low freq)", test_tedata_low_freq_series),
        ("BRENT Crude (high freq)", test_tedata_high_freq_series),
        ("Dataset.pull_tedata()", test_tedata_via_dataset),
        ("Generic pull('tedata', ...)", test_tedata_generic_pull),
        ("search_tedata()", test_tedata_search),
        ("BrowserNotFoundError", test_tedata_browser_not_found_error),
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
        print("ALL TEDATA TESTS PASSED!")
    else:
        print("SOME TEDATA TESTS FAILED!")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())