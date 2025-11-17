"""Core orchestrator using pluggable decomposition, matching, and scheduling.

The orchestrator is the central coordination point implementing:
- Goal lifecycle management
- Task lifecycle management
- State machine enforcement
- Event sourcing
- Agent supervision

Implementation strategies for decomposition, matching, and scheduling
are injected via abstract interfaces, enabling external optimization
systems (e.g., DSPy) to provide custom logic.
"""

from typing import Any

from mac_mcp_core.domain.agents import Agent
from mac_mcp_core.domain.events import (
    Event,
    EventType,
    GoalDecomposedEvent,
    GoalSubmittedEvent,
    TaskAssignedEvent,
    TaskCompletedEvent,
    TaskCreatedEvent,
    TaskFailedEvent,
    TaskProgressEvent,
)
from mac_mcp_core.domain.goals import Goal, GoalState
from mac_mcp_core.domain.tasks import Task, TaskDAG, TaskState
from mac_mcp_core.event_publisher import EventPublisher
from mac_mcp_core.interfaces.decomposer import AbstractGoalDecomposer
from mac_mcp_core.interfaces.matcher import AbstractAgentMatcher
from mac_mcp_core.interfaces.scheduler import AbstractScheduler
from mac_mcp_core.storage.base import EventStore
from mac_mcp_core.supervisor import AgentSupervisor


def _sanitize_error(error: dict[str, Any]) -> dict[str, Any]:
    """Sanitize error dict to remove PII before logging.

    Args:
        error: Raw error dictionary

    Returns:
        Sanitized error dictionary safe for logging
    """
    return {
        "type": error.get("type", "unknown"),
        "message": (error.get("message", "")[:200] + "...") if len(error.get("message", "")) > 200 else error.get("message", ""),
        "retryable": error.get("retryable", False),
    }


class Orchestrator:
    """Core orchestrator with pluggable orchestration strategies.

    The orchestrator coordinates all aspects of the system while
    delegating key decisions to injected strategy implementations:
    - Goal decomposition (AbstractGoalDecomposer)
    - Agent-task matching (AbstractAgentMatcher)
    - Task scheduling (AbstractScheduler)

    This enables external systems (e.g., DSPy optimization frameworks)
    to provide self-optimizing orchestration intelligence via MCP.

    Attributes:
        event_store: Event store for persistence
        supervisor: Agent supervisor for agent management
        decomposer: Pluggable goal decomposition strategy
        matcher: Pluggable agent matching strategy
        scheduler: Pluggable task scheduling strategy
    """

    def __init__(
        self,
        event_store: EventStore,
        supervisor: AgentSupervisor | None = None,
        decomposer: AbstractGoalDecomposer | None = None,
        matcher: AbstractAgentMatcher | None = None,
        scheduler: AbstractScheduler | None = None,
    ) -> None:
        """Initialize the orchestrator with pluggable strategies.

        Args:
            event_store: Event store for persistence
            supervisor: Optional agent supervisor (creates one if not provided)
            decomposer: Pluggable goal decomposition strategy (required for goal submission)
            matcher: Pluggable agent matching strategy (optional, uses default if not provided)
            scheduler: Pluggable task scheduling strategy (optional, uses default if not provided)

        Note:
            If decomposer is None, goal submission will fail. The decomposer can be
            a local implementation (e.g., SimpleDecomposer) or an MCP remote client.
        """
        self.event_store = event_store
        self.event_publisher = EventPublisher(event_store)
        self.supervisor = supervisor or AgentSupervisor(event_store)
        self.decomposer = decomposer
        self.matcher = matcher
        self.scheduler = scheduler

        self._tasks: dict[str, Task] = {}
        self._goals: dict[str, Goal] = {}

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

        await self.event_publisher.publish(
            TaskCreatedEvent,
            task_id=task_id,
            goal_id=goal_id,
            payload={
                "description": description,
                "required_capabilities": required_capabilities,
                "dependencies": dependencies or [],
                "context": metadata or {},
            },
        )

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

        task.assign_to(agent_id)
        agent.current_tasks.append(task_id)

        await self.event_publisher.publish(
            TaskAssignedEvent,
            task_id=task_id,
            agent_id=agent_id,
            payload={
                "assignment_reason": "capability_match",
            },
        )

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

        await self.event_publisher.publish(
            TaskProgressEvent,
            task_id=task_id,
            agent_id=agent_id,
            payload={
                "progress": progress,
                "message": message,
                "artifacts": artifacts or [],
            },
        )

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

        agent.current_tasks.remove(task_id)
        agent.record_task_completion(success=True)

        await self.event_publisher.publish(
            TaskCompletedEvent,
            task_id=task_id,
            agent_id=agent_id,
            payload={
                "result": result,
            },
        )

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

        if task_id in agent.current_tasks:
            agent.current_tasks.remove(task_id)
        agent.record_task_completion(success=False)

        # Determine action based on error
        retry_count = task.metadata.get("retry_count", 0)
        retryable = error.get("retryable", False)
        max_retries = 3

        if retryable and retry_count < max_retries:
            action = "retry"
            task.state = TaskState.PENDING
            task.assigned_agent = None
            task.metadata["retry_count"] = retry_count + 1
        else:
            action = "fail"

        await self.event_publisher.publish(
            TaskFailedEvent,
            task_id=task_id,
            agent_id=agent_id,
            payload={
                "error": _sanitize_error(error),
                "retry_count": retry_count + 1,
            },
        )

        return action

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            Task if found, None otherwise
        """
        return self._tasks.get(task_id)

    async def get_ready_tasks(self) -> list[Task]:
        """Get tasks ready for assignment using pluggable scheduler.

        Returns:
            Ordered list of tasks ready for assignment

        Note:
            If no scheduler is configured, falls back to default topological ordering.
        """
        if self.scheduler:
            return await self.scheduler.get_ready_tasks(self._tasks)

        # Fallback: Default topological ordering
        ready: list[Task] = []
        for task in self._tasks.values():
            if task.state != TaskState.PENDING:
                continue

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
        capabilities: list[str],  # noqa: ARG002 - kept for API compatibility
    ) -> Task | None:
        """Claim a task for an agent using pluggable matcher (pull-based assignment).

        Args:
            agent_id: Agent identifier
            capabilities: Agent capabilities (ignored, uses registered capabilities)

        Returns:
            Assigned task, or None if no matching tasks available

        Note:
            Uses pluggable matcher if configured, otherwise falls back to basic matching.
        """
        agent = self.supervisor.get_agent(agent_id)
        if agent is None or not agent.can_accept_task():
            return None

        # SECURITY: Use registered agent capabilities, not caller-provided
        agent_capabilities = set(agent.capabilities)

        ready_tasks = await self.get_ready_tasks()

        # Use pluggable matcher if available
        if self.matcher and ready_tasks:
            available_agents = [agent]
            for task in ready_tasks:
                matched_agent_id = await self.matcher.match_agent(task, available_agents)
                if matched_agent_id == agent_id:
                    await self.assign_task(task.id, agent_id)
                    return task
            return None

        # Fallback: Basic capability matching
        for task in ready_tasks:
            required_caps = set(task.required_capabilities)
            if not required_caps.issubset(agent_capabilities):
                continue

            await self.assign_task(task.id, agent_id)
            return task

        return None

    async def preview_goal(
        self,
        goal_id: str,
        description: str,
        context: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> TaskDAG:
        """Preview goal decomposition without persisting (dry-run mode).

        Args:
            goal_id: Unique goal identifier
            description: Goal description
            context: Additional context (language, framework, domain, etc.)
            constraints: Constraints (deadline, max_agents, etc.)

        Returns:
            Task DAG showing planned decomposition (not persisted)

        Raises:
            ValueError: If decomposer not configured or decomposition fails
        """
        if self.decomposer is None:
            msg = "Goal decomposer not configured. Orchestrator must be initialized with an AbstractGoalDecomposer implementation."
            raise ValueError(msg)

        return await self.decomposer.decompose_goal(
            goal_id=goal_id,
            user_prompt=description,
            context=context,
            constraints=constraints,
        )

    async def submit_goal(
        self,
        goal_id: str,
        description: str,
        context: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> Goal | TaskDAG:
        """Submit a new goal for autonomous decomposition.

        Args:
            goal_id: Unique goal identifier
            description: Goal description
            context: Additional context (language, framework, domain, etc.)
            constraints: Constraints (deadline, max_agents, etc.)
            dry_run: If True, preview decomposition without persisting

        Returns:
            Created goal if dry_run=False, TaskDAG preview if dry_run=True

        Raises:
            ValueError: If goal already exists or decomposer not configured
        """
        if dry_run:
            return await self.preview_goal(goal_id, description, context, constraints)

        if self.decomposer is None:
            msg = "Goal decomposer not configured. Orchestrator must be initialized with an AbstractGoalDecomposer implementation."
            raise ValueError(msg)

        if goal_id in self._goals:
            msg = f"Goal {goal_id} already exists"
            raise ValueError(msg)

        goal = Goal(
            id=goal_id,
            description=description,
            context=context or {},
            constraints=constraints or {},
        )
        self._goals[goal_id] = goal

        await self.event_publisher.publish(
            GoalSubmittedEvent,
            goal_id=goal_id,
            payload={
                "description": description,
                "context": context or {},
                "constraints": constraints or {},
            },
        )

        await self.decompose_goal(goal_id)

        return goal

    async def decompose_goal(self, goal_id: str) -> list[Task]:
        """Decompose a goal into tasks using pluggable decomposer.

        Args:
            goal_id: Goal identifier

        Returns:
            List of created tasks

        Raises:
            KeyError: If goal not found
            ValueError: If decomposition fails
        """
        goal = self._goals.get(goal_id)
        if goal is None:
            msg = f"Goal {goal_id} not found"
            raise KeyError(msg)

        goal.start_decomposition()

        try:
            # Call pluggable decomposer
            task_dag = await self.decomposer.decompose_goal(
                goal_id=goal_id,
                user_prompt=goal.description,
                context=goal.context,
                constraints=goal.constraints,
            )

            # Create tasks from DAG
            created_tasks: list[Task] = []
            for task in task_dag.tasks:
                # Update task dependencies from edges
                deps = [from_id for from_id, to_id in task_dag.edges if to_id == task.id]
                task.dependencies = deps

                # Record task creation event FIRST
                await self.event_publisher.publish(
                    TaskCreatedEvent,
                    task_id=task.id,
                    goal_id=goal_id,
                    payload={
                        "description": task.description,
                        "required_capabilities": task.required_capabilities,
                        "dependencies": task.dependencies,
                        "context": task.metadata,
                    },
                )

                # Store task AFTER event is persisted
                self._tasks[task.id] = task
                created_tasks.append(task)

            # Mark goal as ready
            task_ids = [t.id for t in created_tasks]
            goal.mark_ready(task_ids)

            # Record decomposition event
            await self.event_publisher.publish(
                GoalDecomposedEvent,
                goal_id=goal_id,
                payload={
                    "task_ids": task_ids,
                    "reasoning": task_dag.tasks[0].metadata.get("reasoning", "")
                    if task_dag.tasks
                    else "",
                },
            )

            # Start execution
            goal.start_execution()

        except Exception as e:
            error_context = {
                "error_type": type(e).__name__,
                "goal_id": goal_id,
            }
            goal.fail(f"{type(e).__name__}: {str(e)[:200]}")
            msg = f"Goal decomposition failed: {error_context}"
            raise RuntimeError(msg) from e

        else:
            return created_tasks

    def get_goal(self, goal_id: str) -> Goal | None:
        """Get goal by ID.

        Args:
            goal_id: Goal identifier

        Returns:
            Goal if found, None otherwise
        """
        return self._goals.get(goal_id)

    def get_dependency_result(self, task_id: str) -> dict[str, Any] | None:
        """Get the result of a completed dependency task.

        Args:
            task_id: Dependency task identifier

        Returns:
            Task result if task is completed, None otherwise
        """
        task = self._tasks.get(task_id)
        if task is None or task.state != TaskState.SUCCESS:
            return None
        return task.result

    async def rebuild_from_events(self) -> None:
        """Rebuild orchestrator state from event log."""
        self._tasks.clear()
        self._goals.clear()

        async for event in self.event_store.read():
            await self._apply_event(event)

    async def _apply_event(self, event: Event) -> None:
        """Apply an event to update state."""
        if event.type == EventType.GOAL_SUBMITTED and event.goal_id:
            goal = Goal(
                id=event.goal_id,
                description=event.payload.get("description", ""),
                context=event.payload.get("context", {}),
                constraints=event.payload.get("constraints", {}),
            )
            self._goals[event.goal_id] = goal

        elif event.type == EventType.GOAL_DECOMPOSED and event.goal_id:
            goal = self._goals.get(event.goal_id)
            if goal:
                task_ids = event.payload.get("task_ids", [])
                goal.task_ids = task_ids
                goal.state = GoalState.EXECUTING

        elif event.type == EventType.TASK_CREATED and event.task_id:
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
