"""MCP server for AI-powered Ansible Kubernetes playbook generation."""

from mcp.server.fastmcp import FastMCP

from src.config import Settings
from src.engine import generate_playbook, validate_playbook_yaml

# Initialize settings
settings = Settings()
settings.validate_api_keys()

# Create FastMCP server
mcp = FastMCP(settings.mcp_server_name)


@mcp.tool()
def smart_generate_playbook(description: str) -> str:
    """
    Generate a validated Ansible Kubernetes playbook from natural language description.

    This tool uses an LLM to generate an Ansible playbook based on your description,
    then validates it using ansible-lint and syntax checks in a Docker sandbox.
    If validation fails, it retries with error feedback.

    Args:
        description: Natural language description of desired K8s deployment
                    (e.g., "Deploy HA Nginx with 3 replicas and a LoadBalancer")

    Returns:
        Validated YAML playbook content or error message if generation fails
    """
    # Get API key from settings
    api_key = (
        settings.gemini_api_key if settings.llm_provider == "gemini" else settings.claude_api_key
    )

    if not api_key:
        return f"ERROR: {settings.llm_provider.upper()}_API_KEY not set"

    # Call engine
    result = generate_playbook(
        description=description,
        llm_provider=settings.llm_provider,
        api_key=api_key,
        validation_timeout=settings.docker_validation_timeout,
    )

    if result.success:
        return result.playbook_yaml
    else:
        error_details = (
            "\n".join(result.validation_result.errors)
            if result.validation_result
            else "Unknown error"
        )
        return (
            f"ERROR: {result.error_message}\n\n"
            f"Last validation errors:\n{error_details}\n\n"
            f"Please try rephrasing your request or providing more specific details."
        )


@mcp.tool()
def validate_playbook(yaml_content: str) -> str:
    """
    Validate an Ansible playbook YAML.

    Runs ansible-lint and ansible-playbook --syntax-check in a Docker sandbox
    to validate the provided playbook content.

    Args:
        yaml_content: YAML content of the playbook to validate

    Returns:
        Formatted validation results with pass/fail status and details
    """
    validation = validate_playbook_yaml(yaml_content, settings.docker_validation_timeout)

    if validation.is_valid:
        result = "✓ Playbook is valid!\n\n"
        result += "=== Ansible Lint Output ===\n"
        result += validation.lint_output or "(no output)"
        result += "\n\n=== Syntax Check Output ===\n"
        result += validation.syntax_check_output or "(no output)"

        if validation.warnings:
            result += "\n\n⚠️  Warnings:\n"
            result += "\n".join(validation.warnings)

        return result
    else:
        result = "✗ Playbook validation failed!\n\n"
        result += "=== Errors ===\n"
        result += "\n\n".join(validation.errors)

        if validation.warnings:
            result += "\n\n⚠️  Warnings:\n"
            result += "\n".join(validation.warnings)

        return result


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
