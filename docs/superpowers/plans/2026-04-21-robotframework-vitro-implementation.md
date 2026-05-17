# robotframework-vitro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `robotframework-vitro`, a Robot Framework bridge to the `vitro` framework that mirrors `robotframework-boardfarm`'s two-piece architecture (listener + library).

**Architecture:** A `VitroListener` (ROBOT_LISTENER_API_VERSION = 3) owns lifecycle — it runs vitro's pluggy hooks on suite start/end (with an `asyncio.run()` boundary around `vitro_setup_env`) and maintains a LIFO per-test teardown stack. A `VitroLibrary` (GLOBAL scope) exposes seven static infrastructure keywords. A `vitrorobot` CLI wraps `robot` with vitro config flags. Test projects supply their own `@keyword` libraries that import from `vitro-templates` / `vitro-operations` and call `get_listener().register_teardown(...)` at the point of state change — the bridge itself stays thin.

**Tech Stack:** Python ≥3.11 (required by vitro's `asyncio.TaskGroup`), `robotframework`, `vitro`, `flit_core` for packaging, `pytest` + `pytest-mock` for unit tests.

**Repo root:** `/home/rjvisser/projects/req-tst/robotframework-vitro/` — already initialized (commit `b90c1f9` holds the design spec).

**Conventions for every task:**
- All paths are absolute unless shown as relative-to-repo-root.
- Git commands use `-C /home/rjvisser/projects/req-tst/robotframework-vitro` to avoid `cd`.
- Each task ends with `pytest` (run from the repo root) showing green, then a commit.
- TDD: write the failing test first, watch it fail, implement, watch it pass, commit.

---

## Task 1: Scaffold the project

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `README.md`
- Create: `CHANGELOG.md`
- Create: `robotframework_vitro/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Write `.gitignore`**

```gitignore
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
dist/
build/
.venv/
venv/
.env
.vscode/
.idea/
```

- [ ] **Step 2: Write `LICENSE` (BSD-3-Clause, matching `robotframework-boardfarm`)**

Copy the LICENSE file from `/home/rjvisser/projects/req-tst/robotframework-boardfarm/LICENSE` verbatim, replacing the copyright line's project-name reference if any.

```bash
cp /home/rjvisser/projects/req-tst/robotframework-boardfarm/LICENSE \
   /home/rjvisser/projects/req-tst/robotframework-vitro/LICENSE
```

- [ ] **Step 3: Write `pyproject.toml`**

```toml
[build-system]
requires = ["flit_core>=3.9,<4"]
build-backend = "flit_core.buildapi"

[project]
name = "robotframework-vitro"
version = "0.1.0"
description = "Robot Framework bridge for the vitro test framework"
readme = "README.md"
requires-python = ">=3.11"
license = { file = "LICENSE" }
authors = [{ name = "rjvisser" }]
keywords = ["robotframework", "vitro", "testbed", "testing"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Framework :: Robot Framework",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Testing",
]
dependencies = [
    "robotframework>=6.0",
    "vitro>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-mock>=3.10",
    "pytest-cov>=4.0",
]

[project.scripts]
vitrorobot = "robotframework_vitro.cli:main"

[project.urls]
Homepage = "https://github.com/alottabits/robotframework-vitro"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

- [ ] **Step 4: Write placeholder `README.md`**

```markdown
# robotframework-vitro

Robot Framework bridge to the [vitro](https://github.com/…/vitro) test framework.

Full documentation will be added in later tasks. See `docs/superpowers/specs/` for the design.
```

- [ ] **Step 5: Write placeholder `CHANGELOG.md`**

```markdown
# Changelog

## 0.1.0 (unreleased)

Initial release — listener, library, CLI. See design spec for the v0.1 scope.
```

- [ ] **Step 6: Write empty package and test `__init__.py` files**

`robotframework_vitro/__init__.py`:

```python
"""Robot Framework bridge for vitro."""

__version__ = "0.1.0"
```

`tests/__init__.py` — empty file:

```python
```

- [ ] **Step 7: Install the package in editable mode and verify pytest runs**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro
python -m pip install -e ".[dev]"
python -m pytest -q
```

Expected: pytest reports `no tests ran` with exit code 5, or `0 passed`. Either is fine — we haven't written any yet.

- [ ] **Step 8: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add .gitignore LICENSE pyproject.toml README.md CHANGELOG.md robotframework_vitro/__init__.py tests/__init__.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "chore: scaffold robotframework-vitro package"
```

---

## Task 2: Exceptions module

**Files:**
- Create: `robotframework_vitro/exceptions.py`
- Create: `tests/test_exceptions.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_exceptions.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_exceptions.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'robotframework_vitro.exceptions'`.

- [ ] **Step 3: Implement `robotframework_vitro/exceptions.py`**

```python
"""Exception hierarchy for robotframework-vitro."""


class VitroRobotError(Exception):
    """Base exception for the vitro Robot Framework bridge."""


class VitroListenerError(VitroRobotError):
    """Raised when the VitroListener encounters an error."""


class VitroLibraryError(VitroRobotError):
    """Raised when VitroLibrary keyword execution fails."""
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_exceptions.py -v
```

Expected: 4 tests pass.

- [ ] **Step 5: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add robotframework_vitro/exceptions.py tests/test_exceptions.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "feat: add VitroRobotError exception hierarchy"
```

---

## Task 3: Listener — options parsing

**Files:**
- Create: `robotframework_vitro/listener.py`
- Create: `tests/test_listener.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_listener.py`:

```python
"""Tests for VitroListener."""

import pytest

from robotframework_vitro.listener import VitroListener


def test_defaults_populated_when_no_kwargs():
    listener = VitroListener()
    assert listener.options["board_name"] == ""
    assert listener.options["env_config"] == ""
    assert listener.options["inventory_config"] == ""
    assert listener.options["skip_boot"] is False
    assert listener.options["skip_contingency_checks"] is False
    assert listener.options["save_console_logs"] == ""
    assert listener.options["legacy"] is False
    assert listener.options["ignore_devices"] == ""


def test_listener_api_version_is_3():
    assert VitroListener.ROBOT_LISTENER_API_VERSION == 3


def test_dashes_are_normalised_to_underscores():
    listener = VitroListener(**{"board-name": "prplos-1", "env-config": "/tmp/env.json"})
    assert listener.options["board_name"] == "prplos-1"
    assert listener.options["env_config"] == "/tmp/env.json"


@pytest.mark.parametrize("raw,expected", [
    ("true", True), ("True", True), ("1", True), ("yes", True),
    ("false", False), ("False", False), ("0", False), ("no", False), ("", False),
])
def test_boolean_flags_coerced_from_strings(raw, expected):
    listener = VitroListener(skip_boot=raw)
    assert listener.options["skip_boot"] is expected


def test_unknown_option_raises():
    with pytest.raises(TypeError, match="unknown"):
        VitroListener(nonsense_flag=True)


def test_cmdline_args_property_builds_namespace():
    listener = VitroListener(board_name="x", env_config="/e.json", skip_boot=True)
    ns = listener.cmdline_args
    assert ns.board_name == "x"
    assert ns.env_config == "/e.json"
    assert ns.skip_boot is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_listener.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'robotframework_vitro.listener'`.

- [ ] **Step 3: Implement the listener's `__init__` and options machinery**

Create `robotframework_vitro/listener.py`:

```python
"""Robot Framework listener for vitro."""

from __future__ import annotations

from argparse import Namespace
from typing import Any

from robotframework_vitro.exceptions import VitroListenerError


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

    @property
    def cmdline_args(self) -> Namespace:
        """Return options as an argparse Namespace, the shape vitro hooks expect."""
        return Namespace(**self.options)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_listener.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add robotframework_vitro/listener.py tests/test_listener.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "feat: add VitroListener with options parsing"
```

---

## Task 4: Listener — LIFO teardown stack

**Files:**
- Modify: `robotframework_vitro/listener.py`
- Modify: `tests/test_listener.py`

- [ ] **Step 1: Append failing tests to `tests/test_listener.py`**

Append these tests to the existing file:

```python
def test_register_teardown_pushes_entries():
    listener = VitroListener()
    listener.register_teardown("first", lambda: None)
    listener.register_teardown("second", lambda: None)
    assert len(listener._teardown_stack) == 2


def test_drain_teardown_stack_is_lifo():
    listener = VitroListener()
    order: list[str] = []
    listener.register_teardown("first", lambda: order.append("first"))
    listener.register_teardown("second", lambda: order.append("second"))
    listener.register_teardown("third", lambda: order.append("third"))

    listener._drain_teardown_stack()

    assert order == ["third", "second", "first"]
    assert listener._teardown_stack == []


def test_teardown_stack_passes_args_and_kwargs():
    listener = VitroListener()
    captured: list[tuple] = []

    def record(*args, **kwargs):
        captured.append((args, kwargs))

    listener.register_teardown("record", record, 1, 2, a="b")
    listener._drain_teardown_stack()

    assert captured == [((1, 2), {"a": "b"})]


def test_failing_teardown_does_not_block_others():
    listener = VitroListener()
    order: list[str] = []

    def boom():
        order.append("boom")
        raise RuntimeError("kaboom")

    listener.register_teardown("first", lambda: order.append("first"))
    listener.register_teardown("boom", boom)
    listener.register_teardown("last", lambda: order.append("last"))

    listener._drain_teardown_stack()

    assert order == ["last", "boom", "first"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_listener.py -v
```

Expected: 4 new tests fail — `AttributeError` on `_teardown_stack` / `register_teardown` / `_drain_teardown_stack`.

- [ ] **Step 3: Add teardown-stack machinery to `VitroListener`**

Add imports at the top of `robotframework_vitro/listener.py`:

```python
import logging
from collections.abc import Callable
```

Add a module-level logger:

```python
_log = logging.getLogger(__name__)
```

Extend `VitroListener.__init__` (after the existing body) to initialise the stack:

```python
        self._teardown_stack: list[tuple[str, Callable[..., Any], tuple, dict]] = []
```

Add the two methods to `VitroListener`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_listener.py -v
```

Expected: all tests pass (the 6 original tests plus the 4 new ones).

- [ ] **Step 5: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add robotframework_vitro/listener.py tests/test_listener.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "feat: add LIFO teardown stack to VitroListener"
```

---

## Task 5: Listener — module-level instance and `get_listener()`

**Files:**
- Modify: `robotframework_vitro/listener.py`
- Modify: `tests/test_listener.py`

- [ ] **Step 1: Append failing tests to `tests/test_listener.py`**

```python
def test_get_listener_returns_last_constructed_instance():
    from robotframework_vitro.listener import get_listener

    first = VitroListener()
    assert get_listener() is first

    second = VitroListener(board_name="later")
    assert get_listener() is second


def test_get_listener_raises_before_construction(monkeypatch):
    import robotframework_vitro.listener as listener_module

    monkeypatch.setattr(listener_module, "_LISTENER_INSTANCE", None)
    with pytest.raises(listener_module.VitroListenerError, match="not initialised"):
        listener_module.get_listener()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_listener.py -v
```

Expected: the two new tests fail — `ImportError` on `get_listener`.

- [ ] **Step 3: Add the module-level singleton and accessor to `listener.py`**

Add this constant near the top of the module, below `_log`:

```python
_LISTENER_INSTANCE: "VitroListener | None" = None
```

Modify `VitroListener.__init__` to store the instance as its last action (add just before the method ends):

```python
        global _LISTENER_INSTANCE
        _LISTENER_INSTANCE = self
```

Add this function after the `VitroListener` class:

```python
def get_listener() -> "VitroListener":
    """Return the active listener. Raises if the listener hasn't been constructed."""
    if _LISTENER_INSTANCE is None:
        raise VitroListenerError("VitroListener is not initialised")
    return _LISTENER_INSTANCE
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_listener.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add robotframework_vitro/listener.py tests/test_listener.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "feat: expose VitroListener via get_listener() module-level accessor"
```

---

## Task 6: Listener — lifecycle hook shells

Implement `start_suite` / `end_suite` / `start_test` / `end_test` with placeholder deploy/release methods. Task 7 will fill those in.

**Files:**
- Modify: `robotframework_vitro/listener.py`
- Modify: `tests/test_listener.py`

- [ ] **Step 1: Append failing tests to `tests/test_listener.py`**

```python
from types import SimpleNamespace


def _make_suite(is_root: bool = True) -> SimpleNamespace:
    parent = None if is_root else SimpleNamespace(name="root")
    return SimpleNamespace(name="suite", parent=parent)


def _make_test() -> SimpleNamespace:
    return SimpleNamespace(name="test case")


def test_start_suite_deploys_only_at_root(mocker):
    listener = VitroListener()
    deploy = mocker.patch.object(listener, "_deploy_devices")

    listener.start_suite(_make_suite(is_root=True), SimpleNamespace())
    deploy.assert_called_once()

    deploy.reset_mock()
    listener.start_suite(_make_suite(is_root=False), SimpleNamespace())
    deploy.assert_not_called()


def test_end_suite_releases_only_at_root(mocker):
    listener = VitroListener()
    release = mocker.patch.object(listener, "_release_devices")

    listener.end_suite(_make_suite(is_root=False), SimpleNamespace())
    release.assert_not_called()

    listener.end_suite(_make_suite(is_root=True), SimpleNamespace())
    release.assert_called_once()


def test_end_test_drains_stack_and_clears_context():
    listener = VitroListener()
    order: list[str] = []
    listener.register_teardown("a", lambda: order.append("a"))
    listener.register_teardown("b", lambda: order.append("b"))
    listener.test_context["key"] = "value"

    listener.end_test(_make_test(), SimpleNamespace())

    assert order == ["b", "a"]
    assert listener._teardown_stack == []
    assert listener.test_context == {}


def test_start_test_is_noop_for_now():
    listener = VitroListener()
    listener.start_test(_make_test(), SimpleNamespace())  # must not raise
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_listener.py -v
```

Expected: the 4 new tests fail — `AttributeError` on `start_suite` / `end_suite` / `start_test` / `end_test` / `test_context`.

- [ ] **Step 3: Add lifecycle shell to `VitroListener`**

Extend `VitroListener.__init__` (before the `_LISTENER_INSTANCE` assignment) with:

```python
        self.test_context: dict[str, Any] = {}
```

Add these methods to `VitroListener`:

```python
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
        """Placeholder hook. Task 7 wires contingency checks here if wanted."""

    def end_test(self, data: Any, result: Any) -> None:
        """Drain per-test teardown stack and reset per-test context."""
        self._drain_teardown_stack()
        self.test_context.clear()

    def _deploy_devices(self) -> None:
        """Populated in Task 7."""
        raise NotImplementedError

    def _release_devices(self) -> None:
        """Populated in Task 7."""
        raise NotImplementedError
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_listener.py -v
```

Expected: all tests pass. `pytest-mock`'s `mocker.patch.object` short-circuits the unimplemented `_deploy_devices` / `_release_devices`.

- [ ] **Step 5: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add robotframework_vitro/listener.py tests/test_listener.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "feat: add VitroListener lifecycle hook shells"
```

---

## Task 7: Listener — `_deploy_devices` and `_release_devices`

Wire the listener into vitro's pluggy hooks. Mock vitro at the test layer — don't import real vitro devices.

**Files:**
- Modify: `robotframework_vitro/listener.py`
- Modify: `tests/test_listener.py`

- [ ] **Step 1: Append failing tests to `tests/test_listener.py`**

Add these imports at the top of the test file (if `MagicMock` / `call` / `ANY` aren't already imported):

```python
from unittest.mock import ANY, MagicMock, call
```

Then append:

```python
@pytest.fixture
def mock_vitro(mocker):
    """Patch every vitro-side symbol the listener imports at module load."""
    plugin_manager = MagicMock(name="plugin_manager")
    hook = plugin_manager.hook
    device_manager = MagicMock(name="device_manager")
    hook.vitro_register_devices.return_value = device_manager
    vitro_config = MagicMock(name="vitro_config")

    mocker.patch(
        "robotframework_vitro.listener.get_plugin_manager",
        return_value=plugin_manager,
    )
    mocker.patch(
        "robotframework_vitro.listener.get_inventory_config",
        return_value={"inventory": "stub"},
    )
    mocker.patch(
        "robotframework_vitro.listener.get_json",
        return_value={"environment_def": {}},
    )
    mocker.patch(
        "robotframework_vitro.listener.parse_vitro_config",
        return_value=vitro_config,
    )
    asyncio_run = mocker.patch("robotframework_vitro.listener.asyncio.run")

    return SimpleNamespace(
        plugin_manager=plugin_manager,
        hook=hook,
        device_manager=device_manager,
        vitro_config=vitro_config,
        asyncio_run=asyncio_run,
    )


def test_deploy_devices_invokes_hooks_in_order(mock_vitro):
    listener = VitroListener(board_name="b", env_config="/e.json", inventory_config="/i.json")
    listener._deploy_devices()

    expected = [
        "vitro_configure",
        "vitro_reserve_devices",
        "vitro_register_devices",
        "vitro_setup_env",
    ]
    actual = [c[0] for c in mock_vitro.hook.method_calls]
    assert actual == expected


def test_deploy_devices_stores_config_and_device_manager(mock_vitro):
    listener = VitroListener(env_config="/e.json")
    listener._deploy_devices()

    assert listener.vitro_config is mock_vitro.vitro_config
    assert listener.device_manager is mock_vitro.device_manager
    assert listener.plugin_manager is mock_vitro.plugin_manager


def test_deploy_devices_wraps_setup_env_in_asyncio_run(mock_vitro):
    listener = VitroListener(env_config="/e.json")
    listener._deploy_devices()

    mock_vitro.asyncio_run.assert_called_once()
    mock_vitro.hook.vitro_setup_env.assert_called_once_with(
        config=mock_vitro.vitro_config,
        device_manager=mock_vitro.device_manager,
        cmdline_args=ANY,
    )


def test_release_devices_calls_vitro_release_hook(mock_vitro):
    listener = VitroListener(env_config="/e.json")
    listener._deploy_devices()
    mock_vitro.hook.reset_mock()
    mock_vitro.asyncio_run.reset_mock()

    listener._release_devices()

    mock_vitro.hook.vitro_release_devices.assert_called_once_with(
        device_manager=mock_vitro.device_manager,
        cmdline_args=ANY,
    )


def test_release_devices_is_safe_when_never_deployed(mock_vitro):
    listener = VitroListener()
    listener._release_devices()  # must not raise
    mock_vitro.hook.vitro_release_devices.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_listener.py -v
```

Expected: the 5 new tests fail — either `NotImplementedError` or `ModuleNotFoundError` when patching vitro symbols the listener does not yet import.

- [ ] **Step 3: Implement `_deploy_devices` / `_release_devices` in `listener.py`**

Add imports at the top of the module (below the existing imports):

```python
import asyncio

from vitro.main import get_plugin_manager
from vitro.libraries.vitro_config import (
    get_inventory_config,
    get_json,
    parse_vitro_config,
)
```

Extend `VitroListener.__init__` (alongside the other instance attributes, before the `_LISTENER_INSTANCE` assignment):

```python
        self.plugin_manager: Any | None = None
        self.device_manager: Any | None = None
        self.vitro_config: Any | None = None
```

Replace the two `NotImplementedError` stubs with real implementations:

```python
    def _deploy_devices(self) -> None:
        self.plugin_manager = get_plugin_manager()
        hook = self.plugin_manager.hook

        hook.vitro_configure(cmdline_args=self.cmdline_args)
        hook.vitro_reserve_devices(cmdline_args=self.cmdline_args)

        inventory = get_inventory_config(
            self.options["board_name"],
            self.options["inventory_config"],
        )
        env = get_json(self.options["env_config"])
        self.vitro_config = parse_vitro_config(inventory, env)

        self.device_manager = hook.vitro_register_devices(
            config=self.vitro_config,
            cmdline_args=self.cmdline_args,
        )

        asyncio.run(
            hook.vitro_setup_env(
                config=self.vitro_config,
                device_manager=self.device_manager,
                cmdline_args=self.cmdline_args,
            )
        )

    def _release_devices(self) -> None:
        if self.plugin_manager is None:
            return
        self.plugin_manager.hook.vitro_release_devices(
            device_manager=self.device_manager,
            cmdline_args=self.cmdline_args,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_listener.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add robotframework_vitro/listener.py tests/test_listener.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "feat: wire VitroListener into vitro deploy/release hooks"
```

---

## Task 8: Library — context keywords and `Log Step`

**Files:**
- Create: `robotframework_vitro/library.py`
- Create: `tests/test_library.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_library.py`:

```python
"""Tests for VitroLibrary."""

from unittest.mock import MagicMock

import pytest

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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_library.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'robotframework_vitro.library'`.

- [ ] **Step 3: Implement `robotframework_vitro/library.py`**

```python
"""VitroLibrary — Robot Framework keywords that expose the vitro bridge."""

from __future__ import annotations

import logging
from typing import Any

from robot.api.deco import keyword

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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_library.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add robotframework_vitro/library.py tests/test_library.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "feat: add VitroLibrary context and logging keywords"
```

---

## Task 9: Library — `Get Device Manager` and `Get Vitro Config`

**Files:**
- Modify: `robotframework_vitro/library.py`
- Modify: `tests/test_library.py`

- [ ] **Step 1: Append failing tests to `tests/test_library.py`**

```python
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
```

Also add the import near the other imports at the top of `tests/test_library.py`:

```python
from robotframework_vitro.exceptions import VitroLibraryError
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_library.py -v
```

Expected: the 4 new tests fail — `AttributeError` on `get_device_manager` / `get_vitro_config`.

- [ ] **Step 3: Add the two keywords to `VitroLibrary`**

Add these methods to the class:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_library.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add robotframework_vitro/library.py tests/test_library.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "feat: add Get Device Manager and Get Vitro Config keywords"
```

---

## Task 10: Library — device type resolution + `Get Device By Type` + `Get Devices By Type`

**Files:**
- Modify: `robotframework_vitro/library.py`
- Modify: `tests/test_library.py`

- [ ] **Step 1: Append failing tests to `tests/test_library.py`**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_library.py -v
```

Expected: the 6 new tests fail — `AttributeError` on `_resolve_device_type` / `get_device_by_type` / `get_devices_by_type`.

- [ ] **Step 3: Extend `library.py`**

Add to the imports at the top:

```python
from importlib import import_module
```

Add a static type map and the resolver + two keywords to `VitroLibrary`:

```python
    _TYPE_MAP = {
        "CPE": "testprotocols.devices.cpe:CpeDevice",
        "ACS": "testprotocols.devices.infra:AcsDevice",
        "LAN": "testprotocols.devices.client:LanClientDevice",
        "WAN": "testprotocols.devices.wan:WanServerDevice",
        "SIPPHONE": "testprotocols.devices.voice:SipPhoneDevice",
        "SIPSERVER": "testprotocols.devices.voice:SipServerDevice",
        "TRAFFIC_CONTROLLER": "testprotocols.devices.traffic:TrafficControllerDevice",
        "QOE_CLIENT": "testprotocols.devices.client:QoeClientDevice",
        "SDWAN_ROUTER": "testprotocols.devices.sdwan:SdwanRouterDevice",
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
        if spec is None:
            try:
                module_name, _, class_name = type_name.rpartition(":")
                if not module_name:
                    raise ValueError
                cls = getattr(import_module(module_name), class_name)
            except (ValueError, ImportError, AttributeError) as exc:
                raise VitroLibraryError(
                    f"unknown device type: {type_name!r}"
                ) from exc
        else:
            module_name, _, class_name = spec.partition(":")
            cls = getattr(import_module(module_name), class_name)

        self._type_cache[key] = cls
        return cls

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
        return list(devices.values())[int(index)]

    @keyword("Get Devices By Type")
    def get_devices_by_type(self, type_name: str) -> dict[str, Any]:
        """Return a ``dict[name, device]`` for every device of the given type."""
        cls = self._resolve_device_type(type_name)
        dm = get_listener().device_manager
        if dm is None:
            raise VitroLibraryError("Vitro devices are not deployed yet")
        return dm.get_devices_by_type(cls)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_library.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add robotframework_vitro/library.py tests/test_library.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "feat: add device type resolution and device-access keywords"
```

---

## Task 11: Variables module (environment-variable support)

**Files:**
- Create: `robotframework_vitro/variables.py`
- Create: `tests/test_variables.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_variables.py`:

```python
"""Tests for robotframework_vitro.variables."""

import pytest

from robotframework_vitro.variables import get_variables


def test_empty_env_returns_empty_dict(monkeypatch):
    for var in [
        "VITRO_BOARD_NAME",
        "VITRO_ENV_CONFIG",
        "VITRO_INVENTORY_CONFIG",
        "VITRO_SKIP_BOOT",
        "VITRO_SKIP_CONTINGENCY_CHECKS",
        "VITRO_SAVE_CONSOLE_LOGS",
        "VITRO_LEGACY",
        "VITRO_IGNORE_DEVICES",
    ]:
        monkeypatch.delenv(var, raising=False)
    assert get_variables() == {}


def test_populated_env_surfaces_as_variables(monkeypatch):
    monkeypatch.setenv("VITRO_BOARD_NAME", "prplos-1")
    monkeypatch.setenv("VITRO_ENV_CONFIG", "/tmp/env.json")
    monkeypatch.setenv("VITRO_SKIP_BOOT", "true")

    result = get_variables()

    assert result["VITRO_BOARD_NAME"] == "prplos-1"
    assert result["VITRO_ENV_CONFIG"] == "/tmp/env.json"
    assert result["VITRO_SKIP_BOOT"] == "true"


def test_get_variables_ignores_empty_env_entries(monkeypatch):
    monkeypatch.setenv("VITRO_BOARD_NAME", "")
    monkeypatch.delenv("VITRO_ENV_CONFIG", raising=False)
    assert get_variables() == {}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_variables.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'robotframework_vitro.variables'`.

- [ ] **Step 3: Implement `robotframework_vitro/variables.py`**

```python
"""Robot Framework variable file: surfaces VITRO_* env vars as variables."""

from __future__ import annotations

import os


_SUPPORTED = (
    "VITRO_BOARD_NAME",
    "VITRO_ENV_CONFIG",
    "VITRO_INVENTORY_CONFIG",
    "VITRO_SKIP_BOOT",
    "VITRO_SKIP_CONTINGENCY_CHECKS",
    "VITRO_SAVE_CONSOLE_LOGS",
    "VITRO_LEGACY",
    "VITRO_IGNORE_DEVICES",
)


def get_variables() -> dict[str, str]:
    """Return non-empty VITRO_* environment variables as Robot variables."""
    return {name: os.environ[name] for name in _SUPPORTED if os.environ.get(name)}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_variables.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add robotframework_vitro/variables.py tests/test_variables.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "feat: add VITRO_* env var → Robot variable bridge"
```

---

## Task 12: CLI — `vitrorobot`

**Files:**
- Create: `robotframework_vitro/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_cli.py`:

```python
"""Tests for the vitrorobot CLI wrapper."""

from unittest.mock import MagicMock

import pytest

from robotframework_vitro.cli import build_listener_arg, main


def test_build_listener_arg_combines_options():
    args = {
        "board_name": "prplos-1",
        "env_config": "/e.json",
        "inventory_config": "/i.json",
        "skip_boot": True,
        "skip_contingency_checks": False,
        "save_console_logs": "",
        "legacy": False,
        "ignore_devices": "wan_phone2",
    }
    listener_arg = build_listener_arg(args)
    assert listener_arg.startswith("robotframework_vitro.VitroListener:")
    assert "board_name=prplos-1" in listener_arg
    assert "env_config=/e.json" in listener_arg
    assert "skip_boot=true" in listener_arg
    assert "skip_contingency_checks=false" in listener_arg
    assert "save_console_logs" not in listener_arg  # empty values omitted
    assert "ignore_devices=wan_phone2" in listener_arg


def test_main_requires_env_config(mocker):
    mocker.patch("robotframework_vitro.cli.robot_run_cli")
    with pytest.raises(SystemExit):
        main(["path/to/suite"])


def test_main_forwards_to_robot(mocker):
    robot_cli = mocker.patch("robotframework_vitro.cli.robot_run_cli")
    main([
        "--env-config", "/e.json",
        "--board-name", "prplos-1",
        "--skip-boot",
        "--outputdir", "results",
        "suite/",
    ])
    (argv,), _ = robot_cli.call_args
    assert "--listener" in argv
    listener_idx = argv.index("--listener")
    assert argv[listener_idx + 1].startswith("robotframework_vitro.VitroListener:")
    assert "--outputdir" in argv
    assert "results" in argv
    assert "suite/" in argv
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_cli.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'robotframework_vitro.cli'`.

- [ ] **Step 3: Implement `robotframework_vitro/cli.py`**

```python
"""``vitrorobot`` — thin wrapper that invokes robot with a VitroListener."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from robot import run_cli as robot_run_cli


_VITRO_ARGS = [
    ("--board-name", "board_name", dict(default=None)),
    ("--env-config", "env_config", dict(default=None)),
    ("--inventory-config", "inventory_config", dict(default=None)),
    ("--skip-boot", "skip_boot", dict(action="store_true")),
    ("--skip-contingency-checks", "skip_contingency_checks", dict(action="store_true")),
    ("--save-console-logs", "save_console_logs", dict(default=None)),
    ("--legacy", "legacy", dict(action="store_true")),
    ("--ignore-devices", "ignore_devices", dict(default=None)),
]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vitrorobot",
        description="Run Robot Framework tests with the vitro bridge listener",
    )
    for flag, dest, opts in _VITRO_ARGS:
        parser.add_argument(flag, dest=dest, **opts)
    return parser


def _value_to_cli(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if value == "":
        return None
    return str(value)


def build_listener_arg(options: dict[str, object]) -> str:
    """Render ``options`` as a ``--listener`` argument for robot."""
    parts = ["robotframework_vitro.VitroListener"]
    for key, value in options.items():
        rendered = _value_to_cli(value)
        if rendered is None:
            continue
        parts.append(f"{key}={rendered}")
    return ":".join(parts)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    known, extra = parser.parse_known_args(argv if argv is not None else sys.argv[1:])

    if not known.env_config:
        parser.error("--env-config is required")

    options = {dest: getattr(known, dest) for _, dest, _ in _VITRO_ARGS}
    listener_arg = build_listener_arg(options)

    robot_argv = ["--listener", listener_arg, *extra]
    return robot_run_cli(robot_argv)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_cli.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add robotframework_vitro/cli.py tests/test_cli.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "feat: add vitrorobot CLI wrapper"
```

---

## Task 13: Public API exports

**Files:**
- Modify: `robotframework_vitro/__init__.py`
- Create: `tests/test_public_api.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_public_api.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest tests/test_public_api.py -v
```

Expected: FAIL — `ImportError: cannot import name 'VitroListener' from 'robotframework_vitro'`.

- [ ] **Step 3: Replace `robotframework_vitro/__init__.py`**

```python
"""Robot Framework bridge for vitro."""

from robotframework_vitro.exceptions import (
    VitroLibraryError,
    VitroListenerError,
    VitroRobotError,
)
from robotframework_vitro.library import VitroLibrary
from robotframework_vitro.listener import VitroListener, get_listener

__version__ = "0.1.0"

__all__ = [
    "VitroLibrary",
    "VitroLibraryError",
    "VitroListener",
    "VitroListenerError",
    "VitroRobotError",
    "__version__",
    "get_listener",
]
```

- [ ] **Step 4: Run all tests to verify nothing regressed**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest -v
```

Expected: every test passes.

- [ ] **Step 5: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add robotframework_vitro/__init__.py tests/test_public_api.py
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "feat: expose public API at package root"
```

---

## Task 14: Example suite

**Files:**
- Create: `examples/basic_test.robot`
- Create: `examples/README.md`

- [ ] **Step 1: Write the example `.robot` file**

Create `examples/basic_test.robot`:

```robot
*** Settings ***
Documentation     Smoke example. Run with:
...               vitrorobot --env-config path/to/env.json
...                         --inventory-config path/to/inventory.json
...                         examples/basic_test.robot
Library           robotframework_vitro.VitroLibrary

Suite Setup       Resolve Suite Devices

*** Keywords ***
Resolve Suite Devices
    ${device_manager}=    Get Device Manager
    ${vitro_config}=      Get Vitro Config
    Set Suite Variable    ${DEVICE_MANAGER}    ${device_manager}
    Set Suite Variable    ${VITRO_CONFIG}      ${vitro_config}

*** Test Cases ***
Vitro Device Manager Is Available
    [Documentation]    Verify the listener deployed devices and the library can reach them.
    Should Not Be Equal    ${DEVICE_MANAGER}    ${NONE}

Vitro Config Is Available
    [Documentation]    Verify the merged config is reachable.
    Should Not Be Equal    ${VITRO_CONFIG}    ${NONE}
```

- [ ] **Step 2: Write `examples/README.md`**

```markdown
# Examples

`basic_test.robot` is a smoke test. It imports `robotframework_vitro.VitroLibrary`
and verifies that the listener has deployed devices by the time Suite Setup runs.

## Run it

```bash
vitrorobot \
    --env-config  path/to/env.json \
    --inventory-config path/to/inventory.json \
    examples/basic_test.robot
```

Or directly via robot if you prefer:

```bash
robot \
    --listener "robotframework_vitro.VitroListener:env_config=path/to/env.json:inventory_config=path/to/inventory.json" \
    examples/basic_test.robot
```
```

- [ ] **Step 3: Sanity-check the Robot file parses**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m robot --dryrun --outputdir /tmp/vitrorobot-dryrun examples/basic_test.robot
```

Expected: dry-run reports that the listener did not initialise (no env config provided) or that Suite Setup fails on `Get Device Manager` — both are acceptable. The point of this step is only that Robot parses the file syntactically.

- [ ] **Step 4: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add examples/basic_test.robot examples/README.md
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "docs: add basic Robot example"
```

---

## Task 15: User-facing README and CHANGELOG entry

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Rewrite `README.md`**

```markdown
# robotframework-vitro

Robot Framework bridge for the [vitro](https://github.com/…/vitro) test framework.
A thin adapter: a listener that owns vitro lifecycle, a library of infrastructure
keywords, and a CLI wrapper. Test projects supply their own scenario-aligned
keyword libraries that delegate to `vitro-templates` and `vitro-operations`.

## Install

```bash
pip install robotframework-vitro
```

## Run tests

```bash
vitrorobot \
    --env-config bf_config/env.json \
    --inventory-config bf_config/inventory.json \
    robot/tests/
```

Or invoke `robot` directly:

```bash
robot \
    --listener "robotframework_vitro.VitroListener:env_config=bf_config/env.json:inventory_config=bf_config/inventory.json" \
    robot/tests/
```

## Keywords (`VitroLibrary`)

| Keyword | Purpose |
| --- | --- |
| `Get Device Manager` | Returns the vitro `DeviceManager` |
| `Get Device By Type` | Resolve type name → class → instance (optional `index`) |
| `Get Devices By Type` | Return `dict[name, instance]` |
| `Get Vitro Config` | Returns the merged `VitroConfig` |
| `Log Step` | Emits `[STEP] <message>` at INFO level |
| `Set Test Context` / `Get Test Context` / `Clear Test Context` | Per-test dict; cleared automatically in `end_test` |

## Key design principles

1. **Libraries are thin wrappers.** Test projects create `robot/libraries/*.py`
   keyword files that call into `vitro-templates` / `vitro-operations`. The
   bridge does not ship scenario-specific keywords.

2. **Cleanup is implicit.** Keyword implementations call
   `get_listener().register_teardown(description, func, *args, **kwargs)` at the
   point of state change. `end_test` drains the stack in LIFO order. Tests do
   not need `[Teardown]` blocks for state they did not introduce.

3. **No hard-coded testbed configuration in resources.** Read from the device
   objects directly (`${cpe.device_name}`, `${router.router.active_wan_interface}`).

## Listener options

| Option | Env var | Purpose |
| --- | --- | --- |
| `board_name` | `VITRO_BOARD_NAME` | Board identifier from the inventory |
| `env_config` | `VITRO_ENV_CONFIG` | Path to `environment.json` (required) |
| `inventory_config` | `VITRO_INVENTORY_CONFIG` | Path to `inventory.json` |
| `skip_boot` | `VITRO_SKIP_BOOT` | Skip the device-boot phase |
| `skip_contingency_checks` | `VITRO_SKIP_CONTINGENCY_CHECKS` | Skip pre-test checks |
| `save_console_logs` | `VITRO_SAVE_CONSOLE_LOGS` | Directory for device console logs |
| `legacy` | `VITRO_LEGACY` | Expose `devices.<device>` legacy namespace |
| `ignore_devices` | `VITRO_IGNORE_DEVICES` | Comma-separated list of device names to skip |

## Writing a test-project keyword library

```python
from robot.api.deco import keyword
from testprotocols.models.impairment import ImpairmentProfile


def _get_listener():
    from robotframework_vitro.listener import get_listener
    return get_listener()


class RouterKeywords:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    @keyword("Apply Impairment Profile")
    def apply_impairment_profile(self, router, profile_name):
        original = router.netem.get_impairment_profile()
        profile = ImpairmentProfile.from_preset(profile_name)
        router.netem.set_impairment_profile(profile)
        _get_listener().register_teardown(
            f"Restore impairment profile on {router.device_name}",
            router.netem.set_impairment_profile,
            original,
        )
```

## License

BSD-3-Clause. See `LICENSE`.
```

- [ ] **Step 2: Update `CHANGELOG.md`**

```markdown
# Changelog

## 0.1.0 (unreleased)

### Added
- `VitroListener` — Robot Framework listener (v3) that runs vitro's pluggy hooks
  on suite start/end, wraps `vitro_setup_env` in `asyncio.run`, and maintains a
  LIFO per-test teardown stack.
- `VitroLibrary` — GLOBAL-scope Robot library with `Get Device Manager`,
  `Get Device By Type`, `Get Devices By Type`, `Get Vitro Config`, `Log Step`,
  and context-dict keywords.
- `vitrorobot` CLI — wraps `robot` with vitro configuration flags.
- `robotframework_vitro.variables` — surfaces `VITRO_*` environment variables
  as Robot variables.
- Package exports: `VitroListener`, `VitroLibrary`, `VitroRobotError`,
  `get_listener`.
```

- [ ] **Step 3: Run full test suite one more time**

```bash
cd /home/rjvisser/projects/req-tst/robotframework-vitro && python -m pytest -v
```

Expected: every test passes.

- [ ] **Step 4: Commit**

```bash
git -C /home/rjvisser/projects/req-tst/robotframework-vitro add README.md CHANGELOG.md
git -C /home/rjvisser/projects/req-tst/robotframework-vitro commit -m "docs: write user-facing README and changelog for 0.1.0"
```

---

## Self-review

**Spec coverage check:**

- §2 architecture → Task 1 (scaffold).
- §2 naming table → Task 13 (public API) + Task 12 (CLI).
- §3 Listener class shape → Tasks 3, 6.
- §3 `_deploy_devices` / `_release_devices` with vitro hook order + asyncio → Task 7.
- §3 LIFO teardown stack + `register_teardown` + error isolation → Task 4.
- §3 module-level `_LISTENER_INSTANCE` + `get_listener()` → Task 5.
- §3 env-var `variables.py` → Task 11.
- §4 seven library keywords → Tasks 8, 9, 10.
- §4 device type resolution with static map + dynamic fallback + cache → Task 10.
- §5 `vitrorobot` CLI → Task 12.
- §6 consumption pattern → documented in Task 15 README.
- §7 testing scope → covered by tests created in every task; `test_utils.py` intentionally omitted per spec §7.
- §8 examples → Task 14.
- §9 out-of-scope items → none of them have tasks (correct).

**Placeholder scan:** no `TBD`, `TODO`, `implement later`, "add error handling", etc. remain. Every code step shows full code; every test step shows full test code.

**Type consistency:**
- `VitroListener.options` dict used consistently across Tasks 3, 6, 7.
- `VitroListener.test_context`, `device_manager`, `vitro_config`, `plugin_manager` attributes introduced in one place each and referenced elsewhere.
- `get_listener()` signature and raised error are consistent across library tests and implementation.
- `VitroLibrary._resolve_device_type` signature is the same in Task 10 tests and implementation.
- `build_listener_arg` used the same way in test and implementation.

No gaps found.
