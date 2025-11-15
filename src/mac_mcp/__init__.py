"""
Multi-Agent Coordination MCP Server.

A protocol-sound orchestrator for autonomous LLM-based agent teams.
"""

__version__ = "0.1.0"
__author__ = "geehexx"
__license__ = "MIT"

from mac_mcp.domain.events import Event, EventType
from mac_mcp.domain.tasks import Task, TaskState
from mac_mcp.domain.agents import Agent, AgentStatus

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "Event",
    "EventType",
    "Task",
    "TaskState",
    "Agent",
    "AgentStatus",
]
