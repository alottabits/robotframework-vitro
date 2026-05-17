"""VitroLibrary — Robot Framework keywords that expose the vitro bridge."""

from __future__ import annotations

import logging
from typing import Any

from robot.api.deco import keyword

from vitro.devices.base_devices.vitro_device import VitroDevice

from robotframework_vitro.exceptions import VitroLibraryError
from robotframework_vitro.listener import get_listener


_log = logging.getLogger(__name__)

_SENTINEL = object()


class VitroLibrary:
    """Infrastructure keywords for the vitro Robot Framework bridge."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    @keyword("Set Test Context")
    def set_test_context(self, key: str, value: Any) -> None:
        """Store ``value`` under ``key`` in the per-test context dict."""
        get_listener().test_context[key] = value

    @keyword("Get Test Context")
    def get_test_context(self, key: str, default: Any = _SENTINEL) -> Any:
        """Return the value previously stored under ``key``."""
        context = get_listener().test_context
        if key in context:
            return context[key]
        if default is _SENTINEL:
            raise KeyError(key)
        return default

    @keyword("Clear Test Context")
    def clear_test_context(self) -> None:
        """Drop every entry from the per-test context dict."""
        get_listener().test_context.clear()

    @keyword("Log Step")
    def log_step(self, message: str) -> None:
        """Emit ``[STEP] <message>`` at INFO level."""
        _log.info("[STEP] %s", message)

    @keyword("Get Device Manager")
    def get_device_manager(self) -> Any:
        """Return the vitro DeviceManager for the current suite."""
        dm = get_listener().device_manager
        if dm is None:
            raise VitroLibraryError("Vitro devices are not deployed yet")
        return dm

    @keyword("Get Vitro Config")
    def get_vitro_config(self) -> Any:
        """Return the merged VitroConfig for the current suite."""
        cfg = get_listener().vitro_config
        if cfg is None:
            raise VitroLibraryError("Vitro devices are not deployed yet")
        return cfg

    @keyword("Get Device")
    def get_device(self, name: str) -> Any:
        """Return the device registered under ``name`` in vitro's inventory."""
        devices = self._all_devices()
        try:
            return devices[name]
        except KeyError as exc:
            available = sorted(devices)
            raise VitroLibraryError(
                f"unknown device name: {name!r}; available: {available}"
            ) from exc

    @keyword("Get All Devices")
    def get_all_devices(self) -> dict[str, Any]:
        """Return ``dict[name, device]`` of every device registered with vitro."""
        return self._all_devices()

    def _all_devices(self) -> dict[str, Any]:
        dm = get_listener().device_manager
        if dm is None:
            raise VitroLibraryError("Vitro devices are not deployed yet")
        return dm.get_devices_by_type(VitroDevice)
