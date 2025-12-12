"""MCP server for AI-powered Ansible Kubernetes playbook generation."""

from mcp.server.fastmcp import FastMCP

from src.config import Settings
from src.llm_engine import GenerationRequest, create_llm_engine
from src.prompts import load_system_prompt
from src.validator import PlaybookValidator

# Initialize settings and components
settings = Settings()
settings.validate_api_keys()

# Create FastMCP server
mcp = FastMCP(settings.mcp_server_name)

# Initialize LLM engine and validator
llm_engine = create_llm_engine(settings)
validator = PlaybookValidator(timeout=settings.docker_validation_timeout)
system_prompt = load_system_prompt()


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
    max_retries = 2
    current_description = description

    for attempt in range(max_retries):
        # Generate playbook using LLM
        request = GenerationRequest(
            user_prompt=current_description,
            system_prompt=system_prompt,
            max_tokens=4096,
            temperature=0.3,  # Lower temperature for more consistent code generation
        )

        response = llm_engine.generate(request)
        playbook_yaml = response.content

        # Validate generated playbook
        validation = validator.validate(playbook_yaml)

        if validation.is_valid:
            # Success! Return validated playbook
            return playbook_yaml

        # Validation failed - prepare retry with error feedback
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
    final_errors = "\n".join(validation.errors)
    return (
        f"ERROR: Failed to generate valid playbook after {max_retries} attempts.\n\n"
        f"Last validation errors:\n{final_errors}\n\n"
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
    validation = validator.validate(yaml_content)

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
