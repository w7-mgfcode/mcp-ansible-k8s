"""Tests for LLM engine abstraction."""

from unittest.mock import Mock, patch

import pytest

from src.config import Settings
from src.llm_engine import (
    ClaudeEngine,
    GeminiEngine,
    GenerationRequest,
    create_llm_engine,
)


def test_generation_request_defaults() -> None:
    """Test GenerationRequest default values."""
    request = GenerationRequest(
        user_prompt="Test prompt",
        system_prompt="System instructions",
    )

    assert request.max_tokens == 4096
    assert request.temperature == 0.7


def test_gemini_engine_generation() -> None:
    """Test Gemini engine generates content."""
    with patch("src.llm_engine.genai.Client") as mock_client_class:
        # Setup mock response
        mock_response = Mock()
        mock_response.text = "---\n- name: Test playbook\n  hosts: localhost"
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.total_token_count = 100

        # Setup mock client
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Test generation
        engine = GeminiEngine("fake_api_key")
        request = GenerationRequest(
            user_prompt="Deploy Redis",
            system_prompt="You are an expert",
            max_tokens=1000,
        )

        response = engine.generate(request)

        assert "Test playbook" in response.content
        assert response.model == "gemini-2.0-flash-001"
        assert response.usage_tokens == 100


def test_claude_engine_generation() -> None:
    """Test Claude engine generates content."""
    with patch("src.llm_engine.Anthropic") as mock_anthropic_class:
        # Setup mock response
        mock_content = Mock()
        mock_content.text = "---\n- name: Test playbook\n  hosts: localhost"

        mock_usage = Mock()
        mock_usage.input_tokens = 50
        mock_usage.output_tokens = 150

        mock_message = Mock()
        mock_message.content = [mock_content]
        mock_message.usage = mock_usage

        # Setup mock client
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic_class.return_value = mock_client

        # Test generation
        engine = ClaudeEngine("fake_api_key")
        request = GenerationRequest(
            user_prompt="Deploy Nginx",
            system_prompt="You are an expert",
            max_tokens=2000,
        )

        response = engine.generate(request)

        assert "Test playbook" in response.content
        assert response.model == "claude-sonnet-4-5-20250929"
        assert response.usage_tokens == 200  # 50 + 150


def test_create_llm_engine_gemini() -> None:
    """Test factory creates Gemini engine."""
    settings = Settings(llm_provider="gemini", gemini_api_key="test_key")

    with patch("src.llm_engine.GeminiEngine") as mock_gemini:
        create_llm_engine(settings)
        mock_gemini.assert_called_once_with("test_key")


def test_create_llm_engine_claude() -> None:
    """Test factory creates Claude engine."""
    settings = Settings(llm_provider="claude", claude_api_key="test_key")

    with patch("src.llm_engine.ClaudeEngine") as mock_claude:
        create_llm_engine(settings)
        mock_claude.assert_called_once_with("test_key")


def test_create_llm_engine_missing_gemini_key() -> None:
    """Test factory raises error when Gemini API key missing."""
    settings = Settings(llm_provider="gemini", gemini_api_key=None)

    with pytest.raises(ValueError, match="GEMINI_API_KEY not set"):
        create_llm_engine(settings)


def test_create_llm_engine_missing_claude_key() -> None:
    """Test factory raises error when Claude API key missing."""
    settings = Settings(llm_provider="claude", claude_api_key=None)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not set"):
        create_llm_engine(settings)


def test_create_llm_engine_invalid_provider() -> None:
    """Test factory raises error for unknown provider."""
    settings = Settings(llm_provider="gemini", gemini_api_key="test")
    settings.llm_provider = "unknown"  # type: ignore

    with pytest.raises(ValueError, match="Unknown LLM provider"):
        create_llm_engine(settings)
