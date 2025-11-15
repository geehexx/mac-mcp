"""Task domain models.

This module defines the Task entity and its state machine.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field


class TaskState(str, Enum):
    """Valid states for a task.

    State transitions are defined by the task state machine.
    See ARCHITECTURE.md for the complete state diagram.
    """

    PENDING = "PENDING"  # Created, waiting for agent
    RUNNING = "RUNNING"  # Agent actively executing
    AWAITING = "AWAITING"  # Blocked on dependency task
    SUCCESS = "SUCCESS"  # Completed successfully (terminal)
    ERROR = "ERROR"  # Failed permanently (terminal)
    BLOCKED = "BLOCKED"  # Dependencies not satisfied


class Task(BaseModel):
    """Task entity representing a unit of work.

    Tasks are created by goal decomposition and assigned to agents
    based on capability matching.

    Attributes:
        id: Unique task identifier
        goal_id: Parent goal identifier
        description: Human-readable task description
        state: Current task state
        assigned_agent: Agent currently executing the task (if any)
        created_at: When the task was created
        updated_at: When the task was last updated
        progress: Completion progress (0.0 to 1.0)
        dependencies: Task IDs that must complete before this task
        required_capabilities: Capabilities needed to execute this task
        result: Task output (when state is SUCCESS)
        error: Error information (when state is ERROR)
        metadata: Additional task-specific data
    """

    id: str
    goal_id: str
    description: str
    state: TaskState = TaskState.PENDING
    assigned_agent: str | None = None
    created_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    updated_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    progress: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
    dependencies: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "t1",
                    "goal_id": "g1",
                    "description": "Design database schema",
                    "state": "PENDING",
                    "required_capabilities": ["database", "postgresql"],
                    "dependencies": [],
                }
            ]
        }
    }

    def can_transition_to(self, new_state: TaskState) -> bool:
        """Check if transition to new state is valid.

        Args:
            new_state: Target state

        Returns:
            True if transition is allowed, False otherwise
        """
        # Define valid state transitions
        transitions: dict[TaskState, set[TaskState]] = {
            TaskState.PENDING: {TaskState.RUNNING, TaskState.BLOCKED},
            TaskState.BLOCKED: {TaskState.PENDING},
            TaskState.RUNNING: {
                TaskState.AWAITING,
                TaskState.SUCCESS,
                TaskState.ERROR,
                TaskState.RUNNING,  # Progress updates
            },
            TaskState.AWAITING: {TaskState.RUNNING},
            TaskState.ERROR: {TaskState.PENDING},  # Retry
            TaskState.SUCCESS: set(),  # Terminal state
        }

        return new_state in transitions.get(self.state, set())

    def assign_to(self, agent_id: str) -> None:
        """Assign task to an agent.

        Args:
            agent_id: Agent identifier

        Raises:
            ValueError: If task is not in PENDING state
        """
        if self.state != TaskState.PENDING:
            msg = f"Cannot assign task in {self.state} state"
            raise ValueError(msg)

        self.assigned_agent = agent_id
        self.state = TaskState.RUNNING
        self.updated_at = datetime.now(UTC)

    def update_progress(self, progress: float, message: str | None = None) -> None:
        """Update task progress.

        Args:
            progress: New progress value (0.0 to 1.0)
            message: Optional progress message

        Raises:
            ValueError: If progress is out of range or task is not RUNNING
        """
        if self.state != TaskState.RUNNING:
            msg = f"Cannot update progress for task in {self.state} state"
            raise ValueError(msg)

        if not 0.0 <= progress <= 1.0:
            msg = f"Progress must be between 0.0 and 1.0, got {progress}"
            raise ValueError(msg)

        self.progress = progress
        if message:
            self.metadata["last_progress_message"] = message
        self.updated_at = datetime.now(UTC)

    def complete(self, result: dict[str, Any]) -> None:
        """Mark task as completed.

        Args:
            result: Task completion result

        Raises:
            ValueError: If task is not in RUNNING state
        """
        if self.state != TaskState.RUNNING:
            msg = f"Cannot complete task in {self.state} state"
            raise ValueError(msg)

        self.state = TaskState.SUCCESS
        self.progress = 1.0
        self.result = result
        self.updated_at = datetime.now(UTC)

    def fail(self, error: dict[str, Any]) -> None:
        """Mark task as failed.

        Args:
            error: Error information (type, message, retryable, etc.)

        Raises:
            ValueError: If task is not in RUNNING state
        """
        if self.state != TaskState.RUNNING:
            msg = f"Cannot fail task in {self.state} state"
            raise ValueError(msg)

        self.state = TaskState.ERROR
        self.error = error
        self.updated_at = datetime.now(UTC)

    def is_terminal(self) -> bool:
        """Check if task is in a terminal state.

        Returns:
            True if task is in SUCCESS or ERROR state
        """
        return self.state in {TaskState.SUCCESS, TaskState.ERROR}


class TaskDAG(BaseModel):
    """Directed Acyclic Graph of tasks.

    Represents the decomposition of a goal into tasks with dependencies.

    Attributes:
        tasks: List of tasks in the DAG
        edges: Dependency edges (from_task -> to_task)
    """

    tasks: list[Task]
    edges: list[tuple[str, str]]  # (from_task_id, to_task_id)

    def validate_acyclic(self) -> bool:
        """Validate that the graph is acyclic.

        Returns:
            True if the graph has no cycles

        Raises:
            ValueError: If a cycle is detected
        """
        # Build adjacency list
        adj: dict[str, list[str]] = {task.id: [] for task in self.tasks}
        for from_id, to_id in self.edges:
            adj[from_id].append(to_id)

        # DFS to detect cycles
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in adj[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for task in self.tasks:
            if task.id not in visited:
                if has_cycle(task.id):
                    msg = "Task DAG contains a cycle"
                    raise ValueError(msg)

        return True

    def get_ready_tasks(self) -> list[Task]:
        """Get tasks that are ready to execute.

        A task is ready if:
        - It's in PENDING state
        - All its dependencies are in SUCCESS state

        Returns:
            List of ready tasks
        """
        # Get task by ID
        task_map = {task.id: task for task in self.tasks}

        # Get dependencies for each task
        dependencies: dict[str, set[str]] = {task.id: set() for task in self.tasks}
        for from_id, to_id in self.edges:
            dependencies[to_id].add(from_id)

        ready: list[Task] = []
        for task in self.tasks:
            if task.state != TaskState.PENDING:
                continue

            # Check if all dependencies are satisfied
            deps = dependencies[task.id]
            if all(
                task_map[dep_id].state == TaskState.SUCCESS for dep_id in deps if dep_id in task_map
            ):
                ready.append(task)

        return ready
