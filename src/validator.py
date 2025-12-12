"""Docker-based validation engine for Ansible playbooks."""

import subprocess
import tempfile
from pathlib import Path

from pydantic import BaseModel


class ValidationResult(BaseModel):
    """
    Result of playbook validation.

    Attributes:
        is_valid: Whether the playbook passed all validation checks
        lint_output: stdout from ansible-lint
        syntax_check_output: stdout from syntax check
        errors: List of error messages
        warnings: List of warning messages
    """

    is_valid: bool
    lint_output: str
    syntax_check_output: str
    errors: list[str]
    warnings: list[str]


class PlaybookValidator:
    """Validates Ansible playbooks using Docker sandbox."""

    def __init__(self, docker_image: str = "mcp-ansible-validator:latest", timeout: int = 30):
        """
        Initialize playbook validator.

        Args:
            docker_image: Docker image name to use for validation
            timeout: Timeout in seconds for validation commands
        """
        self.docker_image = docker_image
        self.timeout = timeout

    def validate(self, playbook_yaml: str) -> ValidationResult:
        """
        Validate playbook in Docker container.

        This method writes the playbook to a temporary file, mounts it into a Docker
        container, and runs both ansible-lint and ansible-playbook --syntax-check.

        Args:
            playbook_yaml: YAML content to validate

        Returns:
            ValidationResult with validation details

        Raises:
            subprocess.TimeoutExpired: If validation exceeds timeout
            FileNotFoundError: If Docker is not available
        """
        # Run validation via stdin instead of file mount
        # This avoids Docker-out-of-Docker volume mounting issues where
        # the validator container can't access temp files from the web container
        try:
            # Run ansible-lint with stdin
            # Note: ansible-lint expects a file, so we use /dev/stdin
            lint_result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-i",  # Interactive mode for stdin
                    self.docker_image,
                    "sh",
                    "-c",
                    "cat > /tmp/playbook.yml && ansible-lint /tmp/playbook.yml",
                ],
                input=playbook_yaml,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )

            # Run ansible-playbook --syntax-check with stdin
            syntax_result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-i",
                    self.docker_image,
                    "sh",
                    "-c",
                    "cat > /tmp/playbook.yml && ansible-playbook --syntax-check /tmp/playbook.yml",
                ],
                input=playbook_yaml,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )

            # Parse results
            errors: list[str] = []
            warnings: list[str] = []

            # Check lint results
            if lint_result.returncode != 0:
                lint_error = lint_result.stderr.strip() or lint_result.stdout.strip()
                if lint_error:
                    errors.append(f"ansible-lint failed:\n{lint_error}")

            # Check syntax results
            if syntax_result.returncode != 0:
                syntax_error = syntax_result.stderr.strip() or syntax_result.stdout.strip()
                if syntax_error:
                    errors.append(f"Syntax check failed:\n{syntax_error}")

            # Look for warnings in lint output
            if "warning" in lint_result.stdout.lower():
                warnings.append(lint_result.stdout)

            is_valid = len(errors) == 0

            return ValidationResult(
                is_valid=is_valid,
                lint_output=lint_result.stdout,
                syntax_check_output=syntax_result.stdout,
                errors=errors,
                warnings=warnings,
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                is_valid=False,
                lint_output="",
                syntax_check_output="",
                errors=[f"Validation timeout after {self.timeout} seconds"],
                warnings=[],
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                lint_output="",
                syntax_check_output="",
                errors=[f"Validation error: {type(e).__name__}: {str(e)}"],
                warnings=[],
            )
