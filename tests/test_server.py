"""Tests for MCP server functionality.

Note: Server tests are skipped by default because the server module initializes
components at import time, which requires valid API keys in environment variables.

To run these tests, set up .env with valid credentials and remove the skip markers.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Server tests require valid API keys in .env")


def test_server_requires_env_config() -> None:
    """Placeholder to indicate server tests need environment configuration."""
    # The server module requires valid API keys at import time.
    # For integration testing:
    # 1. Create .env with valid GEMINI_API_KEY or ANTHROPIC_API_KEY
    # 2. Remove the pytestmark skip decorator above
    # 3. Run: pytest tests/test_server.py -v
    pass
