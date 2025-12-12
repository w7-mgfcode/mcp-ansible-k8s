"""Core playbook generation engine - shared between MCP server and web app."""

import logging
from typing import Literal

from pydantic import BaseModel

from src.config import Settings
from src.llm_engine import GenerationRequest, create_llm_engine
from src.prompts import load_system_prompt
from src.validator import PlaybookValidator, ValidationResult

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PlaybookGenerationResult(BaseModel):
    """
    Result of playbook generation.

    Attributes:
        success: Whether generation succeeded
        playbook_yaml: Generated YAML content
        validation_result: Validation details
        error_message: Error message if failed
        model_used: LLM model name
        tokens_used: Token count
    """

    success: bool
    playbook_yaml: str
    validation_result: ValidationResult | None = None
    error_message: str | None = None
    model_used: str | None = None
    tokens_used: int | None = None


def generate_playbook(
    description: str,
    llm_provider: Literal["gemini", "claude"],
    api_key: str,
    max_retries: int = 2,
    temperature: float = 0.3,
    validation_timeout: int = 30,
) -> PlaybookGenerationResult:
    """
    Generate and validate an Ansible Kubernetes playbook.

    This is a stateless function that can be used by both MCP server and web app.

    Args:
        description: Natural language description of deployment
        llm_provider: LLM provider ('gemini' or 'claude')
        api_key: API key for the selected provider
        max_retries: Maximum retry attempts on validation failure
        temperature: LLM sampling temperature
        validation_timeout: Docker validation timeout in seconds

    Returns:
        PlaybookGenerationResult with playbook or error details
    """
    # Debug logging
    logger.info(
        f"🔍 generate_playbook called: provider={llm_provider}, "
        f"key_prefix={api_key[:4] if api_key else 'NONE'}****, "
        f"key_length={len(api_key) if api_key else 0}, "
        f"max_retries={max_retries}"
    )

    # Validate provider early
    if llm_provider not in ("gemini", "claude"):
        return PlaybookGenerationResult(
            success=False,
            playbook_yaml="",
            error_message=f"Unsupported llm_provider: {llm_provider}. Must be 'gemini' or 'claude'",
        )

    # Initialize variables before loop to avoid undefined references
    playbook_yaml = ""
    validation: ValidationResult | None = None

    try:
        # Create settings with provided credentials
        settings = Settings(
            llm_provider=llm_provider,
            gemini_api_key=api_key if llm_provider == "gemini" else None,
            claude_api_key=api_key if llm_provider == "claude" else None,
            docker_validation_timeout=validation_timeout,
        )
        logger.info(f"✓ Settings created for {llm_provider}")

        # Initialize components
        llm_engine = create_llm_engine(settings)
        validator = PlaybookValidator(timeout=validation_timeout)
        system_prompt = load_system_prompt()
        logger.info(f"✓ Components initialized")

        current_description = description

        for attempt in range(max_retries):
            logger.info(f"📝 Attempt {attempt + 1}/{max_retries}: Generating playbook...")

            # Generate playbook
            request = GenerationRequest(
                user_prompt=current_description,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=temperature,
            )

            try:
                response = llm_engine.generate(request)
                playbook_yaml = response.content
                logger.info(
                    f"✅ Generation successful: model={response.model}, tokens={response.usage_tokens}"
                )
            except Exception as gen_error:
                logger.error(
                    f"❌ Generation failed on attempt {attempt + 1}: "
                    f"{type(gen_error).__name__}: {str(gen_error)[:200]}"
                )
                raise  # Re-raise to be caught by outer try/except

            # Validate
            logger.info(f"🔍 Validating generated playbook...")
            validation = validator.validate(playbook_yaml)

            if validation.is_valid:
                return PlaybookGenerationResult(
                    success=True,
                    playbook_yaml=playbook_yaml,
                    validation_result=validation,
                    model_used=response.model,
                    tokens_used=response.usage_tokens,
                )

            # Retry with error feedback
            if attempt < max_retries - 1:
                error_feedback = "\n".join(validation.errors)
                current_description = (
                    f"{description}\n\n"
                    f"Previous attempt had validation errors:\n{error_feedback}\n\n"
                    f"Please fix these issues and ensure:\n"
                    f"- All modules use FQCN (kubernetes.core.k8s not k8s)\n"
                    f"- No kubectl commands are used\n"
                    f"- YAML syntax is correct\n"
                    f"- All required fields are present"
                )

        # All retries failed
        return PlaybookGenerationResult(
            success=False,
            playbook_yaml=playbook_yaml,
            validation_result=validation,
            error_message=f"Failed to generate valid playbook after {max_retries} attempts",
        )

    except Exception as e:
        return PlaybookGenerationResult(
            success=False,
            playbook_yaml="",
            error_message=f"Generation error: {str(e)}",
        )


def validate_playbook_yaml(yaml_content: str, validation_timeout: int = 30) -> ValidationResult:
    """
    Validate an Ansible playbook YAML.

    Args:
        yaml_content: YAML content to validate
        validation_timeout: Docker validation timeout in seconds

    Returns:
        ValidationResult with validation details
    """
    validator = PlaybookValidator(timeout=validation_timeout)
    return validator.validate(yaml_content)


def generate_readme(
    playbook_yaml: str, llm_provider: Literal["gemini", "claude"], api_key: str
) -> str:
    """
    Generate README.md documentation for a playbook using LLM.

    Args:
        playbook_yaml: Playbook YAML content
        llm_provider: LLM provider ('gemini' or 'claude')
        api_key: API key for the selected provider

    Returns:
        Generated README markdown content
    """
    try:
        settings = Settings(
            llm_provider=llm_provider,
            gemini_api_key=api_key if llm_provider == "gemini" else None,
            claude_api_key=api_key if llm_provider == "claude" else None,
        )

        llm_engine = create_llm_engine(settings)

        readme_prompt = f"""Generate a comprehensive README.md in markdown format for this Ansible Kubernetes playbook.

Include:
1. **Overview**: What this playbook deploys
2. **Prerequisites**: Required tools, access, and dependencies
3. **Usage**: Step-by-step commands to run the playbook
4. **What Gets Created**: Detailed list of Kubernetes resources
5. **Customization**: How to modify for different environments
6. **Troubleshooting**: Common issues and solutions

Be clear, professional, and provide actionable instructions.

Playbook:
```yaml
{playbook_yaml}
```
"""

        request = GenerationRequest(
            user_prompt=readme_prompt,
            system_prompt="You are a technical writer. Generate clear, professional documentation in markdown format.",
            max_tokens=2048,
            temperature=0.5,
        )

        response = llm_engine.generate(request)
        return response.content

    except Exception as e:
        return f"# README Generation Failed\n\nError: {str(e)}"
