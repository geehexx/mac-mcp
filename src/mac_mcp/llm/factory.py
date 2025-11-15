"""Factory for creating LLM providers."""

from mac_mcp.config import LLMConfig, LLMProvider as LLMProviderEnum
from mac_mcp.llm.anthropic_provider import AnthropicProvider
from mac_mcp.llm.base import LLMProvider
from mac_mcp.llm.bedrock_provider import BedrockProvider


def create_llm_provider(config: LLMConfig) -> LLMProvider:
    """Create an LLM provider based on configuration.

    Args:
        config: LLM configuration

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider is invalid or credentials are missing
    """
    config.validate_credentials()

    if config.provider == LLMProviderEnum.ANTHROPIC:
        if not config.api_key:
            msg = "Anthropic API key is required"
            raise ValueError(msg)

        return AnthropicProvider(
            api_key=config.api_key,
            model=config.model,
        )

    if config.provider == LLMProviderEnum.BEDROCK:
        return BedrockProvider(
            model=config.model,
            region=config.aws_region,
            aws_access_key_id=config.aws_access_key_id,
            aws_secret_access_key=config.aws_secret_access_key,
            profile_name=config.aws_profile,
        )

    msg = f"Unsupported LLM provider: {config.provider}"
    raise ValueError(msg)
