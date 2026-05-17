# robotframework-vitro — Design

**Date:** 2026-04-21
**Status:** Design approved, pending implementation plan
**Relationship:** Sibling bridge to `robotframework-boardfarm`, adapting `vitro` for Robot Framework.

## 1. Goals and non-goals

### Goals

- Expose the `vitro` framework to Robot Framework with the same two-piece architecture as `robotframework-boardfarm`: a listener that owns lifecycle plus a library of infrastructure keywords.
- Match the boardfarm bridge's conventions so a developer fluent in one is fluent in both: same keyword names where semantics carry over, same LIFO per-test teardown model, same CLI shape, same environment-variable conventions.
- Stay thin. Test projects supply their own `@keyword`-decorated libraries that delegate to `vitro-templates` and `vitro-operations`; the bridge does not ship scenario-specific keywords.

### Non-goals

- Auto-generating keywords by introspecting device classes. `robotframework-boardfarm` removed this in commit `6841162`; this bridge does not reintroduce it.
- Shipping a convenience library parallel to `vitro-operations`. Test projects own that.
- Environment-requirement tags (`env_req:`) and a `Require Environment` keyword. Vitro has no environment-matching utility today; the feature is deferred until vitro grows one.
- Per-test console refresh. Boardfarm's bridge has a CPE-specific `_refresh_cpe_console()`. Vitro is device-agnostic; test projects that need this register a teardown for it.

## 2. Architecture

Two classes, one CLI, one support module.

```
robotframework-vitro/
├── robotframework_vitro/
│   ├── __init__.py          # Public exports: VitroListener, VitroLibrary, VitroRobotError
│   ├── listener.py          # VitroListener (ROBOT_LISTENER_API_VERSION = 3)
│   ├── library.py           # VitroLibrary (ROBOT_LIBRARY_SCOPE = "GLOBAL")
│   ├── cli.py               # vitrorobot CLI wrapper
│   ├── variables.py         # Env-var → listener kwarg helpers
│   └── exceptions.py        # VitroRobotError hierarchy
├── tests/                   # pytest unit tests
├── examples/                # basic_test.robot + README
├── pyproject.toml           # flit_core build backend
├── README.md
└── CHANGELOG.md
```

### Dependencies

- `vitro` — required. Provides the plugin manager, `DeviceManager`, `VitroConfig`, `parse_vitro_config`, and the hook set.
- `robotframework` — required.
- **Not** depended on: `vitro-templates`, `vitro-operations`, `pytest-vitro`. Those are concerns of the test project, not the bridge.

### Naming

| Element | Name |
| --- | --- |
| PyPI / repo | `robotframework-vitro` |
| Import path | `robotframework_vitro` |
| Listener class | `VitroListener` |
| Library class | `VitroLibrary` |
| CLI entry point | `vitrorobot` |
| Exception base | `VitroRobotError` |

## 3. Listener

`VitroListener` owns every lifecycle concern the bridge has. Ported from `BoardfarmListener` with vitro hook names and an async boundary.

### Class shape

```python
class VitroListener:
    ROBOT_LISTENER_API_VERSION = 3

    _DEFAULT_OPTIONS = {
        "board_name": "",
        "env_config": "",
        "inventory_config": "",
        "skip_boot": False,
        "skip_contingency_checks": False,
        "save_console_logs": "",
        "legacy": False,
        "ignore_devices": "",
    }

    def __init__(self, **kwargs): ...
    def start_suite(self, data, result): ...   # root suite only: _deploy_devices()
    def end_suite(self, data, result): ...     # root suite only: _release_devices()
    def start_test(self, data, result): ...    # contingency checks
    def end_test(self, data, result): ...      # drain teardown stack, clear context

    def register_teardown(self, description, func, *args, **kwargs): ...

    @property
    def cmdline_args(self) -> Namespace: ...   # built from _options
```

Module-level `_LISTENER_INSTANCE` and `get_listener()` function give keyword libraries a stable handle, matching the boardfarm bridge.

### `_deploy_devices()`

The vitro-specific phase. Mirrors the call order and argument shape in `vitro/src/vitro/main.py`. Every hook that the vitro hookspecs declare as requiring `plugin_manager` receives it, and `vitro_reserve_devices` + `vitro_parse_config` are called as hooks (not library-level helpers) so plugin overrides are honoured:

```python
import asyncio
from vitro.main import get_plugin_manager
from vitro.libraries.vitro_config import get_json


def _deploy_devices(self):
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
    # vitro_post_setup_env is deliberately skipped — same choice the boardfarm bridge makes.
```

`_release_devices()` calls `vitro_release_devices` with the full hookspec signature (`config`, `cmdline_args`, `plugin_manager`, `deployment_status`, `device_manager`) and guards on both `plugin_manager` and `device_manager` being non-None so a mid-deploy failure does not send `None` into a plugin:

```python
def _release_devices(self):
    if self.plugin_manager is None or self.device_manager is None:
        return
    self.plugin_manager.hook.vitro_release_devices(
        config=self.vitro_config,
        cmdline_args=self.cmdline_args,
        plugin_manager=self.plugin_manager,
        deployment_status=self._deployment_status,
        device_manager=self.device_manager,
    )
```

`vitro_release_devices` is synchronous in vitro today, so no `asyncio.run` wrapper is needed. Only `vitro_setup_env` crosses the async boundary — one `asyncio.run` per suite start. No persistent event loop is maintained between hooks; vitro itself uses the same one-shot pattern in `main.py:74`.

### Per-test cleanup — LIFO teardown stack

Ported verbatim from `robotframework-boardfarm`:

- `register_teardown(description, func, *args, **kwargs)` pushes a tuple onto `self._teardown_stack`.
- `_drain_teardown_stack()` pops in reverse order. Each invocation is wrapped in try/except so one failing teardown does not block the rest; failures are logged and surfaced in the Robot log.
- `end_test()` drains the stack, then clears the library's per-test context dict.

Same semantics means the same unit tests from `robotframework-boardfarm/tests/test_listener.py` can be adapted one-for-one.

### Dropped from `BoardfarmListener`

- `env_req:` tag parsing and environment-matching checks (no vitro equivalent exists).
- `_refresh_cpe_console()` (CPE-specific; not part of vitro's device-agnostic model).

### Environment variable support

`variables.py` provides a Robot variable-file shim that reads:

- `VITRO_BOARD_NAME`
- `VITRO_ENV_CONFIG`
- `VITRO_INVENTORY_CONFIG`
- `VITRO_SKIP_BOOT`
- `VITRO_SKIP_CONTINGENCY_CHECKS`
- `VITRO_SAVE_CONSOLE_LOGS`
- `VITRO_LEGACY`
- `VITRO_IGNORE_DEVICES`

Values feed the listener constructor when the user supplies `-V robotframework_vitro.variables`.

## 4. Library

`VitroLibrary` ships seven infrastructure keywords. It is `BoardfarmLibrary` minus `Require Environment`, with boardfarm-specific type names replaced.

| Keyword | Purpose |
| --- | --- |
| `Get Device Manager` | Returns the `DeviceManager` singleton |
| `Get Device By Type` | Resolves a type name to a class, returns the matching instance (optional `index` arg) |
| `Get Devices By Type` | Returns `dict[name, instance]` for every registered device of a type |
| `Get Vitro Config` | Returns the merged `VitroConfig` |
| `Log Step` | Emits `[STEP] <message>` into the Robot log |
| `Set Test Context` / `Get Test Context` / `Clear Test Context` | Per-test dict; cleared by the listener in `end_test` |

`ROBOT_LIBRARY_SCOPE = "GLOBAL"`. Keyword list is static — no introspection.

### Device type resolution

`_resolve_device_type()` maintains a static map from upper-case type names to vitro / vitro-commons classes (entries for `CPE`, `ACS`, `LAN`, `WAN`, `SIPPHONE`, `SIPSERVER`, `TRAFFIC_CONTROLLER`, `QOE_CLIENT`, `SDWAN_ROUTER`). Map misses fall through to a dynamic import from `palco_templates.*` / plugin-provided device classes. Resolved classes are cached per listener lifetime.

The static map stays minimal on purpose: it covers the types consumers commonly need, and the dynamic fallback keeps the door open for test-project-specific device classes without forcing a release of the bridge.

## 5. CLI

`vitrorobot` wraps `robot` with vitro configuration flags, mirroring `bfrobot`. Implementation in `cli.py`:

- Build argparse parser with the vitro arguments listed below plus an opaque tail forwarded to `robot`.
- Convert parsed args into a `robotframework_vitro.VitroListener:key=value:...` string.
- Invoke `robot.run_cli(["--listener", listener_spec, *tail])`.

Arguments:

```
--board-name                 (optional)
--env-config                 (required)
--inventory-config           (optional)
--skip-boot                  (flag)
--skip-contingency-checks    (flag)
--save-console-logs <dir>
--legacy                     (flag)
--ignore-devices <csv>
```

All other arguments (suite path, `--outputdir`, `--include`, tags, etc.) pass through unchanged.

## 6. Consumption pattern

Test projects continue the boardfarm-bdd pattern. The bridge documents but does not enforce it.

```robot
*** Settings ***
Library    robotframework_vitro.VitroLibrary
Library    ../libraries/router_keywords.py

Suite Setup       Setup SDWAN Suite

*** Keywords ***
Setup SDWAN Suite
    ${router}=    Get Device By Type    SDWAN_ROUTER
    Set Suite Variable    ${ROUTER}    ${router}

*** Test Cases ***
SD-WAN failover maintains application continuity
    Apply Impairment Profile    ${ROUTER}    high_loss
    # No [Teardown] block — the router_keywords library registered the restore step
    # with get_listener().register_teardown() at the point of state change.
```

`router_keywords.py` lives in the test project:

```python
from robot.api.deco import keyword
from palco_templates.models.impairment import ImpairmentProfile

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

## 7. Testing

pytest unit tests in `tests/`:

- `test_listener.py`
  - Options parsing (dashes-to-underscores, boolean coercion).
  - Teardown stack LIFO order.
  - Teardown error isolation — a failing entry does not block later entries.
  - Hook invocation order inside `_deploy_devices()` using a mocked plugin manager and mocked `asyncio.run`.
  - `start_test` / `end_test` clear the per-test context.
- `test_library.py`
  - Context store / get / clear.
  - Device type resolution cache hit and miss.
  - Keyword behaviour against a mocked listener.

`test_utils.py` is deferred — `utils.py` does not earn one in v0.1 because environment matching is out of scope.

## 8. Examples

One `.robot` file and a short README. Not a full scenario:

- `examples/basic_test.robot` — Suite Setup fetches devices via `Get Device By Type`, a single test asserts a property on one of them.
- `examples/README.md` — shows the `vitrorobot` invocation.

## 9. Explicitly out of scope for v0.1

- `env_req:` Robot tags and `Require Environment` keyword.
- Per-test console refresh.
- Auto-generated keywords from device-class introspection.
- A shared `vitro.use_cases`-style convenience library alongside the bridge.
- Integration with `pytest-vitro` (independent bridge; no shared code).

## 10. Open questions

None at the design stage. Implementation-phase details (pyproject.toml specifics, version pin on vitro, exact module paths for device-type static map entries) will be settled in the implementation plan.

## 11. Reference map

| Concept | `robotframework-boardfarm` | `robotframework-vitro` |
| --- | --- | --- |
| Listener class | `BoardfarmListener` | `VitroListener` |
| Library class | `BoardfarmLibrary` | `VitroLibrary` |
| CLI | `bfrobot` | `vitrorobot` |
| Framework dep | `boardfarm3` | `vitro` |
| Hook prefix | `boardfarm_` | `vitro_` |
| Setup hook | `boardfarm_setup_env` (async via hook) | `vitro_setup_env` (async, wrapped in `asyncio.run`) |
| Config object | `BoardfarmConfig` | `VitroConfig` |
| Env matching | `is_env_matching` in `utils.py` | Not present (out of scope) |
| Console refresh | CPE-specific method in listener | Not present (test-project concern) |
| Teardown stack | LIFO, `register_teardown()` | LIFO, `register_teardown()` (identical) |
| Test-project keyword pattern | `@keyword` wrappers delegating to `boardfarm3.use_cases` | `@keyword` wrappers delegating to `vitro-templates` / `vitro-operations` |
