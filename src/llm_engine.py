"""LLM engine abstraction layer for Gemini and Claude APIs."""

from abc import ABC, abstractmethod

from anthropic import Anthropic
from google import genai
from pydantic import BaseModel

from src.config import Settings


class GenerationRequest(BaseModel):
    """
    Request to generate a playbook.

    Attributes:
        user_prompt: User's natural language request
        system_prompt: System prompt with guidelines
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0-1)
    """

    user_prompt: str
    system_prompt: str
    max_tokens: int = 4096
    temperature: float = 0.7


class GenerationResponse(BaseModel):
    """
    Response from LLM generation.

    Attributes:
        content: Generated text content
        model: Model name used for generation
        usage_tokens: Optional token usage count
    """

    content: str
    model: str
    usage_tokens: int | None = None


class LLMEngine(ABC):
    """Abstract base class for LLM integrations."""

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate text from prompt.

        Args:
            request: Generation request with prompts and parameters

        Returns:
            Generated response with content and metadata
        """
        pass


class GeminiEngine(LLMEngine):
    """Google Gemini integration using new google-genai SDK."""

    def __init__(self, api_key: str):
        """
        Initialize Gemini engine.

        Args:
            api_key: Google Gemini API key
        """
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash-001"

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate text using Gemini API.

        Args:
            request: Generation request

        Returns:
            Generated response
        """
        # Combine system and user prompts for Gemini
        combined_prompt = f"{request.system_prompt}\n\nUser: {request.user_prompt}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=combined_prompt,
            config={
                "max_output_tokens": request.max_tokens,
                "temperature": request.temperature,
            },
        )

        # Extract text from response
        content = response.text if response.text else ""

        # Extract token usage if available
        usage_tokens = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage_tokens = response.usage_metadata.total_token_count

        return GenerationResponse(content=content, model=self.model, usage_tokens=usage_tokens)


class ClaudeEngine(LLMEngine):
    """Anthropic Claude integration."""

    def __init__(self, api_key: str):
        """
        Initialize Claude engine.

        Args:
            api_key: Anthropic Claude API key
        """
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate text using Claude API.

        Args:
            request: Generation request

        Returns:
            Generated response
        """
        message = self.client.messages.create(
            model=self.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system=request.system_prompt,
            messages=[{"role": "user", "content": request.user_prompt}],
        )

        # Extract text from response
        # Claude API returns content blocks, we need the first text block
        content = ""
        for block in message.content:
            if hasattr(block, "text"):
                content = block.text
                break

        # Calculate total tokens
        usage_tokens = message.usage.input_tokens + message.usage.output_tokens

        return GenerationResponse(content=content, model=self.model, usage_tokens=usage_tokens)


def create_llm_engine(settings: Settings) -> LLMEngine:
    """
    Factory function to create LLM engine based on configuration.

    Args:
        settings: Application settings

    Returns:
        Configured LLM engine instance

    Raises:
        ValueError: If provider is unknown or API key is missing
    """
    settings.validate_api_keys()

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
