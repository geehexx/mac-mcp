"""Abstract interface for agent-task matching.

This module defines the contract for agent matching strategies,
allowing external systems to implement sophisticated matching logic
(e.g., learned embeddings, workload balancing, cost optimization).
"""

from abc import ABC, abstractmethod
from typing import Any

from mac_mcp_core.domain.agents import Agent
from mac_mcp_core.domain.tasks import Task


class AbstractAgentMatcher(ABC):
    """Abstract base class for agent-task matching strategies.

    Implementations of this interface determine which agent should be
    assigned to a given task. Matching strategies can consider:
    - Capability requirements
    - Agent workload and availability
    - Historical performance
    - Cost optimization
    - Learned preferences (e.g., via DSPy)

    Examples:
        - BasicMatcher: Simple capability subset matching
        - LoadBalancedMatcher: Considers agent workload
        - DSPyMatcher: Learned matching via optimization
        - MCPRemoteMatcher: Delegates to external MCP service
    """

    @abstractmethod
    async def match_agent(
        self,
        task: Task,
        available_agents: list[Agent],
        context: dict[str, Any] | None = None,
    ) -> str | None:
        """Select the best agent for a given task.

        Args:
            task: Task requiring assignment
            available_agents: List of agents available for assignment
            context: Additional context for matching decision

        Returns:
            Agent ID of selected agent, or None if no suitable agent found

        Raises:
            ValueError: If matching logic encounters an error
        """

    @abstractmethod
    def get_implementation_name(self) -> str:
        """Get the name/identifier of this matcher implementation.

        Returns:
            String identifier (e.g., "basic", "load_balanced", "dspy_optimized")
        """
