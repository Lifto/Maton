"""Maton init logic — bootstrap a new maton instance as a git repository."""

import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_BASE_DIR = Path.home() / ".maton" / "matons"


def create_maton(name: str, base_dir: Path | None = None) -> Path:
    """Create a new maton instance at base_dir/name.

    Args:
        name: The government name of the maton (used as directory name and in Maton.md).
        base_dir: Base directory for maton instances. Defaults to ~/.maton/matons.
            Override in tests to use a temporary directory.

    Returns:
        Path to the newly created maton directory.
    """
    if base_dir is None:
        base_dir = DEFAULT_BASE_DIR

    maton_path = base_dir / name
    maton_path.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(tz=UTC).isoformat()
    maton_md = maton_path / "Maton.md"
    maton_md.write_text(
        f"""\
# {name}

## What I Am
I am a maton — an autonomous unit whose state is this git repository.
Every change to my state is a commit. My history is my git log.

## Name
{name}

## Created
{created_at}

## State
This directory is my state. What is committed is what I know and what I am.
Working changes are in progress. Committed changes are truth.

## Tasks
None yet. Tasks live in subdirectories. A task is created when I am
given work to do, and completed when its result is committed.

## How to Interact With Me
Read this file. If you are an LLM operating me, check for pending tasks
and act on them. If there are none, wait for instructions.
"""
    )

    git = shutil.which("git") or "git"
    subprocess.run([git, "init"], cwd=maton_path, check=True, capture_output=True)  # noqa: S603
    subprocess.run([git, "add", "Maton.md"], cwd=maton_path, check=True, capture_output=True)  # noqa: S603
    subprocess.run([git, "commit", "-m", "born"], cwd=maton_path, check=True, capture_output=True)  # noqa: S603

    return maton_path
