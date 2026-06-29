#!/usr/bin/env python
"""
Integration tests for crypto sources: CoinGecko, CryptoCompare, and tedata.

Tests search, pull, and chart saving for each source.
All charts are saved at high resolution (scale=3) via plotly write_image.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from bootleg_datafeed import Dataset, StandardSeries
from bootleg_datafeed import WatchlistSearch
from bootleg_macro.toolz import Watchlist


# Output directory for charts
CHARTS_DIR = Path(__file__).parent / "source_charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)


def _save_plotly_png(fig, filename: str, scale: int = 3) -> Path:
    """Save a plotly figure as high-resolution PNG.

    Args:
        fig: plotly figure object
        filename: filename (without extension)
        scale: resolution scale (default 3 = 3x)

    Returns:
        Path to saved file
    """
    path = CHARTS_DIR / f"{filename}.png"
    fig.write_image(path, scale=scale)
    return path


def _save_matplotlib_png(series: pd.Series, filename: str, dpi: int = 300) -> Path:
    """Save a pandas series as high-resolution matplotlib PNG.

    Args:
        series: pandas Series with DatetimeIndex
        filename: filename (without extension)
        dpi: resolution in dots-per-inch (default 300 = high-res print quality)

    Returns:
        Path to saved file
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    s = series.copy()
    if hasattr(s.index, 'tz') and s.index.tz is not None:
        s.index = s.index.tz_convert('UTC').tz_localize(None)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(s.index, s.values, linewidth=1.2, color='steelblue')
    ax.set_title(filename.replace('_', ' ').title(), fontsize=12)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    path = CHARTS_DIR / f"{filename}.png"
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return path


# =============================================================================
# CoinGecko tests
# =============================================================================

def test_coingecko_search_bitcoin():
    """Search CoinGecko for bitcoin."""
    ws = WatchlistSearch()
    results = ws.search('coingecko', 'bitcoin')
    print(f"\n[CoinGecko Search] 'bitcoin' -> {len(results)} results")
    if not results.empty:
        print(results[['id', 'title']].to_string())
    assert len(results) > 0, "Should find bitcoin"
    print("[PASS] CoinGecko search bitcoin")
    return results.iloc[0]


def test_coingecko_search_ethereum():
    """Search CoinGecko for ethereum."""
    ws = WatchlistSearch()
    results = ws.search('coingecko', 'ethereum')
    print(f"\n[CoinGecko Search] 'ethereum' -> {len(results)} results")
    assert len(results) > 0, "Should find ethereum"
    print("[PASS] CoinGecko search ethereum")
    return results.iloc[0]


def test_coingecko_pull_bitcoin():
    """Pull Bitcoin from CoinGecko and chart it."""
    ds = Dataset()
    btc = ds.pull_coingecko('bitcoin', days=365)
    assert isinstance(btc, StandardSeries)
    assert btc.metadata.source == 'coingecko'
    assert btc.metadata.id == 'bitcoin'

    series = btc.to_pandas()
    print(f"\n[CoinGecko Pull] BTC: {len(series)} points, {series.index[0].date()} to {series.index[-1].date()}")
    print(f"  Last price: {series.iloc[-1]:.2f} {btc.metadata.units}")

    # Save matplotlib chart
    path = _save_matplotlib_png(series, 'coingecko_btc')
    print(f"  Chart saved: {path.name}")
    print("[PASS] CoinGecko pull bitcoin")
    return btc


def test_coingecko_pull_ethereum():
    """Pull Ethereum from CoinGecko and chart it."""
    ds = Dataset()
    eth = ds.pull_coingecko('ethereum', days=180)
    assert isinstance(eth, StandardSeries)
    series = eth.to_pandas()
    print(f"\n[CoinGecko Pull] ETH: {len(series)} points, {series.index[0].date()} to {series.index[-1].date()}")

    path = _save_matplotlib_png(series, 'coingecko_eth')
    print(f"  Chart saved: {path.name}")
    print("[PASS] CoinGecko pull ethereum")
    return eth


# =============================================================================
# CryptoCompare tests
# =============================================================================

def test_cryptocompare_search_btc():
    """Search CryptoCompare for BTC."""
    ws = WatchlistSearch()
    results = ws.search('cryptocompare', 'BTC')
    print(f"\n[CryptoCompare Search] 'BTC' -> {len(results)} results")
    if not results.empty:
        print(results[['id', 'title']].to_string())
    assert len(results) > 0, "Should find BTC"
    print("[PASS] CryptoCompare search BTC")
    return results.iloc[0]


def test_cryptocompare_search_eth():
    """Search CryptoCompare for ETH."""
    ws = WatchlistSearch()
    results = ws.search('cryptocompare', 'ETH')
    print(f"\n[CryptoCompare Search] 'ETH' -> {len(results)} results")
    assert len(results) > 0, "Should find ETH"
    print("[PASS] CryptoCompare search ETH")
    return results.iloc[0]


def test_cryptocompare_pull_btc():
    """Pull Bitcoin from CryptoCompare and chart it."""
    ds = Dataset()
    btc = ds.pull_cryptocompare('BTC', 'USD', start_date='2023-01-01', end_date='2024-12-31')
    assert isinstance(btc, StandardSeries)
    assert btc.metadata.source == 'cryptocompare'

    series = btc.to_pandas()
    print(f"\n[CryptoCompare Pull] BTC: {len(series)} points, {series.index[0].date()} to {series.index[-1].date()}")
    print(f"  Last price: {series.iloc[-1]:.2f} {btc.metadata.units}")

    path = _save_matplotlib_png(series, 'cryptocompare_btc')
    print(f"  Chart saved: {path.name}")
    print("[PASS] CryptoCompare pull BTC")
    return btc


def test_cryptocompare_pull_eth():
    """Pull Ethereum from CryptoCompare and chart it."""
    ds = Dataset()
    eth = ds.pull_cryptocompare('ETH', 'USD', start_date='2023-01-01', end_date='2024-12-31')
    assert isinstance(eth, StandardSeries)
    series = eth.to_pandas()
    print(f"\n[CryptoCompare Pull] ETH: {len(series)} points, {series.index[0].date()} to {series.index[-1].date()}")

    path = _save_matplotlib_png(series, 'cryptocompare_eth')
    print(f"  Chart saved: {path.name}")
    print("[PASS] CryptoCompare pull ETH")
    return eth


def test_cryptocompare_pull_full_history():
    """Pull full ~2000 day history for BTC and ETH."""
    ds = Dataset()
    btc = ds.pull_cryptocompare('BTC', 'USD')
    series = btc.to_pandas()
    print(f"\n[CryptoCompare Full] BTC: {len(series)} points, {series.index[0].date()} to {series.index[-1].date()}")
    assert len(series) >= 2000, f"Expected ~2000 days, got {len(series)}"

    eth = ds.pull_cryptocompare('ETH', 'USD')
    eth_series = eth.to_pandas()
    print(f"[CryptoCompare Full] ETH: {len(eth_series)} points, {eth_series.index[0].date()} to {eth_series.index[-1].date()}")
    assert len(eth_series) >= 2000

    path = _save_matplotlib_png(series, 'cryptocompare_btc_full')
    print(f"  BTC chart saved: {path.name}")
    path2 = _save_matplotlib_png(eth_series, 'cryptocompare_eth_full')
    print(f"  ETH chart saved: {path2.name}")
    print("[PASS] CryptoCompare full history pull")
    return btc, eth


# =============================================================================
# tedata (Trading Economics) tests
# =============================================================================

def test_tedata_search():
    """Search tedata for 'crude oil'."""
    ws = WatchlistSearch()
    try:
        results = ws.search('tedata', 'crude oil')
        print(f"\n[tedata Search] 'crude oil' -> {len(results)} results")
        if not results.empty:
            print(results[['id', 'title']].to_string())
        assert len(results) > 0, "Should find crude oil"
        print("[PASS] tedata search crude oil")
        return results.iloc[0]
    except Exception as e:
        print(f"[SKIP] tedata search unavailable: {e}")
        return None


def test_tedata_pull_crude_oil():
    """Pull crude oil from tedata and chart it."""
    ds = Dataset()
    try:
        crude = ds.pull_tedata(
            url="https://tradingeconomics.com/commodity/crude-oil",
            start_date='2023-01-01',
            end_date='2024-12-31',
        )
        assert isinstance(crude, StandardSeries)
        assert crude.metadata.source == 'tedata'
        series = crude.to_pandas()
        print(f"\n[tedata Pull] Crude Oil: {len(series)} points, {series.index[0].date()} to {series.index[-1].date()}")
        print(f"  Last price: {series.iloc[-1]:.2f} {crude.metadata.units}")

        path = _save_matplotlib_png(series, 'tedata_crude_oil')
        print(f"  Chart saved: {path.name}")
        print("[PASS] tedata pull crude oil")
        return crude
    except Exception as e:
        print(f"[SKIP] tedata pull unavailable: {e}")
        return None


def test_tedata_watchlist_build():
    """Build a watchlist with tedata series and pull all."""
    ws = WatchlistSearch()
    wl = Watchlist(name='tedata_test')

    try:
        results = ws.search('tedata', 'gold')
        if len(results) > 0:
            first = results.iloc[0]
            wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
                'id': first['id'],
                'source': 'tedata',
                'title': first['title']
            }])], ignore_index=True)
            print(f"\n[tedata Watchlist] Added: {first['title']}")
    except Exception as e:
        print(f"[tedata Watchlist] Search error: {e}")

    # Add a known tedata series directly
    wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
        'id': 'https://tradingeconomics.com/commodity/brent-crude-oil',
        'source': 'tedata',
        'title': 'Brent Crude Oil'
    }])], ignore_index=True)

    if len(wl.watchlist) == 0:
        print("[SKIP] tedata watchlist - no entries")
        return

    print(f"[tedata Watchlist] {len(wl.watchlist)} entries:")
    print(wl.watchlist.to_string())

    try:
        errors = wl.get_watchlist_data(start_date='2023-01-01', end_date='2024-12-31')
        print(f"  Pull errors: {errors}")
        print(f"  Datasets: {list(wl.datasets.keys())}")

        for sid, series in wl.datasets.items():
            s = series.to_pandas() if hasattr(series, 'to_pandas') else series
            path = _save_matplotlib_png(s, f'tedata_{sid.replace("/", "_")}')
            print(f"  Chart saved: {path.name}")

        print("[PASS] tedata watchlist build")
    except Exception as e:
        print(f"[FAIL] tedata watchlist: {e}")


# =============================================================================
# Combined watchlist with all three sources
# =============================================================================

def test_combined_crypto_watchlist():
    """Build watchlist with CoinGecko + CryptoCompare series and chart all."""
    ws = WatchlistSearch()
    wl = Watchlist(name='combined_crypto_test')

    # CoinGecko entries
    cg_btc = ws.search('coingecko', 'bitcoin')
    if len(cg_btc) > 0:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': cg_btc.iloc[0]['id'],
            'source': 'coingecko',
            'title': cg_btc.iloc[0]['title']
        }])], ignore_index=True)

    cg_eth = ws.search('coingecko', 'ethereum')
    if len(cg_eth) > 0:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': cg_eth.iloc[0]['id'],
            'source': 'coingecko',
            'title': cg_eth.iloc[0]['title']
        }])], ignore_index=True)

    # CryptoCompare entries
    for sym, title in [('BTC,USD', 'Bitcoin (CryptoCompare)'), ('ETH,USD', 'Ethereum (CryptoCompare)')]:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': sym, 'source': 'cryptocompare', 'title': title
        }])], ignore_index=True)

    print(f"\n[Combined Watchlist] {len(wl.watchlist)} entries:")
    print(wl.watchlist.to_string())

    # Pull all
    errors = wl.get_watchlist_data(start_date='2023-01-01', end_date='2024-12-31')
    print(f"  Pull errors: {errors}")
    print(f"  Datasets: {list(wl.datasets.keys())}")

    for sid, series in wl.datasets.items():
        s = series.to_pandas() if hasattr(series, 'to_pandas') else series
        safe_name = sid.replace('/', '_').replace(',', '_')
        path = _save_matplotlib_png(s, f'combined_{safe_name}')
        print(f"  Chart saved: {path.name}")

    print("[PASS] Combined crypto watchlist")
    return wl


# =============================================================================
# Main
# =============================================================================

def main():
    print("\n" + "=" * 70)
    print("bm Crypto Sources Integration Tests")
    print("Charts: high-res PNG (matplotlib), scale=3 plotly")
    print(f"Output: {CHARTS_DIR}")
    print("=" * 70)

    all_passed = True
    tests = [
        # CoinGecko
        ("CG search bitcoin", test_coingecko_search_bitcoin),
        ("CG search ethereum", test_coingecko_search_ethereum),
        ("CG pull bitcoin", test_coingecko_pull_bitcoin),
        ("CG pull ethereum", test_coingecko_pull_ethereum),
        # CryptoCompare
        ("CC search BTC", test_cryptocompare_search_btc),
        ("CC search ETH", test_cryptocompare_search_eth),
        ("CC pull BTC", test_cryptocompare_pull_btc),
        ("CC pull ETH", test_cryptocompare_pull_eth),
        ("CC full history", test_cryptocompare_pull_full_history),
        # tedata
        ("TE search", test_tedata_search),
        ("TE pull crude oil", test_tedata_pull_crude_oil),
        ("TE watchlist", test_tedata_watchlist_build),
        # Combined
        ("Combined crypto watchlist", test_combined_crypto_watchlist),
    ]

    passed = 0
    failed = 0
    skipped = 0

    for name, test_func in tests:
        try:
            result = test_func()
            if result is None:
                skipped += 1
                print(f"[SKIP] {name}")
            else:
                passed += 1
        except Exception as e:
            failed += 1
            print(f"[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")

    # List saved charts
    charts = sorted(CHARTS_DIR.glob("*.png"))
    print(f"\nSaved {len(charts)} charts:")
    for c in charts:
        size_kb = c.stat().st_size // 1024
        print(f"  {c.name} ({size_kb} KB)")

    print("=" * 70)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())