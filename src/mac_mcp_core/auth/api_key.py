"""API key authentication for MAC MCP Server.

This is a simple authentication mechanism suitable for alpha/development.
For production, use OAuth 2.1 (planned for v0.2.0).
"""

import secrets

from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    """Authentication configuration.

    Attributes:
        enabled: Whether authentication is enabled
        api_keys: Mapping of API key → agent_id
        key_length: Length of generated API keys in bytes (default: 32)
    """

    enabled: bool = True
    api_keys: dict[str, str] = Field(default_factory=dict)
    key_length: int = 32

    model_config = {
        "frozen": False,  # Allow mutation for adding keys
    }


class APIKeyAuth:
    """API key authentication handler.

    Provides simple bearer token authentication using API keys.

    Security Notes:
    - Keys should be cryptographically random (use secrets.token_urlsafe)
    - Keys should be transmitted over TLS only
    - Keys should have per-agent scope (one key = one agent)
    - Keys should be rotated regularly

    Example:
        ```python
        auth = APIKeyAuth(config)

        # Validate request
        agent_id = await auth.validate("sk_test_abc123...")
        if agent_id is None:
            return error_response("Invalid API key")
        ```
    """

    def __init__(self, config: AuthConfig) -> None:
        """Initialize auth handler.

        Args:
            config: Authentication configuration
        """
        self.config = config
        self._enabled = config.enabled
        self._keys = config.api_keys  # key → agent_id mapping

    async def validate(self, api_key: str) -> str | None:
        """Validate API key and return associated agent_id.

        Args:
            api_key: API key from request

        Returns:
            agent_id if valid, None if invalid
        """
        if not self._enabled:
            # Auth disabled - allow any request (development only!)
            return "anonymous"

        # Look up agent_id by key
        return self._keys.get(api_key)

    def generate_key(self, agent_id: str) -> str:
        """Generate a new API key for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Generated API key (store this - it won't be retrievable later)
        """
        # Generate cryptographically random key
        api_key = secrets.token_urlsafe(self.config.key_length)

        # Store mapping
        self._keys[api_key] = agent_id
        self.config.api_keys[api_key] = agent_id

        return api_key

    def revoke_key(self, api_key: str) -> bool:
        """Revoke an API key.

        Args:
            api_key: API key to revoke

        Returns:
            True if key was revoked, False if key didn't exist
        """
        if api_key in self._keys:
            del self._keys[api_key]
            # Note: self._keys and self.config.api_keys reference the same dict
            # so we only need to delete once
            return True
        return False

    def list_keys(self) -> dict[str, str]:
        """List all active API keys.

        Returns:
            Mapping of key → agent_id

        Warning:
            This exposes API keys. Use carefully and only for admin operations.
        """
        return self._keys.copy()
