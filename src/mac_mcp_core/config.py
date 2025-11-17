"""Configuration system for pluggable orchestration components.

This module provides a flexible configuration system for selecting
and configuring orchestration strategy implementations.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DecomposerType(str, Enum):
    """Available decomposer implementations."""

    SIMPLE = "simple"  # Reference: SimpleDecomposer (LLM-based)
    TEMPLATE = "template"  # Template-based matching
    DSPY = "dspy"  # DSPy-optimized decomposition
    MCP_REMOTE = "mcp_remote"  # External MCP service


class MatcherType(str, Enum):
    """Available matcher implementations."""

    BASIC = "basic"  # Reference: BasicMatcher (capability-based)
    LOAD_BALANCED = "load_balanced"  # Load-aware matching
    DSPY = "dspy"  # DSPy-optimized matching
    MCP_REMOTE = "mcp_remote"  # External MCP service


class SchedulerType(str, Enum):
    """Available scheduler implementations."""

    TOPOLOGICAL = "topological"  # Reference: TopologicalScheduler
    PRIORITY = "priority"  # Priority-based scheduling
    DEADLINE = "deadline"  # Deadline-aware scheduling
    DSPY = "dspy"  # DSPy-optimized scheduling
    MCP_REMOTE = "mcp_remote"  # External MCP service


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: str = Field(default="anthropic", description="LLM provider (anthropic, bedrock)")
    model: str = Field(default="claude-sonnet-4-5-20250929", description="Model identifier")
    api_key: str | None = Field(default=None, description="API key (can use ${ENV_VAR})")
    max_tokens: int = Field(default=4096, description="Maximum tokens for responses")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    timeout: float = Field(default=60.0, description="Request timeout in seconds")


class DecomposerConfig(BaseModel):
    """Decomposer configuration."""

    type: DecomposerType = Field(default=DecomposerType.SIMPLE)
    llm: LLMConfig | None = Field(default=None, description="LLM config for LLM-based decomposers")
    mcp_endpoint: str | None = Field(default=None, description="MCP endpoint for remote decomposers")
    options: dict[str, Any] = Field(default_factory=dict, description="Implementation-specific options")


class MatcherConfig(BaseModel):
    """Matcher configuration."""

    type: MatcherType = Field(default=MatcherType.BASIC)
    max_concurrent_tasks: int = Field(default=5, description="Max concurrent tasks per agent")
    mcp_endpoint: str | None = Field(default=None, description="MCP endpoint for remote matchers")
    options: dict[str, Any] = Field(default_factory=dict, description="Implementation-specific options")


class SchedulerConfig(BaseModel):
    """Scheduler configuration."""

    type: SchedulerType = Field(default=SchedulerType.TOPOLOGICAL)
    mcp_endpoint: str | None = Field(default=None, description="MCP endpoint for remote schedulers")
    options: dict[str, Any] = Field(default_factory=dict, description="Implementation-specific options")


class ServerConfig(BaseModel):
    """Server configuration."""

    event_store_path: str = Field(default="data/events.jsonl", description="Event store file path")
    heartbeat_interval: int = Field(default=30, description="Heartbeat interval in seconds")
    heartbeat_timeout: int = Field(default=90, description="Heartbeat timeout in seconds")


class AuthConfig(BaseModel):
    """Authentication configuration."""

    enabled: bool = Field(default=True, description="Enable authentication")
    api_keys: dict[str, str] = Field(default_factory=dict, description="API key to agent_id mapping")


class UIConfig(BaseModel):
    """UI configuration."""

    mode: str = Field(default="headless", description="UI mode (headless, tui, web)")
    theme: str = Field(default="dark", description="UI theme")


class OrchestratorConfig(BaseSettings):
    """Main orchestrator configuration with pluggable strategies.

    This configuration supports both local implementations (from mac_mcp_reference)
    and external MCP-based implementations (e.g., DSPy optimization flows).

    Example usage:
        ```yaml
        # config.yaml - Using reference implementations
        decomposer:
          type: simple
          llm:
            provider: anthropic
            model: claude-sonnet-4-5-20250929
            api_key: ${ANTHROPIC_API_KEY}
        matcher:
          type: basic
        scheduler:
          type: topological
        ```

        ```yaml
        # config.yaml - Using DSPy-optimized external services
        decomposer:
          type: mcp_remote
          mcp_endpoint: "coordination://decomposers/dspy_optimized"
        matcher:
          type: dspy
        scheduler:
          type: dspy
        ```
    """

    model_config = SettingsConfigDict(
        env_prefix="MAC_MCP_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    decomposer: DecomposerConfig = Field(default_factory=DecomposerConfig)
    matcher: MatcherConfig = Field(default_factory=MatcherConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
