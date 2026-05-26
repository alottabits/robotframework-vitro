"""Robot Framework bridge for vitro."""

from robotframework_vitro.exceptions import (
    VitroLibraryError,
    VitroListenerError,
    VitroRobotError,
)
from robotframework_vitro.library import (
    VitroLibrary,
    get_all_devices,
    get_device,
    get_device_manager,
    get_vitro_config,
)
from robotframework_vitro.listener import VitroListener, get_listener

__version__ = "0.1.0"

__all__ = [
    "VitroLibrary",
    "VitroLibraryError",
    "VitroListener",
    "VitroListenerError",
    "VitroRobotError",
    "__version__",
    "get_all_devices",
    "get_device",
    "get_device_manager",
    "get_listener",
    "get_vitro_config",
]
