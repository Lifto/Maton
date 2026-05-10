"""Tests for maton hitch runner."""

import contextlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import yaml

from maton.hitch.runner import (
    assemble_prompt,
    check_cooldown,
    check_quiet_hours,
    has_ready_work,
    load_state,
    select_skill,
)


def _make_instance(tmp_path: Path) -> Path:
    """Set up a minimal maton instance directory for testing."""
    instance = tmp_path / "instance"
    instance.mkdir()
    (instance / "backlog.yaml").write_text("tasks: []\n")
    (instance / "schedule.yaml").write_text("recurring: []\n")
    (instance / "guardrails.yaml").write_text("quiet_hours:\n  enabled: false\n")
    (instance / "self.md").write_text("I am a test maton.\n")
    (instance / "user.md").write_text("Test user.\n")
    skills = instance / "skills"
    skills.mkdir()
    (skills / "dispatch.md").write_text("# Dispatch\n")
    (skills / "ideate.md").write_text("# Ideate\n")
    return instance


def test_load_state_reads_all_files(tmp_path: Path) -> None:
    """load_state returns a dict with all five state keys."""
    instance = _make_instance(tmp_path)
    state = load_state(instance)
    assert set(state.keys()) == {"backlog", "schedule", "guardrails", "identity", "user"}
    assert "test maton" in state["identity"]


def test_load_state_missing_file_returns_empty(tmp_path: Path) -> None:
    """Missing state files produce 'empty' instead of raising."""
    instance = tmp_path / "bare"
    instance.mkdir()
    state = load_state(instance)
    assert state["backlog"] == "empty"
    assert state["identity"] == "empty"


def test_check_cooldown_no_file(tmp_path: Path) -> None:
    """No cooldown file means not in cooldown."""
    assert check_cooldown(tmp_path) is False


def test_check_cooldown_future(tmp_path: Path) -> None:
    """Cooldown with future timestamp is active."""
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    (tmp_path / "cooldown").write_text(future)
    assert check_cooldown(tmp_path) is True


def test_check_cooldown_past(tmp_path: Path) -> None:
    """Cooldown with past timestamp is expired."""
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    (tmp_path / "cooldown").write_text(past)
    assert check_cooldown(tmp_path) is False


def test_check_cooldown_bad_content(tmp_path: Path) -> None:
    """Unparseable cooldown file is treated as no cooldown."""
    (tmp_path / "cooldown").write_text("not-a-date")
    assert check_cooldown(tmp_path) is False


def test_check_quiet_hours_disabled() -> None:
    """Disabled quiet hours returns False."""
    guardrails = yaml.dump({"quiet_hours": {"enabled": False}})
    assert check_quiet_hours(guardrails) is False


def test_check_quiet_hours_inside_window() -> None:
    """Returns True when current time is within quiet hours window."""
    guardrails = yaml.dump(
        {
            "quiet_hours": {
                "enabled": True,
                "start": "00:00",
                "end": "23:59",
                "timezone": "UTC",
            }
        }
    )
    assert check_quiet_hours(guardrails) is True


def test_check_quiet_hours_outside_window() -> None:
    """Returns False when current time is outside quiet hours window."""
    now_hour = datetime.now(UTC).hour
    start = (now_hour + 2) % 24
    end = (now_hour + 3) % 24
    guardrails = yaml.dump(
        {
            "quiet_hours": {
                "enabled": True,
                "start": f"{start:02d}:00",
                "end": f"{end:02d}:00",
                "timezone": "UTC",
            }
        }
    )
    assert check_quiet_hours(guardrails) is False


def test_check_quiet_hours_invalid_yaml() -> None:
    """Invalid YAML is treated as not in quiet hours."""
    assert check_quiet_hours("{{not yaml") is False


def test_has_ready_work_empty_backlog() -> None:
    """Empty backlog and schedule means no ready work."""
    state = {"backlog": "tasks: []\n", "schedule": "recurring: []\n"}
    assert has_ready_work(state) is False


def test_has_ready_work_with_ready_task() -> None:
    """A ready task with no blockers means work is available."""
    backlog = yaml.dump({"tasks": [{"status": "ready", "blocked_by": []}]})
    state = {"backlog": backlog, "schedule": "recurring: []\n"}
    assert has_ready_work(state) is True


def test_has_ready_work_blocked_task() -> None:
    """A ready task with blockers is not actionable."""
    backlog = yaml.dump({"tasks": [{"status": "ready", "blocked_by": ["human"]}]})
    state = {"backlog": backlog, "schedule": "recurring: []\n"}
    assert has_ready_work(state) is False


def test_has_ready_work_done_task() -> None:
    """A done task does not count as ready work."""
    backlog = yaml.dump({"tasks": [{"status": "done", "blocked_by": []}]})
    state = {"backlog": backlog, "schedule": "recurring: []\n"}
    assert has_ready_work(state) is False


def test_has_ready_work_due_recurring() -> None:
    """A recurring task that has never run counts as due."""
    schedule = yaml.dump({"recurring": [{"enabled": True, "frequency": "daily", "last_run": None}]})
    state = {"backlog": "tasks: []\n", "schedule": schedule}
    assert has_ready_work(state) is True


def test_has_ready_work_not_due_recurring() -> None:
    """A recurring task that ran recently is not due."""
    recent = datetime.now(UTC).isoformat()
    schedule = yaml.dump({"recurring": [{"enabled": True, "frequency": "daily", "last_run": recent}]})
    state = {"backlog": "tasks: []\n", "schedule": schedule}
    assert has_ready_work(state) is False


def test_has_ready_work_disabled_recurring() -> None:
    """A disabled recurring task is never due."""
    schedule = yaml.dump({"recurring": [{"enabled": False, "frequency": "daily", "last_run": None}]})
    state = {"backlog": "tasks: []\n", "schedule": schedule}
    assert has_ready_work(state) is False


def test_has_ready_work_every_n_minutes_due() -> None:
    """An every_N_minutes task past its interval is due."""
    old = (datetime.now(UTC) - timedelta(minutes=20)).isoformat()
    schedule = yaml.dump({"recurring": [{"enabled": True, "frequency": "every_10_minutes", "last_run": old}]})
    state = {"backlog": "tasks: []\n", "schedule": schedule}
    assert has_ready_work(state) is True


def test_select_skill_dispatch_when_work(tmp_path: Path) -> None:
    """Selects dispatch skill when backlog has ready tasks."""
    instance = _make_instance(tmp_path)
    backlog = yaml.dump({"tasks": [{"status": "ready", "blocked_by": []}]})
    state = load_state(instance)
    state["backlog"] = backlog
    name, content = select_skill(instance, state)
    assert name == "dispatch"
    assert "Dispatch" in content


def test_select_skill_ideate_when_no_work(tmp_path: Path) -> None:
    """Selects ideate skill when no actionable work exists."""
    instance = _make_instance(tmp_path)
    state = load_state(instance)
    name, content = select_skill(instance, state)
    assert name == "ideate"
    assert "Ideate" in content


def test_assemble_prompt_contains_all_sections() -> None:
    """Assembled prompt includes skill content and all state sections."""
    state = {
        "backlog": "tasks: []",
        "schedule": "recurring: []",
        "guardrails": "limits: {}",
        "identity": "I am maton",
        "user": "My human",
    }
    prompt = assemble_prompt("# Test Skill", state)
    assert "# Test Skill" in prompt
    assert "--- CURRENT STATE ---" in prompt
    assert "=== BACKLOG" in prompt
    assert "tasks: []" in prompt
    assert "=== IDENTITY" in prompt
    assert "I am maton" in prompt
    assert "=== USER" in prompt
    assert "My human" in prompt


@patch("maton.hitch.runner._invoke", return_value=0)
def test_run_skips_on_cooldown(mock_invoke, tmp_path: Path) -> None:
    """run() returns 0 without invoking when cooldown is active."""
    from maton.hitch.runner import run

    instance = _make_instance(tmp_path)
    hitch = tmp_path / "hitch"
    hitch.mkdir()
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    (hitch / "cooldown").write_text(future)

    result = run(instance, hitch, model="test/model")
    assert result == 0
    mock_invoke.assert_not_called()


@patch("maton.hitch.runner._invoke", return_value=0)
def test_run_skips_on_quiet_hours(mock_invoke, tmp_path: Path) -> None:
    """run() returns 0 without invoking during quiet hours."""
    from maton.hitch.runner import run

    instance = _make_instance(tmp_path)
    (instance / "guardrails.yaml").write_text(
        yaml.dump({"quiet_hours": {"enabled": True, "start": "00:00", "end": "23:59", "timezone": "UTC"}})
    )
    hitch = tmp_path / "hitch"
    hitch.mkdir()

    result = run(instance, hitch, model="test/model")
    assert result == 0
    mock_invoke.assert_not_called()


@patch("maton.hitch.runner._invoke", return_value=0)
def test_run_re_arms_trigger_after_dispatch(mock_invoke, tmp_path: Path) -> None:
    """run() re-creates trigger after dispatch to keep the perpetual loop running."""
    from maton.hitch.runner import run

    instance = _make_instance(tmp_path)
    hitch = tmp_path / "hitch"
    hitch.mkdir()
    (hitch / "trigger").touch()

    result = run(instance, hitch, model="test/model")
    assert result == 0
    assert (hitch / "trigger").exists()
    assert not (hitch / "lock").exists()
    mock_invoke.assert_called_once()


@patch("maton.hitch.runner._invoke", return_value=0)
def test_run_releases_lock_on_error(mock_invoke, tmp_path: Path) -> None:
    """Lock is released even if invocation raises."""
    from maton.hitch.runner import run

    instance = _make_instance(tmp_path)
    hitch = tmp_path / "hitch"
    hitch.mkdir()
    mock_invoke.side_effect = RuntimeError("boom")

    with contextlib.suppress(RuntimeError):
        run(instance, hitch, model="test/model")
    assert not (hitch / "lock").exists()
