# Changelog

## 0.1.1

### Fixed
- README: corrected the delegation targets from the non-existent
  `vitro-templates` / `vitro-operations` to `testoperations` composition
  functions over `testprotocols`-typed devices.

## 0.1.0

First public release.

### Added
- `VitroListener` — Robot Framework listener (v3) that runs vitro's pluggy hooks
  on suite start/end, wraps `vitro_setup_env` in `asyncio.run`, and maintains a
  LIFO per-test teardown stack.
- `VitroLibrary` — Robot library of infrastructure keywords: `Get Device Manager`,
  `Get Vitro Config`, `Get Device <name>`, `Get All Devices`, `Log Step`, and the
  `Set Test Context` / `Get Test Context` / `Clear Test Context` keywords. Device
  lookup is name-based, keyed on the inventory name (`Get Device <inventory_name>`);
  for type-filtered lookups, reach the DeviceManager via `Get Device Manager` +
  `Call Method ... get_devices_by_type`. `Get Device <name>` raises
  `VitroLibraryError` listing the available names on a miss.
- Module-level functions covering every `VitroLibrary` infrastructure keyword:
  `get_device_manager`, `get_vitro_config`, `get_device`, `get_all_devices`,
  `register_teardown`, `set_test_context`, `get_test_context`,
  `clear_test_context`, and `log_step`. Each matches the surface and error
  semantics of the corresponding keyword and is re-exported from the package
  root, so Python keyword libraries can reach the bridge without instantiating
  `VitroLibrary`. The Robot keywords are one-line forwarders to these functions.
- `vitrorobot` CLI — wraps `robot` with vitro configuration flags; arguments not
  consumed by the wrapper are forwarded to `robot` unchanged (e.g. `--outputdir`,
  `--include`, test paths).
- `py.typed` marker (PEP 561), so downstream type-checkers honour the package's
  annotations.
- Package exports: `VitroListener`, `VitroLibrary`, `VitroListenerError`,
  `VitroLibraryError`, `VitroRobotError`, `get_listener`, `__version__`, and the
  module-level functions above.
