"""AWS Bedrock provider implementation."""

import asyncio
import json
from typing import Any

import boto3

from mac_mcp.llm.base import LLMProvider


class BedrockProvider(LLMProvider):
    """LLM provider using AWS Bedrock.

    Attributes:
        client: Boto3 Bedrock Runtime client
        model: Model identifier
    """

    def __init__(
        self,
        model: str = "anthropic.claude-sonnet-4-5-20250929-v1:0",
        region: str = "us-east-1",
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        profile_name: str | None = None,
    ) -> None:
        """Initialize Bedrock provider.

        Args:
            model: Bedrock model identifier
            region: AWS region
            aws_access_key_id: AWS access key ID (optional)
            aws_secret_access_key: AWS secret access key (optional)
            profile_name: AWS profile name (optional)
        """
        self.model = model

        # Create session with credentials
        session_kwargs: dict[str, Any] = {"region_name": region}
        if profile_name:
            session_kwargs["profile_name"] = profile_name
        elif aws_access_key_id and aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = aws_access_key_id
            session_kwargs["aws_secret_access_key"] = aws_secret_access_key

        session = boto3.Session(**session_kwargs)
        self.client = session.client("bedrock-runtime")

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: float = 60.0,
    ) -> str:
        """Generate text using AWS Bedrock with timeout.

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
        # Prepare request body for Claude models on Bedrock
        # Note: Bedrock uses a slightly different format than Anthropic API
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        # Wrap synchronous API call in executor with timeout
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.invoke_model,
                    modelId=self.model,
                    body=json.dumps(request_body),
                ),
                timeout=timeout,
            )

            # Parse response
            response_body = json.loads(response["body"].read())

            # Extract text from response
            if response_body.get("content"):
                return response_body["content"][0]["text"]
            return ""

        except TimeoutError as e:
            msg = f"AWS Bedrock API call exceeded timeout of {timeout}s"
            # Use standard TimeoutError which accepts message, not asyncio.TimeoutError
            raise TimeoutError(msg) from e

    def get_model_name(self) -> str:
        """Get the model identifier.

        Returns:
            Model name string
        """
        return self.model
