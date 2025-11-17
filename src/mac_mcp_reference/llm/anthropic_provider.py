"""Anthropic API provider implementation."""

import asyncio

from anthropic import Anthropic

from mac_mcp_core.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """LLM provider using Anthropic's API.

    Attributes:
        client: Anthropic API client
        model: Model identifier
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929") -> None:
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Claude model identifier
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: float = 60.0,
    ) -> str:
        """Generate text using Anthropic API with timeout.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout: Timeout in seconds (default: 60s)

        Returns:
            Generated text

        Raises:
            asyncio.TimeoutError: If API call exceeds timeout
            Exception: If API call fails
        """
        # Wrap synchronous API call in executor with timeout
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.messages.create,
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                ),
                timeout=timeout,
            )

            # Extract text from response
            if response.content:
                return response.content[0].text
            return ""  # noqa: TRY300

        except TimeoutError as e:
            msg = f"Anthropic API call exceeded timeout of {timeout}s"
            raise TimeoutError(msg) from e

    def get_model_name(self) -> str:
        """Get the model identifier.

        Returns:
            Model name string
        """
        return self.model
