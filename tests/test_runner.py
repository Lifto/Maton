"""Tests for maton hitch runner."""

import contextlib
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import yaml

from maton.hitch.runner import (
    _count_ready,
    _find_due_schedule,
    _find_ready_task,
    _needs_maintenance,
    assemble_prompt,
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
    (instance / "guardrails.yaml").write_text("limits: {}\n")
    (instance / "self.md").write_text("I am a test maton.\n")
    (instance / "user.md").write_text("Test user.\n")
    skills = instance / "skills"
    skills.mkdir()
    (skills / "dispatch-task.md").write_text("# Dispatch Task\n")
    (skills / "dispatch-schedule.md").write_text("# Dispatch Schedule\n")
    (skills / "dispatch-maintenance.md").write_text("# Dispatch Maintenance\n")
    (skills / "ideate.md").write_text("# Ideate\n")
    # Create .git dir so _needs_maintenance works
    (instance / ".git").mkdir()
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


def test_select_skill_routes_to_dispatch_task_when_backlog_ready(tmp_path: Path) -> None:
    """Selects dispatch-task skill when backlog has ready tasks."""
    instance = _make_instance(tmp_path)
    task = {"status": "ready", "blocked_by": [], "priority": "normal", "created": "2026-01-01"}
    backlog = yaml.dump({"tasks": [task]})
    state = load_state(instance)
    state["backlog"] = backlog
    name, content, ctx = select_skill(instance, state)
    assert name == "dispatch-task"
    assert "Dispatch Task" in content
    assert ctx.get("status") == "ready"


def test_select_skill_routes_to_ideate_when_no_work(tmp_path: Path) -> None:
    """Selects ideate skill when no actionable work exists."""
    instance = _make_instance(tmp_path)
    state = load_state(instance)
    name, content, ctx = select_skill(instance, state)
    assert name == "ideate"
    assert "Ideate" in content
    assert ctx == {}


def test_assemble_prompt_dispatch_task_filters_state() -> None:
    """dispatch-task prompt includes guardrails and user, not backlog or schedule."""
    state = {
        "backlog": "tasks: []",
        "schedule": "recurring: []",
        "guardrails": "limits: {}",
        "identity": "I am maton",
        "user": "My human",
    }
    task_ctx = {"id": "task-001", "summary": "Do something"}
    prompt = assemble_prompt("dispatch-task", "# Dispatch Task\n", state, task_ctx)
    assert "# Dispatch Task" in prompt
    assert "--- CURRENT STATE ---" in prompt
    assert "=== TASK ===" in prompt
    assert "task-001" in prompt
    assert "=== GUARDRAILS" in prompt
    assert "=== USER" in prompt
    # Must NOT include backlog or schedule
    assert "=== BACKLOG" not in prompt
    assert "=== SCHEDULE" not in prompt


def test_assemble_prompt_ideate_filters_state() -> None:
    """ideate prompt includes backlog, user, identity — not guardrails or schedule."""
    state = {
        "backlog": "tasks: []",
        "schedule": "recurring: []",
        "guardrails": "limits: {}",
        "identity": "I am maton",
        "user": "My human",
    }
    prompt = assemble_prompt("ideate", "# Ideate\n", state)
    assert "=== BACKLOG" in prompt
    assert "=== USER" in prompt
    assert "=== IDENTITY" in prompt
    assert "=== GUARDRAILS" not in prompt
    assert "=== SCHEDULE" not in prompt


def test_find_due_schedule_returns_first_due(tmp_path: Path) -> None:
    """_find_due_schedule returns the first due recurring item."""
    schedule = yaml.dump({"recurring": [{"id": "s1", "enabled": True, "frequency": "daily", "last_run": None}]})
    state = {"schedule": schedule}
    result = _find_due_schedule(state)
    assert result is not None
    assert result["id"] == "s1"


def test_find_due_schedule_returns_none_when_not_due(tmp_path: Path) -> None:
    """_find_due_schedule returns None when no items are due."""
    recent = datetime.now(UTC).isoformat()
    schedule = yaml.dump({"recurring": [{"enabled": True, "frequency": "daily", "last_run": recent}]})
    state = {"schedule": schedule}
    assert _find_due_schedule(state) is None


def test_find_ready_task_returns_highest_priority(tmp_path: Path) -> None:
    """_find_ready_task returns the highest-priority unblocked task."""
    backlog = yaml.dump(
        {
            "tasks": [
                {"id": "t1", "status": "ready", "priority": "low", "created": "2026-01-01", "blocked_by": []},
                {"id": "t2", "status": "ready", "priority": "high", "created": "2026-01-01", "blocked_by": []},
            ]
        }
    )
    state = {"backlog": backlog}
    result = _find_ready_task(state)
    assert result is not None
    assert result["id"] == "t2"


def test_find_ready_task_skips_blocked(tmp_path: Path) -> None:
    """_find_ready_task skips tasks with blockers."""
    backlog = yaml.dump(
        {
            "tasks": [
                {"id": "t1", "status": "ready", "priority": "high", "created": "2026-01-01", "blocked_by": ["human"]},
            ]
        }
    )
    state = {"backlog": backlog}
    assert _find_ready_task(state) is None


def test_needs_maintenance_detects_index_lock(tmp_path: Path) -> None:
    """_needs_maintenance returns True when .git/index.lock exists."""
    instance = tmp_path / "instance"
    instance.mkdir()
    git_dir = instance / ".git"
    git_dir.mkdir()
    (git_dir / "index.lock").write_text("")
    assert _needs_maintenance(instance) is True


def test_needs_maintenance_false_when_clean(tmp_path: Path) -> None:
    """_needs_maintenance returns False for a clean instance."""
    instance = tmp_path / "instance"
    instance.mkdir()
    (instance / ".git").mkdir()
    assert _needs_maintenance(instance) is False


def test_select_skill_routes_to_schedule_first(tmp_path: Path) -> None:
    """Schedule takes priority over backlog tasks."""
    instance = _make_instance(tmp_path)
    task = {"status": "ready", "blocked_by": [], "priority": "normal", "created": "2026-01-01"}
    backlog = yaml.dump({"tasks": [task]})
    schedule = yaml.dump({"recurring": [{"id": "s1", "enabled": True, "frequency": "daily", "last_run": None}]})
    state = load_state(instance)
    state["backlog"] = backlog
    state["schedule"] = schedule
    name, _, ctx = select_skill(instance, state)
    assert name == "dispatch-schedule"
    assert ctx["id"] == "s1"


def test_select_skill_routes_to_maintenance(tmp_path: Path) -> None:
    """Routes to maintenance when index.lock exists and no other work."""
    instance = _make_instance(tmp_path)
    (instance / ".git" / "index.lock").write_text("")
    state = load_state(instance)
    name, _, ctx = select_skill(instance, state)
    assert name == "dispatch-maintenance"
    assert ctx == {}


def test_count_ready_empty() -> None:
    """Empty backlog and schedule yields (0, 0)."""
    state = {"backlog": "tasks: []\n", "schedule": "recurring: []\n"}
    assert _count_ready(state) == (0, 0)


def test_count_ready_with_tasks_and_schedules() -> None:
    """Counts ready tasks and due schedules independently."""
    backlog = yaml.dump({"tasks": [{"status": "ready"}, {"status": "done"}, {"status": "ready", "blocked_by": ["x"]}]})
    schedule = yaml.dump({"recurring": [{"enabled": True, "frequency": "daily", "last_run": None}]})
    state = {"backlog": backlog, "schedule": schedule}
    ready, due = _count_ready(state)
    assert ready == 1
    assert due == 1


@patch("maton.hitch.runner._invoke", return_value=0)
def test_run_logs_state_summary(mock_invoke, tmp_path: Path, caplog) -> None:
    """run() logs ready task and due schedule counts before dispatch."""
    from maton.hitch.runner import run

    instance = _make_instance(tmp_path)
    backlog = yaml.dump({"tasks": [{"status": "ready"}]})
    (instance / "backlog.yaml").write_text(backlog)
    hitch = tmp_path / "hitch"
    hitch.mkdir()

    with caplog.at_level(logging.INFO):
        run(instance, hitch, model="test/model")
    assert any("STATE: 1 ready task(s)" in m for m in caplog.messages)


@patch("maton.hitch.runner._invoke", return_value=0)
def test_run_logs_duration(mock_invoke, tmp_path: Path, caplog) -> None:
    """run() logs wall-clock duration in the END message."""
    from maton.hitch.runner import run

    instance = _make_instance(tmp_path)
    hitch = tmp_path / "hitch"
    hitch.mkdir()

    with caplog.at_level(logging.INFO):
        run(instance, hitch, model="test/model")
    end_msgs = [m for m in caplog.messages if m.startswith("END:")]
    assert len(end_msgs) == 1
    assert "exit 0" in end_msgs[0]
    assert "s)" in end_msgs[0]


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
