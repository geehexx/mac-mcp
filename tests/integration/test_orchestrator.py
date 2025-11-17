"""Integration tests for orchestrator."""

from typing import Any

import pytest

from mac_mcp.core.decomposer import GoalDecomposer
from mac_mcp.core.orchestrator import Orchestrator
from mac_mcp.core.supervisor import AgentSupervisor
from mac_mcp.domain.goals import GoalState
from mac_mcp.domain.tasks import TaskState
from mac_mcp.llm.base import LLMProvider
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


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response: str | None = None) -> None:
        """Initialize mock provider.

        Args:
            response: Predefined response to return
        """
        self.response = response or self._default_response()
        self.calls: list[dict[str, Any]] = []

    async def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        timeout: float = 60.0,
    ) -> str:
        """Generate mock response.

        Args:
            prompt: Input prompt
            max_tokens: Max tokens
            temperature: Temperature
            timeout: Timeout in seconds (ignored in mock)

        Returns:
            Mock response
        """
        self.calls.append(
            {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "timeout": timeout,
            }
        )
        return self.response

    def get_model_name(self) -> str:
        """Get model name."""
        return "mock-model"

    @staticmethod
    def _default_response() -> str:
        """Generate default mock decomposition response."""
        return """
        {
          "reasoning": "Breaking down authentication feature into research, implementation, and testing phases",
          "tasks": [
            {
              "id": "task_1",
              "description": "Research and design the feature",
              "required_capabilities": ["research", "design"],
              "dependencies": []
            },
            {
              "id": "task_2",
              "description": "Implement core functionality",
              "required_capabilities": ["python", "coding"],
              "dependencies": ["task_1"]
            },
            {
              "id": "task_3",
              "description": "Write comprehensive tests",
              "required_capabilities": ["testing", "python"],
              "dependencies": ["task_2"]
            }
          ],
          "edges": [
            ["task_1", "task_2"],
            ["task_2", "task_3"]
          ]
        }
        """


@pytest.mark.integration
class TestGoalWorkflowIntegration:
    """Integration tests for complete goal workflow."""

    async def test_goal_submission_and_decomposition(self) -> None:
        """Test goal submission with autonomous decomposition."""
        store = InMemoryEventStore()
        supervisor = AgentSupervisor(store)
        mock_llm = MockLLMProvider()
        decomposer = GoalDecomposer(llm_provider=mock_llm)
        orchestrator = Orchestrator(store, supervisor, decomposer=decomposer)

        # Submit goal (decomposition is awaited, so it completes before returning)
        goal = await orchestrator.submit_goal(
            goal_id="goal_1",
            description="Implement user authentication feature",
            context={"framework": "FastAPI", "auth_type": "JWT"},
            constraints={"timeline": "2 weeks", "security": "high"},
        )

        # Verify goal created and decomposed
        assert goal.id == "goal_1"
        # After submit_goal returns, decomposition is complete and goal is EXECUTING
        assert goal.state == GoalState.EXECUTING
        assert goal.description == "Implement user authentication feature"

        # Verify tasks were created (no sleep needed - decomposition is synchronous)
        tasks = [t for t in orchestrator._tasks.values() if t.goal_id == "goal_1"]
        assert len(tasks) == 3
        assert tasks[0].id == "task_1"
        assert tasks[1].id == "task_2"
        assert tasks[2].id == "task_3"

        # Verify dependencies
        assert len(tasks[0].dependencies) == 0
        assert tasks[1].dependencies == ["task_1"]
        assert tasks[2].dependencies == ["task_2"]

        # Verify LLM was called
        assert len(mock_llm.calls) == 1
        assert "Implement user authentication feature" in mock_llm.calls[0]["prompt"]
        assert "FastAPI" in mock_llm.calls[0]["prompt"]
        assert "JWT" in mock_llm.calls[0]["prompt"]

    async def test_full_goal_workflow_with_dependencies(self) -> None:
        """Test complete workflow: goal → decomposition → task execution → completion."""
        store = InMemoryEventStore()
        supervisor = AgentSupervisor(store)
        mock_llm = MockLLMProvider()
        decomposer = GoalDecomposer(llm_provider=mock_llm)
        orchestrator = Orchestrator(store, supervisor, decomposer=decomposer)

        # Register agents with different capabilities
        await supervisor.register_agent(
            agent_id="research_agent", capabilities=["research", "design"]
        )
        await supervisor.register_agent(
            agent_id="coding_agent", capabilities=["python", "coding"]
        )
        await supervisor.register_agent(
            agent_id="testing_agent", capabilities=["testing", "python"]
        )

        # Submit goal (decomposition completes before returning)
        goal = await orchestrator.submit_goal(
            goal_id="goal_complete",
            description="Build REST API endpoint",
        )

        # Goal should be EXECUTING after submit_goal returns
        assert goal.state == GoalState.EXECUTING

        # Get tasks (already created - no sleep needed)
        task_1 = orchestrator.get_task("task_1")
        task_2 = orchestrator.get_task("task_2")
        task_3 = orchestrator.get_task("task_3")

        assert task_1 is not None
        assert task_2 is not None
        assert task_3 is not None

        # Task 1 should be READY (no dependencies)
        assert task_1.state == TaskState.PENDING

        # Task 2 and 3 should be PENDING (have dependencies)
        assert task_2.state == TaskState.PENDING
        assert task_3.state == TaskState.PENDING

        # Agent 1 claims and completes task 1
        claimed = await orchestrator.claim_task("research_agent", ["research", "design"])
        assert claimed is not None
        assert claimed.id == "task_1"

        await orchestrator.complete_task(
            "task_1",
            "research_agent",
            {"design_doc": "API design complete"},
        )

        # Task 2 should now be available (dependency resolved)
        assert task_2.state == TaskState.PENDING

        # Agent 2 claims and completes task 2
        claimed = await orchestrator.claim_task("coding_agent", ["python", "coding"])
        assert claimed is not None
        assert claimed.id == "task_2"

        # Request dependency result
        dep_result = orchestrator.get_dependency_result("task_1")
        assert dep_result is not None
        assert dep_result["design_doc"] == "API design complete"

        await orchestrator.complete_task(
            "task_2",
            "coding_agent",
            {"code": "endpoint_implemented.py"},
        )

        # Task 3 should now be available
        assert task_3.state == TaskState.PENDING

        # Agent 3 claims and completes task 3
        claimed = await orchestrator.claim_task("testing_agent", ["testing", "python"])
        assert claimed is not None
        assert claimed.id == "task_3"

        await orchestrator.complete_task(
            "task_3",
            "testing_agent",
            {"tests": "test_endpoint.py", "coverage": "100%"},
        )

        # All tasks completed - verify goal state
        updated_goal = orchestrator.get_goal("goal_complete")
        assert updated_goal is not None

        # Calculate progress
        task_states = {t.id: t.state.value for t in [task_1, task_2, task_3]}
        progress = updated_goal.calculate_progress(task_states)
        assert progress == 1.0  # 100% complete

    async def test_dependency_blocking(self) -> None:
        """Test that tasks are blocked until dependencies complete."""
        store = InMemoryEventStore()
        supervisor = AgentSupervisor(store)
        mock_llm = MockLLMProvider()
        decomposer = GoalDecomposer(llm_provider=mock_llm)
        orchestrator = Orchestrator(store, supervisor, decomposer=decomposer)

        # Register agent
        await supervisor.register_agent("agent1", ["research", "design", "python", "coding"])

        # Submit goal (decomposition completes synchronously)
        goal = await orchestrator.submit_goal("goal_dep", "Test dependencies")
        assert goal.state == GoalState.EXECUTING

        # Try to claim task 2 before task 1 is complete
        # Should return task 1 instead (only available task)
        claimed = await orchestrator.claim_task(
            "agent1", ["research", "design", "python", "coding"]
        )
        assert claimed is not None
        assert claimed.id == "task_1"  # Only task 1 is available

        # Complete task 1
        await orchestrator.complete_task("task_1", "agent1", {})

        # Now task 2 should be available
        claimed = await orchestrator.claim_task(
            "agent1", ["research", "design", "python", "coding"]
        )
        assert claimed is not None
        assert claimed.id == "task_2"

    async def test_goal_failure_propagation(self) -> None:
        """Test that goal state reflects task failures."""
        store = InMemoryEventStore()
        supervisor = AgentSupervisor(store)
        mock_llm = MockLLMProvider()
        decomposer = GoalDecomposer(llm_provider=mock_llm)
        orchestrator = Orchestrator(store, supervisor, decomposer=decomposer)

        await supervisor.register_agent("agent1", ["research", "design"])

        # Submit goal (decomposition completes synchronously)
        goal = await orchestrator.submit_goal("goal_fail", "Test failure")
        assert goal.state == GoalState.EXECUTING

        # Claim and fail a task
        claimed = await orchestrator.claim_task("agent1", ["research", "design"])
        assert claimed is not None

        await orchestrator.fail_task(
            claimed.id,
            "agent1",
            {"error": "Critical failure", "retryable": False},
        )

        # Verify task is in ERROR state
        task = orchestrator.get_task(claimed.id)
        assert task is not None
        assert task.state == TaskState.ERROR

        # Goal should reflect failure in progress calculation
        updated_goal = orchestrator.get_goal("goal_fail")
        assert updated_goal is not None
        task_states = {
            t.id: t.state.value for t in orchestrator._tasks.values() if t.goal_id == "goal_fail"
        }
        progress = updated_goal.calculate_progress(task_states)
        assert progress < 1.0  # Not complete due to failure
