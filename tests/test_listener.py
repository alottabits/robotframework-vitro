"""Tests for VitroListener."""

import pytest
from unittest.mock import ANY, MagicMock, call

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


@pytest.fixture
def mock_vitro(mocker):
    """Patch every vitro-side symbol the listener imports at module load."""
    plugin_manager = MagicMock(name="plugin_manager")
    hook = plugin_manager.hook
    device_manager = MagicMock(name="device_manager")
    hook.vitro_register_devices.return_value = device_manager
    vitro_config = MagicMock(name="vitro_config")

    hook.vitro_reserve_devices.return_value = {"inventory": "stub"}
    hook.vitro_parse_config.return_value = vitro_config

    mocker.patch(
        "robotframework_vitro.listener.get_plugin_manager",
        return_value=plugin_manager,
    )
    mocker.patch(
        "robotframework_vitro.listener.get_json",
        return_value={"environment_def": {}},
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
        "vitro_parse_config",
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
        cmdline_args=ANY,
        plugin_manager=ANY,
        device_manager=mock_vitro.device_manager,
    )


def test_release_devices_calls_vitro_release_hook(mock_vitro):
    listener = VitroListener(env_config="/e.json")
    listener._deploy_devices()
    mock_vitro.hook.reset_mock()
    mock_vitro.asyncio_run.reset_mock()

    listener._release_devices()

    mock_vitro.hook.vitro_release_devices.assert_called_once_with(
        config=mock_vitro.vitro_config,
        cmdline_args=ANY,
        plugin_manager=ANY,
        deployment_status=ANY,
        device_manager=mock_vitro.device_manager,
    )


def test_release_devices_is_safe_when_never_deployed(mock_vitro):
    listener = VitroListener()
    listener._release_devices()  # must not raise
    mock_vitro.hook.vitro_release_devices.assert_not_called()


def test_release_devices_skipped_when_register_failed(mock_vitro):
    """If vitro_register_devices raised, device_manager stays None and release must no-op."""
    listener = VitroListener(env_config="/e.json")
    mock_vitro.hook.vitro_register_devices.side_effect = RuntimeError("boom")
    with pytest.raises(RuntimeError, match="boom"):
        listener._deploy_devices()
    # plugin_manager is set, but device_manager is still None
    assert listener.plugin_manager is mock_vitro.plugin_manager
    assert listener.device_manager is None

    listener._release_devices()  # must not raise or call the hook
    mock_vitro.hook.vitro_release_devices.assert_not_called()


def test_deploy_devices_records_success_status(mock_vitro):
    listener = VitroListener(env_config="/e.json")
    listener._deploy_devices()
    assert listener._deployment_status == {"status": "success"}


def test_deploy_devices_records_failure_status(mock_vitro):
    listener = VitroListener(env_config="/e.json")
    mock_vitro.asyncio_run.side_effect = RuntimeError("deploy boom")
    with pytest.raises(RuntimeError, match="deploy boom"):
        listener._deploy_devices()
    assert listener._deployment_status["status"] == "failed"
    assert isinstance(listener._deployment_status["exception"], RuntimeError)
