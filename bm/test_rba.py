"""Tests for RBA source."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bm import Dataset
from bm.sources.rba_source import (
    get_rba_cash_rate,
    list_rba_tables,
    search_rba_tables,
    search_rba_series,
)


def test_rba_cash_rate():
    """Test pulling RBA Official Cash Rate."""
    result = get_rba_cash_rate(monthly=True)
    assert result.metadata.source == 'rba'
    assert result.metadata.length > 0
    print(f"Test 1: RBA Cash Rate - PASS")
    print(f"  ID: {result.metadata.id}")
    print(f"  Title: {result.metadata.title}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Frequency: {result.metadata.frequency}")


def test_rba_dataset_pull():
    """Test pulling RBA via Dataset class."""
    ds = Dataset()
    result = ds.pull_rba(series_id='ARBAMPCNCRT', table_no='A2')
    assert result.metadata.source == 'rba'
    assert result.metadata.length > 0
    print(f"Test 2: Dataset.pull_rba() - PASS")
    print(f"  Length: {result.metadata.length}")


def test_rba_list_tables():
    """Test listing RBA tables."""
    tables = list_rba_tables()
    print(f"Test 3: List tables - {'PASS' if len(tables) > 0 else 'FAIL'}")
    print(f"  Found {len(tables)} tables")


def test_rba_search_tables():
    """Test searching RBA tables."""
    results = search_rba_tables('exchange rate')
    print(f"Test 4: Search tables - {'PASS' if len(results) > 0 else 'FAIL'}")
    print(f"  Found {len(results)} matching tables")
    if len(results) > 0:
        print(f"  First: {results.iloc[0].to_dict()}")


if __name__ == "__main__":
    test_rba_cash_rate()
    test_rba_dataset_pull()
    test_rba_list_tables()
    test_rba_search_tables()
    print("\nAll RBA tests complete.")
