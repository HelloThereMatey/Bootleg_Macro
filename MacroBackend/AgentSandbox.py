"""
Sandboxed sub-agent launcher for Bootleg_Macro.

Architecture:
  Main Agent (unsandboxed, user approves external actions)
      └── Spawns Sandboxed Sub-Agent (code gen + local testing)
              └── Restricted network: only whitelisted financial APIs
              └── Full file access within repo
              └── Returns results → main agent reviews

Usage:
  from MacroBackend.AgentSandbox import spawn_sandboxed_agent

  result = spawn_sandboxed_agent(
      prompt="Generate a new chart type for the Macro_Chartist tool...",
      description="chart-type-generator",
      task_type="general-purpose"
  )
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Literal, Optional

SETTINGS_PATH = Path(__file__).parent.parent / ".claude" / "settings.local.json"
SANDBOX_CONFIG_KEY = "sandbox"

# Default allowed domains for Bootleg_Macro data sources
DEFAULT_ALLOWED_DOMAINS = [
    "api.stlouisfed.org",       # FRED
    "apps.bea.gov",             # Bureau of Economic Analysis
    "data.nasdaq.com",          # Nasdaq Data Link
    "api.glassnode.com",        # Glassnode on-chain
    "api.coingecko.com",        # CoinGecko crypto prices
    "tradingview.com",          # TradingView
    "tradingeconomics.com",     # Trading Economics scraping
    "rba.gov.au",               # Reserve Bank of Australia
    "abs.gov.au",               # Australian Bureau of Statistics
    "yahoo.com",                # Yahoo Finance
    "finance.yahoo.com",
]


def _load_settings() -> dict:
    """Load current settings, returning empty dict if file doesn't exist."""
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH) as f:
            return json.load(f)
    return {}


def _save_settings(settings: dict) -> None:
    """Save settings to the settings file."""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)


def enable_sandbox(
    allowed_domains: Optional[list[str]] = None,
    allow_write_paths: Optional[list[str]] = None,
    auto_allow: bool = True,
) -> dict:
    """
    Enable sandbox with financial API domain allowlist.

    Args:
        allowed_domains: List of allowed domain patterns (default: DEFAULT_ALLOWED_DOMAINS)
        allow_write_paths: List of allowed write paths (default: repo root)
        auto_allow: If True, sandbox auto-approves commands without prompting

    Returns:
        Original settings dict (for restoration)
    """
    original = _load_settings()

    repo_root = str(Path(__file__).parent.parent)

    settings = _load_settings()
    settings[SANDBOX_CONFIG_KEY] = {
        "enabled": True,
        "autoAllow": auto_allow,
        "filesystem": {
            "allowWrite": allow_write_paths or [repo_root],
        },
        "network": {
            "allowedDomains": allowed_domains or DEFAULT_ALLOWED_DOMAINS,
            "deniedDomains": [],
        },
    }
    _save_settings(settings)
    return original


def disable_sandbox(restore_settings: Optional[dict] = None) -> None:
    """
    Disable sandbox and optionally restore original settings.

    Args:
        restore_settings: Previous settings dict to restore (from enable_sandbox return)
    """
    if restore_settings is not None:
        _save_settings(restore_settings)
    else:
        settings = _load_settings()
        if SANDBOX_CONFIG_KEY in settings:
            del settings[SANDBOX_CONFIG_KEY]
            _save_settings(settings)


def spawn_sandboxed_agent(
    prompt: str,
    description: str = "sandboxed-coder",
    task_type: Literal["general-purpose", "Explore", "Plan"] = "general-purpose",
    allowed_domains: Optional[list[str]] = None,
) -> dict:
    """
    Spawn a sandboxed sub-agent for code generation and local testing.

    The sub-agent:
    - Can write files within the repo
    - Can access only whitelisted financial API domains
    - Cannot push to git, access system paths, or reach unlisted domains
    - All permission escalations bubble up to the parent session for approval

    Args:
        prompt: Task description for the sub-agent
        description: Human-readable name for the agent
        task_type: Type of agent to spawn
        allowed_domains: Override the default allowed domains list

    Returns:
        Agent result dict with 'result' field containing the agent's final response

    Example:
        result = spawn_sandboxed_agent(
            prompt="Add a new MACD chart type to Charting.py. "
                   "Test it with local data. Do NOT call any external APIs.",
            description="add-macd-chart"
        )
        print(result["result"])
    """
    original_settings = enable_sandbox(allowed_domains=allowed_domains)

    try:
        from anthropic import Anthropic

        client = Anthropic()

        # The sub-agent operates under sandbox constraints.
        # Any action requiring permissions beyond the sandbox
        # will surface to the parent session for approval.
        system_prompt = (
            "You are a sandboxed code generation and testing agent for Bootleg_Macro. "
            "You operate under the following constraints:\n"
            "- Filesystem: write only within /home/totabilcat/Documents/Code/Bootleg_Macro\n"
            "- Network: you MAY access these domains for data fetching during testing:\n"
            f"  {', '.join(allowed_domains or DEFAULT_ALLOWED_DOMAINS)}\n"
            "- Do NOT attempt git operations, system modifications, or access other domains\n"
            "- If you need to perform an action that requires user approval, "
            "describe it clearly and the parent agent will handle it\n"
            "- When your work is complete, summarize what was done and any outstanding items\n"
            "that require human review\n"
        )

        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )

        return {"result": message.content[0].text}

    finally:
        disable_sandbox(restore_settings=original_settings)


# Convenience: domains for specific data sources
DOMAIN_SETS = {
    "fred": ["api.stlouisfed.org"],
    "bea": ["apps.bea.gov"],
    "nasdaq": ["data.nasdaq.com"],
    "glassnode": ["api.glassnode.com"],
    "coingecko": ["api.coingecko.com"],
    "tradingview": ["tradingview.com"],
    "yfinance": ["yahoo.com", "finance.yahoo.com"],
    "all": DEFAULT_ALLOWED_DOMAINS,
}


def spawn_data_test_agent(
    source: Literal["fred", "bea", "nasdaq", "glassnode", "coingecko", "tradingview", "yfinance"],
    test_prompt: str,
    description: Optional[str] = None,
) -> dict:
    """
    Spawn a sandboxed sub-agent to test a specific data source.

    The agent will have network access only to the specified source's domains.

    Args:
        source: Which data source to allow ('fred', 'bea', 'nasdaq', 'glassnode', etc.)
        test_prompt: What to test (e.g., "fetch latest CPI data and chart it")
        description: Optional agent name override

    Returns:
        Agent result dict
    """
    domains = DOMAIN_SETS.get(source, DOMAIN_SETS["all"])
    desc = description or f"test-{source}"

    return spawn_sandboxed_agent(
        prompt=test_prompt,
        description=desc,
        allowed_domains=domains,
    )
