"""Tests for VitroLibrary."""

from unittest.mock import MagicMock

import pytest

from robotframework_vitro.exceptions import VitroLibraryError
from robotframework_vitro.library import VitroLibrary


@pytest.fixture
def listener(mocker):
    """Return a mocked listener visible via robotframework_vitro.library.get_listener."""
    fake = MagicMock(name="listener")
    fake.test_context = {}
    fake.device_manager = MagicMock(name="device_manager")
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


class FakeDevice:
    """Stand-in for a vitro device class used in library tests."""

    def __init__(self, name: str):
        self.device_name = name


def test_resolve_device_type_hits_static_map(listener):
    lib = VitroLibrary()
    mapping = lib._static_type_map()
    assert "CPE" in mapping
    assert "SDWAN_ROUTER" in mapping


def test_resolve_device_type_caches_resolved_classes(mocker, listener):
    lib = VitroLibrary()

    mocker.patch.object(
        VitroLibrary,
        "_static_type_map",
        return_value={"FAKE": "tests.fixtures.fake_device:FakeDevice"},
    )
    import_module = mocker.patch("robotframework_vitro.library.import_module")
    import_module.return_value = MagicMock(FakeDevice=FakeDevice)

    first = lib._resolve_device_type("FAKE")
    second = lib._resolve_device_type("fake")  # case-insensitive + cache

    assert first is FakeDevice
    assert second is FakeDevice
    import_module.assert_called_once_with("tests.fixtures.fake_device")


def test_resolve_device_type_unknown_raises(listener):
    lib = VitroLibrary()
    with pytest.raises(VitroLibraryError, match="unknown device type"):
        lib._resolve_device_type("NotARealType")


def test_get_device_by_type_delegates_to_device_manager(mocker, listener):
    lib = VitroLibrary()
    mocker.patch.object(
        VitroLibrary,
        "_resolve_device_type",
        return_value=FakeDevice,
    )
    instance = FakeDevice("cpe-0")
    listener.device_manager.get_device_by_type.return_value = instance

    result = lib.get_device_by_type("CPE")

    listener.device_manager.get_device_by_type.assert_called_once_with(FakeDevice)
    assert result is instance


def test_get_device_by_type_with_index(mocker, listener):
    lib = VitroLibrary()
    mocker.patch.object(
        VitroLibrary,
        "_resolve_device_type",
        return_value=FakeDevice,
    )
    instances = {"phone0": FakeDevice("phone0"), "phone1": FakeDevice("phone1")}
    listener.device_manager.get_devices_by_type.return_value = instances

    result = lib.get_device_by_type("SIPPHONE", index=1)

    assert result is instances["phone1"]


def test_get_devices_by_type_returns_dict(mocker, listener):
    lib = VitroLibrary()
    mocker.patch.object(
        VitroLibrary,
        "_resolve_device_type",
        return_value=FakeDevice,
    )
    instances = {"p0": FakeDevice("p0"), "p1": FakeDevice("p1")}
    listener.device_manager.get_devices_by_type.return_value = instances

    assert lib.get_devices_by_type("SIPPHONE") == instances


def test_get_device_by_type_out_of_range_raises_library_error(mocker, listener):
    lib = VitroLibrary()
    mocker.patch.object(VitroLibrary, "_resolve_device_type", return_value=FakeDevice)
    listener.device_manager.get_devices_by_type.return_value = {"p0": FakeDevice("p0")}

    with pytest.raises(VitroLibraryError, match="out of range"):
        lib.get_device_by_type("SIPPHONE", index=5)


def test_resolve_device_type_missing_class_in_static_module_raises(mocker, listener):
    """If the static map points at a real module that lacks the named class, report VitroLibraryError."""
    lib = VitroLibrary()
    mocker.patch.object(
        VitroLibrary,
        "_static_type_map",
        return_value={"FAKE": "tests.fixtures.fake_device:MissingClass"},
    )
    fake_module = MagicMock(spec=[])  # no attributes
    mocker.patch("robotframework_vitro.library.import_module", return_value=fake_module)

    with pytest.raises(VitroLibraryError, match="unknown device type"):
        lib._resolve_device_type("FAKE")
