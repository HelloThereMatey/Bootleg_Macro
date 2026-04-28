"""Tests for Nasdaq Data Link source."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from bm import Dataset

NASDAQ_KEY = "ChHHNTWkY4rb3aYoYepw"


def test_nasdaq_pull():
    """Test basic Nasdaq pull."""
    ds = Dataset()
    result = ds.pull_nasdaq(
        symbol="WIKI/AAPL",
        start_date="2024-01-01",
        end_date="2024-12-31",
    )
    assert result.metadata.source == 'nasdaq'
    assert result.metadata.length > 0
    print(f"Test 1: WIKI/AAPL - PASS")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Frequency: {result.metadata.frequency}")


def test_nasdaq_search():
    """Test Nasdaq search function."""
    result = search_nasdaq("Apple", api_key=NASDAQ_KEY)
    print(f"Test 2: Search results - {'PASS' if len(result) > 0 else 'FAIL'}")
    print(f"  Found {len(result)} results")
    if len(result) > 0:
        print(f"  First result: {result.iloc[0].get('name', 'N/A')}")


def test_nasdaq_metadata():
    """Test getting Nasdaq dataset metadata."""
    meta = get_nasdaq_metadata("WIKI/AAPL", api_key=NASDAQ_KEY)
    print(f"Test 3: Metadata - {'PASS' if meta else 'FAIL'}")
    if meta:
        print(f"  Dataset: {meta.get('dataset_code', 'N/A')}")


if __name__ == "__main__":
    test_nasdaq_pull()
    test_nasdaq_search()
    test_nasdaq_metadata()
    print("\nAll Nasdaq tests complete.")
