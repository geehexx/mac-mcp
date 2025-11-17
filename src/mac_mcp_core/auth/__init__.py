"""Authentication and authorization for MAC MCP Server.

WARNING: v0.1.0 uses API key authentication which is suitable for alpha/development
only. Production deployments MUST use OAuth 2.1 (planned for v0.2.0).

Security Limitations in v0.1.0:
- API keys are bearer tokens (anyone with key has full access)
- No token expiration or rotation
- No rate limiting per key (coming in v0.2.0)
- Keys stored in config file (use secrets manager in production)

Migration Path:
- v0.1.0: API keys (alpha)
- v0.2.0: JWT with OAuth 2.1 (beta)
- v0.3.0: Full OAuth 2.1 with Resource Indicators (production)
"""

from mac_mcp_core.auth.api_key import APIKeyAuth, AuthConfig


__all__ = ["APIKeyAuth", "AuthConfig"]
