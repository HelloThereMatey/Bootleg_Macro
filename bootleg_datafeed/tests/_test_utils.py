"""Shared gating helpers for the bm test suite.

Three classes of test need prerequisites: an API key, an optional third-party
package, or a live service that may be rate-limited. Missing prerequisites are an
environment condition — they should skip, not fail, and above all they must not
abort collection for the whole suite (three modules used to `raise RuntimeError`
at import time, which did exactly that).

Usage in a test module::

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from _test_utils import require_key, has_key, requires_key, require_module

    require_key("glassnode")          # module-level skip
    require_module("tedata")          # module-level skip

    @requires_key("fred")
    def test_something(): ...
"""
from __future__ import annotations

import importlib.util

import pytest


def has_key(service: str) -> bool:
    """True when `service` has a non-empty key in API_Keys.json."""
    try:
        from bootleg_datafeed import Dataset

        return bool(Dataset().get_api_key(service))
    except Exception:  # noqa: BLE001 - a broken config means "no key"
        return False


def has_module(name: str) -> bool:
    """True when an optional dependency is importable."""
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def require_key(service: str) -> None:
    """Skip the whole module when `service` has no configured key."""
    if not has_key(service):
        pytest.skip(f"No {service} API key configured", allow_module_level=True)


def require_module(name: str) -> None:
    """Skip the whole module when an optional dependency is missing."""
    if not has_module(name):
        pytest.skip(f"Optional dependency '{name}' is not installed",
                    allow_module_level=True)


def requires_key(service: str):
    return pytest.mark.skipif(not has_key(service), reason=f"No {service} API key")


def requires_module(name: str):
    return pytest.mark.skipif(not has_module(name),
                              reason=f"Optional dependency '{name}' not installed")


def service_available(probe) -> bool:
    """Run `probe()` once and report whether the live service answered.

    Used for sources with no key but a rate limit (CoinGecko) — a 429 at
    collection time means the whole module should skip rather than fail.
    """
    try:
        probe()
        return True
    except Exception:  # noqa: BLE001
        return False


def skip_on_rate_limit(fn):
    """Turn a provider rate-limit error into a skip instead of a failure.

    A free-tier quota is an environment condition. The source already retries
    with backoff, so if it still returns 429 the test should be skipped, not
    reported as a defect.
    """
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            if "429" in msg or "Rate Limit" in msg or "rate limit" in msg:
                pytest.skip(f"Provider rate limit: {msg[:120]}")
            raise

    return wrapper
