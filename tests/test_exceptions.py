"""Tests for the exceptions module."""

import pytest

from robotframework_vitro.exceptions import (
    VitroRobotError,
    VitroListenerError,
    VitroLibraryError,
)


def test_vitro_robot_error_is_exception():
    assert issubclass(VitroRobotError, Exception)


def test_listener_error_inherits_from_base():
    assert issubclass(VitroListenerError, VitroRobotError)


def test_library_error_inherits_from_base():
    assert issubclass(VitroLibraryError, VitroRobotError)


def test_raises_with_message():
    with pytest.raises(VitroListenerError, match="boom"):
        raise VitroListenerError("boom")
