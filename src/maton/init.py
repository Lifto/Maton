"""Maton init logic — bootstrap a new maton instance as a git repository."""

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

DEFAULT_BASE_DIR = Path.home() / ".maton" / "matons"

_DEFAULT_HITCH_CONFIG = {
    "model": "",
    "timeout": 300,
}


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

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    instance_name = f"maton-{timestamp}"
    instance_path = base_dir / instance_name

    seed_path = Path(__file__).parent / "seed"
    shutil.copytree(seed_path, instance_path)

    journal_dir = instance_path / "journal"
    journal_dir.mkdir(exist_ok=True)
    (journal_dir / ".gitkeep").touch()

    (instance_path / "logs").mkdir(exist_ok=True)

    hitch_dir = instance_path / "hitch"
    hitch_dir.mkdir(exist_ok=True)
    (hitch_dir / "config.yaml").write_text(yaml.dump(_DEFAULT_HITCH_CONFIG, default_flow_style=False))

    (instance_path / ".gitignore").write_text("logs/\nhitch/\n__pycache__/\nrepos/\n")

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
