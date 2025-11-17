"""Event models for event sourcing.

This module defines all event types used in the MAC protocol.
Events are immutable records of state changes in the system.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """Standard event types in the MAC protocol."""

    # Goal events
    GOAL_SUBMITTED = "goal_submitted"
    GOAL_DECOMPOSED = "goal_decomposed"
    GOAL_APPROVED = "goal_approved"
    GOAL_REJECTED = "goal_rejected"
    GOAL_COMPLETED = "goal_completed"

    # Task events
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_AWAITING = "task_awaiting"

    # Agent events
    AGENT_REGISTERED = "agent_registered"
    AGENT_HEARTBEAT = "agent_heartbeat"
    AGENT_FAILED = "agent_failed"
    AGENT_QUARANTINED = "agent_quarantined"

    # Dependency events
    DEPENDENCY_REQUESTED = "dependency_requested"
    DEPENDENCY_RESOLVED = "dependency_resolved"


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
        actor_id: Actor who triggered the event (for audit trail)
        payload: Type-specific event data

    Note:
        actor_id is optional for backward compatibility with schema_version=1 events.
        New events (schema_version=2+) should always include actor_id for audit compliance.
    """

    type: EventType
    schema_version: int = 1  # For future event migrations
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    sequence: int = Field(ge=0)
    task_id: str | None = None
    agent_id: str | None = None
    goal_id: str | None = None
    actor_id: str | None = None  # Actor who triggered event (audit trail)
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "extra": "forbid",
    }

    @field_validator("timestamp", mode="before")
    @classmethod
    def ensure_utc(cls, v: datetime | str) -> datetime:
        """Ensure timestamp is in UTC."""
        dt = datetime.fromisoformat(v.replace("Z", "+00:00")) if isinstance(v, str) else v

        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)


# Specialized event models for type safety


class GoalSubmittedEvent(Event):
    """Event emitted when a new goal is submitted."""

    type: Literal[EventType.GOAL_SUBMITTED] = EventType.GOAL_SUBMITTED
    goal_id: str
    payload: dict[str, Any]  # Contains: description, constraints, requester, priority


class GoalDecomposedEvent(Event):
    """Event emitted when a goal is decomposed into tasks."""

    type: Literal[EventType.GOAL_DECOMPOSED] = EventType.GOAL_DECOMPOSED
    goal_id: str
    payload: dict[str, Any]  # Contains: task_ids, reasoning


class TaskCreatedEvent(Event):
    """Event emitted when a new task is created."""

    type: Literal[EventType.TASK_CREATED] = EventType.TASK_CREATED
    task_id: str
    goal_id: str
    payload: dict[str, Any]  # Contains: description, required_capabilities, dependencies


class TaskAssignedEvent(Event):
    """Event emitted when a task is assigned to an agent."""

    type: Literal[EventType.TASK_ASSIGNED] = EventType.TASK_ASSIGNED
    task_id: str
    agent_id: str
    payload: dict[str, Any]  # Contains: assignment_reason


class TaskProgressEvent(Event):
    """Event emitted when task progress is reported."""

    type: Literal[EventType.TASK_PROGRESS] = EventType.TASK_PROGRESS
    task_id: str
    agent_id: str
    payload: dict[str, Any]  # Contains: progress (0.0-1.0), message, artifacts

    @field_validator("payload")
    @classmethod
    def validate_progress(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate progress is between 0 and 1."""
        if "progress" in v:
            progress = v["progress"]
            if not 0.0 <= progress <= 1.0:
                msg = f"Progress must be between 0.0 and 1.0, got {progress}"
                raise ValueError(msg)
        return v


class TaskCompletedEvent(Event):
    """Event emitted when a task is completed successfully."""

    type: Literal[EventType.TASK_COMPLETED] = EventType.TASK_COMPLETED
    task_id: str
    agent_id: str
    payload: dict[str, Any]  # Contains: result (artifacts, summary, metrics)


class TaskFailedEvent(Event):
    """Event emitted when a task fails."""

    type: Literal[EventType.TASK_FAILED] = EventType.TASK_FAILED
    task_id: str
    agent_id: str
    payload: dict[str, Any]  # Contains: error (type, message, retryable), retry_count


class AgentRegisteredEvent(Event):
    """Event emitted when an agent registers."""

    type: Literal[EventType.AGENT_REGISTERED] = EventType.AGENT_REGISTERED
    agent_id: str
    payload: dict[str, Any]  # Contains: capabilities, metadata


class AgentHeartbeatEvent(Event):
    """Event emitted on agent heartbeat."""

    type: Literal[EventType.AGENT_HEARTBEAT] = EventType.AGENT_HEARTBEAT
    agent_id: str
    payload: dict[str, Any]  # Contains: status, current_tasks, load


class AgentFailedEvent(Event):
    """Event emitted when an agent fails."""

    type: Literal[EventType.AGENT_FAILED] = EventType.AGENT_FAILED
    agent_id: str
    payload: dict[str, Any]  # Contains: reason, last_heartbeat
