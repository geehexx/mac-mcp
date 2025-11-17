"""Tests for authentication and authorization."""

import pytest

from mac_mcp.auth import APIKeyAuth, AuthConfig


@pytest.mark.unit
class TestAPIKeyAuth:
    """Test API key authentication."""

    async def test_generate_key(self) -> None:
        """Test API key generation."""
        auth = APIKeyAuth(AuthConfig())

        key = auth.generate_key("agent1")

        # Key should be non-empty string
        assert isinstance(key, str)
        assert len(key) > 0

        # Key should validate to agent1
        agent_id = await auth.validate(key)
        assert agent_id == "agent1"

    async def test_validate_valid_key(self) -> None:
        """Test validation of valid API key."""
        auth = APIKeyAuth(AuthConfig(api_keys={"test_key": "agent1"}))

        agent_id = await auth.validate("test_key")

        assert agent_id == "agent1"

    async def test_validate_invalid_key(self) -> None:
        """Test validation of invalid API key."""
        auth = APIKeyAuth(AuthConfig(api_keys={"test_key": "agent1"}))

        agent_id = await auth.validate("wrong_key")

        assert agent_id is None

    async def test_validate_when_disabled(self) -> None:
        """Test validation when auth is disabled."""
        auth = APIKeyAuth(AuthConfig(enabled=False))

        # Should allow any key when disabled
        agent_id = await auth.validate("any_key")

        assert agent_id == "anonymous"

    def test_revoke_key(self) -> None:
        """Test API key revocation."""
        config = AuthConfig(api_keys={"test_key": "agent1"})
        auth = APIKeyAuth(config)

        # Revoke key
        result = auth.revoke_key("test_key")

        assert result is True
        assert "test_key" not in auth._keys

    def test_revoke_nonexistent_key(self) -> None:
        """Test revoking non-existent key."""
        auth = APIKeyAuth(AuthConfig())

        result = auth.revoke_key("nonexistent")

        assert result is False

    def test_list_keys(self) -> None:
        """Test listing all API keys."""
        config = AuthConfig(api_keys={"key1": "agent1", "key2": "agent2"})
        auth = APIKeyAuth(config)

        keys = auth.list_keys()

        assert keys == {"key1": "agent1", "key2": "agent2"}

    async def test_multiple_keys_same_agent(self) -> None:
        """Test multiple keys for same agent."""
        auth = APIKeyAuth(AuthConfig())

        key1 = auth.generate_key("agent1")
        key2 = auth.generate_key("agent1")

        # Both keys should be different
        assert key1 != key2

        # Both should validate to agent1
        assert await auth.validate(key1) == "agent1"
        assert await auth.validate(key2) == "agent1"


@pytest.mark.unit
class TestAuthConfig:
    """Test authentication configuration."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = AuthConfig()

        assert config.enabled is True
        assert config.api_keys == {}
        assert config.key_length == 32

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = AuthConfig(
            enabled=False,
            api_keys={"test": "agent1"},
            key_length=64,
        )

        assert config.enabled is False
        assert config.api_keys == {"test": "agent1"}
        assert config.key_length == 64
