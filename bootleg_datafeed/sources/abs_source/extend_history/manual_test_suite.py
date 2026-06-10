#!/usr/bin/env python3
"""Comprehensive manual test suite for extend_history.

Run from the extend_history directory:
    python manual_test_suite.py

Results saved to ./test_suite_results/ (one .txt file per test section).
"""

from __future__ import annotations

import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from readabs.extend_history import extend_catalogue, extend_series, find_cat_for_series

OUT = Path("test_suite_results")
OUT.mkdir(exist_ok=True)
_SEP = "=" * 72


def log(section: str, msg: str = "") -> None:
    path = OUT / f"{section}.txt"
    mode = "a" if path.exists() else "w"
    with open(path, "a") as f:
        print(msg, file=f)
        f.flush()
    print(msg)


def heading(section: str, title: str) -> None:
    log(section, "")
    log(section, _SEP)
    log(section, f"  {title}")
    log(section, _SEP)
    log(section, f"  Started: {datetime.now(UTC).strftime('%H:%M:%S UTC')}")
    log(section, _SEP)


def ok(msg: str, section: str = "000_summary") -> None:
    log(section, f"  ✅  {msg}")


def fail(msg: str, section: str = "000_summary") -> None:
    log(section, f"  ❌  {msg}")


def t_extend(series_id: str, section: str, cat: str | None = None, **kw) -> pd.DataFrame | None:
    label = kw.pop("label", series_id)
    try:
        t0 = time.time()
        data, meta = extend_series(series_id, cat=cat, verbose=True, **kw)
        elapsed = time.time() - t0
        nn = int(data[series_id].notna().sum())
        rng = f"{data.index[0]} → {data.index[-1]}"
        log(section, f"  OK  {label}: {nn} obs, {rng}  ({elapsed:.1f}s)")
        ok(f"{label}: {nn} obs, {rng}", "000_summary")
        return data
    except Exception as e:
        log(section, f"  FAIL  {label}: {type(e).__name__}: {e}")
        fail(f"{label}: {type(e).__name__}", "000_summary")
        return None


# ============================================================================
# 0. Summary header
# ============================================================================
with open(OUT / "000_summary.txt", "w") as f:
    f.write("extend_history manual test suite\n")
    f.write(f"Run: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}\n")
    f.write(f"{_SEP}\n\n")

# ============================================================================
# 1. Regression — monthly → quarterly
# ============================================================================
S = "001_regression_monthly"
heading(S, "Regression: monthly → quarterly")
d1 = t_extend("A130392586J", S, cat="6401.0", label="CPI Rents Sydney")
if d1 is not None:
    nn = int(d1["A130392586J"].notna().sum())
    if nn > 200:
        ok("Rents extended >200 obs", S)
    else:
        fail(f"Rents only {nn} obs", S)

# ============================================================================
# 2. Reverse — quarterly → monthly
# ============================================================================
S = "002_reverse_quarterly"
heading(S, "Reverse: quarterly → monthly")
d2 = t_extend("A2326391L", S, cat="6401.0", label="CPI Rents Quarterly")
if d1 is not None and d2 is not None:
    diff = (d2["A2326391L"] - d1["A130392586J"]).abs().max()
    log(S, f"  Max diff vs forward result: {diff}")
    ok(f"Diff forward vs reverse: {diff}", S)
    if diff < 0.01:
        log(S, "  ✅  Values match forward extension")

t_extend("A2325846C", S, cat="6401.0", label="CPI All Groups Australia Q")
t_extend("A2325806K", S, cat="6401.0", label="CPI All Groups Sydney Q")
t_extend("A2325811C", S, cat="6401.0", label="CPI All Groups Melbourne Q")

# ============================================================================
# 3. Auto-catalogue resolution
# ============================================================================
S = "003_auto_cat"
heading(S, "Auto-catalogue resolution (no cat=)")
t_extend("A84424911K", S, label="Employed Persons (auto-cat)")
t_extend("A130392586J", S, label="CPI Rents (auto-cat)")
t_extend("A2326391L", S, label="Quarterly rents (auto-cat)")

# ============================================================================
# 4. Series with no sibling
# ============================================================================
S = "004_no_sibling"
heading(S, "Series with no sibling (should return base data)")
t_extend("A84423050A", S, label="Unemployment rate (no sibling)")

# ============================================================================
# 5. Level discontinuity check
# ============================================================================
S = "005_level_check"
heading(S, "Level continuity at transition")
d1b = t_extend("A130392586J", S, cat="6401.0", label="CPI Rents (level check)")
if d1b is not None:
    ts = d1b["A130392586J"]
    m_first = ts.loc["2022-07-01"]
    q_last = ts.loc["2022-04-01"]
    ratio = m_first / q_last
    log(S, f"  Monthly first value (2022-07):    {m_first:.4f}")
    log(S, f"  Quarterly last value (2022-04):   {q_last:.4f}")
    log(S, f"  Ratio (should be ≈ 1.0):          {ratio:.6f}")
    if 0.99 < ratio < 1.01:
        ok(f"Level check passed: ratio={ratio:.6f}", S)
    else:
        fail(f"Level discontinuity: ratio={ratio:.6f}", S)

# ============================================================================
# 6. Labour Force reverse direction
# ============================================================================
S = "006_labour_force_reverse"
heading(S, "Labour Force quarterly → monthly")
t_extend("A85060250R", S, cat="6202.0", label="Employed Persons Quarterly")

# forward for comparison
t_extend("A84424911K", S, cat="6202.0", label="Employed Persons Monthly")
t_extend("A84424918A", S, cat="6202.0", label="Employed FT Persons")

# ============================================================================
# 7. extend_catalogue
# ============================================================================
S = "007_extend_catalogue"
heading(S, "extend_catalogue")
try:
    t0 = time.time()
    data_dict, meta = extend_catalogue("6202.0", verbose=True)
    elapsed = time.time() - t0
    extended = 0
    for name, df in data_dict.items():
        log(S, f"  Table {name}: {len(df.columns)} cols")
    ok(f"extend_catalogue 6202.0: {len(data_dict)} tables ({elapsed:.1f}s)", S)
except Exception as e:
    log(S, f"  FAIL: {type(e).__name__}: {e}")
    fail(f"extend_catalogue 6202.0: {type(e).__name__}", S)

# ============================================================================
# 8. find_cat_for_series
# ============================================================================
S = "008_find_cat"
heading(S, "find_cat_for_series")
tests = [
    ("A2326391L", "6401.0"),
    ("A2325846C", "6401.0"),
    ("A85060250R", "6291.0.55.001"),
    ("A130392586J", "6401.0"),
    ("A84424911K", "6202.0"),
]
all_ok = True
for sid, expected in tests:
    try:
        result = find_cat_for_series(sid)
        status = "OK" if result == expected else f"MISMATCH (got {result})"
        log(S, f"  {sid:>15s} → {result:20s}  [{status}]")
        if result != expected:
            all_ok = False
    except Exception as e:
        log(S, f"  {sid:>15s} → ERROR: {e}")
        all_ok = False
if all_ok:
    ok("All catalogue lookups correct", S)
else:
    fail("Some catalogue lookups wrong", S)

# ============================================================================
# 9. Caching check
# ============================================================================
S = "009_caching"
heading(S, "Caching (second call should be fast)")
t0 = time.time()
extend_series("A130392586J", cat="6401.0", verbose=False)
t1 = time.time()
extend_series("A130392586J", cat="6401.0", verbose=False)
t2 = time.time()
first = t1 - t0
second = t2 - t1
log(S, f"  First call:  {first:.2f}s")
log(S, f"  Second call: {second:.2f}s")
log(S, f"  Speedup:     {first/max(second, 0.001):.1f}x")
if second < first:
    ok(f"Caching effective: {first:.1f}s → {second:.1f}s", S)
else:
    fail("Caching not effective", S)

# Historical cache: two series that share same history
t0 = time.time()
extend_series("A130392586J", cat="6401.0", verbose=False)
t_hist_first = time.time() - t0
t0 = time.time()
extend_series("A2331836L", cat="6401.0", verbose=False)
t_hist_second = time.time() - t0
log(S, f"  Historical first:  {t_hist_first:.2f}s (A130392586J)")
log(S, f"  Historical second: {t_hist_second:.2f}s (A2331836L, same history)")
log(S, f"  Speedup:           {t_hist_first/max(t_hist_second, 0.001):.1f}x")

# ============================================================================
# 10. Bidirectional identity check
# ============================================================================
S = "010_identity"
heading(S, "Bidirectional identity (values match)")
pairs = [
    ("A130392586J", "A2326391L", "6401.0", "Rents Sydney"),
    ("A2325846C", "A130393720C", "6401.0", "CPI All Groups Australia"),
]
all_ok = True
for high_id, low_id, cat, label in pairs:
    dh = extend_series(high_id, cat=cat, verbose=False)
    dl = extend_series(low_id, cat=cat, verbose=False)
    if dh is None or dl is None:
        log(S, f"  {label}: one returned None, skipping")
        continue
    dh_s = dh[0][high_id]
    dl_s = dl[0][low_id]
    common = dh_s.index.intersection(dl_s.index)
    if len(common) == 0:
        log(S, f"  {label}: no common dates — skipping diff")
        continue
    diff = (dh_s.loc[common] - dl_s.loc[common]).abs().max()
    log(S, f"  {label}: max diff = {diff:.10f}")
    if diff < 0.01:
        ok(f"{label}: bidirectional identity ({diff:.2e})", S)
    else:
        fail(f"{label}: values differ by {diff}", S)
        all_ok = False

# ============================================================================
# Summary
# ============================================================================
summary_path = OUT / "000_summary.txt"
with open(summary_path) as f:
    content = f.read()
pass_count = content.count("✅")
fail_count = content.count("❌")

print("")
print(_SEP)
print(f"  COMPLETE — {pass_count} passed, {fail_count} failed")
print(f"  Results: {OUT.resolve()}")
for p in sorted(OUT.iterdir()):
    if p.suffix == ".txt":
        sz = p.stat().st_size
        print(f"    {p.name}  ({sz:,} bytes)")
print(_SEP)
