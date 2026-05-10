"""
Integration test: Build a watchlist from search results, pull data, save, chart.

Tests the full flow:
1. Search for series across sources (FRED, yfinance, coingecko, BEA, Glassnode, ABS, RBA)
2. Build watchlist with found series
3. Pull data for all series
4. Save watchlist to Excel/HDF5
5. Produce and save PNG charts to bm/tests/integration_charts/
"""

import os
import tempfile
from pathlib import Path

import pandas as pd

from bm import Watchlist, WatchlistSearch
from bm.dataset import Dataset


def test_watchlist_build_from_search():
    """Build watchlist from search, pull data, save, chart."""

    ws = WatchlistSearch()
    wl = Watchlist(name='search_integration_test')
    ds = Dataset()

    # ---- FRED ----
    print("Searching FRED...")
    fred_unrate = ws.search('fred', 'UNRATE')  # Unemployment Rate
    if len(fred_unrate) > 0:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': 'UNRATE',
            'source': 'fred',
            'title': 'Civilian Unemployment Rate'
        }])], ignore_index=True)

    fred_gdp = ws.search('fred', 'GDPC1')  # Real GDP
    if len(fred_gdp) > 0:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': 'GDPC1',
            'source': 'fred',
            'title': 'Real Gross Domestic Product'
        }])], ignore_index=True)

    # ---- yfinance ----
    print("Searching yfinance...")
    yf_aapl = ws.search('yfinance', 'AAPL')
    if len(yf_aapl) > 0:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': yf_aapl.iloc[0]['id'],
            'source': 'yfinance',
            'title': yf_aapl.iloc[0]['title']
        }])], ignore_index=True)

    yf_spy = ws.search('yfinance', 'SPY')
    if len(yf_spy) > 0:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': yf_spy.iloc[0]['id'],
            'source': 'yfinance',
            'title': yf_spy.iloc[0]['title']
        }])], ignore_index=True)

    # ---- CoinGecko ----
    print("Searching CoinGecko...")
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

    # ---- CryptoCompare (better free crypto history than CoinGecko) ----
    print("Searching CryptoCompare...")
    cc_btc = ws.search('cryptocompare', 'BTC')
    if len(cc_btc) > 0:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': 'BTC,USD',  # CryptoCompare uses fsym,tsym format
            'source': 'cryptocompare',
            'title': 'Bitcoin (CryptoCompare)'
        }])], ignore_index=True)

    cc_eth = ws.search('cryptocompare', 'ETH')
    if len(cc_eth) > 0:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': 'ETH,USD',
            'source': 'cryptocompare',
            'title': 'Ethereum (CryptoCompare)'
        }])], ignore_index=True)

    # ---- BEA ----
    print("Searching BEA...")
    wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
        'id': 'NIPA,T10101',
        'source': 'bea',
        'title': 'BEA NIPA T10101'
    }])], ignore_index=True)

    wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
        'id': 'NIPA,T20100',
        'source': 'bea',
        'title': 'BEA NIPA T20100'
    }])], ignore_index=True)

    # ---- Glassnode ----
    print("Searching Glassnode...")
    gn_price = ws.search('glassnode', '/market/price_usd_close')
    if len(gn_price) > 0:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': '/market/price_usd_close,BTC,24h',
            'source': 'glassnode',
            'title': 'BTC Price USD'
        }])], ignore_index=True)

    gn_addr = ws.search('glassnode', '/addresses/count')
    if len(gn_addr) > 0:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': f'{gn_addr.iloc[0]["id"]},BTC,24h',
            'source': 'glassnode',
            'title': 'BTC Active Addresses'
        }])], ignore_index=True)

    # ---- ABS ----
    print("Searching ABS...")
    abs_unemp = ws.search('abs', 'unemployment rate')
    if len(abs_unemp) > 0:
        # Find the unemployment rate series (A84423050A, not the government benefits one)
        for _, row in abs_unemp.iterrows():
            if row['id'] == 'A84423050A':
                wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
                    'id': 'A84423050A,6202.0',
                    'source': 'abs',
                    'title': row['title']
                }])], ignore_index=True)
                break

    abs_wage = ws.search('abs', 'wage')
    if len(abs_wage) > 0:
        row = abs_wage.iloc[0]
        cat_num = row.get('meta', {}).get('Catalogue number', '6306.0')
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': f'{row["id"]},{cat_num}',
            'source': 'abs',
            'title': row['title']
        }])], ignore_index=True)

    # ---- RBA ----
    print("Searching RBA...")
    # RBA tables are identified by table code (e.g., A2, F12)
    # For series we need to use series IDs like ARBAMPCNCRT for cash rate
    rba_cash = ws.search('rba', 'cash rate')
    if len(rba_cash) > 0:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': 'ARBAMPCNCRT',  # RBA Cash Rate series ID
            'source': 'rba',
            'title': 'RBA Official Cash Rate'
        }])], ignore_index=True)

    rba_fx = ws.search('rba', 'exchange')
    if len(rba_fx) > 0:
        wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
            'id': 'A4',  # Use table A4 for exchange rates (foreign exchange transactions)
            'source': 'rba',
            'title': 'RBA Foreign Exchange Transactions'
        }])], ignore_index=True)

    # ---- Trading Economics (tedata) ----
    # Note: tedata uses Selenium and is slow — only search if browser available
    try:
        print("Searching tedata (slow — Selenium)...")
        te_results = ws.search('tedata', 'crude oil')
        if len(te_results) > 0:
            first_result = te_results.iloc[0]
            wl.watchlist = pd.concat([wl.watchlist, pd.DataFrame([{
                'id': first_result['id'],
                'source': 'tedata',
                'title': first_result['title']
            }])], ignore_index=True)
    except Exception as e:
        print(f"  tedata search unavailable (browser issue): {e}")

    print(f"\nWatchlist built with {len(wl.watchlist)} entries:")
    print(wl.watchlist.to_string())

    # ---- Pull Data ----
    print("\nPulling data for all series...")
    errors = wl.get_watchlist_data(start_date='2023-01-01', end_date='2024-12-31')
    if errors:
        print(f"Errors during pull: {errors}")
    print(f"Pull complete. Datasets: {list(wl.datasets.keys())}")

    # ---- Save Watchlist ----
    charts_dir = Path('/home/totabilcat/Documents/Code/Bootleg_Macro/bm/tests/integration_charts')
    charts_dir.mkdir(parents=True, exist_ok=True)

    xlsx_path = charts_dir / 'search_integration_test.xlsx'
    print(f"\nSaving watchlist to {xlsx_path}...")
    wl.save_watchlist(str(xlsx_path))

    # Verify files exist
    h5s_path = xlsx_path.with_suffix('.h5s')
    print(f"  xlsx exists: {xlsx_path.exists()}")
    print(f"  h5s exists: {h5s_path.exists()}")

    # ---- Save Charts ----
    print(f"\nSaving charts to {charts_dir}...")
    for sid in wl.datasets.keys():
        series = wl.datasets[sid]
        # Convert timezone-aware index to UTC then make naive
        if hasattr(series.index, 'tz') and series.index.tz is not None:
            series = series.copy()
            series.index = series.index.tz_convert('UTC').tz_localize(None)

        print(f"  {sid}: {len(series)} points", end="")
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(series.index, series.values, linewidth=1)
            ax.set_title(f"{sid}")
            ax.set_xlabel('Date')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()

            safe_name = sid.replace('/', '_').replace(',', '_').replace(':', '_')
            chart_path = charts_dir / f"{safe_name}.png"
            fig.savefig(chart_path, dpi=100, bbox_inches='tight')
            plt.close(fig)
            print(f" -> saved {chart_path.name}")
        except Exception as e:
            print(f" -> error: {e}")

    # List all saved charts
    saved = list(charts_dir.glob('*.png'))
    print(f"\n=== Integration test complete ===")
    print(f"Watchlist entries: {len(wl.watchlist)}")
    print(f"Datasets pulled: {len(wl.datasets)}")
    print(f"Pull errors: {errors}")
    print(f"Charts saved: {len(saved)}")
    print(f"Chart files: {[p.name for p in saved]}")


if __name__ == '__main__':
    test_watchlist_build_from_search()