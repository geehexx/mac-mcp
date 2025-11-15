"""Configuration management for MAC MCP Server.

This module provides a type-safe configuration system supporting:
- Environment variables
- YAML configuration files
- Pydantic validation
- Multiple LLM provider configurations
"""

from enum import Enum
from pathlib import Path
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers for goal decomposition."""

    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LLMConfig(BaseSettings):
    """LLM provider configuration.

    Attributes:
        provider: LLM provider to use (anthropic or bedrock)
        model: Model identifier (e.g., claude-sonnet-4-5-20250929)
        api_key: API key for Anthropic (only for anthropic provider)
        aws_region: AWS region for Bedrock (only for bedrock provider)
        aws_access_key_id: AWS access key ID (only for bedrock provider)
        aws_secret_access_key: AWS secret access key (only for bedrock provider)
        aws_profile: AWS profile name (optional, only for bedrock provider)
        max_tokens: Maximum tokens for LLM responses
        temperature: Temperature for LLM sampling (0.0-1.0)
    """

    provider: LLMProvider = Field(
        default=LLMProvider.ANTHROPIC,
        description="LLM provider (anthropic or bedrock)",
    )
    model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Model identifier",
    )

    # Anthropic API configuration
    api_key: str | None = Field(
        default=None,
        description="Anthropic API key (for anthropic provider)",
    )

    # AWS Bedrock configuration
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region for Bedrock",
    )
    aws_access_key_id: str | None = Field(
        default=None,
        description="AWS access key ID",
    )
    aws_secret_access_key: str | None = Field(
        default=None,
        description="AWS secret access key",
    )
    aws_profile: str | None = Field(
        default=None,
        description="AWS profile name (optional)",
    )

    # LLM parameters
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=200000,
        description="Maximum tokens for LLM responses",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature for LLM sampling",
    )

    model_config = SettingsConfigDict(
        env_prefix="MAC_LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("provider", mode="before")
    @classmethod
    def validate_provider(cls, v: Any) -> LLMProvider:
        """Validate and convert provider string to enum."""
        if isinstance(v, str):
            return LLMProvider(v.lower())
        return v

    def validate_credentials(self) -> None:
        """Validate that required credentials are present for the provider.

        Raises:
            ValueError: If required credentials are missing
        """
        if self.provider == LLMProvider.ANTHROPIC and not self.api_key:
            msg = "ANTHROPIC_API_KEY or MAC_LLM_API_KEY must be set for Anthropic provider"
            raise ValueError(msg)

        if self.provider == LLMProvider.BEDROCK:
            # AWS SDK can use default credential chain, so we don't strictly require keys
            # but at least one credential method should be available
            has_keys = self.aws_access_key_id and self.aws_secret_access_key
            has_profile = self.aws_profile
            if not (has_keys or has_profile):
                # Will fall back to AWS default credential chain (env, ~/.aws/credentials, IAM role)
                pass


class ServerConfig(BaseSettings):
    """MCP server configuration.

    Attributes:
        host: Server host (for HTTP mode)
        port: Server port (for HTTP mode)
        transport: Transport mode (stdio or http)
        event_store_path: Path to event store file
        max_agents: Maximum number of concurrent agents
        heartbeat_interval: Expected heartbeat interval in seconds
        heartbeat_timeout: Heartbeat timeout in seconds
    """

    host: str = Field(
        default="127.0.0.1",
        description="Server host",
    )
    port: int = Field(
        default=3000,
        ge=1,
        le=65535,
        description="Server port",
    )
    transport: str = Field(
        default="stdio",
        description="Transport mode (stdio or http)",
    )
    event_store_path: Path = Field(
        default=Path("data/events.jsonl"),
        description="Path to event store file",
    )
    max_agents: int = Field(
        default=100,
        ge=1,
        description="Maximum concurrent agents",
    )
    heartbeat_interval: int = Field(
        default=30,
        ge=1,
        description="Expected heartbeat interval in seconds",
    )
    heartbeat_timeout: int = Field(
        default=90,
        ge=1,
        description="Heartbeat timeout in seconds",
    )

    model_config = SettingsConfigDict(
        env_prefix="MAC_SERVER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class UIConfig(BaseSettings):
    """User interface configuration.

    Attributes:
        mode: UI mode (headless, tui, web)
        refresh_interval: UI refresh interval in seconds
        theme: Color theme (dark, light, auto)
        show_events: Show event stream in UI
        show_metrics: Show performance metrics
    """

    mode: str = Field(
        default="tui",
        description="UI mode (headless, tui, web)",
    )
    refresh_interval: float = Field(
        default=1.0,
        ge=0.1,
        description="UI refresh interval in seconds",
    )
    theme: str = Field(
        default="dark",
        description="Color theme (dark, light, auto)",
    )
    show_events: bool = Field(
        default=True,
        description="Show event stream in UI",
    )
    show_metrics: bool = Field(
        default=True,
        description="Show performance metrics",
    )

    model_config = SettingsConfigDict(
        env_prefix="MAC_UI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class LoggingConfig(BaseSettings):
    """Logging configuration.

    Attributes:
        level: Log level
        format: Log format string
        file: Log file path (optional)
        console: Enable console logging
    """

    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Log level",
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    file: Path | None = Field(
        default=None,
        description="Log file path",
    )
    console: bool = Field(
        default=True,
        description="Enable console logging",
    )

    model_config = SettingsConfigDict(
        env_prefix="MAC_LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class MACConfig(BaseSettings):
    """Main MAC MCP Server configuration.

    This is the root configuration object that composes all sub-configurations.

    Attributes:
        llm: LLM provider configuration
        server: MCP server configuration
        ui: User interface configuration
        logging: Logging configuration
    """

    llm: LLMConfig = Field(default_factory=LLMConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def from_yaml(cls, path: Path) -> "MACConfig":
        """Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            MACConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If YAML is invalid
        """
        import yaml

        if not path.exists():
            msg = f"Configuration file not found: {path}"
            raise FileNotFoundError(msg)

        with path.open() as f:
            data = yaml.safe_load(f)

        return cls.model_validate(data)

    def to_yaml(self, path: Path) -> None:
        """Save configuration to YAML file.

        Args:
            path: Path to save YAML configuration
        """
        import yaml

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        data = self.model_dump(mode="json")
        with path.open("w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def validate(self) -> None:
        """Validate the entire configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        self.llm.validate_credentials()

        # Ensure event store directory exists
        self.server.event_store_path.parent.mkdir(parents=True, exist_ok=True)


def load_config(config_path: Path | None = None) -> MACConfig:
    """Load MAC configuration from file or environment.

    Args:
        config_path: Optional path to YAML config file

    Returns:
        MACConfig instance

    Raises:
        ValueError: If configuration is invalid
    """
    if config_path and config_path.exists():
        config = MACConfig.from_yaml(config_path)
    else:
        # Load from environment variables
        config = MACConfig()

    # Validate configuration
    config.validate()

    return config
