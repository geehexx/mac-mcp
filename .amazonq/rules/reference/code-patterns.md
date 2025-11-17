# Code Patterns

## Import Organization

```python
# 1. Standard library (alphabetical)
import asyncio
import json
from collections.abc import AsyncIterator
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

# 2. Third-party packages (alphabetical)
import aiofiles
from pydantic import BaseModel, Field

# 3. Local imports (alphabetical)
from mac_mcp.domain.events import BaseEvent, TaskCreatedEvent
from mac_mcp.storage.base import EventStore
```

**Enforced by**: ruff isort

## Type Hints

```python
# Modern union syntax (Python 3.10+)
def get_task(task_id: UUID) -> Task | None:
    """Return task or None if not found."""
    pass

# NOT: Optional[Task]

# Modern dict/list syntax
def process_events(events: dict[str, list[BaseEvent]]) -> None:
    """Process events by type."""
    pass

# NOT: Dict[str, List[BaseEvent]]

# Callable from collections.abc
from collections.abc import Callable

def retry(func: Callable[..., Any]) -> Callable[..., Any]:
    """Retry decorator."""
    pass

# NOT: from typing import Callable
```

## Async Patterns

```python
# Async function
async def fetch_data() -> dict[str, Any]:
    """Fetch data asynchronously."""
    async with aiofiles.open("data.json") as f:
        content = await f.read()
    return json.loads(content)

# Async context manager
class AsyncResource:
    """Async resource with cleanup."""
    
    async def __aenter__(self) -> "AsyncResource":
        await self.connect()
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        await self.disconnect()

# Async iterator
async def stream_events() -> AsyncIterator[BaseEvent]:
    """Stream events asynchronously."""
    async with aiofiles.open("events.jsonl") as f:
        async for line in f:
            yield parse_event(line)
```

## Pydantic Models

```python
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class Task(BaseModel):
    """Task domain model."""
    model_config = {"frozen": True}  # Immutable
    
    task_id: UUID = Field(default_factory=uuid4)
    description: str
    state: TaskState = TaskState.PENDING
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    
    def with_state(self, state: TaskState) -> "Task":
        """Return new task with updated state."""
        return self.model_copy(update={"state": state})
```

**Key Points**:
- Use `model_config` for configuration
- `frozen=True` for immutability
- `Field` for validation and defaults
- `model_copy` for updates (immutable pattern)

## Error Handling

```python
# Specific exceptions
try:
    task = await orchestrator.get_task(task_id)
except TaskNotFoundError:
    logger.warning("Task not found", task_id=task_id)
    return None
except Exception:
    logger.exception("Unexpected error", task_id=task_id)
    raise

# NOT: bare except

# Retry with backoff
import asyncio
from functools import wraps

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Retry decorator with exponential backoff."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        "Retry attempt",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
        return wrapper
    return decorator
```

## Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Structured logging with context
logger.info(
    "Task claimed",
    task_id=str(task_id),
    agent_id=str(agent_id),
    capabilities=agent.capabilities,
)

# NOT: f-strings
# logger.info(f"Task {task_id} claimed by {agent_id}")

# Exception logging
try:
    await process_task(task_id)
except Exception:
    logger.exception(
        "Task processing failed",
        task_id=str(task_id),
    )
```

## Docstrings

```python
def submit_goal(description: str, context: dict[str, Any]) -> UUID:
    """Submit a high-level goal for decomposition.
    
    Args:
        description: Natural language goal description
        context: Additional context for decomposition
    
    Returns:
        UUID of created goal
    
    Raises:
        ValueError: If description is empty
    """
    pass

class Orchestrator:
    """Central coordinator for multi-agent task execution.
    
    The orchestrator manages goal decomposition, task assignment,
    and agent supervision using event sourcing for complete audit trail.
    """
    pass
```

**Style**: Google-style docstrings

**Required**:
- Module docstrings
- Class docstrings
- Public function docstrings (>10 lines or complex logic)

**Optional**:
- Private function docstrings (if complex)
- Simple getter/setter docstrings

## State Machine Pattern

```python
from enum import Enum

class TaskState(str, Enum):
    """Task lifecycle states."""
    PENDING = "pending"
    RUNNING = "running"
    AWAITING = "awaiting"
    SUCCESS = "success"
    ERROR = "error"
    BLOCKED = "blocked"

class Task(BaseModel):
    """Task with state machine."""
    state: TaskState = TaskState.PENDING
    
    def claim(self, agent_id: UUID) -> "Task":
        """Transition to RUNNING state."""
        if self.state != TaskState.PENDING:
            raise ValueError(f"Cannot claim task in state {self.state}")
        return self.model_copy(update={"state": TaskState.RUNNING})
    
    def complete(self, result: str) -> "Task":
        """Transition to SUCCESS state."""
        if self.state != TaskState.RUNNING:
            raise ValueError(f"Cannot complete task in state {self.state}")
        return self.model_copy(update={"state": TaskState.SUCCESS})
```

## Concurrency Pattern

```python
import asyncio

# Semaphore for rate limiting
async def process_tasks(tasks: list[Task], max_concurrent: int = 10) -> None:
    """Process tasks with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_limit(task: Task) -> None:
        async with semaphore:
            await process_task(task)
    
    await asyncio.gather(*[process_with_limit(task) for task in tasks])

# Timeout
async def fetch_with_timeout(url: str, timeout: float = 30.0) -> str:
    """Fetch with timeout."""
    try:
        return await asyncio.wait_for(fetch(url), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Fetch timeout", url=url, timeout=timeout)
        raise
```

## Testing Patterns

```python
import pytest
from uuid import uuid4

@pytest.mark.unit
def test_task_state_transition():
    """Test task state machine."""
    task = Task(task_id=uuid4(), description="Test")
    
    # Valid transition
    claimed = task.claim(agent_id=uuid4())
    assert claimed.state == TaskState.RUNNING
    
    # Invalid transition
    with pytest.raises(ValueError, match="Cannot claim"):
        claimed.claim(agent_id=uuid4())

@pytest.mark.integration
async def test_orchestrator_workflow():
    """Test full orchestrator workflow."""
    store = InMemoryEventStore()
    orchestrator = Orchestrator(event_store=store)
    
    # Submit goal
    goal_id = await orchestrator.submit_goal("Build API")
    
    # Decompose
    await orchestrator.decompose_goal(goal_id)
    
    # Verify tasks created
    tasks = await orchestrator.get_pending_tasks()
    assert len(tasks) > 0

@pytest.mark.property
def test_event_ordering():
    """Property test for event ordering."""
    from hypothesis import given
    import hypothesis.strategies as st
    
    @given(st.lists(st.integers(), min_size=1))
    def check_ordering(event_ids: list[int]):
        store = InMemoryEventStore()
        # Test that events maintain order
        pass
    
    check_ordering()
```

## Anti-Patterns

❌ **Optional[T] instead of T | None**
```python
from typing import Optional

def get_task(task_id: UUID) -> Optional[Task]:  # ❌ Old syntax
    pass
```

❌ **Dict/List instead of dict/list**
```python
from typing import Dict, List

def process(data: Dict[str, List[str]]) -> None:  # ❌ Old syntax
    pass
```

❌ **Blocking I/O in async function**
```python
async def load_data() -> str:
    with open("data.txt") as f:  # ❌ Blocking!
        return f.read()
```

❌ **Mutable default arguments**
```python
def process(items: list[str] = []) -> None:  # ❌ Mutable default!
    items.append("new")
```

✅ **Use None and create new list**
```python
def process(items: list[str] | None = None) -> None:
    if items is None:
        items = []
    items.append("new")
```

## Related Patterns

- Event Sourcing: `.amazonq/rules/reference/event-sourcing-patterns.md`
- MCP Protocol: `.amazonq/rules/reference/mcp-protocol-patterns.md`
