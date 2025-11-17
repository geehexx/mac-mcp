"""Factory for creating LLM providers."""

from mac_mcp_core.config import LLMConfig
from mac_mcp_reference.llm.anthropic_provider import AnthropicProvider
from mac_mcp_reference.llm.base import LLMProvider
from mac_mcp_reference.llm.bedrock_provider import BedrockProvider


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """Create an LLM provider based on configuration.

    Args:
        config: LLM configuration

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider is invalid or credentials are missing
    """
    provider = config.provider.lower()

    if provider == "anthropic":
        if not config.api_key:
            msg = "Anthropic API key is required"
            raise ValueError(msg)

        return AnthropicProvider(
            api_key=config.api_key,
            model=config.model,
        )

    if provider == "bedrock":
        return BedrockProvider(
            model=config.model,
        )

    msg = f"Unsupported LLM provider: {config.provider}"
    raise ValueError(msg)
