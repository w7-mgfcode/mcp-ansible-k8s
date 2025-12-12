"""Tests for Docker-based playbook validator."""

from pathlib import Path

import pytest

from src.validator import PlaybookValidator


@pytest.fixture
def validator() -> PlaybookValidator:
    """Create a PlaybookValidator instance."""
    return PlaybookValidator()


@pytest.fixture
def valid_playbook() -> str:
    """Load valid playbook fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "valid_playbook.yml"
    return fixture_path.read_text()


@pytest.fixture
def invalid_syntax_playbook() -> str:
    """Load invalid syntax playbook fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "invalid_syntax.yml"
    return fixture_path.read_text()


@pytest.fixture
def missing_fqcn_playbook() -> str:
    """Load missing FQCN playbook fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "missing_fqcn.yml"
    return fixture_path.read_text()


@pytest.mark.skipif(
    True,  # Skip by default as it requires Docker
    reason="Requires Docker validator image to be built",
)
def test_validate_valid_playbook(validator: PlaybookValidator, valid_playbook: str) -> None:
    """Test validation passes for valid playbook."""
    result = validator.validate(valid_playbook)

    assert result.is_valid
    assert len(result.errors) == 0


@pytest.mark.skipif(
    True,  # Skip by default as it requires Docker
    reason="Requires Docker validator image to be built",
)
def test_validate_invalid_syntax(
    validator: PlaybookValidator, invalid_syntax_playbook: str
) -> None:
    """Test validation catches YAML syntax errors."""
    result = validator.validate(invalid_syntax_playbook)

    assert not result.is_valid
    assert len(result.errors) > 0
    assert any("syntax" in error.lower() for error in result.errors)


@pytest.mark.skipif(
    True,  # Skip by default as it requires Docker
    reason="Requires Docker validator image to be built",
)
def test_validate_missing_fqcn(
    validator: PlaybookValidator, missing_fqcn_playbook: str
) -> None:
    """Test validation fails when FQCN is missing."""
    result = validator.validate(missing_fqcn_playbook)

    assert not result.is_valid
    assert len(result.errors) > 0
    # Check for FQCN-related errors
    assert any("fqcn" in error.lower() or "k8s" in error.lower() for error in result.errors)


def test_validator_initialization() -> None:
    """Test validator initialization with custom parameters."""
    validator = PlaybookValidator(docker_image="custom:latest", timeout=60)

    assert validator.docker_image == "custom:latest"
    assert validator.timeout == 60
