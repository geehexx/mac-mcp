"""Abstract interface for goal decomposition.

This module defines the contract for goal decomposition strategies,
allowing external systems (e.g., DSPy-optimized workflows) to replace
the default decomposition logic.
"""

from abc import ABC, abstractmethod
from typing import Any

from mac_mcp_core.domain.tasks import TaskDAG


class AbstractGoalDecomposer(ABC):
    """Abstract base class for goal decomposition strategies.

    Implementations of this interface analyze high-level goals and
    decompose them into executable task DAGs. The decomposition logic
    can range from simple rule-based systems to sophisticated LLM-powered
    or DSPy-optimized flows.

    Examples:
        - SimpleDecomposer: Basic LLM-based decomposition
        - DSPyDecomposer: Self-optimized decomposition via DSPy
        - TemplateDecomposer: Pattern-matching for common workflows
        - MCPRemoteDecomposer: Delegates to external MCP service
    """

    @abstractmethod
    async def decompose_goal(
        self,
        goal_id: str,
        user_prompt: str,
        context: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> TaskDAG:
        """Decompose a high-level goal into an executable task DAG.

        Args:
            goal_id: Unique identifier for the goal
            user_prompt: Natural language description of the goal
            context: Additional context (e.g., language, framework, domain)
            constraints: Constraints on decomposition (e.g., max_tasks, deadline)

        Returns:
            TaskDAG: Directed acyclic graph of tasks with dependencies

        Raises:
            ValueError: If decomposition fails or produces invalid DAG
            TimeoutError: If decomposition exceeds timeout
        """

    @abstractmethod
    def get_implementation_name(self) -> str:
        """Get the name/identifier of this decomposer implementation.

        Returns:
            String identifier (e.g., "simple", "dspy_optimized", "mcp_remote")
        """
