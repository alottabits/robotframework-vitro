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
