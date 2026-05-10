"""Maton CLI — command-line interface for the Maton agent system."""

from pathlib import Path

import typer

from maton.init import create_maton

app = typer.Typer(help="Maton — self-improving personal agent with git-native memory.")
hitch_app = typer.Typer(help="Manage platform scheduling for a maton instance.")
app.add_typer(hitch_app, name="hitch")


@app.callback()
def main() -> None:
    """Maton — self-improving personal agent with git-native memory."""


@app.command()
def init() -> None:
    """Create a new maton instance as a git repository."""
    maton_path = create_maton()
    typer.echo(f"Created maton at {maton_path}")


@app.command()
def ask(name: str, question: str) -> None:
    """Ask a maton a question."""
    from maton.ask import ask_maton

    response = ask_maton(name, question)
    print(response)


def _resolve_dirs(instance_dir: str) -> tuple[Path, Path]:
    instance = Path(instance_dir).expanduser().resolve()
    if not instance.is_dir():
        typer.echo(f"Instance directory not found: {instance}", err=True)
        raise typer.Exit(1)
    hitch = instance / "hitch"
    if not hitch.is_dir():
        typer.echo(f"No hitch/ directory in {instance}", err=True)
        raise typer.Exit(1)
    return instance, hitch


@hitch_app.command("install")
def hitch_install(instance_dir: str = typer.Argument(help="Path to the maton instance")) -> None:
    """Install platform scheduling (launchd on macOS, systemd on Linux)."""
    from maton.hitch.platform import install

    instance, hitch = _resolve_dirs(instance_dir)
    try:
        result = install(instance, hitch)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None
    typer.echo(f"Installed: {result}")


@hitch_app.command("uninstall")
def hitch_uninstall(instance_dir: str = typer.Argument(help="Path to the maton instance")) -> None:
    """Remove platform scheduling for a maton instance."""
    from maton.hitch.platform import uninstall

    instance, hitch = _resolve_dirs(instance_dir)
    if uninstall(instance, hitch):
        typer.echo("Uninstalled.")
    else:
        typer.echo("Nothing to uninstall.")
