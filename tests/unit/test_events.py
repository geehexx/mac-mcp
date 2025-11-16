"""Unit tests for event models."""

from datetime import UTC

import pytest

from mac_mcp.domain.events import Event, EventType, TaskProgressEvent


class TestEvent:
    """Tests for Event model."""

    def test_event_creation(self) -> None:
        """Test creating a basic event."""
        event = Event(
            type=EventType.TASK_CREATED,
            sequence=1,
            task_id="t1",
            payload={"description": "Test task"},
        )

        assert event.type == EventType.TASK_CREATED
        assert event.sequence == 1
        assert event.task_id == "t1"
        assert event.payload["description"] == "Test task"

    def test_event_immutable(self) -> None:
        """Test that events are immutable."""
        event = Event(
            type=EventType.TASK_CREATED,
            sequence=1,
        )

        with pytest.raises(Exception):  # Pydantic frozen error
            event.sequence = 2  # type: ignore

    def test_event_timestamp_utc(self) -> None:
        """Test that timestamps are in UTC."""
        event = Event(
            type=EventType.TASK_CREATED,
            sequence=1,
        )

        assert event.timestamp.tzinfo == UTC

    def test_event_from_iso_string(self) -> None:
        """Test parsing event from ISO timestamp string."""
        event = Event(
            type=EventType.TASK_CREATED,
            sequence=1,
            timestamp="2025-11-15T20:00:00Z",
        )

        assert event.timestamp.year == 2025
        assert event.timestamp.month == 11
        assert event.timestamp.day == 15


class TestTaskProgressEvent:
    """Tests for TaskProgressEvent."""

    def test_valid_progress(self) -> None:
        """Test creating progress event with valid progress."""
        event = TaskProgressEvent(
            task_id="t1",
            agent_id="a1",
            sequence=1,
            payload={"progress": 0.5, "message": "Half done"},
        )

        assert event.payload["progress"] == 0.5

    def test_invalid_progress_high(self) -> None:
        """Test that progress > 1.0 raises error."""
        with pytest.raises(ValueError, match="Progress must be between"):
            TaskProgressEvent(
                task_id="t1",
                agent_id="a1",
                sequence=1,
                payload={"progress": 1.5},
            )

    def test_invalid_progress_negative(self) -> None:
        """Test that progress < 0.0 raises error."""
        with pytest.raises(ValueError, match="Progress must be between"):
            TaskProgressEvent(
                task_id="t1",
                agent_id="a1",
                sequence=1,
                payload={"progress": -0.5},
            )
