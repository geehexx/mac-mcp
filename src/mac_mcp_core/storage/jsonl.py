"""JSONL file-based event store implementation.

This implementation stores events in a line-delimited JSON (JSONL) file,
providing durability and human-readable event logs.
"""

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import aiofiles
from aiofiles import os as aio_os

from mac_mcp_core.domain.events import Event
from mac_mcp_core.storage.base import EventStore, Snapshot


class JSONLEventStore(EventStore):
    """JSONL file-based event store.

    Events are stored in a .jsonl file with one event per line.
    Snapshots are stored in a separate .snapshot.json file.

    This implementation provides:
    - Durability: Events survive process restarts
    - Human-readable: Can debug with standard tools (jq, grep)
    - Streamable: Can process large logs without loading into memory
    - Appendable: O(1) write operations

    Attributes:
        events_path: Path to the JSONL events file
        snapshot_path: Path to the snapshot file
    """

    def __init__(
        self,
        events_path: str | Path = "events.jsonl",
        snapshot_path: str | Path = "snapshot.json",
    ) -> None:
        """Initialize the JSONL event store.

        Args:
            events_path: Path to events file
            snapshot_path: Path to snapshot file
        """
        self.events_path = Path(events_path)
        self.snapshot_path = Path(snapshot_path)
        self._latest_sequence = 0
        self._initialized = False

    async def _initialize(self) -> None:
        """Initialize the event store by reading existing events."""
        if self._initialized:
            return

        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)

        if await aio_os.path.exists(self.events_path):
            async for event in self.read():
                self._latest_sequence = max(self._latest_sequence, event.sequence)

        self._initialized = True

    async def append(self, event: Event) -> None:
        """Append an event to the store.

        Args:
            event: Event to append

        Raises:
            ValueError: If event sequence is not monotonic or event is invalid
        """
        await self._initialize()

        # Validate event sequence monotonicity
        if event.sequence <= self._latest_sequence:
            msg = f"Event sequence {event.sequence} is not greater than {self._latest_sequence}"
            raise ValueError(msg)

        # Validate event schema (2025 best practice: validate before persistence)
        try:
            # Pydantic validation happens on construction, but re-validate to ensure
            # no modifications occurred after construction
            event.model_validate(event.model_dump())
        except Exception as e:
            msg = f"Event validation failed: {e}"
            raise ValueError(msg) from e

        # Validate event consistency (semantic validation)
        self._validate_event_consistency(event)

        async with aiofiles.open(self.events_path, "a", encoding="utf-8") as f:
            event_json = event.model_dump_json()
            await f.write(event_json + "\n")
            await f.flush()

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
        if not await aio_os.path.exists(self.events_path):
            return

        count = 0
        async with aiofiles.open(self.events_path, encoding="utf-8") as f:
            async for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    event_dict = json.loads(line)
                    event = Event(**event_dict)

                    if event.sequence < since:
                        continue

                    if limit is not None and count >= limit:
                        break

                    yield event
                    count += 1

                except json.JSONDecodeError:
                    continue
                except Exception:
                    continue

    async def get_latest_sequence(self) -> int:
        """Get the latest sequence number in the store.

        Returns:
            Latest sequence number, or 0 if store is empty
        """
        await self._initialize()
        return self._latest_sequence

    async def snapshot(self, state: dict[str, Any]) -> None:
        """Save a snapshot of current state.

        Args:
            state: Current system state
        """
        await self._initialize()

        snapshot = Snapshot(
            sequence=self._latest_sequence,
            state=state,
        )

        # Write snapshot atomically
        temp_path = self.snapshot_path.with_suffix(".tmp")
        async with aiofiles.open(temp_path, "w", encoding="utf-8") as f:
            await f.write(snapshot.model_dump_json(indent=2))
            await f.flush()

        # Atomic rename
        await aio_os.replace(temp_path, self.snapshot_path)

    async def get_latest_snapshot(self) -> Snapshot | None:
        """Get the most recent snapshot.

        Returns:
            Latest snapshot, or None if no snapshots exist
        """
        if not await aio_os.path.exists(self.snapshot_path):
            return None

        async with aiofiles.open(self.snapshot_path, encoding="utf-8") as f:
            content = await f.read()
            snapshot_dict = json.loads(content)
            return Snapshot(**snapshot_dict)

    async def close(self) -> None:
        """Close the event store and release resources."""
        # No resources to release for file-based store

    async def compact(self, keep_since: int = 0) -> None:
        """Compact the event log by removing old events.

        This creates a new event file containing only events since
        the specified sequence number.

        Args:
            keep_since: Keep events from this sequence number onwards

        Note:
            This operation is not atomic. Use with caution in production.
        """
        temp_path = self.events_path.with_suffix(".compacted")

        # Write compacted events to temp file
        async with aiofiles.open(temp_path, "w", encoding="utf-8") as out_f:
            async for event in self.read(since=keep_since):
                await out_f.write(event.model_dump_json() + "\n")

        # Replace original file
        await aio_os.replace(temp_path, self.events_path)
