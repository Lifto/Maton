"""Tests for maton hitch platform scheduling."""

from pathlib import Path
from unittest.mock import patch

import yaml

from maton.hitch.platform import (
    _launchd_plist,
    _launchd_plist_path,
    _load_config,
    _service_name,
    _systemd_timer,
    _systemd_unit,
    detect_platform,
    uninstall_launchd,
)


def _make_hitch(tmp_path: Path, model: str = "test/model", timeout: int = 300) -> Path:
    """Set up a minimal hitch directory for testing."""
    hitch = tmp_path / "hitch"
    hitch.mkdir()
    config = {"model": model, "timeout": timeout}
    (hitch / "config.yaml").write_text(yaml.dump(config))
    return hitch


def test_service_name_uses_instance_dirname(tmp_path: Path) -> None:
    """Service name is com.maton.<instance_dir_name>."""
    instance = tmp_path / "maton-20260510-120000"
    instance.mkdir()
    assert _service_name(instance) == "com.maton.maton-20260510-120000"


def test_load_config_reads_yaml(tmp_path: Path) -> None:
    """_load_config returns parsed config.yaml contents."""
    hitch = _make_hitch(tmp_path, model="drone/Qwen3", timeout=600)
    config = _load_config(hitch)
    assert config["model"] == "drone/Qwen3"
    assert config["timeout"] == 600


def test_load_config_raises_on_missing(tmp_path: Path) -> None:
    """_load_config raises FileNotFoundError when config.yaml is absent."""
    import pytest

    with pytest.raises(FileNotFoundError):
        _load_config(tmp_path)


def test_launchd_plist_contains_key_fields(tmp_path: Path) -> None:
    """Generated plist contains the label and instance path."""
    instance = tmp_path / "maton-test"
    instance.mkdir()
    hitch = _make_hitch(tmp_path, model="drone/Qwen3")
    config = _load_config(hitch)
    plist = _launchd_plist(instance, hitch, config)
    assert "com.maton.maton-test" in plist
    assert str(instance) in plist
    assert "WatchPaths" in plist


def test_launchd_plist_path_is_in_launch_agents(tmp_path: Path) -> None:
    """Plist path targets ~/Library/LaunchAgents/."""
    instance = tmp_path / "maton-test"
    instance.mkdir()
    path = _launchd_plist_path(instance)
    assert "LaunchAgents" in str(path)
    assert path.name == "com.maton.maton-test.plist"


def test_systemd_unit_contains_key_fields(tmp_path: Path) -> None:
    """Generated systemd unit contains instance path and timeout."""
    instance = tmp_path / "maton-test"
    instance.mkdir()
    hitch = _make_hitch(tmp_path, model="drone/Qwen3", timeout=600)
    config = _load_config(hitch)
    unit = _systemd_unit(instance, hitch, config)
    assert str(instance) in unit
    assert "600" in unit


def test_systemd_timer_uses_timeout(tmp_path: Path) -> None:
    """Generated systemd timer uses timeout from config."""
    config = {"timeout": 900}
    timer = _systemd_timer(config)
    assert "OnUnitActiveSec=900" in timer


def test_uninstall_launchd_returns_false_when_nothing(tmp_path: Path) -> None:
    """uninstall_launchd returns False when no plist exists."""
    instance = tmp_path / "maton-test"
    instance.mkdir()
    hitch = _make_hitch(tmp_path)
    assert uninstall_launchd(instance, hitch) is False


@patch("sys.platform", "darwin")
def test_detect_platform_darwin() -> None:
    """detect_platform returns 'launchd' on macOS."""
    assert detect_platform() == "launchd"


@patch("sys.platform", "linux")
def test_detect_platform_linux() -> None:
    """detect_platform returns 'systemd' on Linux."""
    assert detect_platform() == "systemd"


def test_install_launchd_requires_model(tmp_path: Path) -> None:
    """install_launchd raises ValueError when model is empty."""
    import pytest

    from maton.hitch.platform import install_launchd

    instance = tmp_path / "maton-test"
    instance.mkdir()
    hitch = _make_hitch(tmp_path, model="")
    with pytest.raises(ValueError, match="Set 'model'"):
        install_launchd(instance, hitch)


def test_install_systemd_requires_model(tmp_path: Path) -> None:
    """install_systemd raises ValueError when model is empty."""
    import pytest

    from maton.hitch.platform import install_systemd

    instance = tmp_path / "maton-test"
    instance.mkdir()
    hitch = _make_hitch(tmp_path, model="")
    with pytest.raises(ValueError, match="Set 'model'"):
        install_systemd(instance, hitch)
