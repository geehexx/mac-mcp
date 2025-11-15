"""CLI entry point for MAC MCP Server."""

import asyncio
import sys
from pathlib import Path

from mac_mcp.core.orchestrator import Orchestrator
from mac_mcp.core.supervisor import AgentSupervisor
from mac_mcp.mcp.server import run_stdio_server
from mac_mcp.storage.jsonl import JSONLEventStore
from mac_mcp.storage.memory import InMemoryEventStore


def main() -> None:
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Multi-Agent Coordination MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--mode",
        choices=["dev", "prod", "headless"],
        default="dev",
        help="Server mode (default: dev)",
    )

    parser.add_argument(
        "--storage",
        choices=["memory", "file"],
        default="file",
        help="Storage backend (default: file)",
    )

    parser.add_argument(
        "--events-path",
        type=Path,
        default=Path("events.jsonl"),
        help="Path to events file (default: events.jsonl)",
    )

    parser.add_argument(
        "--snapshot-path",
        type=Path,
        default=Path("snapshot.json"),
        help="Path to snapshot file (default: snapshot.json)",
    )

    args = parser.parse_args()

    # Create event store
    if args.storage == "memory":
        event_store = InMemoryEventStore()
    else:
        event_store = JSONLEventStore(
            events_path=args.events_path,
            snapshot_path=args.snapshot_path,
        )

    # Create orchestrator
    supervisor = AgentSupervisor(event_store)
    orchestrator = Orchestrator(event_store, supervisor)

    # Run MCP server
    try:
        asyncio.run(run_stdio_server(event_store, orchestrator))
    except KeyboardInterrupt:
        print("\nShutting down...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
