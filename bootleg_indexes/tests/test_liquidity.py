"""
Test script for liquidity index modules (GM2 + NLQ).

Downloads data, constructs indexes, plots results using bootleg_toolz.charting,
and saves outputs to the user data folder.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

# Ensure packages are importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd

from bootleg_datafeed._user_path import get_user_path
from bootleg_datafeed.dataset import Dataset

from bootleg_indexes.gm2_data_handler import Global_M2
from bootleg_indexes.nlq_clean import NLQDataFetcher, NetLiquidity

from bootleg_toolz.charting import plot_series, plot_multi, save_png, save_html, show

# ---------------------------------------------------------------------------
# Output directory under user data
# ---------------------------------------------------------------------------
OUT = Path(get_user_path()) / "LiquidityTests"
OUT.mkdir(parents=True, exist_ok=True)


# ============================================================================
# PART 1 — Global M2
# ============================================================================

def test_gm2_basic() -> Global_M2:
    """Instantiate Global_M2, download a subset of countries, build aggregates."""
    print("\n" + "=" * 70)
    print("GLOBAL M2 — BASIC TEST")
    print("=" * 70)

    gm2 = Global_M2()
    print(f"Config path: {gm2.config_path}")
    print(f"Countries loaded: {list(gm2.country_list.index)}")

    # Download a small subset for speed
    test_countries = ['United States', 'Japan', 'China']
    gm2.download_data(n_bars=200, countries=test_countries)

    print(f"\nData dict keys: {list(gm2.data_dict.keys())}")
    for country, df in gm2.data_dict.items():
        print(f"  {country}: {df.shape}, {df.index[0]} → {df.index[-1]}")

    return gm2


def test_gm2_aggregates(gm2: Global_M2, m2_groups: list[str] | None = None):
    """Build custom aggregates from downloaded countries and plot them."""
    print("\n" + "=" * 70)
    print("GLOBAL M2 — AGGREGATES")
    print("=" * 70)

    if not gm2.data_dict:
        print("No data loaded, skipping aggregates.")
        return None, None

    available = list(gm2.data_dict.keys())
    print(f"Available countries: {available}")

    if len(available) < 2:
        print("Need at least 2 countries for an aggregate. Skipping.")
        return None, None

    if m2_groups is None:
        m2_groups = available

    # Build aggregate: straight sum of M2_USD columns
    agg_raw, agg_ffill = gm2.create_aggregate(m2_groups, name="TestGroup")

    # Build per-country series dict for primary axis
    primary = {}
    for c in m2_groups:
        df = gm2.data_dict.get(c)
        if df is not None:
            col = [x for x in df.columns if x.endswith("_M2_USD")]
            if col:
                primary[c] = df[col[0]]

    # Plot primary series
    if primary:
        fig1 = plot_multi(
            primary,
            title="Global M2 — Country Comparison (USD)",
            primary_yaxis_title="Billions USD",
            height=500,
        )
        out_png = OUT / "gm2_countries.png"
        out_html = OUT / "gm2_countries.html"
        save_png(fig1, out_png)
        save_html(fig1, out_html)
        print(f"  Saved: {out_png}")
        print(f"  Saved: {out_html}")

    # Plot aggregate series
    if agg_raw is not None:
        fig2 = plot_series(
            agg_raw,
            title="Global M2 — Aggregate Index (USD)",
            yaxis_title="Billions USD",
        )
        out_png2 = OUT / "gm2_aggregate.png"
        save_png(fig2, out_png2)
        print(f"  Saved: {out_png2}")

    return primary, agg_raw


def save_gm2_excel(gm2: Global_M2):
    """Save GM2 data to Excel in user data folder."""
    if not gm2.data_dict:
        print("No GM2 data to save.")
        return

    xlsx = OUT / "gm2_data.xlsx"
    with pd.ExcelWriter(xlsx) as writer:
        for country, df in gm2.data_dict.items():
            df.to_excel(writer, sheet_name=country[:31])  # sheet names max 31 chars
    print(f"  Saved: {xlsx}")


# ============================================================================
# PART 2 — Net Liquidity
# ============================================================================

def test_nlq_fred_fetch() -> NLQDataFetcher:
    """Test FRED data fetching via NLQDataFetcher."""
    print("\n" + "=" * 70)
    print("NET LIQUIDITY — FRED DATA FETCH")
    print("=" * 70)

    fetcher = NLQDataFetcher(save_data=True)
    fred = fetcher.fetch_fred_series(
        ['WALCL', 'RRPONTSYD', 'WTREGEN'],
        '2000-01-01',
        datetime.datetime.today().strftime('%Y-%m-%d'),
    )

    for code, series in fred.items():
        if not series.empty:
            print(f"  {code}: {len(series)} obs  [{series.index[0]} → {series.index[-1]}]  latest={series.iloc[-1]:.2f}")
        else:
            print(f"  {code}: EMPTY")

    return fetcher


def test_tga_fetch():
    """Test the Treasury API TGA fetch."""
    print("\n" + "=" * 70)
    print("NET LIQUIDITY — TGA API FETCH")
    print("=" * 70)

    fetcher = NLQDataFetcher(save_data=True)
    tga = fetcher.fetch_tga_data_treasury_api(start_date="2024-01-01")

    if not tga.empty:
        print(f"  TGA: {len(tga)} obs  [{tga.index[0]} → {tga.index[-1]}]  latest={tga.iloc[-1]:.2f}")
    else:
        print("  TGA: EMPTY")

    return tga


def test_nlq_calc(use_qe_only: bool = False) -> tuple[NetLiquidity, dict]:
    """Run full NLQ calculation, plot results, save to Excel."""
    print("\n" + "=" * 70)
    print("NET LIQUIDITY — FULL CALCULATION")
    print("=" * 70)

    start = "2000-01-01"
    end = datetime.datetime.today().strftime('%Y-%m-%d')

    nlq = NetLiquidity(start_date=start, end_date=end, use_qe_only=use_qe_only)
    results = nlq.calculate_all()

    nlq.summary()

    # Plot components
    components = {
        'Fed Balance Sheet': results.get('fed_balance_sheet_daily', pd.Series()),
        'Reverse Repo': results.get('reverse_repo_daily', pd.Series()),
        'TGA (Treasury)': results.get('tga_treasury_daily', pd.Series()),
    }
    components = {k: v for k, v in components.items() if not v.empty}

    if components:
        fig1 = plot_multi(
            components,
            title="Net Liquidity — Components",
            primary_yaxis_title="Billions USD",
            height=500,
        )
        save_png(fig1, OUT / "nlq_components.png")
        save_html(fig1, OUT / "nlq_components.html")
        print(f"  Saved: {OUT / 'nlq_components.png'}")

    # Plot NLQ series
    nlq_series = {}
    if 'nlq_weekly' in results and not results['nlq_weekly'].empty:
        nlq_series['NLQ Weekly'] = results['nlq_weekly']
    if 'nlq_daily_treasury' in results and not results['nlq_daily_treasury'].empty:
        nlq_series['NLQ Daily (Treasury TGA)'] = results['nlq_daily_treasury']

    if nlq_series:
        fig2 = plot_multi(
            nlq_series,
            title="Net Liquidity — Index",
            primary_yaxis_title="Billions USD",
            height=500,
        )
        save_png(fig2, OUT / "nlq_index.png")
        save_html(fig2, OUT / "nlq_index.html")
        print(f"  Saved: {OUT / 'nlq_index.png'}")

    # Save to Excel (only if there's data)
    xlsx = OUT / "nlq_data.xlsx"
    non_empty = {k: v for k, v in results.items()
                 if isinstance(v, pd.Series) and not v.empty}
    if non_empty:
        with pd.ExcelWriter(xlsx) as writer:
            for name, series in non_empty.items():
                series.to_excel(writer, sheet_name=name[:31])
        print(f"  Saved: {xlsx}")
    else:
        print("  No NLQ data to save to Excel")

    return nlq, results


# ============================================================================
# MAIN
# ============================================================================

def main():
    print(f"Output directory: {OUT}")
    print(f"Python: {sys.version}")

    # --- GM2 ---
    gm2 = test_gm2_basic()
    save_gm2_excel(gm2)

    # Build aggregates from whatever downloaded successfully
    if gm2.data_dict:
        test_gm2_aggregates(gm2, list(gm2.data_dict.keys()))

    # --- NLQ ---
    test_nlq_fred_fetch()
    test_tga_fetch()
    test_nlq_calc(use_qe_only=False)

    print("\n" + "=" * 70)
    print("ALL LIQUIDITY TESTS COMPLETED")
    print(f"Outputs in: {OUT}")
    print("=" * 70)


if __name__ == "__main__":
    main()
