"""Abstract interface for task scheduling.

This module defines the contract for task scheduling strategies,
allowing external systems to implement custom scheduling logic
(e.g., priority-based, deadline-aware, learned scheduling).
"""

from abc import ABC, abstractmethod
from typing import Any

from mac_mcp_core.domain.tasks import Task


class AbstractScheduler(ABC):
    """Abstract base class for task scheduling strategies.

    Implementations of this interface determine the order in which
    ready tasks should be processed. Scheduling strategies can consider:
    - Topological ordering (dependency satisfaction)
    - Task priorities
    - Deadlines and time constraints
    - Resource availability
    - Critical path optimization
    - Learned scheduling policies (e.g., via DSPy)

    Examples:
        - TopologicalScheduler: Basic dependency-ordered scheduling
        - PriorityScheduler: Priority-based scheduling
        - DeadlineScheduler: Deadline-aware scheduling
        - DSPyScheduler: Learned scheduling via optimization
        - MCPRemoteScheduler: Delegates to external MCP service
    """

    @abstractmethod
    async def get_ready_tasks(
        self,
        all_tasks: dict[str, Task],
        context: dict[str, Any] | None = None,
    ) -> list[Task]:
        """Get tasks ready for assignment, ordered by scheduling policy.

        Args:
            all_tasks: Dictionary of all tasks (task_id -> Task)
            context: Additional context for scheduling decision

        Returns:
            Ordered list of tasks ready for assignment

        Raises:
            ValueError: If scheduling logic encounters an error
        """

    @abstractmethod
    def get_implementation_name(self) -> str:
        """Get the name/identifier of this scheduler implementation.

        Returns:
            String identifier (e.g., "topological", "priority", "dspy_optimized")
        """
