"""Ask a maton a question — reads its state and queries the LLM."""

from pathlib import Path

from openai import OpenAI

DEFAULT_BASE_DIR = Path.home() / ".maton" / "matons"
DEFAULT_ENDPOINT = "http://localhost:8080/v1"
DEFAULT_MODEL = "gemma-4-31b-it-UD-MLX-4bit"


def ask_maton(name: str, question: str, base_dir: Path | None = None) -> str:
    """Read a maton's state and ask it a question via the LLM.

    Args:
        name: The maton's name (directory under base_dir).
        question: The question to ask.
        base_dir: Override base directory. Defaults to ~/.maton/matons.

    Returns:
        The maton's response as a string.
    """
    if base_dir is None:
        base_dir = DEFAULT_BASE_DIR

    maton_path = base_dir / name
    maton_md = maton_path / "Maton.md"

    if not maton_md.exists():
        msg = f"No maton found at {maton_path}"
        raise FileNotFoundError(msg)

    state = maton_md.read_text()

    client = OpenAI(
        base_url=DEFAULT_ENDPOINT,
        api_key="not-needed",
    )

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": state},
            {"role": "user", "content": question},
        ],
    )

    return response.choices[0].message.content or ""
