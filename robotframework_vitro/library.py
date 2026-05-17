"""VitroLibrary — Robot Framework keywords that expose the vitro bridge."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

from robot.api.deco import keyword

from robotframework_vitro.exceptions import VitroLibraryError
from robotframework_vitro.listener import get_listener


_log = logging.getLogger(__name__)

_SENTINEL = object()


class VitroLibrary:
    """Infrastructure keywords for the vitro Robot Framework bridge."""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    _TYPE_MAP = {
        "CPE": "palco_templates.cpe:Cpe",
        "ACS": "palco_templates.acs:Acs",
        "LAN": "palco_templates.lan:Lan",
        "WAN": "palco_templates.wan:Wan",
        "SIPPHONE": "palco_templates.sip_phone:SipPhone",
        "SIPSERVER": "palco_templates.sip_server:SipServer",
        "TRAFFIC_CONTROLLER": "palco_templates.traffic_controller:TrafficController",
        "QOE_CLIENT": "palco_templates.qoe_client:QoeClient",
        "SDWAN_ROUTER": "palco_templates.sdwan_router:SdwanRouter",
    }

    def __init__(self) -> None:
        self._type_cache: dict[str, type] = {}

    @classmethod
    def _static_type_map(cls) -> dict[str, str]:
        return cls._TYPE_MAP

    def _resolve_device_type(self, type_name: str) -> type:
        key = type_name.upper()
        if key in self._type_cache:
            return self._type_cache[key]

        spec = self._static_type_map().get(key)
        try:
            if spec is None:
                module_name, _, class_name = type_name.rpartition(":")
                if not module_name:
                    raise ValueError
            else:
                module_name, _, class_name = spec.partition(":")
            cls = getattr(import_module(module_name), class_name)
        except (ValueError, ImportError, AttributeError) as exc:
            raise VitroLibraryError(
                f"unknown device type: {type_name!r}"
            ) from exc

        self._type_cache[key] = cls
        return cls

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

    @keyword("Get Device By Type")
    def get_device_by_type(self, type_name: str, index: int | None = None) -> Any:
        """Return a single device of the given type. ``index`` picks among duplicates."""
        cls = self._resolve_device_type(type_name)
        dm = get_listener().device_manager
        if dm is None:
            raise VitroLibraryError("Vitro devices are not deployed yet")
        if index is None:
            return dm.get_device_by_type(cls)
        devices = dm.get_devices_by_type(cls)
        ordered = list(devices.values())
        try:
            return ordered[int(index)]
        except IndexError as exc:
            raise VitroLibraryError(
                f"index {index} is out of range: "
                f"{len(ordered)} device(s) of type {type_name!r} found"
            ) from exc

    @keyword("Get Devices By Type")
    def get_devices_by_type(self, type_name: str) -> dict[str, Any]:
        """Return a ``dict[name, device]`` for every device of the given type."""
        cls = self._resolve_device_type(type_name)
        dm = get_listener().device_manager
        if dm is None:
            raise VitroLibraryError("Vitro devices are not deployed yet")
        return dm.get_devices_by_type(cls)
