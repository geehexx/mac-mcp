"""In-memory event store implementation.

This implementation is useful for testing and development.
Events are stored in memory and are lost when the process exits.
"""

from collections.abc import AsyncIterator
from typing import Any

from mac_mcp.domain.events import Event
from mac_mcp.storage.base import EventStore, Snapshot


class InMemoryEventStore(EventStore):
    """In-memory event store for testing and development.

    Events and snapshots are stored in memory and lost on process exit.
    This implementation is fast but not durable.
    """

    def __init__(self) -> None:
        """Initialize the in-memory event store."""
        self._events: list[Event] = []
        self._snapshots: list[Snapshot] = []
        self._latest_sequence = 0

    async def append(self, event: Event) -> None:
        """Append an event to the store.

        Args:
            event: Event to append

        Raises:
            ValueError: If event sequence is not monotonic or event is invalid
        """
        # Validate event sequence monotonicity
        if event.sequence <= self._latest_sequence:
            msg = f"Event sequence {event.sequence} is not greater than {self._latest_sequence}"
            raise ValueError(msg)

        # Validate event schema (2025 best practice: validate before persistence)
        try:
            event.model_validate(event.model_dump())
        except Exception as e:
            msg = f"Event validation failed: {e}"
            raise ValueError(msg) from e

        # Validate event consistency (semantic validation)
        self._validate_event_consistency(event)

        self._events.append(event)
        self._latest_sequence = event.sequence

    def _validate_event_consistency(self, event: Event) -> None:
        """Validate event semantic consistency.

        Args:
            event: Event to validate

        Raises:
            ValueError: If event is semantically invalid
        """
        # Validate required fields based on event type
        if event.type.value.startswith("task_") and not event.task_id:
            msg = f"Task event {event.type} requires task_id"
            raise ValueError(msg)

        if event.type.value.startswith("agent_") and not event.agent_id:
            msg = f"Agent event {event.type} requires agent_id"
            raise ValueError(msg)

        if event.type.value.startswith("goal_") and not event.goal_id:
            msg = f"Goal event {event.type} requires goal_id"
            raise ValueError(msg)

        # Validate payload structure for critical events
        if event.type.value == "task_created":
            required_fields = {"description", "required_capabilities"}
            if not all(field in event.payload for field in required_fields):
                msg = f"task_created event missing required payload fields: {required_fields}"
                raise ValueError(msg)

    async def read(
        self,
        since: int = 0,
        limit: int | None = None,
    ) -> AsyncIterator[Event]:
        """Read events from the store.

        Args:
            since: Start reading from this sequence number (inclusive)
            limit: Maximum number of events to read (None for all)

        Yields:
            Events in sequence order
        """
        count = 0
        for event in self._events:
            if event.sequence < since:
                continue

            if limit is not None and count >= limit:
                break

            yield event
            count += 1

    async def get_latest_sequence(self) -> int:
        """Get the latest sequence number in the store.

        Returns:
            Latest sequence number, or 0 if store is empty
        """
        return self._latest_sequence

    async def snapshot(self, state: dict[str, Any]) -> None:
        """Save a snapshot of current state.

        Args:
            state: Current system state
        """
        snapshot = Snapshot(
            sequence=self._latest_sequence,
            state=state,
        )
        self._snapshots.append(snapshot)

    async def get_latest_snapshot(self) -> Snapshot | None:
        """Get the most recent snapshot.

        Returns:
            Latest snapshot, or None if no snapshots exist
        """
        return self._snapshots[-1] if self._snapshots else None

    async def close(self) -> None:
        """Close the event store and release resources."""
        # No resources to release for in-memory store

    def clear(self) -> None:
        """Clear all events and snapshots (testing only)."""
        self._events.clear()
        self._snapshots.clear()
        self._latest_sequence = 0
