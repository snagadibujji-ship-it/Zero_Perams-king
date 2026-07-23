"""Centralized path configuration for AXIMA.

All directory paths are resolved once at import time using environment
variables with sensible defaults. Modules should import paths from here
rather than constructing their own.
"""

from __future__ import annotations

import os
from pathlib import Path


def _resolve_dir(env_var: str, default: Path) -> Path:
    """Resolve a directory path from an environment variable or default."""
    value = os.environ.get(env_var)
    if value:
        return Path(value).resolve()
    return default.resolve()


# Root of the AXIMA installation (parent of src/)
AXIMA_HOME: Path = _resolve_dir(
    "AXIMA_HOME",
    Path(__file__).parent.parent.parent,
)

# Primary data directory (knowledge bases, CSE files)
DATA_DIR: Path = _resolve_dir(
    "AXIMA_DATA_DIR",
    AXIMA_HOME / "data",
)

# User-specific data (learned answers, profile, corrections)
USER_DATA_DIR: Path = _resolve_dir(
    "AXIMA_USER_DATA_DIR",
    AXIMA_HOME / "user_data",
)

# Cache directory (compiled indices, temporary artifacts)
CACHE_DIR: Path = _resolve_dir(
    "AXIMA_CACHE_DIR",
    AXIMA_HOME / ".cache",
)

# Source code root (legacy Python modules)
SRC_PYTHON_DIR: Path = AXIMA_HOME / "src" / "python"

# Eval directory
EVALS_DIR: Path = AXIMA_HOME / "evals"
