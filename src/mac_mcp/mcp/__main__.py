"""MCP server entry point for stdio transport."""

import asyncio
import sys

from mac_mcp.mcp.server import run_stdio_server
from mac_mcp.storage.memory import InMemoryEventStore


async def main() -> None:
    """Run MCP server with stdio transport."""
    # Use in-memory storage for MCP server mode
    # Production deployments should use JSONL or other persistent storage
    event_store = InMemoryEventStore()
    await run_stdio_server(event_store)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
