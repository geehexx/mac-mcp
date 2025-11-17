"""Factory for creating orchestration component implementations.

This module provides a factory pattern for instantiating the correct
implementation based on configuration.
"""

from mac_mcp_core.config import (
    DecomposerConfig,
    DecomposerType,
    MatcherConfig,
    MatcherType,
    SchedulerConfig,
    SchedulerType,
)
from mac_mcp_core.interfaces.decomposer import AbstractGoalDecomposer
from mac_mcp_core.interfaces.matcher import AbstractAgentMatcher
from mac_mcp_core.interfaces.scheduler import AbstractScheduler
from mac_mcp_reference.decomposer import SimpleDecomposer
from mac_mcp_reference.llm.factory import create_llm_provider
from mac_mcp_reference.matcher import BasicMatcher
from mac_mcp_reference.scheduler import TopologicalScheduler


class ComponentFactory:
    """Factory for creating orchestration components.

    This factory encapsulates the logic for instantiating the correct
    implementation based on configuration, making it easy to switch
    between local and remote implementations.
    """

    @staticmethod
    def create_decomposer(config: DecomposerConfig) -> AbstractGoalDecomposer:
        """Create a decomposer implementation based on configuration.

        Args:
            config: Decomposer configuration

        Returns:
            AbstractGoalDecomposer implementation

        Raises:
            ValueError: If decomposer type is not supported or configuration is invalid
        """
        if config.type == DecomposerType.SIMPLE:
            if not config.llm:
                msg = "LLM configuration required for simple decomposer"
                raise ValueError(msg)

            llm_provider = create_llm_provider(config.llm)
            return SimpleDecomposer(
                llm_provider=llm_provider,
                max_tokens=config.llm.max_tokens,
                temperature=config.llm.temperature,
            )

        if config.type == DecomposerType.TEMPLATE:
            # Placeholder for template-based decomposer
            msg = "Template decomposer not yet implemented"
            raise NotImplementedError(msg)

        if config.type == DecomposerType.DSPY:
            # Placeholder for DSPy-optimized decomposer
            msg = "DSPy decomposer not yet implemented. See ROADMAP.md for implementation guide."
            raise NotImplementedError(msg)

        if config.type == DecomposerType.MCP_REMOTE:
            # Placeholder for MCP remote decomposer
            msg = "MCP remote decomposer not yet implemented. See ROADMAP.md for implementation guide."
            raise NotImplementedError(msg)

        msg = f"Unknown decomposer type: {config.type}"
        raise ValueError(msg)

    @staticmethod
    def create_matcher(config: MatcherConfig) -> AbstractAgentMatcher:
        """Create a matcher implementation based on configuration.

        Args:
            config: Matcher configuration

        Returns:
            AbstractAgentMatcher implementation

        Raises:
            ValueError: If matcher type is not supported
        """
        if config.type == MatcherType.BASIC:
            return BasicMatcher(max_concurrent_tasks=config.max_concurrent_tasks)

        if config.type == MatcherType.LOAD_BALANCED:
            msg = "Load balanced matcher not yet implemented"
            raise NotImplementedError(msg)

        if config.type == MatcherType.DSPY:
            msg = "DSPy matcher not yet implemented. See ROADMAP.md for implementation guide."
            raise NotImplementedError(msg)

        if config.type == MatcherType.MCP_REMOTE:
            msg = "MCP remote matcher not yet implemented. See ROADMAP.md for implementation guide."
            raise NotImplementedError(msg)

        msg = f"Unknown matcher type: {config.type}"
        raise ValueError(msg)

    @staticmethod
    def create_scheduler(config: SchedulerConfig) -> AbstractScheduler:
        """Create a scheduler implementation based on configuration.

        Args:
            config: Scheduler configuration

        Returns:
            AbstractScheduler implementation

        Raises:
            ValueError: If scheduler type is not supported
        """
        if config.type == SchedulerType.TOPOLOGICAL:
            return TopologicalScheduler()

        if config.type == SchedulerType.PRIORITY:
            msg = "Priority scheduler not yet implemented"
            raise NotImplementedError(msg)

        if config.type == SchedulerType.DEADLINE:
            msg = "Deadline scheduler not yet implemented"
            raise NotImplementedError(msg)

        if config.type == SchedulerType.DSPY:
            msg = "DSPy scheduler not yet implemented. See ROADMAP.md for implementation guide."
            raise NotImplementedError(msg)

        if config.type == SchedulerType.MCP_REMOTE:
            msg = "MCP remote scheduler not yet implemented. See ROADMAP.md for implementation guide."
            raise NotImplementedError(msg)

        msg = f"Unknown scheduler type: {config.type}"
        raise ValueError(msg)
