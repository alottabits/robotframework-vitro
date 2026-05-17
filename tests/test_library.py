"""Tests for VitroLibrary."""

from unittest.mock import MagicMock

import pytest

from robotframework_vitro.exceptions import VitroLibraryError
from robotframework_vitro.library import VitroLibrary
from vitro.devices.base_devices.vitro_device import VitroDevice


@pytest.fixture
def listener(mocker):
    """Return a mocked listener visible via robotframework_vitro.library.get_listener."""
    fake = MagicMock(name="listener")
    fake.test_context = {}
    fake.device_manager = MagicMock(name="device_manager")
    fake.device_manager.get_devices_by_type.return_value = {}
    fake.vitro_config = MagicMock(name="vitro_config")
    mocker.patch("robotframework_vitro.library.get_listener", return_value=fake)
    return fake


def test_library_scope_is_global():
    assert VitroLibrary.ROBOT_LIBRARY_SCOPE == "GLOBAL"


def test_set_and_get_test_context(listener):
    lib = VitroLibrary()
    lib.set_test_context("answer", 42)
    assert lib.get_test_context("answer") == 42


def test_get_test_context_default_when_missing(listener):
    lib = VitroLibrary()
    assert lib.get_test_context("missing", default="fallback") == "fallback"


def test_get_test_context_raises_without_default(listener):
    lib = VitroLibrary()
    with pytest.raises(KeyError, match="missing"):
        lib.get_test_context("missing")


def test_clear_test_context(listener):
    lib = VitroLibrary()
    lib.set_test_context("a", 1)
    lib.set_test_context("b", 2)
    lib.clear_test_context()
    assert listener.test_context == {}


def test_log_step_emits_prefixed_message(listener, caplog):
    lib = VitroLibrary()
    with caplog.at_level("INFO", logger="robotframework_vitro.library"):
        lib.log_step("Reset router")
    assert any("[STEP] Reset router" in rec.message for rec in caplog.records)


def test_get_device_manager_returns_listener_value(listener):
    lib = VitroLibrary()
    assert lib.get_device_manager() is listener.device_manager


def test_get_vitro_config_returns_listener_value(listener):
    lib = VitroLibrary()
    assert lib.get_vitro_config() is listener.vitro_config


def test_get_device_manager_raises_before_deploy(mocker):
    fake = MagicMock(name="listener")
    fake.device_manager = None
    mocker.patch("robotframework_vitro.library.get_listener", return_value=fake)

    lib = VitroLibrary()
    with pytest.raises(VitroLibraryError, match="not deployed"):
        lib.get_device_manager()


def test_get_vitro_config_raises_before_deploy(mocker):
    fake = MagicMock(name="listener")
    fake.vitro_config = None
    mocker.patch("robotframework_vitro.library.get_listener", return_value=fake)

    lib = VitroLibrary()
    with pytest.raises(VitroLibraryError, match="not deployed"):
        lib.get_vitro_config()


class FakeDevice(VitroDevice):
    """Stand-in for a vitro device class used in library tests."""

    def __init__(self, name: str):
        self.device_name = name


def test_get_device_returns_named_instance(listener):
    phone1 = FakeDevice("phone1")
    listener.device_manager.get_devices_by_type.return_value = {"phone1": phone1}

    lib = VitroLibrary()

    assert lib.get_device("phone1") is phone1


def test_get_device_unknown_name_raises(listener):
    listener.device_manager.get_devices_by_type.return_value = {
        "phone1": FakeDevice("phone1"),
    }

    lib = VitroLibrary()

    with pytest.raises(VitroLibraryError, match="phone2") as excinfo:
        lib.get_device("phone2")
    assert "phone1" in str(excinfo.value)


def test_get_device_raises_before_deploy(mocker):
    fake = MagicMock(name="listener")
    fake.device_manager = None
    mocker.patch("robotframework_vitro.library.get_listener", return_value=fake)

    lib = VitroLibrary()
    with pytest.raises(VitroLibraryError, match="not deployed"):
        lib.get_device("phone1")


def test_get_all_devices_returns_full_dict(listener):
    devices = {
        "phone1": FakeDevice("phone1"),
        "phone2": FakeDevice("phone2"),
    }
    listener.device_manager.get_devices_by_type.return_value = devices

    lib = VitroLibrary()

    assert lib.get_all_devices() == devices


def test_get_all_devices_raises_before_deploy(mocker):
    fake = MagicMock(name="listener")
    fake.device_manager = None
    mocker.patch("robotframework_vitro.library.get_listener", return_value=fake)

    lib = VitroLibrary()
    with pytest.raises(VitroLibraryError, match="not deployed"):
        lib.get_all_devices()


def test_get_all_devices_filters_via_vitro_device_base(listener):
    lib = VitroLibrary()

    lib.get_all_devices()

    listener.device_manager.get_devices_by_type.assert_called_once_with(VitroDevice)
