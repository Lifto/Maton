"""Tests for maton ask."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from maton.ask import ask_maton


def test_ask_reads_maton_md_and_queries_llm(tmp_path: Path) -> None:
    """Test that ask reads Maton.md and sends it as system context."""
    maton_dir = tmp_path / "testmaton"
    maton_dir.mkdir()
    (maton_dir / "Maton.md").write_text("# testmaton\n\n## Name\ntestmaton\n")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "I am testmaton."

    with patch("maton.ask.OpenAI") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_response

        result = ask_maton("testmaton", "what is your name?", base_dir=tmp_path)

    assert result == "I am testmaton."

    # Verify maton.md was sent as system message
    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert "testmaton" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "what is your name?"


def test_ask_raises_when_maton_not_found(tmp_path: Path) -> None:
    """Test that ask raises FileNotFoundError for missing maton."""
    with pytest.raises(FileNotFoundError, match="No maton found"):
        ask_maton("nonexistent", "hello?", base_dir=tmp_path)
