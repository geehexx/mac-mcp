"""Anthropic API provider implementation."""

from anthropic import Anthropic

from mac_mcp.llm.base import LLMProvider


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
    ) -> str:
        """Generate text using Anthropic API.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text

        Raises:
            Exception: If API call fails
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        # Extract text from response
        if response.content:
            return response.content[0].text
        return ""

    def get_model_name(self) -> str:
        """Get the model identifier.

        Returns:
            Model name string
        """
        return self.model
