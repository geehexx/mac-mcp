"""MAC MCP Reference - Default out-of-the-box implementation.

This package provides simple, working implementations of the abstract
interfaces defined in mac_mcp_core:
- SimpleDecomposer: LLM-based goal decomposition
- BasicMatcher: Capability-based agent matching
- TopologicalScheduler: Dependency-ordered task scheduling

These implementations serve as:
1. A working baseline for new deployments
2. Reference examples for custom implementations
3. Test fixtures for development

For production use, these can be replaced with optimized implementations
(e.g., DSPy-powered flows) via the pluggable interface system.
"""

__version__ = "0.1.0"

__all__ = [
    "__version__",
]
