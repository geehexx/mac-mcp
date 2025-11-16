"""Agent domain models.

This module defines the Agent entity and related types.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Valid statuses for an agent."""

    ACTIVE = "active"  # Agent is healthy and accepting work
    INACTIVE = "inactive"  # Agent has disconnected gracefully
    FAILED = "failed"  # Agent has failed (missed heartbeats)
    QUARANTINED = "quarantined"  # Agent is isolated due to repeated failures


class Agent(BaseModel):
    """Agent entity representing a worker in the system.

    Agents register with the orchestrator, claim tasks matching their
    capabilities, and report progress via heartbeats.

    Attributes:
        id: Unique agent identifier
        capabilities: List of capability tags
        metadata: Additional agent information (model, version, etc.)
        status: Current agent status
        registered_at: When the agent registered
        last_heartbeat: Most recent heartbeat timestamp
        current_tasks: Task IDs currently being executed
        task_history: Summary of task execution history
    """

    id: str
    capabilities: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: AgentStatus = AgentStatus.ACTIVE
    registered_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    last_heartbeat: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    current_tasks: list[str] = Field(default_factory=list)
    task_history: dict[str, int] = Field(
        default_factory=lambda: {
            "total": 0,
            "successful": 0,
            "failed": 0,
        }
    )

    model_config = {}

    def matches_capabilities(self, required: list[str]) -> bool:
        """Check if agent has required capabilities.

        Args:
            required: List of required capability tags

        Returns:
            True if agent has at least one matching capability
        """
        return bool(set(self.capabilities) & set(required))

    def update_heartbeat(self, current_tasks: list[str] | None = None) -> None:
        """Update agent heartbeat timestamp.

        Args:
            current_tasks: Optional list of current task IDs
        """
        self.last_heartbeat = datetime.now(UTC)
        if current_tasks is not None:
            self.current_tasks = current_tasks

    def is_healthy(self, timeout_seconds: int = 90) -> bool:
        """Check if agent is healthy based on heartbeat.

        Args:
            timeout_seconds: Heartbeat timeout in seconds

        Returns:
            True if last heartbeat is within timeout
        """
        if self.status != AgentStatus.ACTIVE:
            return False

        elapsed = (datetime.now(UTC) - self.last_heartbeat).total_seconds()
        return elapsed < timeout_seconds

    def can_accept_task(self, max_concurrent: int = 5) -> bool:
        """Check if agent can accept another task.

        Args:
            max_concurrent: Maximum concurrent tasks per agent

        Returns:
            True if agent is active and under task limit
        """
        return self.status == AgentStatus.ACTIVE and len(self.current_tasks) < max_concurrent

    def record_task_completion(self, success: bool) -> None:
        """Record task completion in history.

        Args:
            success: Whether the task succeeded
        """
        self.task_history["total"] += 1
        if success:
            self.task_history["successful"] += 1
        else:
            self.task_history["failed"] += 1

    def success_rate(self) -> float:
        """Calculate agent success rate.

        Returns:
            Success rate as a float between 0.0 and 1.0
        """
        total = self.task_history["total"]
        if total == 0:
            return 0.0
        return self.task_history["successful"] / total

    def should_quarantine(self, failure_threshold: int = 3) -> bool:
        """Check if agent should be quarantined.

        Args:
            failure_threshold: Number of recent failures before quarantine

        Returns:
            True if agent should be quarantined
        """
        # Simple heuristic: quarantine if last N tasks failed
        # In production, this would check recent failure rate
        failed = self.task_history["failed"]
        total = self.task_history["total"]

        if total < failure_threshold:
            return False

        recent_failures = failed
        return recent_failures >= failure_threshold
