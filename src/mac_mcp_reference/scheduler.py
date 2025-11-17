"""Topological task scheduler implementation.

This module provides a simple dependency-ordered task scheduler
implementing the AbstractScheduler interface.
"""

from typing import Any

from mac_mcp_core.domain.tasks import Task, TaskState
from mac_mcp_core.interfaces.scheduler import AbstractScheduler


class TopologicalScheduler(AbstractScheduler):
    """Topological task scheduler.

    Schedules tasks in dependency order, ensuring all dependencies
    are satisfied before a task becomes ready for assignment.

    For production optimization, consider:
    - PriorityScheduler: Priority-based scheduling
    - DeadlineScheduler: Deadline-aware scheduling
    - CriticalPathScheduler: Critical path optimization
    - DSPyScheduler: Learned scheduling via optimization
    - MCPRemoteScheduler: Delegate to external MCP service
    """

    async def get_ready_tasks(
        self,
        all_tasks: dict[str, Task],
        context: dict[str, Any] | None = None,
    ) -> list[Task]:
        """Get tasks ready for assignment in topological order.

        Args:
            all_tasks: Dictionary of all tasks
            context: Additional context (ignored in basic implementation)

        Returns:
            Ordered list of tasks ready for assignment
        """
        ready: list[Task] = []

        for task in all_tasks.values():
            if task.state != TaskState.PENDING:
                continue

            # Check if all dependencies are satisfied
            deps_satisfied = all(
                all_tasks.get(dep_id, Task(id=dep_id, goal_id="", description="")).state
                == TaskState.SUCCESS
                for dep_id in task.dependencies
            )

            if deps_satisfied:
                ready.append(task)

        # Could add priority sorting here if needed
        # For now, just return in arbitrary order
        return ready

    def get_implementation_name(self) -> str:
        """Get the implementation name."""
        return "topological"
