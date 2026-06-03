"""
Yahoo Finance search via Node.js yahoo-finance2 package.

Bridges to the global npm package for symbol search, giving proper
search results (names, symbols, etc.) unlike the Python yfinance
package which can only look up known tickers one at a time.
"""

from __future__ import annotations

import json
import os
import subprocess

import pandas as pd

_MACRO_BACKEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "MacroBackend",
)
_YF_JS = os.path.join(_MACRO_BACKEND, "yfinance2_js.js")

# Resolve global node_modules path (where yahoo-finance2 lives)
_NODE_PATH: str = ""
try:
    _NODE_PATH = subprocess.check_output(
        "npm root -g", shell=True, text=True
    ).strip()
except Exception:
    _NODE_PATH = ""


def search_yf_node(query: str) -> pd.DataFrame:
    """Search Yahoo Finance symbols via the Node.js yahoo-finance2 package.

    Args:
        query: Search term (company name, ticker, etc.)

    Returns:
        DataFrame with columns: symbol, shortName, longName, exchange, type
    """
    if not os.path.isfile(_YF_JS):
        return pd.DataFrame()

    env = os.environ.copy()
    if _NODE_PATH:
        env["NODE_PATH"] = _NODE_PATH

    try:
        result = subprocess.run(
            ["node", _YF_JS],
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

    quotes = data.get("quotes", [])
    if not quotes:
        return pd.DataFrame()

    df = pd.DataFrame(quotes)

    # Normalize column names: yahoo-finance2 v3 returns lowercase keys
    col_map = {}
    for col in df.columns:
        lower = col.lower()
        if lower == 'longname':
            col_map[col] = 'longName'
        elif lower == 'shortname':
            col_map[col] = 'shortName'
    if col_map:
        df = df.rename(columns=col_map)

    # Ensure expected columns exist
    if "symbol" in df.columns and "longName" not in df.columns:
        df["longName"] = df.get("shortName", df.get("symbol", ""))
    return df
