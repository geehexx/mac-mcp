"""Unit tests for storage implementations."""

import pytest
from mac_mcp.domain.events import Event, EventType
from mac_mcp.storage.memory import InMemoryEventStore


class TestInMemoryEventStore:
    """Tests for in-memory event store."""

    async def test_append_event(self) -> None:
        """Test appending events."""
        store = InMemoryEventStore()

        event = Event(type=EventType.TASK_CREATED, sequence=1)
        await store.append(event)

        assert await store.get_latest_sequence() == 1

    async def test_append_non_monotonic(self) -> None:
        """Test that non-monotonic sequences raise error."""
        store = InMemoryEventStore()

        event1 = Event(type=EventType.TASK_CREATED, sequence=2)
        await store.append(event1)

        event2 = Event(type=EventType.TASK_CREATED, sequence=1)
        with pytest.raises(ValueError, match="not greater than"):
            await store.append(event2)

    async def test_read_events(self) -> None:
        """Test reading events."""
        store = InMemoryEventStore()

        events = [
            Event(type=EventType.TASK_CREATED, sequence=1),
            Event(type=EventType.TASK_ASSIGNED, sequence=2),
            Event(type=EventType.TASK_COMPLETED, sequence=3),
        ]

        for event in events:
            await store.append(event)

        read_events = []
        async for event in store.read():
            read_events.append(event)

        assert len(read_events) == 3
        assert read_events[0].sequence == 1
        assert read_events[2].sequence == 3

    async def test_read_with_since(self) -> None:
        """Test reading events from specific sequence."""
        store = InMemoryEventStore()

        for i in range(1, 6):
            await store.append(Event(type=EventType.TASK_CREATED, sequence=i))

        read_events = []
        async for event in store.read(since=3):
            read_events.append(event)

        assert len(read_events) == 3
        assert read_events[0].sequence == 3

    async def test_read_with_limit(self) -> None:
        """Test reading limited number of events."""
        store = InMemoryEventStore()

        for i in range(1, 11):
            await store.append(Event(type=EventType.TASK_CREATED, sequence=i))

        read_events = []
        async for event in store.read(limit=5):
            read_events.append(event)

        assert len(read_events) == 5

    async def test_snapshot(self) -> None:
        """Test creating and retrieving snapshots."""
        store = InMemoryEventStore()

        await store.append(Event(type=EventType.TASK_CREATED, sequence=1))

        state = {"tasks": {"t1": "pending"}}
        await store.snapshot(state)

        snapshot = await store.get_latest_snapshot()
        assert snapshot is not None
        assert snapshot.sequence == 1
        assert snapshot.state == state
