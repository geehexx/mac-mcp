"""MCP server entry point for stdio transport."""

import asyncio
import sys


def main() -> None:
    """Run MCP server with stdio transport."""
    from mac_mcp.mcp.server import run_stdio_server
    from mac_mcp.storage.memory import InMemoryEventStore

    event_store = InMemoryEventStore()
    
    try:
        asyncio.run(run_stdio_server(event_store))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
