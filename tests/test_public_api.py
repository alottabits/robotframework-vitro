"""Top-level import surface stays stable."""

import robotframework_vitro


def test_version_is_exposed():
    assert robotframework_vitro.__version__ == "0.1.0"


def test_listener_is_exported():
    from robotframework_vitro import VitroListener
    assert VitroListener.ROBOT_LISTENER_API_VERSION == 3


def test_library_is_exported():
    from robotframework_vitro import VitroLibrary
    assert VitroLibrary.ROBOT_LIBRARY_SCOPE == "GLOBAL"


def test_error_base_is_exported():
    from robotframework_vitro import VitroRobotError
    assert issubclass(VitroRobotError, Exception)
