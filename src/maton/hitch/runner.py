"""Maton hitch runner — routing, state loading, prompt assembly, and LLM invocation."""

from __future__ import annotations

import fcntl
import logging
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

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


def _count_ready(state: dict[str, str]) -> tuple[int, int]:
    """Count actionable backlog tasks and due scheduled items.

    Returns:
        (ready_tasks, due_schedules) tuple.
    """
    try:
        backlog = yaml.safe_load(state["backlog"]) or {}
    except yaml.YAMLError:
        backlog = {}
    tasks = backlog.get("tasks") or []
    ready = sum(1 for t in tasks if t.get("status") == "ready" and not t.get("blocked_by"))

    try:
        schedule = yaml.safe_load(state["schedule"]) or {}
    except yaml.YAMLError:
        schedule = {}
    recurring = schedule.get("recurring") or []
    due = sum(1 for r in recurring if _is_due(r))

    return ready, due


def has_ready_work(state: dict[str, str]) -> bool:
    """Return True if the backlog has ready tasks or the schedule has due items."""
    ready, due = _count_ready(state)
    return ready > 0 or due > 0


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


def _git_head(instance_dir: Path) -> str | None:
    """Return the current HEAD commit hash, or None if not a git repo."""
    result = subprocess.run(  # noqa: S603
        ["git", "-C", str(instance_dir), "rev-parse", "HEAD"],  # noqa: S607
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _commit_subjects(instance_dir: Path, since: str) -> list[str]:
    """Return commit subject lines added after the given ref."""
    result = subprocess.run(  # noqa: S603
        ["git", "-C", str(instance_dir), "log", f"{since}..HEAD", "--format=%s"],  # noqa: S607
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.strip().splitlines() if line]


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
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)  # noqa: S603, S607
    try:
        _, stderr_bytes = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        log.warning("TIMEOUT: killed after %ds", timeout)
        return -1
    if stderr_bytes:
        for line in stderr_bytes.decode(errors="replace").strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if "SSE read timed out" in line:
                log.warning("SSE_TIMEOUT: model stalled mid-inference (chunkTimeout fired)")
            else:
                log.warning("STDERR: %s", line)
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
    state = load_state(instance_dir)

    lock = _Lock(hitch_dir / "lock")
    if not lock.acquire():
        log.info("SKIP: already running")
        return 0

    try:
        (hitch_dir / "trigger").unlink(missing_ok=True)

        ready, due = _count_ready(state)
        log.info("STATE: %d ready task(s), %d due schedule(s)", ready, due)

        skill_name, skill_content = select_skill(instance_dir, state)
        log.info("START: %s", skill_name)

        prompt = assemble_prompt(skill_content, state)
        index_lock = instance_dir / ".git" / "index.lock"
        if index_lock.exists():
            log.info("GIT_LOCK: removed stale index.lock")
            index_lock.unlink(missing_ok=True)
        head_before = _git_head(instance_dir)
        t0 = time.monotonic()
        exit_code = _invoke(instance_dir, prompt, model, timeout)
        elapsed = time.monotonic() - t0

        log.info("END: %s (exit %d, %.0fs)", skill_name, exit_code, elapsed)

        head_after = _git_head(instance_dir)
        if head_before and head_after and head_before != head_after:
            for subj in _commit_subjects(instance_dir, head_before):
                log.info("COMMIT: %s", subj)
        elif exit_code == 0:
            log.info("RESULT: no commits")
        return exit_code
    finally:
        lock.release()
        index_lock = instance_dir / ".git" / "index.lock"
        if index_lock.exists():
            log.info("GIT_LOCK: removed stale index.lock")
            index_lock.unlink(missing_ok=True)
        (hitch_dir / "trigger").write_text("")


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
