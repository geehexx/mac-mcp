"""LLM provider interface.

The core package defines the abstract LLM provider interface,
while concrete implementations live in mac_mcp_reference.
"""

from mac_mcp_core.llm.base import LLMProvider


__all__ = ["LLMProvider"]
