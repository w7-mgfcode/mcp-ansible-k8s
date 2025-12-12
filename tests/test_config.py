"""Tests for configuration management."""

import pytest

from src.config import Settings


def test_settings_defaults() -> None:
    """Test default settings values."""
    settings = Settings(gemini_api_key="test_key")

    assert settings.llm_provider == "gemini"
    assert settings.docker_validation_timeout == 30
    assert settings.mcp_server_name == "mcp-ansible-k8s"
    assert settings.mcp_server_version == "0.1.0"


def test_settings_custom_values() -> None:
    """Test custom settings values."""
    settings = Settings(
        llm_provider="claude",
        claude_api_key="test_key",
        docker_validation_timeout=60,
        mcp_server_name="custom-server",
    )

    assert settings.llm_provider == "claude"
    assert settings.docker_validation_timeout == 60
    assert settings.mcp_server_name == "custom-server"


def test_invalid_llm_provider() -> None:
    """Test invalid LLM provider raises error."""
    with pytest.raises(ValueError, match="validation error"):
        Settings(llm_provider="invalid")  # type: ignore


def test_validate_gemini_api_key_missing() -> None:
    """Test validation fails when Gemini API key is missing."""
    settings = Settings(llm_provider="gemini", gemini_api_key=None)

    with pytest.raises(ValueError, match="GEMINI_API_KEY not set"):
        settings.validate_api_keys()


def test_validate_claude_api_key_missing() -> None:
    """Test validation fails when Claude API key is missing."""
    settings = Settings(llm_provider="claude", claude_api_key=None)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not set"):
        settings.validate_api_keys()


def test_validate_api_keys_success() -> None:
    """Test validation passes with correct API keys."""
    # Gemini
    settings = Settings(llm_provider="gemini", gemini_api_key="test_key")
    settings.validate_api_keys()  # Should not raise

    # Claude
    settings = Settings(llm_provider="claude", claude_api_key="test_key")
    settings.validate_api_keys()  # Should not raise
