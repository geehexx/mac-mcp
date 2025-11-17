"""Base classes and protocols for event storage."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field

from mac_mcp_core.domain.events import Event


class Snapshot(BaseModel):
    """Point-in-time snapshot of system state.

    Snapshots are used to optimize state reconstruction by avoiding
    full event log replay.

    Attributes:
        sequence: Event sequence number when snapshot was taken
        timestamp: When the snapshot was created
        state: Serialized system state
    """

    sequence: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    state: dict[str, Any]


class EventStore(ABC):
    """Abstract base class for event stores.

    Event stores provide append-only storage for events with the ability
    to read events sequentially or from a specific sequence number.
    """

    @abstractmethod
    async def append(self, event: Event) -> None:
        """Append an event to the store.

        Args:
            event: Event to append

        Raises:
            ValueError: If event sequence is not monotonic
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def get_latest_sequence(self) -> int:
        """Get the latest sequence number in the store.

        Returns:
            Latest sequence number, or 0 if store is empty
        """
        ...

    @abstractmethod
    async def snapshot(self, state: dict[str, Any]) -> None:
        """Save a snapshot of current state.

        Args:
            state: Current system state
        """
        ...

    @abstractmethod
    async def get_latest_snapshot(self) -> Snapshot | None:
        """Get the most recent snapshot.

        Returns:
            Latest snapshot, or None if no snapshots exist
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the event store and release resources."""
        ...


class EventStoreProtocol(Protocol):
    """Protocol for event store implementations.

    This protocol defines the interface that all event stores must implement,
    allowing for type-safe dependency injection and testing.
    """

    async def append(self, event: Event) -> None: ...

    async def read(
        self,
        since: int = 0,
        limit: int | None = None,
    ) -> AsyncIterator[Event]: ...

    async def get_latest_sequence(self) -> int: ...

    async def snapshot(self, state: dict[str, Any]) -> None: ...

    async def get_latest_snapshot(self) -> Snapshot | None: ...

    async def close(self) -> None: ...
