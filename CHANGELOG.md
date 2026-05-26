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
