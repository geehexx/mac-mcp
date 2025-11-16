"""Agent supervisor for managing agent lifecycle and health.

The supervisor implements the Supervisor pattern from Erlang/OTP,
monitoring agent health via heartbeats and recovering from failures.
"""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from mac_mcp.core.event_publisher import EventPublisher
from mac_mcp.domain.agents import Agent, AgentStatus
from mac_mcp.domain.events import AgentFailedEvent, AgentHeartbeatEvent, AgentRegisteredEvent
from mac_mcp.storage.base import EventStore


class AgentSupervisor:
    """Supervises agent lifecycle and health.

    The supervisor:
    - Tracks registered agents
    - Monitors heartbeats
    - Detects failures (missed heartbeats)
    - Quarantines repeatedly failing agents
    - Provides agent lookup by capability

    Attributes:
        event_store: Event store for recording agent events
        heartbeat_interval: Expected heartbeat interval in seconds
        heartbeat_timeout: Heartbeat timeout (missed beats = failure)
        max_concurrent_tasks: Maximum concurrent tasks per agent
    """

    def __init__(
        self,
        event_store: EventStore,
        heartbeat_interval: int = 30,
        heartbeat_timeout: int = 90,
        max_concurrent_tasks: int = 5,
    ) -> None:
        """Initialize the agent supervisor.

        Args:
            event_store: Event store for recording events
            heartbeat_interval: Expected heartbeat interval in seconds
            heartbeat_timeout: Heartbeat timeout in seconds
            max_concurrent_tasks: Max concurrent tasks per agent
        """
        self.event_store = event_store
        self.event_publisher = EventPublisher(event_store)
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.max_concurrent_tasks = max_concurrent_tasks

        self._agents: dict[str, Agent] = {}
        self._monitoring_task: asyncio.Task[None] | None = None
        self._shutdown = False

    async def register_agent(
        self,
        agent_id: str,
        capabilities: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> Agent:
        """Register a new agent.

        Args:
            agent_id: Unique agent identifier
            capabilities: List of capability tags
            metadata: Optional agent metadata

        Returns:
            Registered agent

        Raises:
            ValueError: If agent is already registered
        """
        if agent_id in self._agents:
            msg = f"Agent {agent_id} is already registered"
            raise ValueError(msg)

        agent = Agent(
            id=agent_id,
            capabilities=capabilities,
            metadata=metadata or {},
        )

        self._agents[agent_id] = agent

        await self.event_publisher.publish(
            AgentRegisteredEvent,
            agent_id=agent_id,
            payload={
                "capabilities": capabilities,
                "metadata": metadata or {},
            },
        )

        return agent

    async def update_heartbeat(
        self,
        agent_id: str,
        status: str = "healthy",
        current_tasks: list[str] | None = None,
        load: float | None = None,
    ) -> None:
        """Update agent heartbeat.

        Args:
            agent_id: Agent identifier
            status: Agent status (healthy, degraded, shutting_down)
            current_tasks: Current task IDs
            load: Optional load metric (0.0 to 1.0)

        Raises:
            KeyError: If agent is not registered
        """
        agent = self._agents[agent_id]
        agent.update_heartbeat(current_tasks)

        await self.event_publisher.publish(
            AgentHeartbeatEvent,
            agent_id=agent_id,
            payload={
                "status": status,
                "current_tasks": current_tasks or [],
                "load": load,
            },
        )

    async def mark_agent_failed(
        self,
        agent_id: str,
        reason: str = "missed_heartbeats",
    ) -> list[str]:
        """Mark an agent as failed.

        Args:
            agent_id: Agent identifier
            reason: Failure reason

        Returns:
            List of task IDs that were in progress

        Raises:
            KeyError: If agent is not registered
        """
        agent = self._agents[agent_id]
        in_progress_tasks = agent.current_tasks.copy()

        agent.status = AgentStatus.FAILED
        agent.current_tasks = []

        await self.event_publisher.publish(
            AgentFailedEvent,
            agent_id=agent_id,
            payload={
                "reason": reason,
                "last_heartbeat": agent.last_heartbeat.isoformat(),
                "in_progress_tasks": in_progress_tasks,
            },
        )

        return in_progress_tasks

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get agent by ID.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent if found, None otherwise
        """
        return self._agents.get(agent_id)

    def find_agents_by_capability(
        self,
        required_capabilities: list[str],
        only_available: bool = True,
    ) -> list[Agent]:
        """Find agents matching required capabilities.

        Args:
            required_capabilities: Required capability tags
            only_available: Only return agents that can accept tasks

        Returns:
            List of matching agents
        """
        matches: list[Agent] = []

        for agent in self._agents.values():
            if not agent.matches_capabilities(required_capabilities):
                continue

            if only_available and not agent.can_accept_task(self.max_concurrent_tasks):
                continue

            matches.append(agent)

        # Sort by success rate (best first)
        matches.sort(key=lambda a: a.success_rate(), reverse=True)

        return matches

    async def monitor_health(
        self,
        on_failure: Callable[[str, list[str]], None] | None = None,
    ) -> None:
        """Monitor agent health continuously.

        This coroutine runs in the background and checks for agents
        with missed heartbeats.

        Args:
            on_failure: Optional callback when agent fails (agent_id, tasks)
        """
        while not self._shutdown:
            now = datetime.now(UTC)

            for agent_id, agent in list(self._agents.items()):
                if agent.status != AgentStatus.ACTIVE:
                    continue

                elapsed = (now - agent.last_heartbeat).total_seconds()
                if elapsed > self.heartbeat_timeout:
                    tasks = await self.mark_agent_failed(agent_id, "missed_heartbeats")

                    if on_failure:
                        on_failure(agent_id, tasks)

            # Check every heartbeat_interval seconds
            await asyncio.sleep(self.heartbeat_interval)

    async def start_monitoring(
        self,
        on_failure: Callable[[str, list[str]], None] | None = None,
    ) -> None:
        """Start background health monitoring.

        Args:
            on_failure: Optional callback when agent fails
        """
        if self._monitoring_task is not None:
            return

        self._shutdown = False
        self._monitoring_task = asyncio.create_task(self.monitor_health(on_failure))

    async def stop_monitoring(self) -> None:
        """Stop background health monitoring."""
        self._shutdown = True
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

    def get_all_agents(self) -> list[Agent]:
        """Get all registered agents.

        Returns:
            List of all agents
        """
        return list(self._agents.values())

    def get_active_agents(self) -> list[Agent]:
        """Get all active agents.

        Returns:
            List of active agents
        """
        return [a for a in self._agents.values() if a.status == AgentStatus.ACTIVE]
