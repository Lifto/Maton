"""Platform-specific scheduling for maton hitch (launchd / systemd)."""

from __future__ import annotations

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import yaml


def _service_name(instance_dir: Path) -> str:
    return f"com.maton.{instance_dir.name}"


def _load_config(hitch_dir: Path) -> dict[str, Any]:
    config_path = hitch_dir / "config.yaml"
    if not config_path.exists():
        msg = f"No config.yaml in {hitch_dir}"
        raise FileNotFoundError(msg)
    return yaml.safe_load(config_path.read_text()) or {}


def _hitch_binary() -> str:
    """Find the maton-hitch entry point binary."""
    import shutil as _shutil

    found = _shutil.which("maton-hitch")
    if found:
        return found
    # Fallback: same bin dir as the running Python
    candidate = Path(sys.executable).parent / "maton-hitch"
    if candidate.exists():
        return str(candidate)
    msg = "maton-hitch not found — is maton installed?"
    raise FileNotFoundError(msg)


# ---------------------------------------------------------------------------
# launchd (macOS)
# ---------------------------------------------------------------------------


def _launchd_plist(instance_dir: Path, hitch_dir: Path, config: dict[str, Any]) -> str:
    label = _service_name(instance_dir)
    binary = _hitch_binary()
    timeout = config.get("timeout", 300)
    trigger_path = str(hitch_dir / "trigger")

    return textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>{label}</string>
            <key>ProgramArguments</key>
            <array>
                <string>{binary}</string>
                <string>--instance-dir</string>
                <string>{instance_dir}</string>
                <string>--hitch-dir</string>
                <string>{hitch_dir}</string>
                <string>--timeout</string>
                <string>{timeout}</string>
            </array>
            <key>StartInterval</key>
            <integer>{timeout}</integer>
            <key>WatchPaths</key>
            <array>
                <string>{trigger_path}</string>
            </array>
            <key>StandardOutPath</key>
            <string>{hitch_dir / "stdout.log"}</string>
            <key>StandardErrorPath</key>
            <string>{hitch_dir / "stderr.log"}</string>
            <key>EnvironmentVariables</key>
            <dict>
                <key>PATH</key>
                <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
            </dict>
        </dict>
        </plist>
    """)


def _driver_spec(driver: dict[str, Any]) -> str:
    """Return a CLI driver spec from hitch config."""
    name = driver.get("name") or driver.get("type")
    if not name:
        msg = "Each driver needs a name"
        raise ValueError(msg)
    model = driver.get("model")
    return f"{name}:{model}" if model else str(name)


def _launchd_plist_path(instance_dir: Path) -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{_service_name(instance_dir)}.plist"


def _validate_config_for_install(config: dict[str, Any]) -> None:
    """Validate that hitch config can produce at least one runnable driver."""
    drivers = config.get("drivers") or []
    if not config.get("model") and not drivers:
        msg = "Set 'model' or 'drivers' in hitch/config.yaml before installing"
        raise ValueError(msg)
    for driver in drivers:
        name = driver.get("name") or driver.get("type")
        if name == "opencode" and not driver.get("model"):
            msg = "OpenCode driver needs a model in hitch/config.yaml before installing"
            raise ValueError(msg)


def install_launchd(instance_dir: Path, hitch_dir: Path) -> Path:
    """Write a launchd plist and load it.

    Returns:
        Path to the installed plist file.
    """
    config = _load_config(hitch_dir)
    _validate_config_for_install(config)

    plist_content = _launchd_plist(instance_dir, hitch_dir, config)
    plist_path = _launchd_plist_path(instance_dir)
    plist_path.parent.mkdir(parents=True, exist_ok=True)
    plist_path.write_text(plist_content)

    # Also write a copy in hitch/ for reference
    (hitch_dir / "launchd.plist").write_text(plist_content)

    launchctl = shutil.which("launchctl") or "launchctl"
    subprocess.run([launchctl, "load", str(plist_path)], check=True, capture_output=True)  # noqa: S603

    return plist_path


def uninstall_launchd(instance_dir: Path, hitch_dir: Path) -> bool:
    """Unload and remove the launchd plist.

    Returns:
        True if the plist existed and was removed, False if nothing to remove.
    """
    plist_path = _launchd_plist_path(instance_dir)
    if not plist_path.exists():
        return False

    launchctl = shutil.which("launchctl") or "launchctl"
    subprocess.run([launchctl, "unload", str(plist_path)], check=False, capture_output=True)  # noqa: S603

    plist_path.unlink(missing_ok=True)
    (hitch_dir / "launchd.plist").unlink(missing_ok=True)
    return True


# ---------------------------------------------------------------------------
# systemd (Linux)
# ---------------------------------------------------------------------------


def _systemd_unit(instance_dir: Path, hitch_dir: Path, config: dict[str, Any]) -> str:
    binary = _hitch_binary()
    timeout = config.get("timeout", 300)

    return textwrap.dedent(f"""\
        [Unit]
        Description=Maton hitch: {instance_dir.name}

        [Service]
        Type=oneshot
        ExecStart={binary} \\
            --instance-dir {instance_dir} \\
            --hitch-dir {hitch_dir} \\
            --timeout {timeout}

        [Install]
        WantedBy=default.target
    """)


def _systemd_timer(config: dict[str, Any]) -> str:
    timeout = config.get("timeout", 300)
    return textwrap.dedent(f"""\
        [Unit]
        Description=Maton hitch timer

        [Timer]
        OnBootSec=60
        OnUnitActiveSec={timeout}

        [Install]
        WantedBy=timers.target
    """)


def _systemd_dir() -> Path:
    return Path.home() / ".config" / "systemd" / "user"


def _systemd_service_name(instance_dir: Path) -> str:
    return f"maton-{instance_dir.name}"


def install_systemd(instance_dir: Path, hitch_dir: Path) -> Path:
    """Write a systemd user service + timer and enable it.

    Returns:
        Path to the installed service file.
    """
    config = _load_config(hitch_dir)
    _validate_config_for_install(config)

    unit_name = _systemd_service_name(instance_dir)
    unit_dir = _systemd_dir()
    unit_dir.mkdir(parents=True, exist_ok=True)

    service_path = unit_dir / f"{unit_name}.service"
    timer_path = unit_dir / f"{unit_name}.timer"

    service_path.write_text(_systemd_unit(instance_dir, hitch_dir, config))
    timer_path.write_text(_systemd_timer(config))

    # Also write copies in hitch/ for reference
    (hitch_dir / "systemd.service").write_text(service_path.read_text())
    (hitch_dir / "systemd.timer").write_text(timer_path.read_text())

    systemctl = shutil.which("systemctl") or "systemctl"
    subprocess.run([systemctl, "--user", "daemon-reload"], check=True, capture_output=True)  # noqa: S603
    subprocess.run([systemctl, "--user", "enable", "--now", f"{unit_name}.timer"], check=True, capture_output=True)  # noqa: S603

    return service_path


def uninstall_systemd(instance_dir: Path, hitch_dir: Path) -> bool:
    """Disable and remove the systemd user service + timer.

    Returns:
        True if files existed and were removed, False if nothing to remove.
    """
    unit_name = _systemd_service_name(instance_dir)
    unit_dir = _systemd_dir()
    service_path = unit_dir / f"{unit_name}.service"
    timer_path = unit_dir / f"{unit_name}.timer"

    if not service_path.exists() and not timer_path.exists():
        return False

    systemctl = shutil.which("systemctl") or "systemctl"
    subprocess.run(  # noqa: S603
        [systemctl, "--user", "disable", "--now", f"{unit_name}.timer"], check=False, capture_output=True
    )

    service_path.unlink(missing_ok=True)
    timer_path.unlink(missing_ok=True)
    (hitch_dir / "systemd.service").unlink(missing_ok=True)
    (hitch_dir / "systemd.timer").unlink(missing_ok=True)

    subprocess.run([systemctl, "--user", "daemon-reload"], check=False, capture_output=True)  # noqa: S603

    return True


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def detect_platform() -> str:
    """Return 'launchd' on macOS, 'systemd' on Linux."""
    if sys.platform == "darwin":
        return "launchd"
    return "systemd"


def install(instance_dir: Path, hitch_dir: Path) -> Path:
    """Install platform scheduling for the given instance.

    Returns:
        Path to the primary installed config file.
    """
    platform = detect_platform()
    if platform == "launchd":
        return install_launchd(instance_dir, hitch_dir)
    return install_systemd(instance_dir, hitch_dir)


def uninstall(instance_dir: Path, hitch_dir: Path) -> bool:
    """Remove platform scheduling for the given instance.

    Returns:
        True if scheduling was removed, False if nothing was installed.
    """
    platform = detect_platform()
    if platform == "launchd":
        return uninstall_launchd(instance_dir, hitch_dir)
    return uninstall_systemd(instance_dir, hitch_dir)
