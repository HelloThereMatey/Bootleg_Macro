"""Module hygiene guards.

`fitting.py` and `stats.py` had accumulated copy-paste duplicates: the whole tail
of fitting.py replayed nine definitions, and stats.py defined Pair_stats twice,
the first a 55-line fragment shadowed by the real class. Python silently keeps
the last binding, so nothing failed — but edits made to the first copy had no
effect. These tests fail if a module defines the same top-level name twice.
"""
from __future__ import annotations

import ast
import pathlib

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")

PKG_ROOT = pathlib.Path(__file__).resolve().parents[2]  # .../bootleg_macro


def _module_files():
    return sorted(p for p in PKG_ROOT.rglob("*.py") if "tests" not in p.parts)


@pytest.mark.parametrize(
    "path", _module_files(), ids=lambda p: str(p.relative_to(PKG_ROOT))
)
def test_no_duplicate_top_level_definitions(path):
    tree = ast.parse(path.read_text())
    seen, duplicates = set(), []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if node.name in seen:
                duplicates.append(f"{node.name} (line {node.lineno})")
            seen.add(node.name)
    assert not duplicates, (
        f"{path.relative_to(PKG_ROOT)} defines {', '.join(duplicates)} "
        "more than once; the earlier definition is silently discarded"
    )


def test_normality_tests_reports_three_tests():
    """Anderson-Darling must survive SciPy's mandatory p-value method."""
    import matplotlib.pyplot as plt

    from bootleg_macro.toolz import fitting

    data = pd.Series(np.random.default_rng(0).normal(size=250))
    with plt.rc_context():
        results, fig = fitting.normality_tests(data)
        plt.close("all")

    assert list(results["Test"]) == [
        "Shapiro-Wilk",
        "Anderson-Darling",
        "Kolmogorov-Smirnov",
    ]
    assert fig is not None
    stat = results.loc[results["Test"] == "Anderson-Darling", "Statistic"].iloc[0]
    assert np.isfinite(stat)

    # With SciPy >= 1.17 the p-value is computed rather than left blank.
    ad_p = results.loc[results["Test"] == "Anderson-Darling", "p-value"].iloc[0]
    assert 0.0 <= ad_p <= 1.0
