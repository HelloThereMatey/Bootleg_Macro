"""Tests for TradingView source."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bm.sources.tv_source import pull_tv, search_tv, Interval


def test_pull_tv_nse():
    """Test pulling data from TradingView for NSE symbol."""
    try:
        result = pull_tv(symbol='RELIANCE', exchange='NSE', interval='1D', n_bars=100)
        assert result.metadata.source == 'tradingview'
        assert result.metadata.length > 0
        print(f"Test 1: NSE RELIANCE - PASS")
        print(f"  Length: {result.metadata.length}")
        print(f"  Start: {result.metadata.start_date}")
        print(f"  End: {result.metadata.end_date}")
        return True
    except Exception as e:
        print(f"Test 1: NSE RELIANCE - FAIL: {e}")
        return False


def test_pull_tv_nasdaq():
    """Test pulling data from TradingView for NASDAQ symbol."""
    try:
        result = pull_tv(symbol='AAPL', exchange='NASDAQ', interval='1D', n_bars=100)
        assert result.metadata.source == 'tradingview'
        assert result.metadata.length > 0
        print(f"Test 2: NASDAQ AAPL - PASS")
        print(f"  Length: {result.metadata.length}")
        print(f"  Title: {result.metadata.title}")
        return True
    except Exception as e:
        print(f"Test 2: NASDAQ AAPL - FAIL: {e}")
        return False


def test_pull_tv_hourly():
    """Test pulling hourly data."""
    try:
        result = pull_tv(symbol='AAPL', exchange='NASDAQ', interval='1H', n_bars=50)
        assert result.metadata.source == 'tradingview'
        print(f"Test 3: Hourly AAPL - PASS")
        print(f"  Length: {result.metadata.length}")
        return True
    except Exception as e:
        print(f"Test 3: Hourly AAPL - FAIL: {e}")
        return False


def test_dataset_pull_tradingview():
    """Test pulling via Dataset class."""
    from bm import Dataset
    try:
        ds = Dataset()
        result = ds.pull_tradingview(symbol='AAPL', exchange='NASDAQ', interval='1D', n_bars=50)
        assert result.metadata.source == 'tradingview'
        print(f"Test 4: Dataset.pull_tradingview() - PASS")
        print(f"  Length: {result.metadata.length}")
        return True
    except Exception as e:
        print(f"Test 4: Dataset.pull_tradingview() - FAIL: {e}")
        return False


if __name__ == "__main__":
    results = []
    results.append(test_pull_tv_nse())
    results.append(test_pull_tv_nasdaq())
    results.append(test_pull_tv_hourly())
    results.append(test_dataset_pull_tradingview())

    passed = sum(results)
    print(f"\nTradingView tests: {passed}/{len(results)} passed")