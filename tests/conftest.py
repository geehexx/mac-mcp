"""Pytest configuration and shared fixtures."""

import pytest
from mac_mcp.core.orchestrator import Orchestrator
from mac_mcp.core.supervisor import AgentSupervisor
from mac_mcp.storage.memory import InMemoryEventStore


@pytest.fixture
async def event_store() -> InMemoryEventStore:
    """Create an in-memory event store for testing."""
    store = InMemoryEventStore()
    yield store
    await store.close()


@pytest.fixture
async def supervisor(event_store: InMemoryEventStore) -> AgentSupervisor:
    """Create an agent supervisor for testing."""
    return AgentSupervisor(event_store)


@pytest.fixture
async def orchestrator(
    event_store: InMemoryEventStore,
    supervisor: AgentSupervisor,
) -> Orchestrator:
    """Create an orchestrator for testing."""
    return Orchestrator(event_store, supervisor)
