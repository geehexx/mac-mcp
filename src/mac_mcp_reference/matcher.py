"""Basic capability-based agent matcher implementation.

This module provides a simple but effective implementation of the
AbstractAgentMatcher interface using capability subset matching.
"""

from typing import Any

from mac_mcp_core.domain.agents import Agent
from mac_mcp_core.domain.tasks import Task
from mac_mcp_core.interfaces.matcher import AbstractAgentMatcher


class BasicMatcher(AbstractAgentMatcher):
    """Basic capability-based agent matcher.

    Selects agents based on:
    1. Capability requirements (must have ALL required capabilities)
    2. Agent availability (workload)
    3. Historical success rate

    For production optimization, consider:
    - LoadBalancedMatcher: Advanced workload balancing
    - DSPyMatcher: Learned matching via optimization
    - CostOptimizedMatcher: Cost-aware agent selection
    - MCPRemoteMatcher: Delegate to external MCP service
    """

    def __init__(self, max_concurrent_tasks: int = 5):
        """Initialize the basic matcher.

        Args:
            max_concurrent_tasks: Maximum concurrent tasks per agent
        """
        self.max_concurrent_tasks = max_concurrent_tasks

    async def match_agent(
        self,
        task: Task,
        available_agents: list[Agent],
        _context: dict[str, Any] | None = None,
    ) -> str | None:
        """Select the best agent for a task using capability matching.

        Args:
            task: Task requiring assignment
            available_agents: List of available agents
            _context: Additional context (ignored in basic implementation)

        Returns:
            Agent ID of selected agent, or None if no suitable agent found
        """
        required_caps = set(task.required_capabilities)
        candidates: list[Agent] = []

        # Filter agents by capability and availability
        for agent in available_agents:
            agent_caps = set(agent.capabilities)

            # Must have ALL required capabilities
            if not required_caps.issubset(agent_caps):
                continue

            # Must be able to accept tasks
            if not agent.can_accept_task(self.max_concurrent_tasks):
                continue

            candidates.append(agent)

        if not candidates:
            return None

        # Sort by success rate (best first)
        candidates.sort(key=lambda a: a.success_rate(), reverse=True)

        return candidates[0].id

    def get_implementation_name(self) -> str:
        """Get the implementation name."""
        return "basic_capability"
