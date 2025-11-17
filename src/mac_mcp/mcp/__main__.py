"""MCP server entry point for stdio transport."""

import asyncio
import os
import sys
from pathlib import Path


def main() -> None:
    """Run MCP server with stdio transport.
    
    Environment variables:
    - MAC_STORAGE_PATH: path to JSONL event store (default: in-memory)
    - MAC_LLM_PROVIDER: llm provider (bedrock or anthropic, default: bedrock)
    - MAC_LLM_MODEL: model ID (default: anthropic.claude-sonnet-4-5-20250929-v1:0)
    - AWS_REGION: AWS region for Bedrock (default: us-east-1)
    - ANTHROPIC_API_KEY: API key for Anthropic provider
    """
    from mac_mcp.core.decomposer import GoalDecomposer
    from mac_mcp.core.orchestrator import Orchestrator
    from mac_mcp.core.supervisor import AgentSupervisor
    from mac_mcp.mcp.server import run_stdio_server

    # Storage setup
    storage_path = os.getenv("MAC_STORAGE_PATH")
    if storage_path:
        from mac_mcp.storage.jsonl import JSONLEventStore
        event_store = JSONLEventStore(Path(storage_path))
    else:
        from mac_mcp.storage.memory import InMemoryEventStore
        event_store = InMemoryEventStore()
    
    supervisor = AgentSupervisor(event_store)
    
    # Try to create LLM provider if credentials available
    decomposer = None
    provider = os.getenv("MAC_LLM_PROVIDER", "bedrock")
    
    try:
        if provider == "bedrock" and (os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE")):
            from mac_mcp.llm.bedrock_provider import BedrockProvider
            
            model = os.getenv("MAC_LLM_MODEL", "anthropic.claude-sonnet-4-5-20250929-v1:0")
            region = os.getenv("AWS_REGION", "us-east-1")
            llm = BedrockProvider(model=model, region=region)
            decomposer = GoalDecomposer(llm_provider=llm, temperature=0.3)
            
        elif provider == "anthropic" and os.getenv("ANTHROPIC_API_KEY"):
            from mac_mcp.llm.anthropic_provider import AnthropicProvider
            
            api_key = os.getenv("ANTHROPIC_API_KEY")
            model = os.getenv("MAC_LLM_MODEL", "claude-sonnet-4-5-20250929")
            llm = AnthropicProvider(api_key=api_key, model=model)
            decomposer = GoalDecomposer(llm_provider=llm, temperature=0.3)
    except Exception:
        # LLM not available, submit_goal will fail but other tools work
        pass
    
    orchestrator = Orchestrator(event_store, supervisor, decomposer=decomposer)
    
    try:
        asyncio.run(run_stdio_server(event_store, orchestrator))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
