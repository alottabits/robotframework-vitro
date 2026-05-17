"""Tests for robotframework_vitro.variables."""

import pytest

from robotframework_vitro.variables import get_variables


def test_empty_env_returns_empty_dict(monkeypatch):
    for var in [
        "VITRO_BOARD_NAME",
        "VITRO_ENV_CONFIG",
        "VITRO_INVENTORY_CONFIG",
        "VITRO_SKIP_BOOT",
        "VITRO_SKIP_CONTINGENCY_CHECKS",
        "VITRO_SAVE_CONSOLE_LOGS",
        "VITRO_LEGACY",
        "VITRO_IGNORE_DEVICES",
    ]:
        monkeypatch.delenv(var, raising=False)
    assert get_variables() == {}


def test_populated_env_surfaces_as_variables(monkeypatch):
    monkeypatch.setenv("VITRO_BOARD_NAME", "prplos-1")
    monkeypatch.setenv("VITRO_ENV_CONFIG", "/tmp/env.json")
    monkeypatch.setenv("VITRO_SKIP_BOOT", "true")

    result = get_variables()

    assert result["VITRO_BOARD_NAME"] == "prplos-1"
    assert result["VITRO_ENV_CONFIG"] == "/tmp/env.json"
    assert result["VITRO_SKIP_BOOT"] == "true"


def test_get_variables_ignores_empty_env_entries(monkeypatch):
    monkeypatch.setenv("VITRO_BOARD_NAME", "")
    monkeypatch.delenv("VITRO_ENV_CONFIG", raising=False)
    assert get_variables() == {}
