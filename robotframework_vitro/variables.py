"""Robot Framework variable file: surfaces VITRO_* env vars as variables."""

from __future__ import annotations

import os


_SUPPORTED = (
    "VITRO_BOARD_NAME",
    "VITRO_ENV_CONFIG",
    "VITRO_INVENTORY_CONFIG",
    "VITRO_SKIP_BOOT",
    "VITRO_SKIP_CONTINGENCY_CHECKS",
    "VITRO_SAVE_CONSOLE_LOGS",
    "VITRO_LEGACY",
    "VITRO_IGNORE_DEVICES",
)


def get_variables() -> dict[str, str]:
    """Return non-empty VITRO_* environment variables as Robot variables."""
    return {name: os.environ[name] for name in _SUPPORTED if os.environ.get(name)}
