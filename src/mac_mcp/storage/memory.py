"""In-memory event store implementation.

This implementation is useful for testing and development.
Events are stored in memory and are lost when the process exits.
"""

from collections.abc import AsyncIterator

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
            ValueError: If event sequence is not monotonic
        """
        if event.sequence <= self._latest_sequence:
            msg = f"Event sequence {event.sequence} is not greater than {self._latest_sequence}"
            raise ValueError(msg)

        self._events.append(event)
        self._latest_sequence = event.sequence

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

    async def snapshot(self, state: dict[str, any]) -> None:
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
        pass

    def clear(self) -> None:
        """Clear all events and snapshots (testing only)."""
        self._events.clear()
        self._snapshots.clear()
        self._latest_sequence = 0
