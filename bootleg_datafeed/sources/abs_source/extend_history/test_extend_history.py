#!/usr/bin/env python3
"""Manual test script for extend_history — 50+ ABS series, extended bidirectionally.

Run from the repo root:
    python test_extend_history.py [--fast] [--output-dir results]

Each series is tested through extend_series() with full verbose logging.
Results go to --output-dir (default ./test_extend_results/):
  - test.log           full verbose log
  - summary.md         markdown summary table
  - plots/*.png        time-series plots (extended vs base)
  - data.h5            HDF5 store with keys ``{sid}_data`` and ``{sid}_meta``
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path

from matplotlib import dates as mdates
from matplotlib import pyplot as plt

from bootleg_datafeed.sources.abs_source.extend_history import extend_series

# ---------------------------------------------------------------------------
# Series list — 55 series across several catalogues, both directions
# ---------------------------------------------------------------------------
# Monthly → Quarterly (forward extension): CPI detail, Labour Force
# Quarterly → Monthly (reverse extension): quarterly rents, etc.

SERIES: list[dict] = [
    # ==================== CPI — Table 9 (city detail, monthly→quarterly) ====================
    dict(series_id="A130392957J", cat="6401.0", label="CPI Food Sydney"),
    dict(series_id="A130396695T", cat="6401.0", label="CPI Alcohol Sydney"),
    dict(series_id="A130392964F", cat="6401.0", label="CPI Clothing Sydney"),
    dict(series_id="A130394280C", cat="6401.0", label="CPI Housing Sydney"),
    dict(series_id="A130392999F", cat="6401.0", label="CPI Furnishings Sydney"),
    dict(series_id="A130391270V", cat="6401.0", label="CPI Health Sydney"),
    dict(series_id="A130391683T", cat="6401.0", label="CPI Transport Sydney"),
    dict(series_id="A130391277K", cat="6401.0", label="CPI Communication Sydney"),
    dict(series_id="A130393825X", cat="6401.0", label="CPI Recreation Sydney"),
    dict(series_id="A130396219C", cat="6401.0", label="CPI Education Sydney"),
    dict(series_id="A130399170F", cat="6401.0", label="CPI Food Melbourne"),
    dict(series_id="A130397522L", cat="6401.0", label="CPI Health Melbourne"),
    dict(series_id="A130390402T", cat="6401.0", label="CPI Transport Melbourne"),
    dict(series_id="A130395484X", cat="6401.0", label="CPI Housing Brisbane"),
    dict(series_id="A130397942J", cat="6401.0", label="CPI Transport Brisbane"),
    dict(series_id="A130396205R", cat="6401.0", label="CPI Communication Brisbane"),
    # ==================== CPI — Table 10 (granular items, monthly→quarterly) ====================
    dict(series_id="A130394343A", cat="6401.0", label="CPI Bread Sydney"),
    dict(series_id="A130398033T", cat="6401.0", label="CPI Bread only Sydney"),
    dict(series_id="A130393055R", cat="6401.0", label="CPI Meat Sydney"),
    dict(series_id="A130394462T", cat="6401.0", label="CPI Beef Sydney"),
    dict(series_id="A130391473V", cat="6401.0", label="CPI Pork Sydney"),
    dict(series_id="A130396898T", cat="6401.0", label="CPI Fish Sydney"),
    dict(series_id="A130399226F", cat="6401.0", label="CPI Dairy Sydney"),
    dict(series_id="A130396807X", cat="6401.0", label="CPI Milk Sydney"),
    dict(series_id="A130395603C", cat="6401.0", label="CPI Cheese Sydney"),
    dict(series_id="A130398701L", cat="6401.0", label="CPI Fruit Sydney"),
    dict(series_id="A130389961R", cat="6401.0", label="CPI Vegetables Sydney"),
    dict(series_id="A130391004C", cat="6401.0", label="CPI Oils Sydney"),
    dict(series_id="A130391347F", cat="6401.0", label="CPI Snacks Sydney"),
    dict(series_id="A130391970J", cat="6401.0", label="CPI Coffee Sydney"),
    # ==================== CPI — Table 3 (Australia aggregates, monthly→quarterly) ====================
    dict(series_id="A130391704T", cat="6401.0", label="CPI Bread Australia"),
    dict(series_id="A130398061A", cat="6401.0", label="CPI Other Cereal Australia"),
    # ==================== CPI — Table 16 (tradables/services, monthly→quarterly) ====================
    dict(series_id="A130389877X", cat="6401.0", label="CPI Tradables Sydney"),
    dict(series_id="A130396093J", cat="6401.0", label="CPI Non-tradables Sydney"),
    dict(series_id="A130392369L", cat="6401.0", label="CPI Goods Sydney"),
    dict(series_id="A130389905W", cat="6401.0", label="CPI Services Sydney"),
    dict(series_id="A130396324F", cat="6401.0", label="CPI ex Food Sydney"),
    # ==================== Labour Force 6202 (monthly→quarterly) ====================
    dict(series_id="A84424911K", cat="6202.0", label="Employed Persons"),
    dict(series_id="A84424975W", cat="6202.0", label="Employed Persons (alt)"),
    dict(series_id="A84424918A", cat="6202.0", label="Employed FT Persons"),
    dict(series_id="A84424984X", cat="6202.0", label="Employed PT Persons"),
    dict(series_id="A84424921R", cat="6202.0", label="Employed Males"),
    dict(series_id="A84424941X", cat="6202.0", label="Employed Females"),
    dict(series_id="A84424715A", cat="6202.0", label="Employed FT Students"),
    dict(series_id="A84424708C", cat="6202.0", label="Unemployed Students"),
    dict(series_id="A84424269L", cat="6202.0", label="Unemployment Rate Persons"),
    dict(series_id="A84424185C", cat="6202.0", label="Unemployment Rate Males"),
    dict(series_id="A84424227R", cat="6202.0", label="Unemployment Rate Females"),
    # ==================== Quarterly → Monthly (reverse extension) ====================
    dict(series_id="A2326391L", cat="6401.0", label="CPI Rents Sydney Quarterly"),
    dict(series_id="A2331836L", cat="6401.0", label="CPI Rents Sydney Quarterly (B)"),
    dict(series_id="A2325846C", cat="6401.0", label="CPI All Groups Australia Quarterly"),
    dict(series_id="A2325806K", cat="6401.0", label="CPI All Groups Sydney Quarterly"),
    dict(series_id="A2325811C", cat="6401.0", label="CPI All Groups Melbourne Quarterly"),
    dict(series_id="A85060250R", cat="6202.0", label="Employed Persons Quarterly"),
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _style_plot(ax: plt.Axes, title: str) -> None:
    ax.set_title(title, fontsize=11)
    ax.legend(fontsize=8)
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, alpha=0.3)


def _series_id_ok(sid: str) -> str:
    """Sanitise a Series ID for use as an HDF5 key (no leading digit)."""
    return f"sid_{sid}"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description="Test extend_history on 50+ series")
    p.add_argument("--fast", action="store_true", help="Skip plotting (log + h5 only)")
    p.add_argument("--output-dir", default="test_extend_results", help="Output directory")
    args = p.parse_args()

    out_dir = Path(args.output_dir)
    plots_dir = out_dir / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    # ---- logging setup ----
    log_path = out_dir / "test.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.FileHandler(log_path, mode="w"), logging.StreamHandler(sys.stdout)],
    )
    log = logging.getLogger(__name__)

    log.info("=" * 70)
    log.info("extend_history test — %d series", len(SERIES))
    log.info("Started at %s", datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"))
    log.info("Output dir: %s", out_dir.resolve())
    log.info("=" * 70)

    # ---- run every series ----
    results: list[dict] = []
    h5_path = out_dir / "data.h5"

    for i, spec in enumerate(SERIES, 1):
        sid = spec["series_id"]
        cat = spec.get("cat")
        label = spec.get("label", sid)
        log.info("")
        log.info("[%02d/%02d] %s — %s", i, len(SERIES), sid, label)
        log.info("-" * 50)

        t0 = time.time()
        ok = False
        n_base = n_ext = 0
        t_first = t_last = None
        sibling_id = None
        error_msg = ""

        try:
            data, meta = extend_series(sid, cat=cat, verbose=True)
            elapsed = time.time() - t0
            ser = data[sid]
            n_ext = int(ser.notna().sum())
            t_first = ser.index[0]
            t_last = ser.index[-1]
            ok = True
            log.info("  OK  %d obs  [%s  →  %s]  (%.1fs)", n_ext, t_first, t_last, elapsed)
        except Exception as exc:
            elapsed = time.time() - t0
            error_msg = f"{type(exc).__name__}: {exc}"
            log.warning("  FAIL after %.1fs — %s", elapsed, error_msg)
            traceback.print_exc()

        # ---- save data to HDF5 ----
        if ok:
            key_d = _series_id_ok(sid) + "_data"
            key_m = _series_id_ok(sid) + "_meta"
            data.to_hdf(h5_path, key=key_d, mode="a", complevel=4, format="table")
            # HDF5 table format can't serialise datetime objects buried in object cols
            meta_str = meta.map(lambda v: v.isoformat() if isinstance(v, datetime) else v)
            meta_str.to_hdf(h5_path, key=key_m, mode="a", complevel=4, format="table")

        # ---- plot ----
        if ok and not args.fast:
            fig, ax = plt.subplots(figsize=(10, 4))
            ser.plot(ax=ax, label=f"{label} (extended)", color="tab:blue", linewidth=0.8)
            _style_plot(ax, f"{sid} — {label}")
            fig.tight_layout()
            fig.savefig(plots_dir / f"{sid}.png", dpi=150)
            plt.close(fig)

        results.append(
            dict(
                idx=i,
                series_id=sid,
                label=label,
                cat=cat or "auto",
                ok=ok,
                n_obs=n_ext,
                first=t_first,
                last=t_last,
                elapsed=round(elapsed, 1),
                error=error_msg,
            )
        )

    # ---- summary table ----
    summary_path = out_dir / "summary.md"
    n_ok = sum(1 for r in results if r["ok"])
    n_fail = len(results) - n_ok
    total_extended = sum(r["n_obs"] for r in results if r["ok"])

    with open(summary_path, "w") as f:
        f.write("# extend_history test results\n\n")
        f.write(f"- **Run**: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}\n")
        f.write(f"- **Series tested**: {len(results)}\n")
        f.write(f"- **Succeeded**: {n_ok}\n")
        f.write(f"- **Failed**: {n_fail}\n")
        f.write(f"- **Total extended obs**: {total_extended}\n")
        f.write("- **Log**: `test.log`\n")
        f.write("- **Data**: `data.h5`\n")
        f.write("- **Plots**: `plots/*.png`\n\n")

        # results table
        f.write("| # | Series ID | Label | Cat | Obs | Range | Time | Status |\n")
        f.write("|---|-----------|-------|-----|-----|-------|------|--------|\n")
        for r in results:
            status = "OK" if r["ok"] else "FAIL"
            obs = str(r["n_obs"]) if r["ok"] else "—"
            rng = f"{r['first']} → {r['last']}" if r["ok"] else (r["error"][:60] if r["error"] else "—")
            f.write(
                f"| {r['idx']} | {r['series_id']} | {r['label']} "
                f"| {r['cat']} | {obs} | {rng} | {r['elapsed']}s | {status} |\n"
            )

        # notes on failures
        if n_fail:
            f.write("\n## Failures\n\n")
            for r in results:
                if not r["ok"]:
                    f.write(f"- **{r['series_id']}** ({r['label']}): {r['error']}\n")

    log.info("")
    log.info("=" * 70)
    log.info("Done — %d / %d OK, %d failed", n_ok, len(results), n_fail)
    log.info("Summary:  %s", summary_path.resolve())
    log.info("Data:     %s", h5_path.resolve())
    log.info("Plots:    %s", plots_dir.resolve())
    log.info("=" * 70)


if __name__ == "__main__":
    main()
