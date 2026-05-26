# Changelog

## Unreleased

### Changed (BREAKING)
- Device lookup is now name-based, mirroring pytest-palco. The previous
  `Get Device By Type` / `Get Devices By Type` keywords (which used a hardcoded
  `_TYPE_MAP` of nine testprotocols aliases) are removed. Suites that referenced
  them must switch to `Get Device <inventory_name>` or call the DeviceManager
  directly via `Get Device Manager` + `Call Method ... get_devices_by_type`.

### Added
- `Get Device <name>` keyword — returns the device registered under `<name>`,
  raising `VitroLibraryError` with the available names on miss.
- `Get All Devices` keyword — returns `dict[name, device]` for every registered
  device.
- Module-level accessor functions `get_device_manager`, `get_vitro_config`,
  `get_device`, and `get_all_devices`. Each raises `VitroLibraryError` with
  the same friendly messages as the matching Robot keyword. Re-exported from
  the package root so Python-implemented keyword libraries can reach the
  bridge without instantiating `VitroLibrary`. The Robot keywords are now
  one-line forwarders to these functions; surface and error semantics are
  unchanged.
- `py.typed` marker (PEP 561). Downstream type-checkers now honour the
  package's annotations instead of falling back to "missing stubs".

### Docs
- README: new "Reaching the bridge from Python" section covering the
  module-level accessors, a "Caveat on `skip_boot`" callout, a Robot
  library-name convention warning (filename must match the class name
  case-insensitively), a Python typing note for Robot's auto-conversion
  of annotated keyword arguments, and an explanation of the
  `_get_listener` lazy-import pattern.
- `vitrorobot --help`: argparse description + epilog now document that
  arguments not consumed by the wrapper are forwarded to `robot` unchanged
  (e.g. `--outputdir`, `--include`, test paths), with a worked example.

### Removed
- `Get Device By Type` and `Get Devices By Type` keywords.
- `VitroLibrary._TYPE_MAP`, `_static_type_map`, `_resolve_device_type`, and
  `_type_cache`.
- `testprotocols` runtime dependency.
- `robotframework_vitro.variables` module. The Robot variable-file pattern
  it implemented (surfacing `VITRO_*` env vars as `${VITRO_*}` variables)
  predated the listener's own env-var ingestion and `Get Vitro Config`;
  it had no internal consumers and was not re-exported from the package
  root.

## 0.1.0 (unreleased)

### Added
- `VitroListener` — Robot Framework listener (v3) that runs vitro's pluggy hooks
  on suite start/end, wraps `vitro_setup_env` in `asyncio.run`, and maintains a
  LIFO per-test teardown stack.
- `VitroLibrary` — GLOBAL-scope Robot library with `Get Device Manager`,
  `Get Device By Type`, `Get Devices By Type`, `Get Vitro Config`, `Log Step`,
  and context-dict keywords.
- `vitrorobot` CLI — wraps `robot` with vitro configuration flags.
- Package exports: `VitroListener`, `VitroLibrary`, `VitroRobotError`,
  `get_listener`.
