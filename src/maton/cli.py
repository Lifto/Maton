"""Maton CLI — command-line interface for the Maton agent system."""

import typer

from maton.init import create_maton

app = typer.Typer(help="Maton — self-improving personal agent with git-native memory.")


@app.callback()
def main() -> None:
    """Maton — self-improving personal agent with git-native memory."""


@app.command()
def init(name: str = typer.Argument(..., help="Name of the new maton instance.")) -> None:
    """Create a new maton instance as a git repository."""
    maton_path = create_maton(name)
    typer.echo(f"Created maton '{name}' at {maton_path}")


@app.command()
def ask(name: str, question: str) -> None:
    """Ask a maton a question."""
    from maton.ask import ask_maton

    response = ask_maton(name, question)
    print(response)
