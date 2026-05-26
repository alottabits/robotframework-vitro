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
        description=(
            "Run Robot Framework tests with the vitro bridge listener. "
            "The listed options below configure the VitroListener; "
            "every other argument is forwarded to robot unchanged "
            "(e.g. --outputdir, --include, --exclude, --variable, "
            "test-suite paths)."
        ),
        epilog=(
            "Example:\n"
            "  vitrorobot --env-config env.json --inventory-config inv.json \\\n"
            "    --board-name my-bench --outputdir results/ -i smoke tests/\n\n"
            "The --outputdir, -i, and tests/ arguments are forwarded to robot."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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
