"""Event publisher utility for centralized event creation and persistence.

This module provides a clean abstraction for publishing events to the event store,
eliminating duplication of the sequence number + create + append pattern that appears
throughout the codebase.

2025 Best Practice: Extract repeated patterns into focused utility classes.
"""

from typing import Any, TypeVar

from mac_mcp.domain.events import Event
from mac_mcp.storage.base import EventStore


# Type variable for event subclasses
E = TypeVar("E", bound=Event)


class EventPublisher:
    """Centralized event creation and persistence.

    This class eliminates the repeated pattern of:
    1. Getting next sequence number
    2. Creating event with sequence
    3. Appending event to store

    Example:
        >>> publisher = EventPublisher(event_store)
        >>> await publisher.publish(
        ...     TaskCreatedEvent,
        ...     task_id="task_001",
        ...     goal_id="goal_001",
        ...     payload={"description": "Write tests"}
        ... )
    """

    def __init__(self, event_store: EventStore):
        """Initialize the event publisher.

        Args:
            event_store: Event store for persistence
        """
        self.event_store = event_store

    async def publish(
        self,
        event_type: type[E],
        **kwargs: Any,
    ) -> E:
        """Publish an event to the event store.

        This method handles:
        1. Sequence number generation
        2. Event instantiation
        3. Event persistence

        Args:
            event_type: Event class to instantiate (must subclass Event)
            **kwargs: Event-specific fields (task_id, goal_id, agent_id, payload, etc.)

        Returns:
            The created and persisted event

        Raises:
            ValueError: If event validation fails
            Exception: If event store append fails

        Example:
            >>> from mac_mcp.domain.events import TaskCreatedEvent
            >>> event = await publisher.publish(
            ...     TaskCreatedEvent,
            ...     task_id="task_001",
            ...     goal_id="goal_001",
            ...     payload={
            ...         "description": "Implement authentication",
            ...         "required_capabilities": ["python", "security"]
            ...     }
            ... )
            >>> print(event.sequence)  # Auto-generated sequence number
            42
        """
        # Get next sequence number
        sequence = await self.event_store.get_latest_sequence() + 1

        # Create event with sequence
        event = event_type(sequence=sequence, **kwargs)

        # Persist event (validation happens in event store)
        await self.event_store.append(event)

        return event

    async def get_latest_sequence(self) -> int:
        """Get latest sequence number from event store.

        This is a convenience method to avoid direct event store access.

        Returns:
            Latest sequence number
        """
        return await self.event_store.get_latest_sequence()
