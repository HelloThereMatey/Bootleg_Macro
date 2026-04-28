"""Tests for Glassnode source."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from bm import Dataset

# Note: User should provide their own Glassnode API key for testing
# The key will be loaded from API_Keys.json or passed directly


def test_glassnode_btc_price():
    """Test pulling BTC price from Glassnode."""
    ds = Dataset()
    result = ds.pull_glassnode(
        metric="/market/price_usd_close",
        asset="BTC",
        interval="24h",
    )
    assert result.metadata.source == 'glassnode'
    assert result.metadata.length > 0
    print(f"Test 1: BTC price_usd_close - PASS")
    print(f"  ID: {result.metadata.id}")
    print(f"  Length: {result.metadata.length}")
    print(f"  Frequency: {result.metadata.frequency}")


def test_glassnode_eth_price():
    """Test pulling ETH price from Glassnode."""
    ds = Dataset()
    result = ds.pull_glassnode(
        metric="/market/price_usd_close",
        asset="ETH",
        interval="24h",
    )
    assert result.metadata.source == 'glassnode'
    print(f"Test 2: ETH price_usd_close - PASS")
    print(f"  ID: {result.metadata.id}")
    print(f"  Length: {result.metadata.length}")


def test_glassnode_sol_price():
    """Test pulling SOL price from Glassnode."""
    ds = Dataset()
    result = ds.pull_glassnode(
        metric="/market/price_usd_close",
        asset="SOL",
        interval="24h",
    )
    assert result.metadata.source == 'glassnode'
    print(f"Test 3: SOL price_usd_close - PASS")
    print(f"  ID: {result.metadata.id}")
    print(f"  Length: {result.metadata.length}")


if __name__ == "__main__":
    test_glassnode_btc_price()
    test_glassnode_eth_price()
    test_glassnode_sol_price()
    print("\nAll Glassnode tests complete.")
    print("Note: User should provide their own Glassnode API key in API_Keys.json for testing.")
