"""
TradingView search via Node.js @mathieuc/tradingview package.

Bridges to the global npm package for symbol search, since the
Python HTTP endpoint (tvDatafeedz) is now returning 403.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Optional

import pandas as pd

_MACRO_BACKEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "MacroBackend",
)
_TV_JS = os.path.join(_MACRO_BACKEND, "searchTV_js.js")

# Resolve global node_modules path (where @mathieuc/tradingview lives)
_NODE_PATH: str = ""
try:
    _NODE_PATH = subprocess.check_output(
        "npm root -g", shell=True, text=True
    ).strip()
except Exception:
    _NODE_PATH = ""


def search_tv_node(
    query: str,
    exchange: str = "",
) -> pd.DataFrame:
    """Search TradingView symbols via the Node.js @mathieuc/tradingview package.

    Args:
        query: Symbol search string.
        exchange: Optional exchange filter (applied post-search).

    Returns:
        DataFrame with columns: symbol, description, exchange, type, id
    """
    if not os.path.isfile(_TV_JS):
        return pd.DataFrame()

    env = os.environ.copy()
    if _NODE_PATH:
        env["NODE_PATH"] = _NODE_PATH

    try:
        result = subprocess.run(
            ["node", _TV_JS],
            input=json.dumps(query),
            text=True,
            capture_output=True,
            env=env,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return pd.DataFrame()

    if result.returncode != 0:
        return pd.DataFrame()

    try:
        data = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return pd.DataFrame()

    if not isinstance(data, list) or not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Rename to match what _normalize expects
    if "symbol" in df.columns:
        pass  # already have it
    if "description" not in df.columns:
        df["description"] = df.get("id", "")

    # Build an id column as "exchange:symbol"
    df["ticker"] = df["symbol"]

    # Filter by exchange if requested
    if exchange:
        ex = exchange.upper()
        df = df[df.get("exchange", "").str.upper() == ex]

    return df
