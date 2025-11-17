"""Abstract interfaces for pluggable orchestration components.

These interfaces define the contract that external implementations
(including DSPy-optimized flows) must satisfy to integrate with the
MAC MCP core orchestration engine.
"""

from mac_mcp_core.interfaces.decomposer import AbstractGoalDecomposer
from mac_mcp_core.interfaces.matcher import AbstractAgentMatcher
from mac_mcp_core.interfaces.scheduler import AbstractScheduler

__all__ = [
    "AbstractGoalDecomposer",
    "AbstractAgentMatcher",
    "AbstractScheduler",
]
