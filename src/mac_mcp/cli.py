"""CLI entry point for MAC MCP Server."""

import asyncio
import logging
import sys
from pathlib import Path

from mac_mcp.config import MACConfig, load_config
from mac_mcp.core.decomposer import GoalDecomposer
from mac_mcp.core.orchestrator import Orchestrator
from mac_mcp.core.supervisor import AgentSupervisor
from mac_mcp.llm.factory import create_llm_provider
from mac_mcp.mcp.server import run_stdio_server
from mac_mcp.storage.jsonl import JSONLEventStore
from mac_mcp.ui.dashboard import Dashboard


def setup_logging(config: MACConfig) -> None:
    """Setup logging based on configuration.

    Args:
        config: MAC configuration
    """
    log_config = config.logging

    # Create logger
    logger = logging.getLogger("mac_mcp")
    logger.setLevel(getattr(logging, log_config.level.value))

    # Console handler
    if log_config.console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_config.format))
        logger.addHandler(console_handler)

    # File handler
    if log_config.file:
        log_file = Path(log_config.file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_config.format))
        logger.addHandler(file_handler)


async def run_with_tui(
    orchestrator: Orchestrator,
    event_store: JSONLEventStore,
    config: MACConfig,
) -> None:
    """Run server with TUI dashboard.

    Args:
        orchestrator: Orchestrator instance
        event_store: Event store
        config: MAC configuration
    """
    # Create dashboard
    dashboard = Dashboard(orchestrator, config.ui)

    # Run server and dashboard concurrently
    server_task = asyncio.create_task(
        run_stdio_server(event_store, orchestrator)
    )

    dashboard_task = asyncio.create_task(
        dashboard.run()
    )

    # Wait for either to complete (dashboard will complete on Ctrl+C)
    done, pending = await asyncio.wait(
        [server_task, dashboard_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    # Cancel remaining tasks
    for task in pending:
        task.cancel()


async def async_main(config_path: Path | None = None) -> int:
    """Async main entry point.

    Args:
        config_path: Optional path to config file

    Returns:
        Exit code
    """
    try:
        # Load configuration
        config = load_config(config_path)

        # Setup logging
        setup_logging(config)

        logger = logging.getLogger("mac_mcp")
        logger.info("Starting MAC MCP Server")
        logger.info(f"LLM Provider: {config.llm.provider.value}")
        logger.info(f"Model: {config.llm.model}")
        logger.info(f"UI Mode: {config.ui.mode}")

        # Create LLM provider
        llm_provider = create_llm_provider(config.llm)
        logger.info(f"LLM provider initialized: {llm_provider.get_model_name()}")

        # Create goal decomposer
        decomposer = GoalDecomposer(
            llm_provider=llm_provider,
            max_tokens=config.llm.max_tokens,
            temperature=config.llm.temperature,
        )

        # Create event store
        event_store = JSONLEventStore(config.server.event_store_path)

        # Create supervisor
        supervisor = AgentSupervisor(event_store)

        # Create orchestrator
        orchestrator = Orchestrator(
            event_store=event_store,
            supervisor=supervisor,
            decomposer=decomposer,
        )

        # Rebuild state from event log
        logger.info("Rebuilding state from event log...")
        await orchestrator.rebuild_from_events()
        logger.info(
            f"State rebuilt: {len(orchestrator._goals)} goals, "
            f"{len(orchestrator._tasks)} tasks, "
            f"{len(supervisor.get_all_agents())} agents"
        )

        # Run based on UI mode
        if config.ui.mode == "tui":
            logger.info("Starting in TUI mode")
            await run_with_tui(orchestrator, event_store, config)
        elif config.ui.mode == "headless":
            logger.info("Starting in headless mode")
            await run_stdio_server(event_store, orchestrator)
        else:
            logger.error(f"Unsupported UI mode: {config.ui.mode}")
            return 1

        logger.info("MAC MCP Server stopped")
        return 0

    except KeyboardInterrupt:
        logger = logging.getLogger("mac_mcp")
        logger.info("Received keyboard interrupt, shutting down...")
        return 0

    except Exception as e:
        logger = logging.getLogger("mac_mcp")
        logger.exception(f"Fatal error: {e}")
        return 1


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    # Parse command line arguments
    config_path = None
    if len(sys.argv) > 1:
        config_path = Path(sys.argv[1])

    # Run async main
    return asyncio.run(async_main(config_path))


if __name__ == "__main__":
    sys.exit(main())
