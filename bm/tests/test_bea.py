"""Tests for BEA source."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from bm import Dataset

BEA_KEY = "779F26DA-1DB0-4CC2-94DD-2AE3492DA4FC"


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
    from bm.sources.bea_source import list_bea_datasets
    datasets = list_bea_datasets(api_key=BEA_KEY)
    print(f"Test 2: List datasets - {'PASS' if len(datasets) > 0 else 'FAIL'}")
    print(f"  Found {len(datasets)} datasets")
    if len(datasets) > 0:
        print(f"  First: {datasets.iloc[0].to_dict()}")


def test_bea_search_tables():
    """Test searching BEA tables."""
    from bm.sources.bea_source import search_bea_tables
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
