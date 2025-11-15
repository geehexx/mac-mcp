"""Property-based tests using Hypothesis."""

from hypothesis import given
from hypothesis import strategies as st

from mac_mcp.domain.events import Event, EventType
from mac_mcp.domain.tasks import Task, TaskState


class TestEventProperties:
    """Property-based tests for events."""

    @given(
        sequence=st.integers(min_value=1, max_value=1000000),
        task_id=st.text(min_size=1, max_size=50),
    )
    def test_event_sequence_is_preserved(self, sequence: int, task_id: str) -> None:
        """Property: Event sequence is always preserved."""
        event = Event(
            type=EventType.TASK_CREATED,
            sequence=sequence,
            task_id=task_id,
        )

        assert event.sequence == sequence
        assert event.task_id == task_id

    @given(
        progress=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_task_progress_always_valid(self, progress: float) -> None:
        """Property: Task progress is always between 0 and 1."""
        task = Task(
            id="t1",
            goal_id="g1",
            description="Test",
            state=TaskState.RUNNING,
        )

        task.update_progress(progress)

        assert 0.0 <= task.progress <= 1.0
        assert task.progress == progress

    @given(
        state=st.sampled_from(list(TaskState)),
    )
    def test_terminal_states_are_consistent(self, state: TaskState) -> None:
        """Property: Terminal state detection is consistent."""
        task = Task(id="t1", goal_id="g1", description="Test", state=state)

        is_terminal = task.is_terminal()
        expected_terminal = state in {TaskState.SUCCESS, TaskState.ERROR}

        assert is_terminal == expected_terminal

    @given(
        capabilities=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10),
        required=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10),
    )
    def test_capability_matching_is_symmetric(
        self,
        capabilities: list[str],
        required: list[str],
    ) -> None:
        """Property: Capability matching is based on set intersection."""
        from mac_mcp.domain.agents import Agent

        agent = Agent(id="a1", capabilities=capabilities)
        matches = agent.matches_capabilities(required)

        expected_match = bool(set(capabilities) & set(required))
        assert matches == expected_match
