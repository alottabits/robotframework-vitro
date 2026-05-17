"""Robot Framework listener for vitro."""

from __future__ import annotations

import asyncio
import logging
from argparse import Namespace
from collections.abc import Callable
from typing import Any

from vitro.main import get_plugin_manager
from vitro.libraries.vitro_config import get_json

from robotframework_vitro.exceptions import VitroListenerError

_log = logging.getLogger(__name__)

_LISTENER_INSTANCE: "VitroListener | None" = None

_DEFAULT_OPTIONS: dict[str, Any] = {
    "board_name": "",
    "env_config": "",
    "inventory_config": "",
    "skip_boot": False,
    "skip_contingency_checks": False,
    "save_console_logs": "",
    "legacy": False,
    "ignore_devices": "",
}

_BOOLEAN_OPTIONS = {
    "skip_boot",
    "skip_contingency_checks",
    "legacy",
}

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off", ""}


def _coerce_boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        low = value.strip().lower()
        if low in _TRUTHY:
            return True
        if low in _FALSY:
            return False
        raise VitroListenerError(f"Cannot coerce {value!r} to boolean")
    return bool(value)


def _normalise_key(key: str) -> str:
    return key.replace("-", "_")


class VitroListener:
    """Robot Framework listener that orchestrates vitro lifecycle."""

    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, **kwargs: Any) -> None:
        self.options: dict[str, Any] = dict(_DEFAULT_OPTIONS)

        for raw_key, raw_value in kwargs.items():
            key = _normalise_key(raw_key)
            if key not in _DEFAULT_OPTIONS:
                raise TypeError(f"VitroListener: unknown option {raw_key!r}")
            if key in _BOOLEAN_OPTIONS:
                self.options[key] = _coerce_boolean(raw_value)
            else:
                self.options[key] = raw_value

        self._teardown_stack: list[tuple[str, Callable[..., Any], tuple, dict]] = []
        self.test_context: dict[str, Any] = {}
        self.plugin_manager: Any | None = None
        self.device_manager: Any | None = None
        self.vitro_config: Any | None = None
        self._deployment_status: dict[str, Any] = {}

        global _LISTENER_INSTANCE
        _LISTENER_INSTANCE = self

    @property
    def cmdline_args(self) -> Namespace:
        """Return options as an argparse Namespace, the shape vitro hooks expect."""
        return Namespace(**self.options)

    def register_teardown(
        self,
        description: str,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Push a cleanup callable onto the LIFO teardown stack."""
        self._teardown_stack.append((description, func, args, kwargs))

    def _drain_teardown_stack(self) -> None:
        """Execute every registered teardown in reverse order, isolating errors."""
        while self._teardown_stack:
            description, func, args, kwargs = self._teardown_stack.pop()
            try:
                func(*args, **kwargs)
            except Exception:
                _log.exception("Teardown %r raised", description)


    def start_suite(self, data: Any, result: Any) -> None:
        """Deploy vitro devices when the root suite starts."""
        if getattr(data, "parent", None) is not None:
            return
        self._deploy_devices()

    def end_suite(self, data: Any, result: Any) -> None:
        """Release vitro devices when the root suite ends."""
        if getattr(data, "parent", None) is not None:
            return
        self._release_devices()

    def start_test(self, data: Any, result: Any) -> None:
        """No-op; reserved for future pre-test contingency checks."""

    def end_test(self, data: Any, result: Any) -> None:
        """Drain per-test teardown stack and reset per-test context."""
        self._drain_teardown_stack()
        self.test_context.clear()

    def _deploy_devices(self) -> None:
        self.plugin_manager = get_plugin_manager()
        hook = self.plugin_manager.hook

        try:
            hook.vitro_configure(
                cmdline_args=self.cmdline_args,
                plugin_manager=self.plugin_manager,
            )
            inventory_config = hook.vitro_reserve_devices(
                cmdline_args=self.cmdline_args,
                plugin_manager=self.plugin_manager,
            )
            env_config = get_json(self.options["env_config"])
            self.vitro_config = hook.vitro_parse_config(
                cmdline_args=self.cmdline_args,
                inventory_config=inventory_config,
                env_config=env_config,
            )
            self.device_manager = hook.vitro_register_devices(
                config=self.vitro_config,
                cmdline_args=self.cmdline_args,
                plugin_manager=self.plugin_manager,
            )
            asyncio.run(
                hook.vitro_setup_env(
                    config=self.vitro_config,
                    cmdline_args=self.cmdline_args,
                    plugin_manager=self.plugin_manager,
                    device_manager=self.device_manager,
                )
            )
            self._deployment_status = {"status": "success"}
        except Exception as exc:
            self._deployment_status = {"status": "failed", "exception": exc}
            raise

    def _release_devices(self) -> None:
        if self.plugin_manager is None or self.device_manager is None:
            return
        self.plugin_manager.hook.vitro_release_devices(
            config=self.vitro_config,
            cmdline_args=self.cmdline_args,
            plugin_manager=self.plugin_manager,
            deployment_status=self._deployment_status,
            device_manager=self.device_manager,
        )


def get_listener() -> "VitroListener":
    """Return the active listener. Raises if the listener hasn't been constructed."""
    if _LISTENER_INSTANCE is None:
        raise VitroListenerError("VitroListener is not initialised")
    return _LISTENER_INSTANCE
