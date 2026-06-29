#!/usr/bin/env python
"""
build_docs.py — generate HTML API docs with pdoc.

Usage:
    python build_docs.py

Generates complete documentation for both packages (bootleg_datafeed +
bootleg_macro) into ./docs/.

Why this script exists:
  * pdoc only recurses one level into subpackages whose submodules are
    re-exported via `from . import x` in __init__ (true for toolz and
    watchlist_gui). We therefore enumerate ALL importable submodules with
    pkgutil and pass them to pdoc explicitly.
  * Submodules that fail to import (missing optional deps, e.g. tv_source
    needs tvDatafeedz) are skipped with a warning so the rest still builds.

Run inside the `bm` conda environment, which has pdoc + all deps installed.
"""

from __future__ import annotations

import importlib
import pkgutil
import subprocess
import sys

PACKAGES = ("bootleg_datafeed", "bootleg_macro")
OUTPUT_DIR = "docs"
DOCFORMAT = "google"  # codebase uses Google-style docstrings (Args:/Returns:/Raises:)


def discover_modules() -> list[str]:
    """Top-level packages + every importable submodule (skip private + tests)."""
    modules: list[str] = []
    skipped: list[tuple[str, str]] = []

    for pkg in PACKAGES:
        modules.append(pkg)  # top-level package itself
        try:
            top = importlib.import_module(pkg)
        except Exception as exc:  # pragma: no cover
            skipped.append((pkg, f"{type(exc).__name__}: {exc}"))
            continue
        for modinfo in pkgutil.walk_packages(top.__path__, prefix=f"{pkg}."):
            name = modinfo.name
            parts = name.split(".")
            if any(p.startswith("_") for p in parts):
                continue
            if ".tests" in name or name.endswith(".tests"):
                continue
            try:
                importlib.import_module(name)
            except Exception as exc:
                skipped.append((name, f"{type(exc).__name__}: {exc}"))
                continue
            modules.append(name)

    return sorted(set(modules)), skipped


def main() -> int:
    modules, skipped = discover_modules()

    print(f"Documenting {len(modules)} module(s):")
    for m in modules:
        print(f"  + {m}")

    if skipped:
        print(f"\nSkipping {len(skipped)} un-importable module(s):", file=sys.stderr)
        for name, why in skipped:
            print(f"  - {name}: {why}", file=sys.stderr)

    cmd = [
        sys.executable, "-m", "pdoc",
        "--docformat", DOCFORMAT,
        "-o", OUTPUT_DIR,
        *modules,
    ]
    print(f"\n$ {' '.join(cmd)}\n")
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
