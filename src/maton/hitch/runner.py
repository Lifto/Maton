"""Maton hitch runner — routing, state loading, prompt assembly, and LLM invocation."""

from __future__ import annotations

import fcntl
import logging
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import yaml

if TYPE_CHECKING:
    from typing import Any, TextIO

log = logging.getLogger(__name__)

_STATE_FILES = {
    "backlog": "backlog.yaml",
    "schedule": "schedule.yaml",
    "guardrails": "guardrails.yaml",
    "identity": "self.md",
    "user": "user.md",
}

_FREQ_SECONDS = {"hourly": 3600, "daily": 86400, "weekly": 604800}


def load_state(instance_dir: Path) -> dict[str, str]:
    """Read all state files from the instance directory as raw text."""
    return {
        key: path.read_text() if (path := instance_dir / filename).exists() else "empty"
        for key, filename in _STATE_FILES.items()
    }


def check_cooldown(hitch_dir: Path) -> bool:
    """Return True if a cooldown file exists and hasn't expired."""
    cooldown_file = hitch_dir / "cooldown"
    if not cooldown_file.exists():
        return False
    try:
        dt = datetime.fromisoformat(cooldown_file.read_text().strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return datetime.now(UTC) < dt
    except (ValueError, OSError):
        return False


def check_quiet_hours(guardrails_text: str) -> bool:
    """Return True if the current time falls within configured quiet hours."""
    try:
        guardrails = yaml.safe_load(guardrails_text) or {}
    except yaml.YAMLError:
        return False
    qh = guardrails.get("quiet_hours", {})
    if not qh.get("enabled"):
        return False
    try:
        now = datetime.now(ZoneInfo(qh.get("timezone", "UTC"))).time()
        start = datetime.strptime(qh["start"], "%H:%M").time()  # noqa: DTZ007
        end = datetime.strptime(qh["end"], "%H:%M").time()  # noqa: DTZ007
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end
    except (KeyError, ValueError):
        return False


def _is_due(task: dict[str, Any]) -> bool:
    """Check whether a recurring task is past its next scheduled time."""
    if not task.get("enabled", True):
        return False
    last_run = task.get("last_run")
    if last_run is None:
        return True
    try:
        if isinstance(last_run, str):
            last_dt = datetime.fromisoformat(last_run)
        elif isinstance(last_run, datetime):
            last_dt = last_run
        else:
            return True
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=UTC)
        elapsed = (datetime.now(UTC) - last_dt).total_seconds()
        freq = task.get("frequency", "daily")
        if freq in _FREQ_SECONDS:
            return elapsed >= _FREQ_SECONDS[freq]
        if freq.startswith("every_") and freq.endswith("_minutes"):
            return elapsed >= int(freq.removeprefix("every_").removesuffix("_minutes")) * 60
        return elapsed >= _FREQ_SECONDS["daily"]
    except (ValueError, TypeError):
        return True


def has_ready_work(state: dict[str, str]) -> bool:
    """Return True if the backlog has ready tasks or the schedule has due items."""
    try:
        backlog = yaml.safe_load(state["backlog"]) or {}
    except yaml.YAMLError:
        backlog = {}
    tasks = backlog.get("tasks") or []
    if any(t.get("status") == "ready" and not t.get("blocked_by") for t in tasks):
        return True

    try:
        schedule = yaml.safe_load(state["schedule"]) or {}
    except yaml.YAMLError:
        schedule = {}
    recurring = schedule.get("recurring") or []
    return any(_is_due(r) for r in recurring)


def select_skill(instance_dir: Path, state: dict[str, str]) -> tuple[str, str]:
    """Pick the skill to invoke based on current state.

    Returns:
        (skill_name, skill_content) tuple.
    """
    if has_ready_work(state):
        return ("dispatch", (instance_dir / "skills" / "dispatch.md").read_text())
    return ("ideate", (instance_dir / "skills" / "ideate.md").read_text())


def assemble_prompt(skill_content: str, state: dict[str, str]) -> str:
    """Combine skill instructions with inline state for the LLM."""
    return (
        f"{skill_content}\n\n"
        "--- CURRENT STATE ---\n\n"
        f"=== BACKLOG (backlog.yaml) ===\n{state['backlog']}\n\n"
        f"=== SCHEDULE (schedule.yaml) ===\n{state['schedule']}\n\n"
        f"=== GUARDRAILS (guardrails.yaml) ===\n{state['guardrails']}\n\n"
        f"=== IDENTITY (self.md) ===\n{state['identity']}\n\n"
        f"=== USER (user.md) ===\n{state['user']}"
    )


class _Lock:
    """File-based mutual exclusion using fcntl.flock (Unix only)."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._file: TextIO | None = None

    def acquire(self) -> bool:
        """Try to acquire the lock without blocking."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        f = self._path.open("w")
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            f.close()
            return False
        f.write(str(os.getpid()))
        f.flush()
        self._file = f
        return True

    def release(self) -> None:
        """Release the lock and remove the lock file."""
        if self._file is not None:
            fcntl.flock(self._file, fcntl.LOCK_UN)
            self._file.close()
            self._file = None
            self._path.unlink(missing_ok=True)


def _invoke(instance_dir: Path, prompt: str, model: str, timeout: int) -> int:
    """Invoke the LLM driver and return its exit code."""
    cmd = [
        "opencode",
        "run",
        "--dir",
        str(instance_dir),
        "-m",
        model,
        "--dangerously-skip-permissions",
        prompt,
    ]
    proc = subprocess.Popen(cmd)  # noqa: S603, S607
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        log.warning("killed after %ds timeout", timeout)
    return proc.returncode


def run(
    instance_dir: Path,
    hitch_dir: Path,
    model: str,
    timeout: int = 300,
) -> int:
    """Execute one dispatch cycle.

    Guards (cooldown, quiet hours, lock) are checked first. If all pass, the
    runner loads state, selects a skill, assembles the prompt, and invokes the
    LLM driver.

    Args:
        instance_dir: Path to the maton instance (a git repo).
        hitch_dir: Path to the hitch directory (lock, trigger, cooldown files).
        model: Model identifier for the LLM driver.
        timeout: Maximum seconds before killing the LLM process.

    Returns:
        0 on success or skip, negative on timeout, positive on LLM error.
    """
    if check_cooldown(hitch_dir):
        log.info("SKIP: cooldown active")
        return 0

    state = load_state(instance_dir)

    if check_quiet_hours(state["guardrails"]):
        log.info("SKIP: quiet hours")
        return 0

    lock = _Lock(hitch_dir / "lock")
    if not lock.acquire():
        log.info("SKIP: already running")
        return 0

    try:
        (hitch_dir / "trigger").unlink(missing_ok=True)

        skill_name, skill_content = select_skill(instance_dir, state)
        log.info("START: %s", skill_name)

        prompt = assemble_prompt(skill_content, state)
        exit_code = _invoke(instance_dir, prompt, model, timeout)

        log.info("END: %s (exit %d)", skill_name, exit_code)
        return exit_code
    finally:
        lock.release()


def main() -> None:
    """CLI entry point for standalone invocation."""
    import argparse

    parser = argparse.ArgumentParser(description="Maton hitch runner")
    parser.add_argument("--instance-dir", required=True, type=Path, help="path to the maton instance")
    parser.add_argument("--hitch-dir", required=True, type=Path, help="path to the hitch directory")
    parser.add_argument("--model", required=True, help="LLM model identifier")
    parser.add_argument("--timeout", type=int, default=300, help="max seconds per dispatch (default: 300)")
    parser.add_argument("--log-file", type=Path, default=None, help="log file path (default: hitch_dir/runner.log)")
    args = parser.parse_args()

    import setproctitle

    setproctitle.setproctitle(f"{args.instance_dir.name}-hitch")

    logging.basicConfig(
        filename=str(args.log_file or args.hitch_dir / "runner.log"),
        format="%(asctime)s %(message)s",
        level=logging.INFO,
    )

    sys.exit(run(args.instance_dir, args.hitch_dir, args.model, args.timeout))


if __name__ == "__main__":
    main()
