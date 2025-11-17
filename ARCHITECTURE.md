```# Architecture: Core / Plugin / MCP Extension

This document describes the architectural principles and patterns used in MAC MCP.

## Overview

MAC MCP follows a **Core / Plugin / MCP Extension** architecture that separates:
1. **Protocol-agnostic infrastructure** (core)
2. **Reference implementations** (plugins)
3. **External optimization systems** (MCP extensions)

## Package Structure

```
mac-mcp/
├── src/
│   ├── mac_mcp_core/          # Core infrastructure package
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration system
│   │   ├── orchestrator.py    # Core orchestrator (uses injected strategies)
│   │   ├── supervisor.py      # Agent supervisor
│   │   ├── event_publisher.py # Event publishing utility
│   │   ├── interfaces/        # Abstract base classes
│   │   │   ├── decomposer.py  # AbstractGoalDecomposer
│   │   │   ├── matcher.py     # AbstractAgentMatcher
│   │   │   └── scheduler.py   # AbstractScheduler
│   │   ├── domain/            # Domain models
│   │   │   ├── agents.py
│   │   │   ├── events.py
│   │   │   ├── goals.py
│   │   │   └── tasks.py
│   │   ├── storage/           # Event store implementations
│   │   │   ├── base.py
│   │   │   ├── memory.py
│   │   │   └── jsonl.py
│   │   ├── auth/              # Authentication
│   │   │   └── api_key.py
│   │   ├── mcp/               # MCP protocol handlers
│   │   │   ├── server.py
│   │   │   ├── handlers.py
│   │   │   └── __main__.py
│   │   └── llm/               # LLM provider interface
│   │       └── base.py
│   │
│   └── mac_mcp_reference/     # Reference implementations package
│       ├── __init__.py
│       ├── factory.py         # ComponentFactory for DI
│       ├── decomposer.py      # SimpleDecomposer (LLM-based)
│       ├── matcher.py         # BasicMatcher (capability-based)
│       ├── scheduler.py       # TopologicalScheduler
│       └── llm/               # LLM provider implementations
│           ├── anthropic_provider.py
│           ├── bedrock_provider.py
│           └── factory.py
```

## Core Principles

### 1. Separation of Concerns

The **core** package (`mac_mcp_core`) contains:
- Event sourcing infrastructure (events, storage, audit trail)
- Agent lifecycle management (supervisor, heartbeat, state)
- MCP protocol handlers
- **Abstract interfaces only** - no hard-coded orchestration logic

The **reference** package (`mac_mcp_reference`) contains:
- Concrete implementations of abstract interfaces
- LLM provider integrations
- Component factory for dependency injection

### 2. Strategy Pattern for Orchestration

The orchestrator uses **three pluggable strategies**:

```python
class Orchestrator:
    def __init__(
        self,
        event_store: EventStore,
        decomposer: AbstractGoalDecomposer,  # Pluggable
        matcher: AbstractAgentMatcher,        # Pluggable
        scheduler: AbstractScheduler,         # Pluggable
    ):
        self.decomposer = decomposer
        self.matcher = matcher
        self.scheduler = scheduler
```

#### Abstract Interfaces

```python
class AbstractGoalDecomposer(ABC):
    """Decomposes high-level goals into task DAGs."""

    @abstractmethod
    async def decompose_goal(
        self, goal_id: str, user_prompt: str,
        context: dict, constraints: dict
    ) -> TaskDAG:
        pass

class AbstractAgentMatcher(ABC):
    """Matches agents to tasks based on capabilities and context."""

    @abstractmethod
    async def match_agent(
        self, task: Task, available_agents: list[Agent],
        context: dict
    ) -> str | None:
        pass

class AbstractScheduler(ABC):
    """Determines task execution order."""

    @abstractmethod
    async def get_ready_tasks(
        self, all_tasks: dict[str, Task], context: dict
    ) -> list[Task]:
        pass
```

### 3. Configuration-Driven Component Selection

Components are selected via configuration:

```yaml
# config.yaml
decomposer:
  type: simple               # or: template, dspy, mcp_remote
  llm:
    provider: anthropic
    model: claude-sonnet-4-5-20250929
    api_key: ${ANTHROPIC_API_KEY}

matcher:
  type: basic                # or: load_balanced, dspy, mcp_remote
  max_concurrent_tasks: 5

scheduler:
  type: topological          # or: priority, deadline, dspy, mcp_remote
```

The `ComponentFactory` creates implementations:

```python
from mac_mcp_reference.factory import ComponentFactory

decomposer = ComponentFactory.create_decomposer(config.decomposer)
matcher = ComponentFactory.create_matcher(config.matcher)
scheduler = ComponentFactory.create_scheduler(config.scheduler)

orchestrator = Orchestrator(
    event_store=event_store,
    decomposer=decomposer,
    matcher=matcher,
    scheduler=scheduler,
)
```

### 4. MCP Extension Points

External systems can provide implementations via MCP:

```yaml
# DSPy-optimized decomposition via MCP
decomposer:
  type: mcp_remote
  mcp_endpoint: "coordination://decomposers/dspy_optimized"
  options:
    model: claude-sonnet-4-5-20250929
    optimizer: BootstrapFewShot
    metrics: [completion_rate, time_to_complete]
```

## Reference Implementations

### SimpleDecomposer (LLM-based)

Uses an LLM to analyze goals and generate task DAGs:

```python
class SimpleDecomposer(AbstractGoalDecomposer):
    def __init__(self, llm_provider: LLMProvider, max_tokens: int, temperature: float):
        self.llm_provider = llm_provider
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def decompose_goal(self, goal_id, user_prompt, context, constraints):
        prompt = self._build_prompt(user_prompt, context, constraints)
        response = await self.llm_provider.generate(prompt, self.max_tokens, self.temperature)
        result = self._parse_response(response)
        return self._create_task_dag(result, goal_id)
```

### BasicMatcher (Capability-based)

Matches agents based on capability requirements and success rate:

```python
class BasicMatcher(AbstractAgentMatcher):
    async def match_agent(self, task, available_agents, context):
        required_caps = set(task.required_capabilities)
        candidates = [
            agent for agent in available_agents
            if required_caps.issubset(set(agent.capabilities))
            and agent.can_accept_task()
        ]
        # Sort by success rate, return best
        candidates.sort(key=lambda a: a.success_rate(), reverse=True)
        return candidates[0].id if candidates else None
```

### TopologicalScheduler

Returns tasks in dependency order:

```python
class TopologicalScheduler(AbstractScheduler):
    async def get_ready_tasks(self, all_tasks, context):
        ready = []
        for task in all_tasks.values():
            if task.state != TaskState.PENDING:
                continue
            deps_satisfied = all(
                all_tasks[dep_id].state == TaskState.SUCCESS
                for dep_id in task.dependencies
            )
            if deps_satisfied:
                ready.append(task)
        return ready
```

## Event Sourcing

All state changes are persisted as events:

```python
# Example: Goal submission
await event_publisher.publish(
    GoalSubmittedEvent,
    goal_id=goal_id,
    payload={
        "description": description,
        "context": context,
        "constraints": constraints,
    },
)
```

Events enable:
- **Audit trail**: Complete history of all actions
- **State reconstruction**: Rebuild state from event log
- **Time-travel debugging**: Replay events to any point in time
- **Analytics**: Extract metrics and patterns from event stream

## Extension Guide: Implementing Custom Strategies

### Example: DSPy-Optimized Decomposer

```python
import dspy
from mac_mcp_core.interfaces.decomposer import AbstractGoalDecomposer
from mac_mcp_core.domain.tasks import TaskDAG, Task

class DSPyDecomposer(AbstractGoalDecomposer):
    """DSPy-optimized goal decomposer using learned patterns."""

    def __init__(self, dspy_model, optimizer, training_data):
        # Define DSPy signature
        self.signature = dspy.Signature(
            "goal_description, context -> tasks: list[Task], edges: list[tuple]"
        )

        # Create and optimize predictor
        self.predictor = dspy.ChainOfThought(self.signature)
        if training_data:
            self.predictor = optimizer.compile(
                self.predictor,
                trainset=training_data
            )

    async def decompose_goal(self, goal_id, user_prompt, context, constraints):
        # Use DSPy to generate decomposition
        result = self.predictor(
            goal_description=user_prompt,
            context=str(context)
        )

        # Convert DSPy output to TaskDAG
        tasks = [
            Task(
                id=f"{goal_id}_{i}",
                goal_id=goal_id,
                description=task_desc["description"],
                required_capabilities=task_desc["capabilities"],
                dependencies=task_desc.get("dependencies", []),
            )
            for i, task_desc in enumerate(result.tasks)
        ]

        return TaskDAG(tasks=tasks, edges=result.edges)

    def get_implementation_name(self) -> str:
        return "dspy_optimized"
```

### Registering Custom Implementation

```python
# In mac_mcp_reference/factory.py
from mac_mcp_core.config import DecomposerType

# Add enum value
class DecomposerType(str, Enum):
    SIMPLE = "simple"
    DSPY = "dspy"
    CUSTOM = "custom"  # Your implementation

# Update factory
def create_decomposer(config: DecomposerConfig):
    if config.type == DecomposerType.DSPY:
        from my_implementations import DSPyDecomposer
        return DSPyDecomposer(
            dspy_model=config.dspy_model,
            optimizer=config.dspy_optimizer,
            training_data=load_training_data()
        )
    # ... existing implementations
```

## Benefits of This Architecture

1. **Testability**: Core logic can be tested with mock implementations
2. **Flexibility**: Swap implementations without changing core code
3. **Extensibility**: Add new strategies by implementing abstract interfaces
4. **MCP-First**: External systems can provide optimized implementations
5. **Event Sourcing**: Complete audit trail and state reconstruction
6. **Separation of Concerns**: Infrastructure separate from business logic

## Future Enhancements

- **MCP Remote Implementations**: Delegate to external services via MCP
- **DSPy Integration**: Self-optimizing orchestration via learned patterns
- **Multi-Tenancy**: Per-tenant strategy configurations
- **A/B Testing**: Compare strategy performance in production
- **Metrics Collection**: Track decomposition quality, matching accuracy, scheduling efficiency
```
