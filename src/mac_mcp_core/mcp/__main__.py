"""MCP server entry point for stdio transport."""

import asyncio
import os
import sys
from pathlib import Path


def main() -> None:
    """Run MCP server with stdio transport.

    Environment variables:
    - MAC_STORAGE_PATH: path to JSONL event store (default: in-memory)
    - MAC_MCP_DECOMPOSER__TYPE: decomposer type (simple, template, dspy, mcp_remote)
    - MAC_MCP_DECOMPOSER__LLM__PROVIDER: llm provider (anthropic, bedrock)
    - MAC_MCP_DECOMPOSER__LLM__MODEL: model ID
    - MAC_MCP_DECOMPOSER__LLM__API_KEY: API key for Anthropic provider
    - MAC_MCP_MATCHER__TYPE: matcher type (basic, load_balanced, dspy, mcp_remote)
    - MAC_MCP_SCHEDULER__TYPE: scheduler type (topological, priority, deadline, dspy, mcp_remote)
    - AWS_REGION: AWS region for Bedrock (default: us-east-1)
    - ANTHROPIC_API_KEY: API key for Anthropic provider (legacy, use MAC_MCP_DECOMPOSER__LLM__API_KEY)
    """
    from mac_mcp_core.config import OrchestratorConfig, DecomposerConfig, LLMConfig
    from mac_mcp_core.orchestrator import Orchestrator
    from mac_mcp_core.supervisor import AgentSupervisor
    from mac_mcp_core.mcp.server import run_stdio_server
    from mac_mcp_reference.factory import ComponentFactory

    # Storage setup
    storage_path = os.getenv("MAC_STORAGE_PATH")
    if storage_path:
        from mac_mcp_core.storage.jsonl import JSONLEventStore
        event_store = JSONLEventStore(Path(storage_path))
    else:
        from mac_mcp_core.storage.memory import InMemoryEventStore
        event_store = InMemoryEventStore()

    # Load configuration from environment
    config = OrchestratorConfig()

    # Legacy environment variable support for backward compatibility
    if not config.decomposer.llm and os.getenv("ANTHROPIC_API_KEY"):
        config.decomposer.llm = LLMConfig(
            provider="anthropic",
            model=os.getenv("MAC_LLM_MODEL", "claude-sonnet-4-5-20250929"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )
    elif not config.decomposer.llm and os.getenv("AWS_ACCESS_KEY_ID"):
        config.decomposer.llm = LLMConfig(
            provider="bedrock",
            model=os.getenv("MAC_LLM_MODEL", "anthropic.claude-sonnet-4-5-20250929-v1:0"),
        )

    # Create supervisor
    supervisor = AgentSupervisor(event_store)

    # Create pluggable components using factory
    try:
        decomposer = None
        if config.decomposer.llm:
            decomposer = ComponentFactory.create_decomposer(config.decomposer)
    except Exception as e:
        # LLM not available, submit_goal will fail but other tools work
        print(f"Warning: Could not create decomposer: {e}", file=sys.stderr)

    try:
        matcher = ComponentFactory.create_matcher(config.matcher)
    except Exception as e:
        print(f"Critical Error: Could not create agent matcher: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        scheduler = ComponentFactory.create_scheduler(config.scheduler)
    except Exception as e:
        print(f"Critical Error: Could not create task scheduler: {e}", file=sys.stderr)
        sys.exit(1)

    # Create orchestrator with pluggable components
    orchestrator = Orchestrator(
        event_store=event_store,
        supervisor=supervisor,
        decomposer=decomposer,
        matcher=matcher,
        scheduler=scheduler,
    )

    try:
        asyncio.run(run_stdio_server(event_store, orchestrator))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
