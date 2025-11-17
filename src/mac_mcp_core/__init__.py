"""MAC MCP Core - Protocol-agnostic event-sourced orchestration backbone.

This package provides the essential infrastructure for multi-agent coordination:
- Event sourcing (events, storage)
- Agent management (heartbeat, state models)
- Authentication and authorization
- MCP protocol handlers
- Abstract interfaces for pluggable orchestration components

The core is decoupled from specific implementation strategies for:
- Goal decomposition
- Agent matching
- Task scheduling

External systems (e.g., DSPy optimization frameworks) can provide these
implementations via the Model Context Protocol (MCP).
"""

__version__ = "0.1.0"

__all__ = [
    "__version__",
]
