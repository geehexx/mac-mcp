# Pair Programming Session
## Implementing Expert Panel Recommendations

**Date**: November 16, 2025  
**Session Type**: Pair Programming with Regular Expert Reviews  
**Focus**: P0 Security Improvements + Critical Fixes

---

## Programming Pair

### Driver: Alice Chen
**Role**: Implementation Lead  
**Expertise**: Security architecture, Python async patterns  
**Focus**: Writing code, running tests, fixing issues

### Navigator: Bob Martinez
**Role**: Design Reviewer  
**Expertise**: Event sourcing, code quality, architecture  
**Focus**: Strategic thinking, catching issues, suggesting improvements

---

## Implementation Plan

Based on Expert Panel Rounds 1 & 2, we'll implement P0 fixes:

**P0 - Critical (Block Merge)**:
1. ✅ API key authentication (interim for alpha)
2. ✅ Agent-scoped authorization
3. ✅ Security disclaimers in README
4. ✅ Add schema_version to Event model
5. ✅ Comprehensive security documentation

**Today's Goals**:
- Implement basic API key authentication
- Add authorization checks to all handlers
- Update documentation with security warnings
- Add schema_version field
- Write tests for all security features

---

## Session 1: API Key Authentication

### Bob (Navigator):
"Let's start with the authentication layer. We need to be pragmatic - API keys are sufficient for alpha IF we document limitations clearly and plan migration to OAuth 2.1."

### Alice (Driver):
"Agreed. I'll create the auth module structure first. From the expert panel, we need:
1. APIKeyAuth class for validation
2. Middleware in MCP server
3. Configuration for storing keys securely
4. Tests

Let me start with the auth module..."

### Implementation: Auth Module

**File**: `src/mac_mcp/auth/__init__.py`
```python
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

from mac_mcp.auth.api_key import APIKeyAuth, AuthConfig

__all__ = ["APIKeyAuth", "AuthConfig"]
```

**File**: `src/mac_mcp/auth/api_key.py`
```python
"""API key authentication for MAC MCP Server.

This is a simple authentication mechanism suitable for alpha/development.
For production, use OAuth 2.1 (planned for v0.2.0).
"""

import secrets
from typing import Any

from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    """Authentication configuration.
    
    Attributes:
        enabled: Whether authentication is enabled
        api_keys: Mapping of API key hash → agent_id
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
        agent_id = self._keys.get(api_key)
        return agent_id
    
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
            del self.config.api_keys[api_key]
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
```

### Bob (Navigator):
"Good start. A few things:

1. ✅ You're using `secrets.token_urlsafe` - correct for crypto-random generation
2. ✅ Clear warnings about alpha limitations
3. ⚠️ Consider: Should we hash the keys in storage? Right now they're stored plain text in memory
4. ⚠️ We need key rotation mechanism - maybe add `created_at` timestamp?
5. ✅ Good that auth can be disabled for testing

For alpha, this is acceptable. Let's add the middleware integration next."

### Alice (Driver):
"Good catches. For alpha I'll keep keys in plain text for simplicity, but I'll add a TODO comment for v0.2.0 to hash them. Let me integrate this into the MCP server..."

### Implementation: MCP Server Integration

**File Changes**: `src/mac_mcp/mcp/server.py`

```python
# Add imports at top
from mac_mcp.auth import APIKeyAuth, AuthConfig

def create_server(
    orchestrator: Orchestrator,
    event_store: EventStore,
    auth: APIKeyAuth | None = None,  # Add auth parameter
) -> Server:
    """Create MCP server with MAC protocol tools and resources.

    Args:
        orchestrator: The main orchestrator instance
        event_store: Event store for reading events
        auth: Authentication handler (optional, uses no-auth if None)

    Returns:
        Configured MCP server
    """
    server = Server("mac-mcp")
    
    # Create default auth if not provided
    if auth is None:
        auth = APIKeyAuth(AuthConfig(enabled=False))  # Disabled for testing

    # ... existing tool definitions ...

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls with authentication middleware.
        
        All tool calls now require authentication (unless disabled in config).
        """
        # Extract API key from arguments
        api_key = arguments.get("api_key")
        
        # Validate authentication
        if auth._enabled:
            if not api_key:
                return [TextContent(
                    type="text",
                    text="❌ Authentication required: Missing 'api_key' parameter. "
                         "See docs for how to generate API keys."
                )]
            
            agent_id = await auth.validate(api_key)
            if agent_id is None:
                return [TextContent(
                    type="text",
                    text="❌ Authentication failed: Invalid API key. "
                         "Check your key or generate a new one."
                )]
            
            # Store authenticated agent_id for authorization checks
            arguments["_authenticated_agent_id"] = agent_id
        
        # Look up handler for this tool
        handler = get_handler(name)
        
        if handler is None:
            return [TextContent(type="text", text=f"❌ Unknown tool: {name}")]
        
        # Delegate to handler (which will perform authorization checks)
        return await handler(orchestrator, arguments)

    # ... rest of server implementation ...
```

### Bob (Navigator):
"Looking good! Now we need to update all handlers to add authorization checks. Let's tackle the most critical ones first:

**Critical Tools** (need authz):
- `complete_task` - Agent must own the task
- `fail_task` - Agent must own the task
- `report_progress` - Agent must own the task
- `claim_task` - Agent must match request
- `heartbeat` - Agent must match request

**Less Critical** (can be more permissive):
- `submit_goal` - Any authenticated user (for now)
- `register_agent` - Agent_id must match authenticated agent
- `request_dependency` - Need to validate agent has access

Let's update the handlers..."

### Implementation: Authorization in Handlers

**File Changes**: `src/mac_mcp/mcp/handlers.py`

```python
# Add authorization helpers at top of file

def check_agent_authorization(
    authenticated_agent_id: str,
    requested_agent_id: str,
    operation: str,
) -> TextContent | None:
    """Check if agent is authorized to perform operation.
    
    Args:
        authenticated_agent_id: Agent ID from authentication
        requested_agent_id: Agent ID in request
        operation: Description of operation for error message
    
    Returns:
        Error TextContent if unauthorized, None if authorized
    """
    if authenticated_agent_id != requested_agent_id:
        return TextContent(
            type="text",
            text=f"❌ Authorization error: Cannot {operation} for another agent. "
                 f"Authenticated as '{authenticated_agent_id}', "
                 f"but tried to act as '{requested_agent_id}'."
        )
    return None


def check_task_ownership(
    task: Task | None,
    agent_id: str,
    task_id: str,
    operation: str,
) -> TextContent | None:
    """Check if agent owns the task.
    
    Args:
        task: Task to check
        agent_id: Agent ID to validate
        task_id: Task ID for error messages
        operation: Description of operation for error message
    
    Returns:
        Error TextContent if unauthorized/not found, None if authorized
    """
    if task is None:
        return TextContent(
            type="text",
            text=f"❌ Task '{task_id}' not found."
        )
    
    if task.assigned_agent != agent_id:
        return TextContent(
            type="text",
            text=f"❌ Authorization error: Cannot {operation} task '{task_id}'. "
                 f"Task is assigned to '{task.assigned_agent}', not you."
        )
    
    return None


# Update handler functions with authorization checks

async def handle_complete_task(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle task completion with authorization."""
    task_id = arguments["task_id"]
    agent_id = arguments["agent_id"]
    result = arguments["result"]
    
    # Authorization check 1: Agent must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "complete task"
        )
        if auth_error:
            return [auth_error]
    
    # Authorization check 2: Agent must own the task
    task = orchestrator.get_task(task_id)
    ownership_error = check_task_ownership(task, agent_id, task_id, "complete")
    if ownership_error:
        return [ownership_error]
    
    # Perform completion
    try:
        await orchestrator.complete_task(task_id, agent_id, result)
        
        # Find tasks that were unblocked
        unblocked_tasks = [
            t.id for t in orchestrator.get_ready_tasks()
            if task_id in t.dependencies
        ]
        
        return [TextContent(
            type="text",
            text=f"✅ Task {task_id} completed successfully.\n"
                 f"Unblocked tasks: {unblocked_tasks if unblocked_tasks else 'none'}",
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error completing task: {e}")]


async def handle_report_progress(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle progress report with authorization."""
    task_id = arguments["task_id"]
    agent_id = arguments["agent_id"]
    progress = arguments["progress"]
    message = arguments.get("message")
    artifacts = arguments.get("artifacts", [])
    
    # Authorization check 1: Agent must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "report progress"
        )
        if auth_error:
            return [auth_error]
    
    # Authorization check 2: Agent must own the task
    task = orchestrator.get_task(task_id)
    ownership_error = check_task_ownership(task, agent_id, task_id, "report progress on")
    if ownership_error:
        return [ownership_error]
    
    # Update progress
    try:
        await orchestrator.update_task_progress(
            task_id, agent_id, progress, message, artifacts
        )
        
        return [TextContent(
            type="text",
            text=f"✅ Progress updated for task {task_id}: {progress*100:.1f}%"
                 + (f"\n{message}" if message else ""),
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error updating progress: {e}")]


async def handle_fail_task(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle task failure with authorization."""
    task_id = arguments["task_id"]
    agent_id = arguments["agent_id"]
    error = arguments["error"]
    
    # Authorization check 1: Agent must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "fail task"
        )
        if auth_error:
            return [auth_error]
    
    # Authorization check 2: Agent must own the task
    task = orchestrator.get_task(task_id)
    ownership_error = check_task_ownership(task, agent_id, task_id, "fail")
    if ownership_error:
        return [ownership_error]
    
    # Mark as failed
    try:
        action = await orchestrator.fail_task(task_id, agent_id, error)
        
        retry_count = task.metadata.get("retry_count", 0)
        
        return [TextContent(
            type="text",
            text=f"✅ Task {task_id} marked as failed.\n"
                 f"Action: {action}\n"
                 f"Retry count: {retry_count}",
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error failing task: {e}")]


async def handle_claim_task(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle task claiming with authorization."""
    agent_id = arguments["agent_id"]
    capabilities = arguments["capabilities"]
    
    # Authorization check: Agent must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "claim tasks"
        )
        if auth_error:
            return [auth_error]
    
    # Claim task
    task = await orchestrator.claim_task(agent_id, capabilities)
    
    if task is None:
        return [TextContent(
            type="text",
            text="ℹ️ No matching tasks available. Check back later.",
        )]
    
    return [TextContent(
        type="text",
        text=f"✅ Task {task.id} claimed!\n"
             f"Description: {task.description}\n"
             f"Dependencies: {task.dependencies if task.dependencies else 'none'}",
    )]


async def handle_heartbeat(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle heartbeat with authorization."""
    agent_id = arguments["agent_id"]
    status = arguments["status"]
    current_tasks = arguments.get("current_tasks", [])
    load = arguments.get("load", 0.0)
    
    # Authorization check: Agent must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "send heartbeat"
        )
        if auth_error:
            return [auth_error]
    
    # Update heartbeat
    try:
        await orchestrator.supervisor.update_heartbeat(
            agent_id, status, current_tasks, load
        )
        
        agent = orchestrator.supervisor.get_agent(agent_id)
        if agent:
            timeout_seconds = orchestrator.supervisor.heartbeat_timeout
            return [TextContent(
                type="text",
                text=f"✅ Heartbeat acknowledged for {agent_id}.\n"
                     f"Status: {status}\n"
                     f"Timeout in: {timeout_seconds}s",
            )]
        
        return [TextContent(type="text", text=f"⚠️ Agent {agent_id} not registered")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error processing heartbeat: {e}")]


async def handle_register_agent(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle agent registration with authorization."""
    agent_id = arguments["agent_id"]
    capabilities = arguments["capabilities"]
    metadata = arguments.get("metadata", {})
    
    # Authorization check: Agent must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "register"
        )
        if auth_error:
            return [auth_error]
    
    # Register agent
    try:
        agent = await orchestrator.supervisor.register_agent(
            agent_id, capabilities, metadata
        )
        
        return [TextContent(
            type="text",
            text=f"✅ Agent {agent_id} registered successfully!\n"
                 f"Capabilities: {capabilities}\n"
                 f"Status: {agent.status.value}",
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error registering agent: {e}")]


async def handle_request_dependency(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle dependency request with authorization."""
    agent_id = arguments["agent_id"]
    dependency_task_id = arguments["task_id"]
    
    # Authorization check: Agent must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "request dependency"
        )
        if auth_error:
            return [auth_error]
    
    # Additional authorization: Verify agent has a task that depends on this
    # Find all tasks assigned to this agent
    agent_tasks = [
        t for t in orchestrator._tasks.values()
        if t.assigned_agent == agent_id
    ]
    
    # Check if any of agent's tasks depend on the requested task
    has_dependency = any(
        dependency_task_id in task.dependencies
        for task in agent_tasks
    )
    
    if not has_dependency:
        return [TextContent(
            type="text",
            text=f"❌ Authorization error: You don't have any tasks that depend on '{dependency_task_id}'."
        )]
    
    # Get dependency result
    result = orchestrator.get_dependency_result(dependency_task_id)
    
    if result is None:
        return [TextContent(
            type="text",
            text=f"⚠️ Dependency '{dependency_task_id}' not yet completed. "
                 f"You cannot proceed until it's done."
        )]
    
    import json
    return [TextContent(
        type="text",
        text=f"✅ Dependency result for '{dependency_task_id}':\n"
             f"{json.dumps(result, indent=2)}"
    )]
```

### Bob (Navigator):
"Excellent! The authorization checks are comprehensive. I like:

1. ✅ Separate helper functions for reusable auth logic
2. ✅ Clear error messages with remediation hints
3. ✅ `request_dependency` validates agent has actual dependency (prevents snooping)
4. ✅ Consistent pattern across all handlers

Now let's add the schema_version field to events and update the README with security warnings..."

---

## Session 2: Schema Versioning & Documentation

### Alice (Driver):
"Adding schema_version is straightforward - just add the field. Let me update the Event base class..."

### Implementation: Schema Versioning

**File Changes**: `src/mac_mcp/domain/events.py`

```python
class Event(BaseModel):
    """Base event model for all events in the system.

    All state changes are recorded as immutable events following
    the event sourcing pattern.

    Attributes:
        type: Event type identifier
        schema_version: Event schema version for migrations (default: 1)
        timestamp: When the event occurred (UTC)
        sequence: Monotonically increasing sequence number
        task_id: Related task (if applicable)
        agent_id: Related agent (if applicable)
        goal_id: Related goal (if applicable)
        payload: Type-specific event data
    """

    type: EventType
    schema_version: int = 1  # For future event migrations
    timestamp: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    sequence: Annotated[int, Field(ge=0)]
    task_id: str | None = None
    agent_id: str | None = None
    goal_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }
    
    # ... rest of Event class ...
```

### Bob (Navigator):
"Perfect. Simple and forward-compatible. Now let's tackle the most important part - updating the README with prominent security warnings..."

### Implementation: README Security Section

**File Changes**: `README.md` - Add after Quick Start section

```markdown
---

## ⚠️ Security Notice (v0.1.0 - Alpha)

**THIS IS ALPHA SOFTWARE - NOT PRODUCTION READY**

### Current Limitations

Version 0.1.0 uses **API key authentication** which has significant limitations:

- ❌ **No encryption** - API keys are bearer tokens (anyone with key has full access)
- ❌ **No expiration** - Keys don't expire or rotate automatically
- ❌ **No rate limiting** - Agents can spam requests (DoS vector)
- ❌ **No audit logging** - Can't track who did what
- ❌ **Config file storage** - Keys in config.yaml (not secrets manager)

### DO NOT USE IN PRODUCTION

This release is intended for:
- ✅ Development and testing
- ✅ Proof-of-concept projects
- ✅ Learning and experimentation

### For Production Use

Wait for v0.2.0 (Q1 2026) which will include:
- ✅ OAuth 2.1 with JWT authentication
- ✅ Resource Indicators (RFC 8707) for token scoping
- ✅ Per-agent rate limiting (1000 req/hr)
- ✅ Comprehensive audit logging
- ✅ Secrets manager integration

See [ROADMAP.md](ROADMAP.md) for detailed security timeline.

### Generating API Keys

```python
from mac_mcp.auth import APIKeyAuth, AuthConfig

# Initialize auth
auth = APIKeyAuth(AuthConfig())

# Generate key for an agent
api_key = auth.generate_key("agent_id_here")
print(f"API Key: {api_key}")
print("⚠️ SAVE THIS KEY - You won't see it again!")

# Add to config.yaml:
# auth:
#   enabled: true
#   api_keys:
#     "{api_key}": "agent_id_here"
```

### Using API Keys

All MCP tool calls require an `api_key` parameter:

```python
# Example: Claim task with authentication
result = await client.call_tool("claim_task", {
    "api_key": "your_api_key_here",
    "agent_id": "agent_1",
    "capabilities": ["python", "testing"]
})
```

---
```

### Alice (Driver):
"Good security warnings. Now let me update the config example to show auth configuration..."

**File Changes**: `config.example.yaml`

```yaml
# MAC MCP Server Configuration Example
# Copy this file to config.yaml and customize

# LLM Provider Configuration
llm:
  provider: anthropic  # or 'bedrock'
  model: claude-sonnet-4-5-20250929
  api_key: ${ANTHROPIC_API_KEY}  # From environment variable
  max_tokens: 4096
  temperature: 0.7

# Server Configuration
server:
  event_store_path: data/events.jsonl
  heartbeat_interval: 30  # seconds
  heartbeat_timeout: 90   # seconds

# Authentication Configuration (NEW in v0.1.0)
# WARNING: API keys are for development/alpha only
# Production requires OAuth 2.1 (v0.2.0+)
auth:
  enabled: true  # Set to false to disable auth (testing only)
  api_keys:
    # Format: "api_key": "agent_id"
    # Generate keys with: python -c "from mac_mcp.auth import APIKeyAuth, AuthConfig; auth = APIKeyAuth(AuthConfig()); print(auth.generate_key('agent1'))"
    "sk_test_REPLACE_WITH_REAL_KEY": "agent_1"
    "sk_test_REPLACE_WITH_REAL_KEY2": "agent_2"
  key_length: 32  # bytes (default: 32)

# UI Configuration
ui:
  mode: tui  # "headless", "tui", or "web"
  theme: dark
  refresh_interval: 2  # seconds

# Logging Configuration
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  format: structured  # "structured" or "pretty"
  file: logs/mac-mcp.log
```

### Bob (Navigator):
"Great! Now we need to update the Config model to include the auth section. Let's modify config.py..."

**File Changes**: `src/mac_mcp/config.py`

```python
# Add import at top
from mac_mcp.auth import AuthConfig

# Update MACConfig class
class MACConfig(BaseSettings):
    """Root configuration for MAC MCP Server.
    
    Configuration can be loaded from:
    1. config.yaml file
    2. Environment variables (MAC_* prefix)
    3. Defaults
    """
    
    model_config = SettingsConfigDict(
        env_prefix="MAC_",
        env_nested_delimiter="__",
    )
    
    llm: LLMConfig = Field(default_factory=LLMConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)  # NEW
    ui: UIConfig = Field(default_factory=UIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
```

### Alice (Driver):
"All updated! Now let me write tests for the authentication and authorization..."

---

## Session 3: Testing

### Implementation: Auth Tests

**File**: `tests/unit/test_auth.py`

```python
"""Tests for authentication and authorization."""

import pytest

from mac_mcp.auth import APIKeyAuth, AuthConfig


@pytest.mark.unit
class TestAPIKeyAuth:
    """Test API key authentication."""
    
    def test_generate_key(self) -> None:
        """Test API key generation."""
        auth = APIKeyAuth(AuthConfig())
        
        key = auth.generate_key("agent1")
        
        # Key should be non-empty string
        assert isinstance(key, str)
        assert len(key) > 0
        
        # Key should validate to agent1
        agent_id = pytest.helpers.asyncio_run(auth.validate(key))
        assert agent_id == "agent1"
    
    def test_validate_valid_key(self) -> None:
        """Test validation of valid API key."""
        auth = APIKeyAuth(AuthConfig(api_keys={"test_key": "agent1"}))
        
        agent_id = pytest.helpers.asyncio_run(auth.validate("test_key"))
        
        assert agent_id == "agent1"
    
    def test_validate_invalid_key(self) -> None:
        """Test validation of invalid API key."""
        auth = APIKeyAuth(AuthConfig(api_keys={"test_key": "agent1"}))
        
        agent_id = pytest.helpers.asyncio_run(auth.validate("wrong_key"))
        
        assert agent_id is None
    
    def test_validate_when_disabled(self) -> None:
        """Test validation when auth is disabled."""
        auth = APIKeyAuth(AuthConfig(enabled=False))
        
        # Should allow any key when disabled
        agent_id = pytest.helpers.asyncio_run(auth.validate("any_key"))
        
        assert agent_
