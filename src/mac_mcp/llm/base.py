"""Base LLM provider interface."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    This defines the interface that all LLM providers must implement
    for goal decomposition functionality.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate text completion from the LLM.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Generated text completion

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model identifier.

        Returns:
            Model name string
        """
        pass
