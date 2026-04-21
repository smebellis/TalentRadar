from unittest.mock import MagicMock, patch

import pytest

from llm.claude import ClaudeClient
from llm.protocol import LLMClient


def test_llm_client_is_a_protocol():
    from typing import Protocol, runtime_checkable

    assert issubclass(LLMClient, Protocol)


def test_claude_client_implements_llm_client_protocol():
    with patch("llm.claude.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = MagicMock()
        client = ClaudeClient(api_key="test-key")
        assert isinstance(client, LLMClient)


def test_claude_client_complete_calls_sdk_messages_create():
    with patch("llm.claude.anthropic") as mock_anthropic:
        mock_messages = MagicMock()
        mock_messages.create.return_value.content = [MagicMock(text="response text")]
        mock_anthropic.Anthropic.return_value.messages = mock_messages

        client = ClaudeClient(api_key="test-key")
        result = client.complete(system="You are helpful.", user="Hello")

        mock_messages.create.assert_called_once()
        assert result == "response text"


def test_claude_client_passes_system_and_user_to_sdk():
    with patch("llm.claude.anthropic") as mock_anthropic:
        mock_messages = MagicMock()
        mock_messages.create.return_value.content = [MagicMock(text="ok")]
        mock_anthropic.Anthropic.return_value.messages = mock_messages

        client = ClaudeClient(api_key="key")
        client.complete(system="sys prompt", user="user msg")

        call_kwargs = mock_messages.create.call_args.kwargs
        assert call_kwargs["system"] == "sys prompt"
        assert call_kwargs["messages"][0]["content"] == "user msg"
