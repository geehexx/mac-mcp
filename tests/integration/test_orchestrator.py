"""Integration tests for orchestrator."""

import pytest
from mac_mcp.core.orchestrator import Orchestrator
from mac_mcp.core.supervisor import AgentSupervisor
from mac_mcp.domain.tasks import TaskState
from mac_mcp.storage.memory import InMemoryEventStore


@pytest.mark.integration
class TestOrchestratorIntegration:
    """Integration tests for orchestrator."""

    async def test_full_task_lifecycle(self) -> None:
        """Test complete task lifecycle from creation to completion."""
        store = InMemoryEventStore()
        supervisor = AgentSupervisor(store)
        orchestrator = Orchestrator(store, supervisor)

        # Register agent
        agent = await supervisor.register_agent(
            agent_id="agent1",
            capabilities=["python", "testing"],
        )

        # Create task
        task = await orchestrator.create_task(
            task_id="t1",
            goal_id="g1",
            description="Write tests",
            required_capabilities=["testing"],
        )

        assert task.state == TaskState.PENDING

        # Assign task
        await orchestrator.assign_task("t1", "agent1")
        assert task.state == TaskState.RUNNING
        assert task.assigned_agent == "agent1"

        # Update progress
        await orchestrator.update_task_progress("t1", "agent1", 0.5)
        assert task.progress == 0.5

        # Complete task
        await orchestrator.complete_task(
            "t1",
            "agent1",
            {"artifacts": ["tests.py"], "summary": "Tests written"},
        )

        assert task.state == TaskState.SUCCESS
        assert task.progress == 1.0
        assert agent.task_history["successful"] == 1

    async def test_task_failure_and_retry(self) -> None:
        """Test task failure and retry mechanism."""
        store = InMemoryEventStore()
        supervisor = AgentSupervisor(store)
        orchestrator = Orchestrator(store, supervisor)

        await supervisor.register_agent("agent1", ["python"])

        task = await orchestrator.create_task(
            "t1",
            "g1",
            "Test task",
            ["python"],
        )

        await orchestrator.assign_task("t1", "agent1")

        # Fail task (retryable)
        action = await orchestrator.fail_task(
            "t1",
            "agent1",
            {"type": "network_error", "message": "Timeout", "retryable": True},
        )

        assert action == "retry"
        assert task.state == TaskState.PENDING  # Reset for retry
        assert task.metadata["retry_count"] == 1

    async def test_claim_task_pull_model(self) -> None:
        """Test pull-based task claiming."""
        store = InMemoryEventStore()
        supervisor = AgentSupervisor(store)
        orchestrator = Orchestrator(store, supervisor)

        await supervisor.register_agent("agent1", ["python", "testing"])

        await orchestrator.create_task("t1", "g1", "Task 1", ["python"])
        await orchestrator.create_task("t2", "g1", "Task 2", ["testing"])

        # Agent claims first matching task
        claimed = await orchestrator.claim_task("agent1", ["python", "testing"])

        assert claimed is not None
        assert claimed.id in ["t1", "t2"]
        assert claimed.state == TaskState.RUNNING

    async def test_state_rebuild_from_events(self) -> None:
        """Test rebuilding state from event log."""
        store = InMemoryEventStore()
        supervisor = AgentSupervisor(store)
        orchestrator = Orchestrator(store, supervisor)

        # Perform operations
        await supervisor.register_agent("agent1", ["python"])
        await orchestrator.create_task("t1", "g1", "Test", ["python"])
        await orchestrator.assign_task("t1", "agent1")

        # Create new orchestrator and rebuild
        new_orchestrator = Orchestrator(store, supervisor)
        await new_orchestrator.rebuild_from_events()

        # Verify state was reconstructed
        task = new_orchestrator.get_task("t1")
        assert task is not None
        assert task.state == TaskState.RUNNING
        assert task.assigned_agent == "agent1"
