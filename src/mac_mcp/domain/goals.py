"""Goal domain models.

This module defines the Goal entity and its lifecycle.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field


class GoalState(str, Enum):
    """Valid states for a goal.

    Goals go through these states as they are decomposed and executed.
    """

    SUBMITTED = "SUBMITTED"  # Goal received, pending decomposition
    DECOMPOSING = "DECOMPOSING"  # Being decomposed into tasks
    READY = "READY"  # Tasks created, ready for execution
    EXECUTING = "EXECUTING"  # Tasks being executed by agents
    COMPLETED = "COMPLETED"  # All tasks completed successfully
    FAILED = "FAILED"  # One or more critical tasks failed


class Goal(BaseModel):
    """Goal entity representing a high-level objective.

    Goals are submitted to the orchestrator, decomposed into tasks,
    and tracked until completion.

    Attributes:
        id: Unique goal identifier
        description: Human-readable goal description
        state: Current goal state
        context: Additional context for decomposition
        constraints: Constraints on execution (deadline, resources, etc.)
        submitted_at: When the goal was submitted
        updated_at: When the goal was last updated
        task_ids: IDs of tasks created from this goal
        metadata: Additional goal-specific data
        result: Aggregated result when completed
    """

    id: str
    description: str
    state: GoalState = GoalState.SUBMITTED
    context: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    submitted_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    updated_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    task_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None

    model_config = {}

    def can_transition_to(self, new_state: GoalState) -> bool:
        """Check if transition to new state is valid.

        Args:
            new_state: Target state

        Returns:
            True if transition is allowed
        """
        transitions: dict[GoalState, set[GoalState]] = {
            GoalState.SUBMITTED: {GoalState.DECOMPOSING},
            GoalState.DECOMPOSING: {GoalState.READY, GoalState.FAILED},
            GoalState.READY: {GoalState.EXECUTING},
            GoalState.EXECUTING: {GoalState.COMPLETED, GoalState.FAILED},
            GoalState.COMPLETED: set(),  # Terminal
            GoalState.FAILED: set(),  # Terminal
        }

        return new_state in transitions.get(self.state, set())

    def start_decomposition(self) -> None:
        """Mark goal as being decomposed.

        Raises:
            ValueError: If not in SUBMITTED state
        """
        if self.state != GoalState.SUBMITTED:
            msg = f"Cannot start decomposition from {self.state} state"
            raise ValueError(msg)

        self.state = GoalState.DECOMPOSING
        self.updated_at = datetime.now(UTC)

    def mark_ready(self, task_ids: list[str]) -> None:
        """Mark goal as ready for execution.

        Args:
            task_ids: List of task IDs created from decomposition

        Raises:
            ValueError: If not in DECOMPOSING state or no tasks
        """
        if self.state != GoalState.DECOMPOSING:
            msg = f"Cannot mark ready from {self.state} state"
            raise ValueError(msg)

        if not task_ids:
            msg = "Cannot mark ready without tasks"
            raise ValueError(msg)

        self.state = GoalState.READY
        self.task_ids = task_ids
        self.updated_at = datetime.now(UTC)

    def start_execution(self) -> None:
        """Mark goal as executing.

        Raises:
            ValueError: If not in READY state
        """
        if self.state != GoalState.READY:
            msg = f"Cannot start execution from {self.state} state"
            raise ValueError(msg)

        self.state = GoalState.EXECUTING
        self.updated_at = datetime.now(UTC)

    def complete(self, result: dict[str, Any]) -> None:
        """Mark goal as completed.

        Args:
            result: Aggregated result from all tasks

        Raises:
            ValueError: If not in EXECUTING state
        """
        if self.state != GoalState.EXECUTING:
            msg = f"Cannot complete from {self.state} state"
            raise ValueError(msg)

        self.state = GoalState.COMPLETED
        self.result = result
        self.updated_at = datetime.now(UTC)

    def fail(self, reason: str) -> None:
        """Mark goal as failed.

        Args:
            reason: Failure reason

        Raises:
            ValueError: If already in terminal state
        """
        if self.state in {GoalState.COMPLETED, GoalState.FAILED}:
            msg = f"Cannot fail from {self.state} state"
            raise ValueError(msg)

        self.state = GoalState.FAILED
        self.metadata["failure_reason"] = reason
        self.updated_at = datetime.now(UTC)

    def is_terminal(self) -> bool:
        """Check if goal is in terminal state.

        Returns:
            True if COMPLETED or FAILED
        """
        return self.state in {GoalState.COMPLETED, GoalState.FAILED}

    def calculate_progress(self, task_states: dict[str, str]) -> float:
        """Calculate goal progress based on task states.

        Args:
            task_states: Mapping of task_id to state

        Returns:
            Progress as float between 0.0 and 1.0
        """
        if not self.task_ids:
            return 0.0

        completed = sum(1 for tid in self.task_ids if task_states.get(tid) == "SUCCESS")
        return completed / len(self.task_ids)
