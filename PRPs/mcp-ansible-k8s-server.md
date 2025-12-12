name: "MCP Ansible-K8s Server: AI-Powered DevOps Factory"
description: |

## Purpose
Build a production-ready MCP (Model Context Protocol) server that leverages LLMs (Google Gemini or Anthropic Claude) to dynamically generate Ansible Kubernetes playbooks from natural language descriptions, with sandboxed Docker validation for security and quality assurance.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Create an MCP server that accepts natural language requests (e.g., "Deploy HA Nginx with 3 replicas") and returns production-ready, validated Ansible Kubernetes playbooks. The server must support both Gemini and Claude APIs, validate all generated YAML in a Docker sandbox, and expose tools via the MCP protocol for client consumption.

## Why
- **Business value**: Automates DevOps workflow creation, reducing time from intent to deployment from hours to seconds
- **Integration**: Provides standardized MCP interface for AI assistants and tools to generate infrastructure code
- **Problems solved**: Eliminates manual YAML writing errors, enforces best practices (FQCN, idempotency), prevents security issues through sandboxed validation

## What
A Python-based MCP server that:
- Exposes two MCP tools: `smart_generate_playbook` and `validate_playbook`
- Integrates with Google Gemini API OR Anthropic Claude API for code generation
- Uses specialized system prompts to enforce `kubernetes.core` best practices
- Validates all generated playbooks in isolated Docker containers using `ansible-lint` and `ansible-playbook --syntax-check`
- Returns only validated, production-ready YAML to users

### Success Criteria
- [ ] MCP server successfully registers and accepts connections via stdio transport
- [ ] `smart_generate_playbook` tool generates playbooks from natural language
- [ ] Generated playbooks use FQCN (kubernetes.core modules only, no kubectl commands)
- [ ] Docker validation catches syntax errors and lint issues before returning code
- [ ] Both Gemini and Claude APIs work interchangeably (configured via .env)
- [ ] Example script (`examples/test_generation.py`) successfully demonstrates full workflow
- [ ] All tests pass and code meets quality standards (ruff, mypy, pytest)

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window

# MCP Protocol
- url: https://github.com/modelcontextprotocol/python-sdk
  why: Official Python SDK for building MCP servers with stdio/SSE/HTTP transports
  critical: FastMCP is the recommended interface for server creation

- url: https://modelcontextprotocol.github.io/python-sdk/
  why: Full MCP server documentation with tool registration patterns
  section: Server setup, tool decorators, resource handling

# LLM APIs
- url: https://github.com/googleapis/python-genai
  why: New unified Google GenAI SDK (GA in 2025)
  critical: Old google-generativeai SDK deprecated Nov 2025, must use google-genai

- url: https://googleapis.github.io/python-genai/
  why: Full API reference for Gemini text generation
  section: Client setup, messages API, function calling

- url: https://github.com/anthropics/anthropic-sdk-python
  why: Official Anthropic Claude SDK
  section: Messages API, streaming, model selection

- url: https://docs.claude.com/en/docs/claude-code/sdk/sdk-python
  why: Claude Python SDK reference with examples

# Ansible Validation
- url: https://docs.ansible.com/projects/lint/rules/fqcn/
  why: FQCN rule enforcement - all modules must use fully qualified names
  critical: kubernetes.core.k8s NOT k8s, ansible.builtin.command NOT command

- url: https://docs.ansible.com/projects/lint/usage/
  why: ansible-lint command usage and exit codes

- url: https://docs.ansible.com/ansible/latest/collections/kubernetes/core/k8s_module.html
  why: kubernetes.core collection reference for K8s resource management
  critical: This is what the LLM should generate, not kubectl commands

- url: https://github.com/agaffney/ansible-sandbox
  why: Example of Docker-based Ansible playbook validation sandbox pattern

# Best Practices
- url: https://timgrt.github.io/Ansible-Best-Practices/ansible/tasks/
  why: Ansible task structure best practices including FQCN usage

- file: INITIAL.md
  why: Project requirements, features, tools specification

- file: PRPs/EXAMPLE_multi_agent_prp.md
  why: Example PRP structure and validation patterns

- file: CLAUDE.md
  why: Project-specific conventions, code structure rules, testing requirements
```

### Current Codebase Tree
```bash
.
├── .claude/
│   ├── commands/           # Slash commands for PRP workflow
│   └── settings.local.json
├── .devcontainer/          # Node.js devcontainer (for Claude Code)
│   ├── Dockerfile
│   └── devcontainer.json
├── PRPs/
│   ├── EXAMPLE_multi_agent_prp.md
│   └── templates/
│       └── prp_base.md
├── INITIAL.md              # Feature specification
├── CLAUDE.md               # Development guidelines
└── .gitignore              # Includes venv_linux
```

### Desired Codebase Tree with Files to be Added
```bash
.
├── src/
│   ├── __init__.py                    # Package init
│   ├── server.py                      # Main MCP server entry point
│   ├── llm_engine.py                  # LLM abstraction layer (Gemini/Claude)
│   ├── validator.py                   # Docker-based validation engine
│   ├── prompts.py                     # System prompts for LLM
│   └── config.py                      # Settings management (pydantic-settings)
│
├── examples/
│   ├── __init__.py
│   ├── test_generation.py             # Demo script showing full workflow
│   └── prompts/
│       └── ansible_k8s_expert.txt     # System prompt template
│
├── tests/
│   ├── __init__.py
│   ├── test_server.py                 # MCP server tests
│   ├── test_llm_engine.py             # LLM integration tests (mocked)
│   ├── test_validator.py              # Docker validation tests
│   └── fixtures/
│       ├── valid_playbook.yml         # Test fixtures
│       └── invalid_playbook.yml
│
├── docker/
│   └── Dockerfile.validator           # Validation environment image
│
├── .env.example                       # Environment variables template
├── requirements.txt                   # Python dependencies
├── README.md                          # Setup and usage documentation
├── pyproject.toml                     # Project metadata and tool config
└── pytest.ini                         # Pytest configuration
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: MCP SDK
# - Use FastMCP from mcp.server.fastmcp for easier server creation
# - Tools must be registered with @mcp.tool() decorator
# - Stdio transport is the standard for MCP servers
# - All tool functions must have proper docstrings (used in MCP schema)

# CRITICAL: Google GenAI SDK
# - MUST use google-genai (new SDK), NOT google-generativeai (deprecated Nov 2025)
# - Install with: pip install google-genai
# - Model names: "gemini-2.0-flash-001" (recommended for code generation)
# - API key via GEMINI_API_KEY environment variable

# CRITICAL: Anthropic SDK
# - Model names: "claude-sonnet-4-5-20250929" or "claude-3-5-haiku-20241022"
# - API key via ANTHROPIC_API_KEY environment variable
# - Messages API is the standard (not legacy completions)

# CRITICAL: Ansible Validation
# - ansible-lint exit code 0 = success, non-zero = issues found
# - ansible-playbook --syntax-check exit code 0 = valid, non-zero = syntax errors
# - MUST check both lint AND syntax-check for full validation
# - Docker container needs ansible, ansible-lint, kubernetes.core collection installed

# CRITICAL: Docker Subprocess
# - Use subprocess.run() with capture_output=True for validation
# - Set timeout to prevent hanging (30s recommended)
# - Mount generated YAML as volume or use stdin to pass content
# - Parse stdout/stderr to extract validation errors

# CRITICAL: System Prompts
# - MUST explicitly forbid kubectl commands: "NEVER use command: kubectl"
# - MUST require FQCN: "ALWAYS use kubernetes.core.k8s, NOT k8s"
# - MUST enforce idempotency: "Use state: present/absent"
# - Include example playbook structure in prompt

# CRITICAL: Python Environment
# - Use venv_linux for all Python commands (as per CLAUDE.md)
# - python-dotenv for .env loading
# - Use pydantic-settings for config management
```

## Implementation Blueprint

### Data Models and Structure

```python
# config.py - Configuration management
from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # LLM Configuration
    llm_provider: Literal["gemini", "claude"] = "gemini"
    gemini_api_key: str | None = None
    claude_api_key: str | None = None

    # Validation Configuration
    docker_validation_timeout: int = 30
    ansible_lint_config: str | None = None

    # MCP Configuration
    mcp_server_name: str = "mcp-ansible-k8s"
    mcp_server_version: str = "0.1.0"

    class Config:
        env_file = ".env"
        case_sensitive = False

# llm_engine.py - LLM abstraction models
from pydantic import BaseModel

class GenerationRequest(BaseModel):
    """Request to generate a playbook."""
    user_prompt: str
    system_prompt: str
    max_tokens: int = 4096
    temperature: float = 0.7

class GenerationResponse(BaseModel):
    """Response from LLM generation."""
    content: str
    model: str
    usage_tokens: int | None = None

# validator.py - Validation result models
class ValidationResult(BaseModel):
    """Result of playbook validation."""
    is_valid: bool
    lint_output: str
    syntax_check_output: str
    errors: list[str]
    warnings: list[str]
```

### List of Tasks to be Completed

```yaml
Task 1: Project Setup and Configuration
CREATE pyproject.toml:
  - PATTERN: Standard Python project metadata with ruff, mypy, pytest config
  - Include tool.ruff.lint and tool.mypy sections
  - Set Python version to 3.11+

CREATE requirements.txt:
  - mcp>=1.0.0 (MCP SDK)
  - google-genai>=1.0.0 (NEW Gemini SDK)
  - anthropic>=0.40.0 (Claude SDK)
  - pydantic>=2.0.0
  - pydantic-settings>=2.0.0
  - python-dotenv>=1.0.0
  - pyyaml>=6.0.0

CREATE .env.example:
  - Template for all required environment variables
  - Include comments explaining each variable

CREATE src/config.py:
  - PATTERN: Use pydantic-settings.BaseSettings
  - Load from .env file automatically
  - Validate required keys based on llm_provider

Task 2: System Prompt Engineering
CREATE examples/prompts/ansible_k8s_expert.txt:
  - CRITICAL: Explicit prohibition of kubectl commands
  - CRITICAL: Require FQCN for all modules (kubernetes.core.*)
  - CRITICAL: Enforce idempotency patterns (state: present/absent)
  - Include example playbook structure
  - Specify YAML formatting requirements

CREATE src/prompts.py:
  - Load system prompt from file
  - Provide function to format prompt with user request
  - Include validation that prompt contains critical keywords

Task 3: LLM Engine Abstraction
CREATE src/llm_engine.py:
  - PATTERN: Factory pattern for LLM client creation
  - Class: LLMEngine with abstract interface
  - Class: GeminiEngine(LLMEngine) using google-genai
  - Class: ClaudeEngine(LLMEngine) using anthropic
  - Method: generate(request: GenerationRequest) -> GenerationResponse
  - CRITICAL: Use new google-genai SDK, NOT deprecated google-generativeai
  - Handle API errors gracefully with retries

Task 4: Docker Validation Engine
CREATE docker/Dockerfile.validator:
  - Base image: python:3.11-slim
  - Install: ansible, ansible-lint, kubernetes.core collection
  - WORKDIR /workspace for playbook validation

CREATE src/validator.py:
  - Class: PlaybookValidator
  - Method: validate(playbook_yaml: str) -> ValidationResult
  - PATTERN: subprocess.run() with Docker
  - Step 1: Write YAML to temp file
  - Step 2: docker run with volume mount to temp file
  - Step 3: Run ansible-lint inside container
  - Step 4: Run ansible-playbook --syntax-check inside container
  - Step 5: Parse outputs and return ValidationResult
  - CRITICAL: Set timeout to 30s to prevent hanging
  - Handle Docker errors (container not running, image not found)

Task 5: MCP Server Implementation
CREATE src/server.py:
  - PATTERN: Use FastMCP from mcp.server.fastmcp
  - Initialize MCP server with name and version
  - Register two tools: smart_generate_playbook, validate_playbook
  - Tool 1: smart_generate_playbook(description: str) -> str
    - Load system prompt
    - Call LLM engine with user description
    - Validate generated YAML
    - If validation fails: retry generation with error feedback
    - Return validated YAML or error message
  - Tool 2: validate_playbook(yaml_content: str) -> str
    - Validate provided YAML
    - Return validation results as formatted string
  - CRITICAL: All tools need docstrings (used for MCP schema)
  - CRITICAL: Use stdio transport for server

Task 6: Example Script
CREATE examples/test_generation.py:
  - PATTERN: Simulate MCP client interaction
  - Test case 1: "Deploy Redis with 1 replica and ClusterIP service"
  - Test case 2: "Deploy HA Nginx with 3 replicas and LoadBalancer"
  - Print generated playbooks
  - Print validation results
  - PATTERN: Use async/await if MCP SDK requires it

Task 7: Comprehensive Testing
CREATE tests/test_server.py:
  - Test MCP server initialization
  - Test tool registration
  - Mock MCP client connection
  - Verify tool schemas are correct

CREATE tests/test_llm_engine.py:
  - PATTERN: Mock API calls (don't hit real APIs in tests)
  - Test GeminiEngine generation
  - Test ClaudeEngine generation
  - Test error handling (invalid API key, rate limits)
  - Test factory pattern (create_llm_engine)

CREATE tests/test_validator.py:
  - Test validation with valid playbook
  - Test validation with invalid YAML syntax
  - Test validation with lint errors (missing FQCN)
  - Test Docker timeout handling
  - PATTERN: Use fixtures for sample playbooks

CREATE tests/fixtures/:
  - valid_playbook.yml: Correct kubernetes.core usage
  - invalid_syntax.yml: YAML syntax errors
  - missing_fqcn.yml: Uses 'k8s' instead of 'kubernetes.core.k8s'

Task 8: Documentation
CREATE README.md:
  - PATTERN: Clear setup instructions
  - Section: Installation (venv setup, requirements)
  - Section: Configuration (.env file setup)
  - Section: Usage (running the MCP server)
  - Section: Testing (pytest commands)
  - Section: Docker Setup (building validator image)
  - Section: Example Usage (with test_generation.py)
  - Include architecture diagram (ASCII or link to image)

UPDATE CLAUDE.md (if needed):
  - Add any project-specific validation commands discovered
  - Document any new conventions established

Task 9: Docker Image Building
BUILD docker/Dockerfile.validator:
  - Command: docker build -t mcp-ansible-validator:latest -f docker/Dockerfile.validator .
  - Verify ansible-lint and ansible-playbook are accessible
  - Test with sample playbook

Task 10: Integration Validation
RUN full workflow test:
  - Start MCP server: python -m src.server
  - Run example script: python examples/test_generation.py
  - Verify playbooks are generated and validated
  - Check logs for errors
```

### Per Task Pseudocode

```python
# Task 3: LLM Engine Abstraction
# src/llm_engine.py

from abc import ABC, abstractmethod
from google import genai  # NEW SDK
from anthropic import Anthropic

class LLMEngine(ABC):
    """Abstract base for LLM integrations."""

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text from prompt."""
        pass

class GeminiEngine(LLMEngine):
    """Google Gemini integration using new google-genai SDK."""

    def __init__(self, api_key: str):
        # CRITICAL: Use new SDK
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash-001"

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        # PATTERN: Messages API
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{request.system_prompt}\n\nUser: {request.user_prompt}",
            config={
                "max_output_tokens": request.max_tokens,
                "temperature": request.temperature,
            }
        )

        # Extract text from response
        content = response.text

        return GenerationResponse(
            content=content,
            model=self.model,
            usage_tokens=response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else None
        )

class ClaudeEngine(LLMEngine):
    """Anthropic Claude integration."""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        # PATTERN: Messages API with system parameter
        message = self.client.messages.create(
            model=self.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system=request.system_prompt,
            messages=[
                {"role": "user", "content": request.user_prompt}
            ]
        )

        # Extract text from response
        content = message.content[0].text

        return GenerationResponse(
            content=content,
            model=self.model,
            usage_tokens=message.usage.input_tokens + message.usage.output_tokens
        )

def create_llm_engine(settings: Settings) -> LLMEngine:
    """Factory function to create LLM engine based on config."""
    # PATTERN: Factory pattern
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not set")
        return GeminiEngine(settings.gemini_api_key)
    elif settings.llm_provider == "claude":
        if not settings.claude_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return ClaudeEngine(settings.claude_api_key)
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")


# Task 4: Docker Validation Engine
# src/validator.py

import subprocess
import tempfile
from pathlib import Path

class PlaybookValidator:
    """Validates Ansible playbooks using Docker sandbox."""

    def __init__(self, docker_image: str = "mcp-ansible-validator:latest", timeout: int = 30):
        self.docker_image = docker_image
        self.timeout = timeout

    def validate(self, playbook_yaml: str) -> ValidationResult:
        """
        Validate playbook in Docker container.

        Args:
            playbook_yaml: YAML content to validate

        Returns:
            ValidationResult with validation details
        """
        # PATTERN: Temp file for YAML content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(playbook_yaml)
            temp_path = Path(f.name)

        try:
            # CRITICAL: Run ansible-lint in Docker
            lint_result = subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{temp_path.absolute()}:/workspace/playbook.yml:ro",
                self.docker_image,
                "ansible-lint", "/workspace/playbook.yml"
            ], capture_output=True, text=True, timeout=self.timeout)

            # CRITICAL: Run ansible-playbook --syntax-check in Docker
            syntax_result = subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{temp_path.absolute()}:/workspace/playbook.yml:ro",
                self.docker_image,
                "ansible-playbook", "--syntax-check", "/workspace/playbook.yml"
            ], capture_output=True, text=True, timeout=self.timeout)

            # Parse results
            errors = []
            warnings = []

            if lint_result.returncode != 0:
                errors.append(f"ansible-lint failed: {lint_result.stderr}")

            if syntax_result.returncode != 0:
                errors.append(f"Syntax check failed: {syntax_result.stderr}")

            # PATTERN: Consider warnings from stdout
            if "warning" in lint_result.stdout.lower():
                warnings.append(lint_result.stdout)

            is_valid = len(errors) == 0

            return ValidationResult(
                is_valid=is_valid,
                lint_output=lint_result.stdout,
                syntax_check_output=syntax_result.stdout,
                errors=errors,
                warnings=warnings
            )

        finally:
            # PATTERN: Cleanup temp file
            temp_path.unlink(missing_ok=True)


# Task 5: MCP Server Implementation
# src/server.py

from mcp.server.fastmcp import FastMCP
from src.config import Settings
from src.llm_engine import create_llm_engine
from src.validator import PlaybookValidator
from src.prompts import load_system_prompt

# PATTERN: Initialize FastMCP server
settings = Settings()
mcp = FastMCP(settings.mcp_server_name)

# Initialize components
llm_engine = create_llm_engine(settings)
validator = PlaybookValidator(timeout=settings.docker_validation_timeout)
system_prompt = load_system_prompt()

@mcp.tool()
def smart_generate_playbook(description: str) -> str:
    """
    Generate a validated Ansible Kubernetes playbook from natural language description.

    Args:
        description: Natural language description of desired K8s deployment

    Returns:
        Validated YAML playbook or error message
    """
    # PATTERN: LLM generation with validation loop
    max_retries = 2

    for attempt in range(max_retries):
        # Generate playbook
        request = GenerationRequest(
            user_prompt=description,
            system_prompt=system_prompt,
            max_tokens=4096,
            temperature=0.3  # Lower temp for more consistent code generation
        )

        response = llm_engine.generate(request)
        playbook_yaml = response.content

        # CRITICAL: Validate before returning
        validation = validator.validate(playbook_yaml)

        if validation.is_valid:
            return playbook_yaml

        # PATTERN: Retry with error feedback
        if attempt < max_retries - 1:
            # Add validation errors to next prompt
            error_feedback = "\n".join(validation.errors)
            description += f"\n\nPrevious attempt had errors:\n{error_feedback}\n\nPlease fix these issues."

    # If all retries failed
    return f"ERROR: Failed to generate valid playbook after {max_retries} attempts.\n\nLast errors:\n" + "\n".join(validation.errors)

@mcp.tool()
def validate_playbook(yaml_content: str) -> str:
    """
    Validate an Ansible playbook YAML.

    Args:
        yaml_content: YAML content to validate

    Returns:
        Validation results as formatted string
    """
    validation = validator.validate(yaml_content)

    if validation.is_valid:
        return "✓ Playbook is valid!\n\n" + validation.lint_output
    else:
        return "✗ Playbook validation failed:\n\n" + "\n".join(validation.errors)

# CRITICAL: Run server with stdio transport
if __name__ == "__main__":
    mcp.run()
```

### Integration Points

```yaml
ENVIRONMENT:
  - add to: .env
  - vars: |
      # LLM Provider Selection
      LLM_PROVIDER=gemini  # or "claude"

      # Google Gemini API (if using gemini)
      GEMINI_API_KEY=your_api_key_here

      # Anthropic Claude API (if using claude)
      ANTHROPIC_API_KEY=your_api_key_here

      # Validation Settings
      DOCKER_VALIDATION_TIMEOUT=30

      # MCP Settings
      MCP_SERVER_NAME=mcp-ansible-k8s
      MCP_SERVER_VERSION=0.1.0

DOCKER:
  - image: mcp-ansible-validator:latest
  - build: docker build -t mcp-ansible-validator:latest -f docker/Dockerfile.validator .
  - requirements:
      - ansible>=2.14
      - ansible-lint>=6.0
      - kubernetes.core collection

DEPENDENCIES:
  - Python 3.11+
  - Docker daemon running
  - venv_linux for Python commands (as per CLAUDE.md)

SYSTEM_PROMPT:
  - location: examples/prompts/ansible_k8s_expert.txt
  - critical_keywords:
      - "NEVER use command: kubectl"
      - "ALWAYS use kubernetes.core.k8s"
      - "Use FQCN (fully qualified collection names)"
      - "Ensure idempotency with state: present/absent"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# CRITICAL: Run these FIRST in venv_linux - fix any errors before proceeding

# Activate venv
source venv_linux/bin/activate

# Lint and format
ruff check src/ tests/ examples/ --fix
ruff format src/ tests/ examples/

# Type checking
mypy src/ tests/ examples/

# Expected: No errors. If errors, READ the error message and fix.
```

### Level 2: Unit Tests
```python
# tests/test_llm_engine.py - Example test structure

import pytest
from unittest.mock import Mock, patch
from src.llm_engine import GeminiEngine, ClaudeEngine, create_llm_engine
from src.config import Settings

def test_gemini_engine_generation():
    """Test Gemini engine generates content."""
    # PATTERN: Mock API call
    with patch('google.genai.Client') as mock_client:
        mock_response = Mock()
        mock_response.text = "---\n- name: Test playbook\n  hosts: localhost"
        mock_response.usage_metadata.total_token_count = 100

        mock_client.return_value.models.generate_content.return_value = mock_response

        engine = GeminiEngine("fake_api_key")
        request = GenerationRequest(
            user_prompt="Deploy Redis",
            system_prompt="You are an expert",
            max_tokens=1000
        )

        response = engine.generate(request)

        assert "Test playbook" in response.content
        assert response.usage_tokens == 100

def test_factory_creates_correct_engine():
    """Test factory creates engine based on settings."""
    settings = Settings(llm_provider="gemini", gemini_api_key="test_key")
    engine = create_llm_engine(settings)
    assert isinstance(engine, GeminiEngine)

    settings = Settings(llm_provider="claude", claude_api_key="test_key")
    engine = create_llm_engine(settings)
    assert isinstance(engine, ClaudeEngine)

def test_missing_api_key_raises_error():
    """Test factory raises error when API key missing."""
    settings = Settings(llm_provider="gemini", gemini_api_key=None)
    with pytest.raises(ValueError, match="GEMINI_API_KEY not set"):
        create_llm_engine(settings)

# tests/test_validator.py

def test_validate_valid_playbook():
    """Test validation passes for valid playbook."""
    validator = PlaybookValidator()

    valid_yaml = """---
- name: Deploy Redis
  hosts: localhost
  tasks:
    - name: Create Redis deployment
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: apps/v1
          kind: Deployment
          metadata:
            name: redis
          spec:
            replicas: 1
"""

    result = validator.validate(valid_yaml)
    assert result.is_valid
    assert len(result.errors) == 0

def test_validate_missing_fqcn():
    """Test validation fails when FQCN missing."""
    validator = PlaybookValidator()

    invalid_yaml = """---
- name: Deploy Redis
  hosts: localhost
  tasks:
    - name: Create Redis deployment
      k8s:  # Missing FQCN!
        state: present
"""

    result = validator.validate(invalid_yaml)
    assert not result.is_valid
    assert any("fqcn" in error.lower() for error in result.errors)

def test_validate_syntax_error():
    """Test validation catches YAML syntax errors."""
    validator = PlaybookValidator()

    invalid_yaml = """---
- name: Deploy Redis
  hosts: localhost
  tasks:
    - name: Bad indentation
     kubernetes.core.k8s:  # Wrong indentation
"""

    result = validator.validate(invalid_yaml)
    assert not result.is_valid
    assert any("syntax" in error.lower() for error in result.errors)
```

```bash
# Run tests iteratively until passing:
source venv_linux/bin/activate
pytest tests/ -v --cov=src --cov-report=term-missing

# If failing: Debug specific test, fix code, re-run (never mock to pass)
# Target: 80%+ code coverage
```

### Level 3: Integration Test
```bash
# CRITICAL: Build Docker validator image first
docker build -t mcp-ansible-validator:latest -f docker/Dockerfile.validator .

# Verify Docker image works
docker run --rm mcp-ansible-validator:latest ansible-lint --version
docker run --rm mcp-ansible-validator:latest ansible-playbook --version

# Create .env file from template
cp .env.example .env
# Edit .env and add your API keys

# Run the example script
source venv_linux/bin/activate
python examples/test_generation.py

# Expected output:
# ✓ Generated playbook for: Deploy Redis with 1 replica
# ✓ Validation passed
# --- Playbook YAML ---
# [Valid kubernetes.core playbook content]
#
# ✓ Generated playbook for: Deploy HA Nginx with 3 replicas
# ✓ Validation passed
# --- Playbook YAML ---
# [Valid kubernetes.core playbook content]

# Test MCP server directly
python -m src.server
# (Server should start and listen on stdio)
# In another terminal, test with MCP client or inspector tool
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check src/ tests/ examples/`
- [ ] No type errors: `mypy src/ tests/ examples/`
- [ ] Docker validator image builds successfully
- [ ] Example script generates valid playbooks
- [ ] Generated playbooks use FQCN (kubernetes.core.*)
- [ ] Generated playbooks pass ansible-lint
- [ ] Generated playbooks pass ansible-playbook --syntax-check
- [ ] No kubectl commands in generated playbooks
- [ ] Both Gemini and Claude providers work (test by switching .env)
- [ ] MCP server starts without errors
- [ ] README includes clear setup and usage instructions
- [ ] .env.example has all required variables documented

---

## Anti-Patterns to Avoid
- ❌ Don't use deprecated google-generativeai SDK - use google-genai
- ❌ Don't skip Docker validation - it's critical for security
- ❌ Don't return unvalidated YAML to users
- ❌ Don't hardcode API keys - always use environment variables
- ❌ Don't use short Docker timeouts - 30s minimum for validation
- ❌ Don't forget FQCN in system prompts - LLMs will use shortcuts
- ❌ Don't allow kubectl commands in generated playbooks
- ❌ Don't skip type hints - they're required per CLAUDE.md
- ❌ Don't create files >500 lines - refactor into modules
- ❌ Don't skip docstrings - MCP requires them for tool schemas

## Research Sources

**MCP Protocol:**
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Server Documentation](https://modelcontextprotocol.github.io/python-sdk/)

**LLM APIs:**
- [Google GenAI SDK](https://github.com/googleapis/python-genai)
- [Google GenAI Docs](https://googleapis.github.io/python-genai/)
- [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python)
- [Claude Python SDK Reference](https://docs.claude.com/en/docs/claude-code/sdk/sdk-python)

**Ansible Validation:**
- [FQCN Rule Documentation](https://docs.ansible.com/projects/lint/rules/fqcn/)
- [Ansible-lint Usage](https://docs.ansible.com/projects/lint/usage/)
- [Kubernetes Core Collection](https://docs.ansible.com/ansible/latest/collections/kubernetes/core/k8s_module.html)
- [Ansible Sandbox Example](https://github.com/agaffney/ansible-sandbox)
- [Ansible Best Practices](https://timgrt.github.io/Ansible-Best-Practices/ansible/tasks/)

## Confidence Score: 8.5/10

**High confidence due to:**
- Clear API documentation for all integrations (MCP, Gemini, Claude)
- Well-defined validation pattern (Docker sandbox)
- Established best practices for Ansible/K8s
- Comprehensive test strategy with fixtures
- Detailed pseudocode covering critical paths

**Minor uncertainty on:**
- Exact format of MCP tool registration with FastMCP (may need minor adjustments)
- Docker volume mounting permissions in different environments (should handle in tests)
- LLM prompt engineering effectiveness (may need iteration to get perfect FQCN compliance)

**Mitigation:**
- Validation loops ensure iterative fixes
- Extensive testing at each level catches issues early
- Clear documentation references for troubleshooting
