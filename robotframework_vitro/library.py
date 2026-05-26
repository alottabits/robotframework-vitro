"""VitroLibrary — Robot Framework keywords that expose the vitro bridge.

The module also exposes the same accessors as plain Python functions
(``get_device_manager``, ``get_vitro_config``, ``get_device``,
``get_all_devices``) so downstream keyword libraries written as Python
classes can reach the vitro bridge without instantiating
``VitroLibrary`` just to call one method. The Robot keywords delegate
to those module-level functions and stay one-liners.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from robot.api.deco import keyword

from vitro.devices.base_devices.vitro_device import VitroDevice

from robotframework_vitro.exceptions import VitroLibraryError
from robotframework_vitro.listener import get_listener


_log = logging.getLogger(__name__)

_SENTINEL = object()


# ---------------------------------------------------------------------------
# Module-level accessors
#
# The same guards used by ``VitroLibrary`` keywords, made available as plain
# Python functions so Python-implemented keyword libraries can call them
# directly. Keeps the friendly error messages ("Vitro devices are not deployed
# yet" / "unknown device name") consistent with the Robot keyword surface.
# ---------------------------------------------------------------------------


def get_device_manager() -> Any:
    """Return the vitro ``DeviceManager`` for the current suite.

    Raises ``VitroLibraryError`` if devices have not been deployed yet
    (the ``VitroListener`` populates the device manager during
    ``start_suite``).
    """
    dm = get_listener().device_manager
    if dm is None:
        raise VitroLibraryError("Vitro devices are not deployed yet")
    return dm


def get_vitro_config() -> Any:
    """Return the merged ``VitroConfig`` for the current suite.

    Raises ``VitroLibraryError`` if the config has not been parsed yet.
    """
    cfg = get_listener().vitro_config
    if cfg is None:
        raise VitroLibraryError("Vitro devices are not deployed yet")
    return cfg


def get_device(name: str) -> Any:
    """Return the device registered under ``name`` in vitro's inventory.

    Raises ``VitroLibraryError`` if devices are not deployed yet, or if
    no device is registered under that name (the error lists the names
    that are available).
    """
    devices = get_all_devices()
    try:
        return devices[name]
    except KeyError as exc:
        available = sorted(devices)
        raise VitroLibraryError(
            f"unknown device name: {name!r}; available: {available}"
        ) from exc


def get_all_devices() -> dict[str, Any]:
    """Return ``dict[name, device]`` of every device registered with vitro.

    Raises ``VitroLibraryError`` if devices are not deployed yet.
    """
    dm = get_device_manager()
    return dm.get_devices_by_type(VitroDevice)


def register_teardown(
    description: str,
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> None:
    """Push a cleanup callable onto the listener's LIFO teardown stack.

    Drained automatically when the current test ends. ``description`` is
    used only for logging if the cleanup raises.
    """
    get_listener().register_teardown(description, func, *args, **kwargs)


def set_test_context(key: str, value: Any) -> None:
    """Store ``value`` under ``key`` in the per-test context dict."""
    get_listener().test_context[key] = value


def get_test_context(key: str, default: Any = _SENTINEL) -> Any:
    """Return the value previously stored under ``key``.

    Raises ``KeyError`` if ``key`` is absent and no ``default`` is given.
    """
    context = get_listener().test_context
    if key in context:
        return context[key]
    if default is _SENTINEL:
        raise KeyError(key)
    return default


def clear_test_context() -> None:
    """Drop every entry from the per-test context dict."""
    get_listener().test_context.clear()


def log_step(message: str) -> None:
    """Emit ``[STEP] <message>`` at INFO level."""
    _log.info("[STEP] %s", message)


# ---------------------------------------------------------------------------
# VitroLibrary — Robot Framework library facade
#
# Robot test files import this as ``Library robotframework_vitro.VitroLibrary``.
# Each keyword is a one-line forwarder to the matching module-level function so
# the friendly-error behaviour stays in one place.
# ---------------------------------------------------------------------------


class VitroLibrary:
    """Infrastructure keywords for the vitro Robot Framework bridge."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    @keyword("Set Test Context")
    def set_test_context(self, key: str, value: Any) -> None:
        """Store ``value`` under ``key`` in the per-test context dict."""
        set_test_context(key, value)

    @keyword("Get Test Context")
    def get_test_context(self, key: str, default: Any = _SENTINEL) -> Any:
        """Return the value previously stored under ``key``."""
        return get_test_context(key, default)

    @keyword("Clear Test Context")
    def clear_test_context(self) -> None:
        """Drop every entry from the per-test context dict."""
        clear_test_context()

    @keyword("Log Step")
    def log_step(self, message: str) -> None:
        """Emit ``[STEP] <message>`` at INFO level."""
        log_step(message)

    @keyword("Get Device Manager")
    def get_device_manager(self) -> Any:
        """Return the vitro DeviceManager for the current suite."""
        return get_device_manager()

    @keyword("Get Vitro Config")
    def get_vitro_config(self) -> Any:
        """Return the merged VitroConfig for the current suite."""
        return get_vitro_config()

    @keyword("Get Device")
    def get_device(self, name: str) -> Any:
        """Return the device registered under ``name`` in vitro's inventory."""
        return get_device(name)

    @keyword("Get All Devices")
    def get_all_devices(self) -> dict[str, Any]:
        """Return ``dict[name, device]`` of every device registered with vitro."""
        return get_all_devices()
