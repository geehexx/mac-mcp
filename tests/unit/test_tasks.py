"""Unit tests for task models."""

import pytest
from mac_mcp.domain.tasks import Task, TaskState


class TestTask:
    """Tests for Task model."""

    def test_task_creation(self) -> None:
        """Test creating a task."""
        task = Task(
            id="t1",
            goal_id="g1",
            description="Test task",
            required_capabilities=["python"],
        )

        assert task.id == "t1"
        assert task.goal_id == "g1"
        assert task.state == TaskState.PENDING
        assert task.progress == 0.0

    def test_task_assign(self) -> None:
        """Test assigning task to agent."""
        task = Task(
            id="t1",
            goal_id="g1",
            description="Test task",
        )

        task.assign_to("agent1")

        assert task.assigned_agent == "agent1"
        assert task.state == TaskState.RUNNING

    def test_task_assign_wrong_state(self) -> None:
        """Test that assign fails if not PENDING."""
        task = Task(
            id="t1",
            goal_id="g1",
            description="Test task",
            state=TaskState.RUNNING,
        )

        with pytest.raises(ValueError, match="Cannot assign"):
            task.assign_to("agent1")

    def test_task_update_progress(self) -> None:
        """Test updating task progress."""
        task = Task(
            id="t1",
            goal_id="g1",
            description="Test task",
            state=TaskState.RUNNING,
        )

        task.update_progress(0.5, "Half done")

        assert task.progress == 0.5
        assert task.metadata["last_progress_message"] == "Half done"

    def test_task_update_progress_invalid(self) -> None:
        """Test that invalid progress raises error."""
        task = Task(
            id="t1",
            goal_id="g1",
            description="Test task",
            state=TaskState.RUNNING,
        )

        with pytest.raises(ValueError, match="Progress must be between"):
            task.update_progress(1.5)

    def test_task_complete(self) -> None:
        """Test completing a task."""
        task = Task(
            id="t1",
            goal_id="g1",
            description="Test task",
            state=TaskState.RUNNING,
        )

        task.complete({"artifacts": ["file.py"]})

        assert task.state == TaskState.SUCCESS
        assert task.progress == 1.0
        assert task.result is not None

    def test_task_fail(self) -> None:
        """Test failing a task."""
        task = Task(
            id="t1",
            goal_id="g1",
            description="Test task",
            state=TaskState.RUNNING,
        )

        task.fail({"type": "error", "message": "Failed"})

        assert task.state == TaskState.ERROR
        assert task.error is not None

    def test_task_state_transitions(self) -> None:
        """Test valid state transitions."""
        task = Task(id="t1", goal_id="g1", description="Test")

        assert task.can_transition_to(TaskState.RUNNING)
        assert not task.can_transition_to(TaskState.SUCCESS)

        task.state = TaskState.RUNNING
        assert task.can_transition_to(TaskState.SUCCESS)
        assert task.can_transition_to(TaskState.ERROR)

        task.state = TaskState.SUCCESS
        assert not task.can_transition_to(TaskState.PENDING)

    def test_task_is_terminal(self) -> None:
        """Test terminal state detection."""
        task = Task(id="t1", goal_id="g1", description="Test")

        assert not task.is_terminal()

        task.state = TaskState.SUCCESS
        assert task.is_terminal()

        task.state = TaskState.ERROR
        assert task.is_terminal()
