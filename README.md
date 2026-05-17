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

~~~python
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
~~~

## License

BSD-3-Clause. See `LICENSE`.
