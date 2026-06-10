"""
User data directory configuration for bm packages.

Provides a centralised, configurable user data path that all bm packages
reference. The path defaults to ~/Documents/Bootleg_Macro and can be
overridden by setting the BM_USER_PATH environment variable.

Usage:
    from bootleg_datafeed._user_path import get_user_path, set_user_path

    # Get the current path (default or env var)
    data_dir = get_user_path()

    # Override for the current session
    set_user_path("/path/to/data")
"""

from __future__ import annotations

import os
from pathlib import Path

_DEFAULT = str(Path.home() / "Documents" / "Bootleg_Macro")
_ENV_VAR = "BM_USER_PATH"


def get_user_path() -> str:
    """Return the user data directory path.

    Resolution order:
        1. BM_USER_PATH environment variable
        2. Default: ~/Documents/Bootleg_Macro

    Returns the path as a string. Does not create the directory.
    """
    return os.environ.get(_ENV_VAR, _DEFAULT)


def set_user_path(path: str) -> None:
    """Set the user data directory for the current session.

    Sets the BM_USER_PATH environment variable, which affects all bm
    packages that call :func:`get_user_path`. Does NOT persist between
    sessions — add ``export BM_USER_PATH=/your/path`` to your shell
    profile (``~/.bashrc``, ``~/.zshrc``, ``~/.profile``) for a
    permanent setting.

    Parameters
    ----------
    path : str
        Absolute path to the desired user data directory.
    """
    os.environ[_ENV_VAR] = str(Path(path).resolve())
