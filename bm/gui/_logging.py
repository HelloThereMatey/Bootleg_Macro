"""
Logging setup for bm GUI.

Provides a pre-configured logger (`log`) that writes INFO+ to stderr
with timestamps, used across all GUI modules for action tracing.

Usage:
    from bm.gui._logging import log
    log.info("Search triggered: source=%s query=%s", src, q)
    log.warning("Slow search: %.2fs", elapsed)
"""

import logging

log = logging.getLogger("bm.gui")
log.setLevel(logging.INFO)

_handler = logging.StreamHandler()
_handler.setLevel(logging.INFO)
_fmt = logging.Formatter(
    "[%(asctime)s] %(levelname)-7s %(name)s.%(funcName)s  %(message)s",
    datefmt="%H:%M:%S",
)
_handler.setFormatter(_fmt)
log.addHandler(_handler)
log.propagate = False  # don't duplicate to root logger
