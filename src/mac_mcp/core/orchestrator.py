"""Main orchestrator coordinating agents and tasks.

The orchestrator is the central coordination point implementing:
- Goal decomposition
- Task assignment
- State machine enforcement
- Dependency management
"""

from typing import Any

from mac_mcp.core.supervisor import AgentSupervisor
from mac_mcp.domain.agents import Agent
from mac_mcp.domain.events import (
    Event,
    EventType,
    TaskAssignedEvent,
    TaskCompletedEvent,
    TaskCreatedEvent,
    TaskFailedEvent,
    TaskProgressEvent,
)
from mac_mcp.domain.tasks import Task, TaskDAG, TaskState
from mac_mcp.storage.base import EventStore


class Orchestrator:
    """Main orchestrator for multi-agent coordination.

    The orchestrator coordinates all aspects of the system:
    - Task lifecycle management
    - Agent supervision
    - Event sourcing
    - State reconstruction

    Attributes:
        event_store: Event store for persistence
        supervisor: Agent supervisor for agent management
    """

    def __init__(
        self,
        event_store: EventStore,
        supervisor: AgentSupervisor | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            event_store: Event store for persistence
            supervisor: Optional agent supervisor (creates one if not provided)
        """
        self.event_store = event_store
        self.supervisor = supervisor or AgentSupervisor(event_store)

        self._tasks: dict[str, Task] = {}
        self._goals: dict[str, dict[str, Any]] = {}

    async def create_task(
        self,
        task_id: str,
        goal_id: str,
        description: str,
        required_capabilities: list[str],
        dependencies: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Task:
        """Create a new task.

        Args:
            task_id: Unique task identifier
            goal_id: Parent goal identifier
            description: Task description
            required_capabilities: Required capabilities
            dependencies: Task dependencies (task IDs)
            metadata: Optional task metadata

        Returns:
            Created task

        Raises:
            ValueError: If task already exists
        """
        if task_id in self._tasks:
            msg = f"Task {task_id} already exists"
            raise ValueError(msg)

        task = Task(
            id=task_id,
            goal_id=goal_id,
            description=description,
            required_capabilities=required_capabilities,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )

        self._tasks[task_id] = task

        # Record creation event
        sequence = await self.event_store.get_latest_sequence() + 1
        event = TaskCreatedEvent(
            task_id=task_id,
            goal_id=goal_id,
            sequence=sequence,
            payload={
                "description": description,
                "required_capabilities": required_capabilities,
                "dependencies": dependencies or [],
                "context": metadata or {},
            },
        )
        await self.event_store.append(event)

        return task

    async def assign_task(
        self,
        task_id: str,
        agent_id: str,
    ) -> None:
        """Assign a task to an agent.

        Args:
            task_id: Task identifier
            agent_id: Agent identifier

        Raises:
            KeyError: If task or agent not found
            ValueError: If task cannot be assigned
        """
        task = self._tasks[task_id]
        agent = self.supervisor.get_agent(agent_id)

        if agent is None:
            msg = f"Agent {agent_id} not found"
            raise KeyError(msg)

        # Validate agent has required capabilities
        if not agent.matches_capabilities(task.required_capabilities):
            msg = f"Agent {agent_id} lacks required capabilities"
            raise ValueError(msg)

        # Assign task
        task.assign_to(agent_id)
        agent.current_tasks.append(task_id)

        # Record assignment event
        sequence = await self.event_store.get_latest_sequence() + 1
        event = TaskAssignedEvent(
            task_id=task_id,
            agent_id=agent_id,
            sequence=sequence,
            payload={
                "assignment_reason": "capability_match",
            },
        )
        await self.event_store.append(event)

    async def update_task_progress(
        self,
        task_id: str,
        agent_id: str,
        progress: float,
        message: str | None = None,
        artifacts: list[str] | None = None,
    ) -> None:
        """Update task progress.

        Args:
            task_id: Task identifier
            agent_id: Agent identifier
            progress: Progress value (0.0 to 1.0)
            message: Optional progress message
            artifacts: Optional artifact paths

        Raises:
            KeyError: If task not found
            ValueError: If progress is invalid
        """
        task = self._tasks[task_id]

        if task.assigned_agent != agent_id:
            msg = f"Task {task_id} is not assigned to agent {agent_id}"
            raise ValueError(msg)

        task.update_progress(progress, message)

        # Record progress event
        sequence = await self.event_store.get_latest_sequence() + 1
        event = TaskProgressEvent(
            task_id=task_id,
            agent_id=agent_id,
            sequence=sequence,
            payload={
                "progress": progress,
                "message": message,
                "artifacts": artifacts or [],
            },
        )
        await self.event_store.append(event)

    async def complete_task(
        self,
        task_id: str,
        agent_id: str,
        result: dict[str, Any],
    ) -> None:
        """Mark task as completed.

        Args:
            task_id: Task identifier
            agent_id: Agent identifier
            result: Task result (artifacts, summary, metrics)

        Raises:
            KeyError: If task or agent not found
            ValueError: If task cannot be completed
        """
        task = self._tasks[task_id]
        agent = self.supervisor.get_agent(agent_id)

        if agent is None:
            msg = f"Agent {agent_id} not found"
            raise KeyError(msg)

        if task.assigned_agent != agent_id:
            msg = f"Task {task_id} is not assigned to agent {agent_id}"
            raise ValueError(msg)

        task.complete(result)

        # Update agent state
        agent.current_tasks.remove(task_id)
        agent.record_task_completion(success=True)

        # Record completion event
        sequence = await self.event_store.get_latest_sequence() + 1
        event = TaskCompletedEvent(
            task_id=task_id,
            agent_id=agent_id,
            sequence=sequence,
            payload={
                "result": result,
            },
        )
        await self.event_store.append(event)

    async def fail_task(
        self,
        task_id: str,
        agent_id: str,
        error: dict[str, Any],
    ) -> str:
        """Mark task as failed.

        Args:
            task_id: Task identifier
            agent_id: Agent identifier
            error: Error information (type, message, retryable)

        Returns:
            Action taken (retry, reassign, escalate, fail)

        Raises:
            KeyError: If task or agent not found
        """
        task = self._tasks[task_id]
        agent = self.supervisor.get_agent(agent_id)

        if agent is None:
            msg = f"Agent {agent_id} not found"
            raise KeyError(msg)

        task.fail(error)

        # Update agent state
        if task_id in agent.current_tasks:
            agent.current_tasks.remove(task_id)
        agent.record_task_completion(success=False)

        # Determine action based on error
        retry_count = task.metadata.get("retry_count", 0)
        retryable = error.get("retryable", False)
        max_retries = 3

        if retryable and retry_count < max_retries:
            action = "retry"
            # Reset task to PENDING for retry
            task.state = TaskState.PENDING
            task.assigned_agent = None
            task.metadata["retry_count"] = retry_count + 1
        else:
            action = "fail"

        # Record failure event
        sequence = await self.event_store.get_latest_sequence() + 1
        event = TaskFailedEvent(
            task_id=task_id,
            agent_id=agent_id,
            sequence=sequence,
            payload={
                "error": error,
                "retry_count": retry_count + 1,
            },
        )
        await self.event_store.append(event)

        return action

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task if found, None otherwise
        """
        return self._tasks.get(task_id)

    def get_ready_tasks(self) -> list[Task]:
        """Get tasks ready for assignment.

        Returns:
            List of tasks in PENDING state with satisfied dependencies
        """
        ready: list[Task] = []

        for task in self._tasks.values():
            if task.state != TaskState.PENDING:
                continue

            # Check if all dependencies are satisfied
            deps_satisfied = all(
                self._tasks.get(dep_id, Task(id=dep_id, goal_id="", description="")).state
                == TaskState.SUCCESS
                for dep_id in task.dependencies
            )

            if deps_satisfied:
                ready.append(task)

        return ready

    async def claim_task(
        self,
        agent_id: str,
        capabilities: list[str],
    ) -> Task | None:
        """Claim a task for an agent (pull-based assignment).

        Args:
            agent_id: Agent identifier
            capabilities: Agent capabilities

        Returns:
            Assigned task, or None if no matching tasks available
        """
        agent = self.supervisor.get_agent(agent_id)
        if agent is None or not agent.can_accept_task():
            return None

        # Find ready tasks matching capabilities
        ready_tasks = self.get_ready_tasks()
        for task in ready_tasks:
            # Check capability match
            if not any(cap in capabilities for cap in task.required_capabilities):
                continue

            # Assign task
            await self.assign_task(task.id, agent_id)
            return task

        return None

    async def rebuild_from_events(self) -> None:
        """Rebuild orchestrator state from event log.

        This method replays all events to reconstruct the current state.
        Used for recovery and state synchronization.
        """
        self._tasks.clear()
        self._goals.clear()

        async for event in self.event_store.read():
            await self._apply_event(event)

    async def _apply_event(self, event: Event) -> None:
        """Apply an event to update state.

        Args:
            event: Event to apply
        """
        if event.type == EventType.TASK_CREATED and event.task_id:
            task = Task(
                id=event.task_id,
                goal_id=event.goal_id or "",
                description=event.payload.get("description", ""),
                required_capabilities=event.payload.get("required_capabilities", []),
                dependencies=event.payload.get("dependencies", []),
                metadata=event.payload.get("context", {}),
            )
            self._tasks[event.task_id] = task

        elif event.type == EventType.TASK_ASSIGNED and event.task_id and event.agent_id:
            task = self._tasks.get(event.task_id)
            if task:
                task.state = TaskState.RUNNING
                task.assigned_agent = event.agent_id

        elif event.type == EventType.TASK_PROGRESS and event.task_id:
            task = self._tasks.get(event.task_id)
            if task:
                task.progress = event.payload.get("progress", 0.0)

        elif event.type == EventType.TASK_COMPLETED and event.task_id:
            task = self._tasks.get(event.task_id)
            if task:
                task.state = TaskState.SUCCESS
                task.progress = 1.0
                task.result = event.payload.get("result")

        elif event.type == EventType.TASK_FAILED and event.task_id:
            task = self._tasks.get(event.task_id)
            if task:
                task.state = TaskState.ERROR
                task.error = event.payload.get("error")
