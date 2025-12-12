"""Configuration management for MCP Ansible-K8s server."""

from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Attributes:
        llm_provider: LLM provider to use ('gemini' or 'claude')
        gemini_api_key: Google Gemini API key
        claude_api_key: Anthropic Claude API key
        docker_validation_timeout: Timeout for Docker validation in seconds
        ansible_lint_config: Optional path to ansible-lint configuration
        mcp_server_name: MCP server name
        mcp_server_version: MCP server version
    """

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider selection."""
        if v not in ["gemini", "claude"]:
            raise ValueError(f"Invalid LLM provider: {v}. Must be 'gemini' or 'claude'")
        return v

    def validate_api_keys(self) -> None:
        """
        Validate that the appropriate API key is set for the selected provider.

        Raises:
            ValueError: If required API key is missing
        """
        if self.llm_provider == "gemini" and not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not set but LLM_PROVIDER is 'gemini'")
        if self.llm_provider == "claude" and not self.claude_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set but LLM_PROVIDER is 'claude'")
