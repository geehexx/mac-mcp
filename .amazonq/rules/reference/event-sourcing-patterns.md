# Event Sourcing Patterns

## Core Principles

1. **Events are immutable** - Use Pydantic `frozen=True`
2. **Append-only log** - Never modify or delete events
3. **State reconstruction** - Derive current state from event replay
4. **Complete audit trail** - Every state change is an event

## Event Model Pattern

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class EventType(str, Enum):
    """All event types in the system."""
    GOAL_SUBMITTED = "goal_submitted"
    TASK_CREATED = "task_created"
    TASK_CLAIMED = "task_claimed"
    TASK_COMPLETED = "task_completed"

class BaseEvent(BaseModel):
    """Base class for all events."""
    model_config = {"frozen": True}  # Immutable
    
    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    aggregate_id: UUID  # ID of entity this event affects

class TaskCreatedEvent(BaseEvent):
    """Event emitted when task is created."""
    event_type: EventType = EventType.TASK_CREATED
    task_id: UUID
    goal_id: UUID
    description: str
    required_capabilities: list[str]
    dependencies: list[UUID]
```

**Key Points**:
- `frozen=True` prevents modification after creation
- `event_id` for deduplication
- `timestamp` for ordering
- `aggregate_id` for entity grouping
- Specific event classes inherit from base

## Event Store Pattern

```python
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

class EventStore(ABC):
    """Abstract event store interface."""
    
    @abstractmethod
    async def append(self, event: BaseEvent) -> None:
        """Append event to store (idempotent)."""
        pass
    
    @abstractmethod
    async def get_events(
        self,
        aggregate_id: UUID | None = None,
        after_event_id: UUID | None = None,
    ) -> AsyncIterator[BaseEvent]:
        """Stream events, optionally filtered."""
        pass
    
    @abstractmethod
    async def get_snapshot(self, aggregate_id: UUID) -> dict[str, Any] | None:
        """Get latest snapshot for aggregate."""
        pass
    
    @abstractmethod
    async def save_snapshot(self, aggregate_id: UUID, state: dict[str, Any]) -> None:
        """Save snapshot for aggregate."""
        pass
```

**Key Points**:
- Async interface for I/O
- Idempotent append (duplicate event_id ignored)
- Streaming for memory efficiency
- Snapshots for performance optimization

## JSONL Storage Pattern

```python
import aiofiles
from pathlib import Path

class JSONLEventStore(EventStore):
    """JSONL file-based event store."""
    
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
    
    async def append(self, event: BaseEvent) -> None:
        """Append event as JSON line."""
        async with aiofiles.open(self.path, mode="a") as f:
            await f.write(event.model_dump_json() + "\n")
    
    async def get_events(
        self,
        aggregate_id: UUID | None = None,
        after_event_id: UUID | None = None,
    ) -> AsyncIterator[BaseEvent]:
        """Stream events from JSONL file."""
        seen_after = after_event_id is None
        
        async with aiofiles.open(self.path, mode="r") as f:
            async for line in f:
                event_dict = json.loads(line)
                event = self._deserialize_event(event_dict)
                
                if not seen_after:
                    if event.event_id == after_event_id:
                        seen_after = True
                    continue
                
                if aggregate_id is None or event.aggregate_id == aggregate_id:
                    yield event
```

**Key Points**:
- One event per line (JSONL format)
- Append-only (mode="a")
- Async file I/O with aiofiles
- Streaming to avoid loading all events in memory

## State Reconstruction Pattern

```python
class TaskAggregate:
    """Aggregate that reconstructs state from events."""
    
    def __init__(self, task_id: UUID) -> None:
        self.task_id = task_id
        self.state = TaskState.PENDING
        self.agent_id: UUID | None = None
        self.progress: float = 0.0
        self.result: str | None = None
    
    def apply_event(self, event: BaseEvent) -> None:
        """Apply event to update state."""
        if isinstance(event, TaskCreatedEvent):
            self.state = TaskState.PENDING
        elif isinstance(event, TaskClaimedEvent):
            self.state = TaskState.RUNNING
            self.agent_id = event.agent_id
        elif isinstance(event, TaskProgressEvent):
            self.progress = event.progress
        elif isinstance(event, TaskCompletedEvent):
            self.state = TaskState.SUCCESS
            self.result = event.result
        elif isinstance(event, TaskFailedEvent):
            self.state = TaskState.ERROR
            self.result = event.error_message
    
    @classmethod
    async def load(cls, task_id: UUID, store: EventStore) -> "TaskAggregate":
        """Reconstruct aggregate from event stream."""
        aggregate = cls(task_id)
        
        async for event in store.get_events(aggregate_id=task_id):
            aggregate.apply_event(event)
        
        return aggregate
```

**Key Points**:
- Aggregate holds current state
- `apply_event` updates state based on event type
- `load` replays all events to reconstruct state
- Pure functions (no side effects in apply_event)

## Snapshot Pattern

```python
class TaskAggregate:
    """Aggregate with snapshot support."""
    
    SNAPSHOT_INTERVAL = 100  # Snapshot every N events
    
    @classmethod
    async def load(cls, task_id: UUID, store: EventStore) -> "TaskAggregate":
        """Load from snapshot + recent events."""
        aggregate = cls(task_id)
        event_count = 0
        last_event_id: UUID | None = None
        
        # Try to load snapshot
        snapshot = await store.get_snapshot(task_id)
        if snapshot:
            aggregate._restore_from_snapshot(snapshot)
            last_event_id = snapshot["last_event_id"]
        
        # Replay events after snapshot
        async for event in store.get_events(
            aggregate_id=task_id,
            after_event_id=last_event_id,
        ):
            aggregate.apply_event(event)
            event_count += 1
            last_event_id = event.event_id
        
        # Save new snapshot if needed
        if event_count >= cls.SNAPSHOT_INTERVAL:
            await store.save_snapshot(
                task_id,
                aggregate._create_snapshot(last_event_id),
            )
        
        return aggregate
    
    def _create_snapshot(self, last_event_id: UUID) -> dict[str, Any]:
        """Create snapshot of current state."""
        return {
            "task_id": str(self.task_id),
            "state": self.state.value,
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "progress": self.progress,
            "result": self.result,
            "last_event_id": str(last_event_id),
        }
    
    def _restore_from_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Restore state from snapshot."""
        self.state = TaskState(snapshot["state"])
        self.agent_id = UUID(snapshot["agent_id"]) if snapshot["agent_id"] else None
        self.progress = snapshot["progress"]
        self.result = snapshot["result"]
```

**Key Points**:
- Snapshot every N events to reduce replay time
- Snapshot includes `last_event_id` for resumption
- Load snapshot + replay recent events
- Auto-save snapshot after threshold

## Event Validation Pattern

```python
class TaskAggregate:
    """Aggregate with event validation."""
    
    def apply_event(self, event: BaseEvent) -> None:
        """Apply event with validation."""
        if isinstance(event, TaskClaimedEvent):
            if self.state != TaskState.PENDING:
                raise ValueError(
                    f"Cannot claim task in state {self.state}. "
                    f"Expected PENDING."
                )
            self.state = TaskState.RUNNING
            self.agent_id = event.agent_id
        
        elif isinstance(event, TaskCompletedEvent):
            if self.state != TaskState.RUNNING:
                raise ValueError(
                    f"Cannot complete task in state {self.state}. "
                    f"Expected RUNNING."
                )
            self.state = TaskState.SUCCESS
            self.result = event.result
```

**Key Points**:
- Validate state transitions in `apply_event`
- Raise exceptions for invalid transitions
- Prevents corrupted state from bad events

## Anti-Patterns

❌ **Mutable Events**
```python
class TaskEvent(BaseModel):
    # Missing frozen=True - can be modified!
    task_id: UUID
    state: TaskState
```

❌ **Modifying Past Events**
```python
# NEVER modify or delete events
async def fix_event(event_id: UUID) -> None:
    # This breaks event sourcing!
    await store.update_event(event_id, new_data)
```

❌ **Side Effects in apply_event**
```python
def apply_event(self, event: BaseEvent) -> None:
    # NEVER do I/O or side effects here
    if isinstance(event, TaskCompletedEvent):
        await notify_user(event.result)  # ❌ Side effect!
```

❌ **Loading All Events at Once**
```python
# Memory inefficient for large event streams
events = await store.get_all_events()  # ❌ Loads everything
for event in events:
    aggregate.apply_event(event)
```

✅ **Use Async Iterator**
```python
# Memory efficient streaming
async for event in store.get_events(aggregate_id=task_id):
    aggregate.apply_event(event)
```

## Testing Patterns

```python
@pytest.mark.unit
async def test_task_state_reconstruction():
    """Test state reconstruction from events."""
    store = InMemoryEventStore()
    task_id = uuid4()
    
    # Append events
    await store.append(TaskCreatedEvent(aggregate_id=task_id, task_id=task_id, ...))
    await store.append(TaskClaimedEvent(aggregate_id=task_id, task_id=task_id, ...))
    await store.append(TaskCompletedEvent(aggregate_id=task_id, task_id=task_id, ...))
    
    # Reconstruct state
    aggregate = await TaskAggregate.load(task_id, store)
    
    assert aggregate.state == TaskState.SUCCESS

@pytest.mark.property
def test_event_immutability():
    """Property test: events cannot be modified."""
    from hypothesis import given
    import hypothesis.strategies as st
    
    @given(st.text())
    def check_immutable(description: str):
        event = TaskCreatedEvent(
            aggregate_id=uuid4(),
            task_id=uuid4(),
            description=description,
        )
        
        with pytest.raises(ValidationError):
            event.description = "modified"  # Should fail
    
    check_immutable()
```

## Related Patterns

- Actor Model: `.amazonq/rules/reference/actor-model-patterns.md`
- MCP Protocol: `.amazonq/rules/reference/mcp-protocol-patterns.md`
- Code Patterns: `.amazonq/rules/reference/code-patterns.md`
