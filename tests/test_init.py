"""Tests for maton init logic."""

import inspect
import re
import shutil
import subprocess
import time
from pathlib import Path

from maton.init import create_maton


def test_create_maton_returns_path_with_timestamp_format(tmp_path: Path) -> None:
    """Return value name matches maton-YYYYMMDD-HHMMSS format."""
    result = create_maton(base_dir=tmp_path)
    assert re.match(r"maton-\d{8}-\d{6}$", result.name)


def test_create_maton_creates_directory(tmp_path: Path) -> None:
    """create_maton creates the instance directory on disk."""
    result = create_maton(base_dir=tmp_path)
    assert result.is_dir()


def test_create_maton_copies_maton_md(tmp_path: Path) -> None:
    """Maton.md is present in the instance."""
    result = create_maton(base_dir=tmp_path)
    assert (result / "Maton.md").is_file()


def test_create_maton_copies_agents_md(tmp_path: Path) -> None:
    """AGENTS.md is present in the instance."""
    result = create_maton(base_dir=tmp_path)
    assert (result / "AGENTS.md").is_file()


def test_create_maton_copies_self_md(tmp_path: Path) -> None:
    """self.md is present in the instance."""
    result = create_maton(base_dir=tmp_path)
    assert (result / "self.md").is_file()


def test_create_maton_copies_user_md(tmp_path: Path) -> None:
    """user.md is present in the instance."""
    result = create_maton(base_dir=tmp_path)
    assert (result / "user.md").is_file()


def test_create_maton_copies_skills(tmp_path: Path) -> None:
    """Skill files are present in the instance."""
    result = create_maton(base_dir=tmp_path)
    assert (result / "skills" / "update.md").is_file()
    assert (result / "skills" / "dispatch.md").is_file()
    assert (result / "skills" / "ideate.md").is_file()


def test_create_maton_copies_state_files(tmp_path: Path) -> None:
    """State files (guardrails, schedule, backlog) are present in the instance."""
    result = create_maton(base_dir=tmp_path)
    assert (result / "guardrails.yaml").is_file()
    assert (result / "schedule.yaml").is_file()
    assert (result / "backlog.yaml").is_file()


def test_create_maton_excludes_python_package_files(tmp_path: Path) -> None:
    """Package code (init.py, cli.py, ask.py) is NOT copied to instances."""
    result = create_maton(base_dir=tmp_path)
    assert not (result / "init.py").exists()
    assert not (result / "cli.py").exists()
    assert not (result / "ask.py").exists()
    assert not (result / "__init__.py").exists()


def test_create_maton_creates_gitignore(tmp_path: Path) -> None:
    """.gitignore is present and contains logs/ and __pycache__/."""
    result = create_maton(base_dir=tmp_path)
    gitignore = result / ".gitignore"
    assert gitignore.is_file()
    content = gitignore.read_text()
    assert "logs/" in content
    assert "__pycache__/" in content


def test_create_maton_creates_journal_dir(tmp_path: Path) -> None:
    """journal/ directory exists and contains .gitkeep."""
    result = create_maton(base_dir=tmp_path)
    assert (result / "journal").is_dir()
    assert (result / "journal" / ".gitkeep").is_file()


def test_create_maton_creates_logs_dir(tmp_path: Path) -> None:
    """logs/ directory exists in the instance."""
    result = create_maton(base_dir=tmp_path)
    assert (result / "logs").is_dir()


def test_create_maton_initializes_git_repo(tmp_path: Path) -> None:
    """.git/ exists, there is exactly 1 commit, and the commit message is 'born'."""
    result = create_maton(base_dir=tmp_path)
    assert (result / ".git").is_dir()
    git = shutil.which("git") or "git"
    log = subprocess.run(  # noqa: S603
        [git, "log", "--oneline"],
        capture_output=True,
        text=True,
        cwd=result,
    )
    lines = log.stdout.strip().splitlines()
    assert len(lines) == 1
    assert "born" in lines[0]


def test_create_maton_logs_not_tracked(tmp_path: Path) -> None:
    """logs/ directory is not tracked by git."""
    result = create_maton(base_dir=tmp_path)
    git = shutil.which("git") or "git"
    tracked = subprocess.run(  # noqa: S603
        [git, "ls-files"],
        capture_output=True,
        text=True,
        cwd=result,
    )
    assert "logs/" not in tracked.stdout


def test_create_maton_excludes_pycache(tmp_path: Path) -> None:
    """No __pycache__ directory is present in the instance."""
    result = create_maton(base_dir=tmp_path)
    pycache_dirs = list(result.rglob("__pycache__"))
    assert pycache_dirs == []


def test_create_maton_creates_parent_dirs(tmp_path: Path) -> None:
    """create_maton works when base_dir is a nested path that doesn't exist yet."""
    nested_base = tmp_path / "deep" / "nested" / "path"
    result = create_maton(base_dir=nested_base)
    assert result.is_dir()


def test_create_maton_two_calls_distinct(tmp_path: Path) -> None:
    """Two calls produce two different directories with different names."""
    first = create_maton(base_dir=tmp_path)
    time.sleep(1)
    second = create_maton(base_dir=tmp_path)
    assert first != second
    assert first.is_dir()
    assert second.is_dir()


def test_create_maton_no_name_parameter(tmp_path: Path) -> None:
    """create_maton signature has no 'name' parameter."""
    sig = inspect.signature(create_maton)
    assert "name" not in sig.parameters
