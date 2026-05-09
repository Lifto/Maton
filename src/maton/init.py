"""Maton init logic — bootstrap a new maton instance as a git repository."""

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

DEFAULT_BASE_DIR = Path.home() / ".maton" / "matons"


def create_maton(base_dir: Path | None = None) -> Path:
    """Create a new maton instance by copying the package seed.

    Args:
        base_dir: Base directory for maton instances. Defaults to ~/.maton/matons.
            Override in tests to use a temporary directory.

    Returns:
        Path to the newly created maton directory.
    """
    if base_dir is None:
        base_dir = DEFAULT_BASE_DIR

    base_dir.mkdir(parents=True, exist_ok=True)

    # Timestamp-based directory name
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    instance_name = f"maton-{timestamp}"
    instance_path = base_dir / instance_name

    # Copy entire package directory (this file's parent) to instance
    seed_path = Path(__file__).parent
    shutil.copytree(seed_path, instance_path, ignore=shutil.ignore_patterns("__pycache__"))

    # Create journal/ with .gitkeep (so git tracks the directory)
    journal_dir = instance_path / "journal"
    journal_dir.mkdir(exist_ok=True)
    (journal_dir / ".gitkeep").touch()

    # Create logs/ directory (git-ignored)
    (instance_path / "logs").mkdir(exist_ok=True)

    # Write .gitignore
    (instance_path / ".gitignore").write_text("logs/\n__pycache__/\nrepos/\n")

    # Initialize git repo
    git = shutil.which("git") or "git"
    subprocess.run([git, "init"], cwd=str(instance_path), check=True, capture_output=True)  # noqa: S603
    subprocess.run([git, "add", "."], cwd=str(instance_path), check=True, capture_output=True)  # noqa: S603
    subprocess.run(  # noqa: S603
        [git, "commit", "-m", "born"],
        cwd=str(instance_path),
        check=True,
        capture_output=True,
    )

    return instance_path
