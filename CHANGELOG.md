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
