"""Integration tests with real LLM (AWS Bedrock Claude Sonnet 4.5).

These tests use actual LLM API calls and incur costs.
Run with: pytest tests/integration/test_real_llm.py -v
"""

import os

import pytest

from mac_mcp.core.decomposer import GoalDecomposer
from mac_mcp.core.orchestrator import Orchestrator
from mac_mcp.core.supervisor import AgentSupervisor
from mac_mcp.domain.goals import GoalState
from mac_mcp.domain.tasks import TaskState
from mac_mcp.llm.bedrock_provider import BedrockProvider
from mac_mcp.storage.memory import InMemoryEventStore

# Skip if AWS credentials not available
pytestmark = pytest.mark.skipif(
    not os.environ.get("AWS_ACCESS_KEY_ID"),
    reason="AWS credentials required for Bedrock tests",
)


@pytest.mark.integration
@pytest.mark.slow
class TestRealLLMIntegration:
    """Integration tests with real Bedrock Claude Sonnet 4.5."""

    @pytest.fixture
    async def bedrock_provider(self) -> BedrockProvider:
        """Create Bedrock provider with Claude Sonnet 4.5."""
        return BedrockProvider(
            model="anthropic.claude-sonnet-4-5-20250929-v1:0",
            region="us-east-1",
        )

    @pytest.fixture
    async def orchestrator_with_llm(
        self, bedrock_provider: BedrockProvider
    ) -> Orchestrator:
        """Create orchestrator with real LLM."""
        store = InMemoryEventStore()
        supervisor = AgentSupervisor(store)
        decomposer = GoalDecomposer(llm_provider=bedrock_provider, temperature=0.3)
        return Orchestrator(store, supervisor, decomposer=decomposer)

    async def test_simple_goal_decomposition(
        self, orchestrator_with_llm: Orchestrator
    ) -> None:
        """Test basic goal decomposition with real LLM."""
        goal = await orchestrator_with_llm.submit_goal(
            goal_id="test_simple",
            description="Create a REST API endpoint for user authentication",
            context={"framework": "FastAPI", "auth_type": "JWT"},
            constraints={"timeline": "1 week"},
        )

        assert goal.state == GoalState.EXECUTING
        tasks = [
            t for t in orchestrator_with_llm._tasks.values() if t.goal_id == "test_simple"
        ]

        # Verify decomposition quality
        assert 3 <= len(tasks) <= 10, f"Expected 3-10 tasks, got {len(tasks)}"
        assert all(t.description for t in tasks), "All tasks should have descriptions"
        assert all(
            t.required_capabilities for t in tasks
        ), "All tasks should have capabilities"

        # Verify at least one task has no dependencies (entry point)
        entry_tasks = [t for t in tasks if not t.dependencies]
        assert entry_tasks, "Should have at least one task with no dependencies"

        # Verify task IDs are unique
        task_ids = [t.id for t in tasks]
        assert len(task_ids) == len(set(task_ids)), "Task IDs should be unique"

    async def test_complex_goal_with_dependencies(
        self, orchestrator_with_llm: Orchestrator
    ) -> None:
        """Test complex goal decomposition with dependency chains."""
        goal = await orchestrator_with_llm.submit_goal(
            goal_id="test_complex",
            description="Build a microservices-based e-commerce platform with user service, product catalog, shopping cart, and payment processing",
            context={
                "architecture": "microservices",
                "tech_stack": "Python, FastAPI, PostgreSQL, Redis, RabbitMQ",
                "deployment": "Kubernetes",
            },
            constraints={"timeline": "3 months", "team_size": "5 developers"},
        )

        assert goal.state == GoalState.EXECUTING
        tasks = [
            t for t in orchestrator_with_llm._tasks.values() if t.goal_id == "test_complex"
        ]

        # Complex goal should produce more tasks
        assert 5 <= len(tasks) <= 10, f"Expected 5-10 tasks, got {len(tasks)}"

        # Verify dependency structure
        tasks_with_deps = [t for t in tasks if t.dependencies]
        assert tasks_with_deps, "Complex goal should have tasks with dependencies"

        # Verify all dependencies reference valid task IDs
        all_task_ids = {t.id for t in tasks}
        for task in tasks:
            for dep_id in task.dependencies:
                assert (
                    dep_id in all_task_ids
                ), f"Dependency {dep_id} not found in task list"

    async def test_goal_with_specific_constraints(
        self, orchestrator_with_llm: Orchestrator
    ) -> None:
        """Test goal decomposition respects constraints."""
        goal = await orchestrator_with_llm.submit_goal(
            goal_id="test_constraints",
            description="Implement real-time chat feature",
            context={"framework": "FastAPI", "protocol": "WebSocket"},
            constraints={
                "max_tasks": "5",
                "priority": "high",
                "security": "end-to-end encryption required",
            },
        )

        assert goal.state == GoalState.EXECUTING
        tasks = [
            t
            for t in orchestrator_with_llm._tasks.values()
            if t.goal_id == "test_constraints"
        ]

        # Should respect max_tasks constraint (with some tolerance)
        assert len(tasks) <= 7, f"Expected ≤7 tasks (max_tasks=5 + tolerance), got {len(tasks)}"

        # Verify security-related capabilities are present
        all_capabilities = set()
        for task in tasks:
            all_capabilities.update(task.required_capabilities)

        # At least some tasks should mention security/encryption
        task_descriptions = " ".join(t.description.lower() for t in tasks)
        assert (
            "security" in task_descriptions
            or "encryption" in task_descriptions
            or "auth" in task_descriptions
        ), "Security constraints should be reflected in tasks"

    @pytest.mark.xfail(reason="May hit Bedrock rate limits", strict=False)
    async def test_concurrent_goal_processing(
        self, orchestrator_with_llm: Orchestrator
    ) -> None:
        """Test processing multiple goals with rate limiting."""
        import asyncio

        goals_data = [
            {
                "goal_id": "concurrent_1",
                "description": "Create user registration API",
                "context": {"framework": "FastAPI"},
            },
            {
                "goal_id": "concurrent_2",
                "description": "Implement email notification service",
                "context": {"service": "SendGrid"},
            },
        ]

        # Submit goals with delays to avoid throttling
        goals = []
        for goal_data in goals_data:
            goal = await orchestrator_with_llm.submit_goal(**goal_data)
            goals.append(goal)
            await asyncio.sleep(5)  # Rate limit: 5s between requests

        # Verify all goals were processed
        assert all(g.state == GoalState.EXECUTING for g in goals)

        # Verify tasks were created for each goal
        for goal_data in goals_data:
            goal_id = goal_data["goal_id"]
            tasks = [
                t
                for t in orchestrator_with_llm._tasks.values()
                if t.goal_id == goal_id
            ]
            assert len(tasks) >= 3, f"Goal {goal_id} should have at least 3 tasks"

    @pytest.mark.xfail(reason="May hit Bedrock rate limits", strict=False)
    async def test_task_claiming_and_execution(
        self, orchestrator_with_llm: Orchestrator
    ) -> None:
        """Test complete workflow: decomposition → claiming → execution."""
        # Register agent
        supervisor = orchestrator_with_llm.supervisor
        await supervisor.register_agent(
            "test_agent", ["python", "fastapi", "testing", "api_design"]
        )

        # Submit goal
        goal = await orchestrator_with_llm.submit_goal(
            goal_id="test_workflow",
            description="Create a simple CRUD API for blog posts",
            context={"framework": "FastAPI", "database": "PostgreSQL"},
        )

        assert goal.state == GoalState.EXECUTING

        # Claim first available task
        claimed_task = await orchestrator_with_llm.claim_task(
            "test_agent", ["python", "fastapi", "testing", "api_design"]
        )

        assert claimed_task is not None
        assert claimed_task.state == TaskState.RUNNING
        assert claimed_task.assigned_agent == "test_agent"

        # Update progress
        await orchestrator_with_llm.update_task_progress(
            claimed_task.id, "test_agent", 0.5, "Halfway done"
        )

        # Verify progress updated
        task = orchestrator_with_llm.get_task(claimed_task.id)
        assert task is not None
        assert task.progress == 0.5

        # Complete task
        await orchestrator_with_llm.complete_task(
            claimed_task.id, "test_agent", {"status": "success"}
        )

        # Verify completion
        task = orchestrator_with_llm.get_task(claimed_task.id)
        assert task is not None
        assert task.state == TaskState.SUCCESS
        assert task.progress == 1.0

    async def test_decomposition_quality_metrics(
        self, orchestrator_with_llm: Orchestrator
    ) -> None:
        """Test and measure decomposition quality."""
        goal = await orchestrator_with_llm.submit_goal(
            goal_id="test_quality",
            description="Implement a machine learning pipeline for sentiment analysis",
            context={
                "ml_framework": "scikit-learn",
                "data_source": "Twitter API",
                "deployment": "AWS Lambda",
            },
            constraints={"accuracy_target": "85%", "latency": "<100ms"},
        )

        tasks = [
            t for t in orchestrator_with_llm._tasks.values() if t.goal_id == "test_quality"
        ]

        # Quality metrics
        metrics = {
            "task_count": len(tasks),
            "avg_description_length": sum(len(t.description) for t in tasks)
            / len(tasks),
            "avg_capabilities_per_task": sum(len(t.required_capabilities) for t in tasks)
            / len(tasks),
            "tasks_with_dependencies": len([t for t in tasks if t.dependencies]),
            "max_dependency_depth": self._calculate_max_depth(tasks),
        }

        # Assertions for quality
        assert metrics["task_count"] >= 4, "ML pipeline should have ≥4 tasks"
        assert (
            metrics["avg_description_length"] >= 30
        ), "Task descriptions should be detailed"
        assert (
            metrics["avg_capabilities_per_task"] >= 1.5
        ), "Tasks should require multiple capabilities"
        assert (
            metrics["tasks_with_dependencies"] >= 2
        ), "Should have dependency chains"

        # Print metrics for analysis
        print("\n=== Decomposition Quality Metrics ===")
        for key, value in metrics.items():
            print(f"{key}: {value}")

    def _calculate_max_depth(self, tasks: list) -> int:
        """Calculate maximum dependency depth in task DAG."""
        task_map = {t.id: t for t in tasks}
        depths = {}

        def get_depth(task_id: str) -> int:
            if task_id in depths:
                return depths[task_id]

            task = task_map.get(task_id)
            if not task or not task.dependencies:
                depths[task_id] = 0
                return 0

            max_dep_depth = max(
                (get_depth(dep_id) for dep_id in task.dependencies), default=0
            )
            depths[task_id] = max_dep_depth + 1
            return depths[task_id]

        return max((get_depth(t.id) for t in tasks), default=0)

    @pytest.mark.xfail(reason="May hit Bedrock rate limits", strict=False)
    async def test_error_recovery_and_retry(
        self, bedrock_provider: BedrockProvider
    ) -> None:
        """Test decomposer retry logic with real LLM."""
        decomposer = GoalDecomposer(llm_provider=bedrock_provider, temperature=0.3)

        # Test with a goal that might need retry
        dag = await decomposer.decompose(
            goal_id="test_retry",
            description="Build a distributed system",
            context={"architecture": "microservices"},
            max_retries=3,
        )

        # Should succeed after retries if needed
        assert len(dag.tasks) >= 3
        assert dag.validate_acyclic()
