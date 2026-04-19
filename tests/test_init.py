"""Tests for maton init logic."""

import subprocess
from pathlib import Path

from maton.init import create_maton


def test_create_maton_returns_correct_path(tmp_path: Path) -> None:
    """create_maton returns the path to the new maton directory."""
    result = create_maton("TestMaton", base_dir=tmp_path)
    assert result == tmp_path / "TestMaton"


def test_create_maton_creates_directory(tmp_path: Path) -> None:
    """create_maton creates the maton directory on disk."""
    create_maton("TestMaton", base_dir=tmp_path)
    assert (tmp_path / "TestMaton").is_dir()


def test_create_maton_writes_maton_md(tmp_path: Path) -> None:
    """create_maton creates a Maton.md file in the maton directory."""
    create_maton("TestMaton", base_dir=tmp_path)
    assert (tmp_path / "TestMaton" / "Maton.md").is_file()


def test_create_maton_md_contains_name(tmp_path: Path) -> None:
    """Maton.md contains the maton name as an H1 heading."""
    create_maton("MyAgent", base_dir=tmp_path)
    content = (tmp_path / "MyAgent" / "Maton.md").read_text()
    assert "# MyAgent" in content


def test_create_maton_md_contains_created_timestamp(tmp_path: Path) -> None:
    """Maton.md contains a Created: line with an ISO 8601 timestamp."""
    create_maton("MyAgent", base_dir=tmp_path)
    content = (tmp_path / "MyAgent" / "Maton.md").read_text()
    assert "**Created**:" in content


def test_create_maton_initializes_git_repo(tmp_path: Path) -> None:
    """create_maton initializes a git repository with one commit."""
    create_maton("TestMaton", base_dir=tmp_path)
    result = subprocess.run(  # noqa: S603
        ["git", "log", "--oneline"],  # noqa: S607
        cwd=tmp_path / "TestMaton",
        capture_output=True,
        text=True,
        check=True,
    )
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert "born" in lines[0]


def test_create_maton_creates_parent_dirs(tmp_path: Path) -> None:
    """create_maton creates parent directories if they don't exist."""
    nested_base = tmp_path / "deep" / "nested" / "path"
    create_maton("TestMaton", base_dir=nested_base)
    assert (nested_base / "TestMaton").is_dir()
