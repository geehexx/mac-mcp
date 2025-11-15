"""
Multi-Agent Coordination MCP Server.

A protocol-sound orchestrator for autonomous LLM-based agent teams.
"""

__version__ = "0.1.0"
__author__ = "geehexx"
__license__ = "MIT"

from mac_mcp.domain.agents import Agent, AgentStatus
from mac_mcp.domain.events import Event, EventType
from mac_mcp.domain.goals import Goal, GoalState
from mac_mcp.domain.tasks import Task, TaskState

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "Agent",
    "AgentStatus",
    "Event",
    "EventType",
    "Goal",
    "GoalState",
    "Task",
    "TaskState",
]
