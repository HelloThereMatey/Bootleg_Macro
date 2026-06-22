"""Tests for BEA source.

API keys are loaded from the Dataset instance (reads {user_path}/system/API_Keys.json).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from bootleg_datafeed import Dataset

# Load API key from Dataset config (not hardcoded)
_ds = Dataset()
BEA_KEY = _ds.get_api_key('bea')
if not BEA_KEY:
    raise RuntimeError(
        "BEA API key not found. Add 'bea' key to your API_Keys.json "
        f"at {Path(_ds._api_keys_path) / 'API_Keys.json'} or use set_api_key('bea', 'your_key')."
    )


def test_bea_gdp():
    """Test pulling GDP data from BEA."""
    ds = Dataset()
    result = ds.pull_bea(
        dataset="NIPA",
        table_code="T10101",
        frequency="Q",
    )
    assert result.metadata.source == 'bea'
    assert result.metadata.length > 0
    print(f"Test 1: NIPA T10101 GDP - PASS")
    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Frequency: {result.metadata.frequency}")


def test_bea_list_datasets():
    """Test listing BEA datasets."""
    from bootleg_datafeed.sources.bea_source import list_bea_datasets
    datasets = list_bea_datasets(api_key=BEA_KEY)
    print(f"Test 2: List datasets - {'PASS' if len(datasets) > 0 else 'FAIL'}")
    print(f"  Found {len(datasets)} datasets")
    if len(datasets) > 0:
        print(f"  First: {datasets.iloc[0].to_dict()}")


def test_bea_search_tables():
    """Test searching BEA tables."""
    from bootleg_datafeed.sources.bea_source import search_bea_tables
    tables = search_bea_tables(dataset="NIPA", api_key=BEA_KEY)
    print(f"Test 3: Search tables - {'PASS' if len(tables) > 0 else 'FAIL'}")
    print(f"  Found {len(tables)} tables")
    if len(tables) > 0:
        print(f"  First table: {tables.iloc[0].to_dict()}")


if __name__ == "__main__":
    test_bea_gdp()
    test_bea_list_datasets()
    test_bea_search_tables()
    print("\nAll BEA tests complete.")
