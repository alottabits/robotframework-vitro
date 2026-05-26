# robotframework-vitro

Robot Framework bridge for the [vitro](https://github.com/…/vitro) test framework.
A thin adapter: a listener that owns vitro lifecycle, a library of infrastructure
keywords, and a CLI wrapper. Test projects supply their own scenario-aligned
keyword libraries that delegate to `vitro-templates` and `vitro-operations`.

## Install

    pip install robotframework-vitro

## Run tests

    vitrorobot \
        --env-config vitro_config/env.json \
        --inventory-config vitro_config/inventory.json \
        robot/tests/

Or invoke `robot` directly:

    robot \
        --listener "robotframework_vitro.VitroListener:env_config=vitro_config/env.json:inventory_config=vitro_config/inventory.json" \
        robot/tests/

## Keywords (`VitroLibrary`)

| Keyword | Purpose |
| --- | --- |
| `Get Device Manager` | Returns the vitro `DeviceManager` |
| `Get Vitro Config` | Returns the merged `VitroConfig` |
| `Get Device <name>` | Returns the device registered under `<name>` in the inventory |
| `Get All Devices` | Returns `dict[name, device]` for every registered device |
| `Log Step` | Emits `[STEP] <message>` at INFO level |
| `Set Test Context` / `Get Test Context` / `Clear Test Context` | Per-test dict; cleared automatically in `end_test` |

### Resolving devices

Devices are looked up by their inventory name — the same key vitro plugins
register them under via `vitro_add_devices`. There is no string-to-class type
resolver: vitro's plugin manager and `DeviceManager` are the single source of
truth. If the name isn't in the inventory, `Get Device` raises
`VitroLibraryError` and lists the names that are available.

For type-filtered lookups (e.g. "all SIP phones") a testbed-specific Robot
resource file can import its own device class and reach the DeviceManager via
`Get Device Manager`, then invoke `get_devices_by_type` on it through Robot's
`Call Method`. That stays a testbed concern; robotframework-vitro itself only
offers name-based access.

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

> **Caveat on `skip_boot`.** This option skips `vitro_device_boot` entirely.
> Any state a driver caches *during* that hook (ACS references for reboot
> verification, post-boot console activation, capability-prep that happens
> on first boot, etc.) will not be present. Tests that exercise such state
> must run without `--skip-boot`.

## Reaching the bridge from Python

The infrastructure keywords in `VitroLibrary` are also exposed as
module-level functions, so Python-implemented keyword libraries can reach
the bridge without instantiating the Robot library class:

~~~python
from robotframework_vitro import (
    get_all_devices,
    get_device,
    get_device_manager,
    get_vitro_config,
)
~~~

Each raises `VitroLibraryError` with the same friendly message as the
corresponding Robot keyword if it is called before devices are deployed,
or (for `get_device`) the name isn't in the inventory.

## Writing a test-project keyword library

~~~python
# File: RouterKeywords.py  ← filename must match the class name (see note below)
from robot.api.deco import keyword


def _get_listener():
    # Lazy import: Robot's library loader can pull this module before the
    # listener's own module is fully initialised, so resolve get_listener at
    # call time instead of import time.
    from robotframework_vitro.listener import get_listener
    return get_listener()


class RouterKeywords:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    @keyword("Set Router Hostname")
    def set_router_hostname(self, router, hostname):
        original = router.hostname
        router.set_hostname(hostname)
        _get_listener().register_teardown(
            f"Restore hostname on {router.device_name}",
            router.set_hostname,
            original,
        )
~~~

Robot tests obtain `${router}` via `${router}=    Get Device    edge_router`
and pass it into the keyword. The teardown registered here runs automatically
when the test ends; the test itself does not need a `[Teardown]` block.

> **Robot library-name convention.** When a Python library file contains a
> single class, Robot Framework expects the filename to match the class name
> (case-insensitive) — `RouterKeywords` in a `RouterKeywords.py` file. If the
> names disagree (for example `router_keywords.py` + class `RouterKeywords`),
> Robot's library loader silently falls back to module-level functions, finds
> none, and reports every keyword as "No keyword with name '...' found". Use
> the class-matching filename, or import with qualified notation
> (`Library    router_keywords.RouterKeywords`).

> **Python typing.** Robot Framework 3.1+ auto-converts keyword arguments to
> their Python type hints before the keyword body runs. Annotating
> `port: int` / `timeout: int` etc. is sufficient — no `int(...)` casts in
> the body are needed. If the cast fails, Robot raises a clear conversion
> error before the keyword is called.

## License

BSD-3-Clause. See `LICENSE`.
