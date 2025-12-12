"""Tests for core playbook generation engine."""

from unittest.mock import Mock, patch

from src.engine import (
    generate_playbook,
    generate_readme,
    validate_playbook_yaml,
)
from src.llm_engine import GenerationResponse
from src.validator import ValidationResult


def test_generate_playbook_success() -> None:
    """Test successful playbook generation."""
    with (
        patch("src.engine.create_llm_engine") as mock_llm_factory,
        patch("src.engine.PlaybookValidator") as mock_validator_class,
        patch("src.engine.load_system_prompt") as mock_prompt,
    ):
        # Setup mocks
        mock_prompt.return_value = "System prompt"

        mock_engine = Mock()
        mock_response = GenerationResponse(
            content="---\nvalid playbook", model="gemini-2.0-flash-001", usage_tokens=500
        )
        mock_engine.generate.return_value = mock_response
        mock_llm_factory.return_value = mock_engine

        mock_validator = Mock()
        mock_validation = ValidationResult(
            is_valid=True, lint_output="passed", syntax_check_output="OK", errors=[], warnings=[]
        )
        mock_validator.validate.return_value = mock_validation
        mock_validator_class.return_value = mock_validator

        # Test
        result = generate_playbook(
            description="Deploy Redis",
            llm_provider="gemini",
            api_key="test_key",
        )

        assert result.success
        assert "valid playbook" in result.playbook_yaml
        assert result.model_used == "gemini-2.0-flash-001"
        assert result.tokens_used == 500


def test_generate_playbook_with_claude() -> None:
    """Test playbook generation with Claude provider and API key wiring."""
    with (
        patch("src.engine.create_llm_engine") as mock_llm_factory,
        patch("src.engine.PlaybookValidator") as mock_validator_class,
        patch("src.engine.load_system_prompt") as mock_prompt,
    ):
        mock_prompt.return_value = "System prompt"

        mock_engine = Mock()
        mock_response = GenerationResponse(
            content="---\nvalid playbook", model="claude-sonnet-4-5", usage_tokens=600
        )
        mock_engine.generate.return_value = mock_response
        mock_llm_factory.return_value = mock_engine

        mock_validator = Mock()
        mock_validation = ValidationResult(
            is_valid=True, lint_output="OK", syntax_check_output="OK", errors=[], warnings=[]
        )
        mock_validator.validate.return_value = mock_validation
        mock_validator_class.return_value = mock_validator

        result = generate_playbook(
            description="Deploy Nginx", llm_provider="claude", api_key="claude_test_key"
        )

        assert result.success
        assert "valid playbook" in result.playbook_yaml

        # Verify Settings was configured for Claude (not Gemini)
        call_args = mock_llm_factory.call_args
        settings_arg = call_args[0][0]
        assert settings_arg.llm_provider == "claude"
        assert settings_arg.claude_api_key == "claude_test_key"
        assert settings_arg.gemini_api_key is None


def test_generate_playbook_retry_on_failure() -> None:
    """Test playbook generation retries on validation failure."""
    with (
        patch("src.engine.create_llm_engine") as mock_llm_factory,
        patch("src.engine.PlaybookValidator") as mock_validator_class,
        patch("src.engine.load_system_prompt") as mock_prompt,
    ):
        mock_prompt.return_value = "System prompt"

        # First attempt fails, second succeeds
        mock_engine = Mock()
        mock_response1 = GenerationResponse(
            content="---\ninvalid", model="gemini", usage_tokens=100
        )
        mock_response2 = GenerationResponse(content="---\nvalid", model="gemini", usage_tokens=150)
        mock_engine.generate.side_effect = [mock_response1, mock_response2]
        mock_llm_factory.return_value = mock_engine

        mock_validator = Mock()
        mock_validation_fail = ValidationResult(
            is_valid=False, lint_output="", syntax_check_output="", errors=["Error 1"], warnings=[]
        )
        mock_validation_success = ValidationResult(
            is_valid=True, lint_output="OK", syntax_check_output="OK", errors=[], warnings=[]
        )
        mock_validator.validate.side_effect = [mock_validation_fail, mock_validation_success]
        mock_validator_class.return_value = mock_validator

        result = generate_playbook(
            description="Deploy Redis", llm_provider="gemini", api_key="test_key"
        )

        assert result.success
        assert "valid" in result.playbook_yaml
        assert mock_engine.generate.call_count == 2

        # Verify second retry includes validation error feedback
        # The engine calls: llm_engine.generate(request) where request is GenerationRequest
        second_call = mock_engine.generate.call_args_list[1]
        # Extract the GenerationRequest argument
        generation_request = second_call[0][0] if second_call[0] else second_call.kwargs.get("request")

        # Verify the retry prompt includes validation error feedback
        assert "Error 1" in generation_request.user_prompt
        assert "Previous attempt had validation errors" in generation_request.user_prompt
        assert "kubernetes.core.k8s" in generation_request.user_prompt  # Guidance text


def test_generate_playbook_max_retries_exceeded() -> None:
    """Test playbook generation fails after max retries."""
    with (
        patch("src.engine.create_llm_engine") as mock_llm_factory,
        patch("src.engine.PlaybookValidator") as mock_validator_class,
        patch("src.engine.load_system_prompt") as mock_prompt,
    ):
        mock_prompt.return_value = "System prompt"

        mock_engine = Mock()
        mock_response = GenerationResponse(content="---\ninvalid", model="gemini", usage_tokens=100)
        mock_engine.generate.return_value = mock_response
        mock_llm_factory.return_value = mock_engine

        mock_validator = Mock()
        mock_validation = ValidationResult(
            is_valid=False, lint_output="", syntax_check_output="", errors=["Error"], warnings=[]
        )
        mock_validator.validate.return_value = mock_validation
        mock_validator_class.return_value = mock_validator

        result = generate_playbook(
            description="Deploy Redis", llm_provider="gemini", api_key="test_key", max_retries=2
        )

        assert not result.success
        assert result.error_message is not None
        assert "Failed to generate valid playbook" in result.error_message
        assert mock_engine.generate.call_count == 2


def test_generate_playbook_exception_handling() -> None:
    """Test playbook generation handles exceptions gracefully."""
    with patch("src.engine.create_llm_engine") as mock_llm_factory:
        mock_llm_factory.side_effect = Exception("API Error")

        result = generate_playbook(
            description="Deploy Redis", llm_provider="gemini", api_key="test_key"
        )

        assert not result.success
        assert result.error_message is not None
        assert "Generation error" in result.error_message


def test_validate_playbook_yaml() -> None:
    """Test YAML validation function with timeout propagation."""
    with patch("src.engine.PlaybookValidator") as mock_validator_class:
        mock_validator = Mock()
        mock_result = ValidationResult(
            is_valid=True, lint_output="OK", syntax_check_output="OK", errors=[], warnings=[]
        )
        mock_validator.validate.return_value = mock_result
        mock_validator_class.return_value = mock_validator

        result = validate_playbook_yaml("---\ntest: yaml", validation_timeout=45)

        assert result.is_valid
        mock_validator.validate.assert_called_once_with("---\ntest: yaml")
        # Verify timeout is propagated to PlaybookValidator constructor
        mock_validator_class.assert_called_once_with(timeout=45)


def test_generate_readme() -> None:
    """Test README generation from playbook."""
    with (
        patch("src.engine.create_llm_engine") as mock_llm_factory,
    ):
        mock_engine = Mock()
        mock_response = GenerationResponse(
            content="# README\nGenerated documentation", model="gemini", usage_tokens=200
        )
        mock_engine.generate.return_value = mock_response
        mock_llm_factory.return_value = mock_engine

        readme = generate_readme(
            playbook_yaml="---\ntest: playbook",
            llm_provider="gemini",
            api_key="test_key",
        )

        assert "README" in readme
        assert "Generated documentation" in readme


def test_generate_readme_error_handling() -> None:
    """Test README generation handles errors."""
    with patch("src.engine.create_llm_engine") as mock_llm_factory:
        mock_llm_factory.side_effect = Exception("API Error")

        readme = generate_readme(
            playbook_yaml="---\ntest: playbook",
            llm_provider="gemini",
            api_key="test_key",
        )

        assert "README Generation Failed" in readme
        assert "API Error" in readme
