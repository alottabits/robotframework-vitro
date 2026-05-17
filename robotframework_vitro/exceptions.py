"""Exception hierarchy for robotframework-vitro."""


class VitroRobotError(Exception):
    """Base exception for the vitro Robot Framework bridge."""


class VitroListenerError(VitroRobotError):
    """Raised when the VitroListener encounters an error."""


class VitroLibraryError(VitroRobotError):
    """Raised when VitroLibrary keyword execution fails."""
