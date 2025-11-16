# MAC MCP Server

Multi-Agent Coordination server for autonomous LLM agent teams using the Model Context Protocol.

## Features

- **Autonomous Goal Decomposition**: LLM-powered task graph generation
- **Agent Orchestration**: Supervisor/worker pattern with capability matching
- **Event Sourcing**: Immutable JSONL event log for state management
- **Pull-based Task Assignment**: Agents claim work matching their capabilities
- **Fault Tolerance**: Heartbeat monitoring and automatic task reassignment
- **Multi-Provider LLM**: Anthropic API or AWS Bedrock support

## Installation

```bash
git clone https://github.com/geehexx/mac-mcp.git
cd mac-mcp
pip install -e .
```

## Configuration

Create `config.yaml`:

```yaml
llm:
  provider: "anthropic"  # or "bedrock"
  model: "claude-sonnet-4-5-20250929"
  api_key: "your-api-key"

server:
  transport: "stdio"
  event_store_path: "data/events.jsonl"

ui:
  mode: "tui"  # or "headless"
```

Or use environment variables with `MAC_` prefix.

## Usage

```bash
# Start server
mac-mcp --config config.yaml

# With TUI dashboard
mac-mcp --config config.yaml --ui tui

# Headless mode
mac-mcp --config config.yaml --ui headless
```

## MCP Tools

Agents use these tools to interact with the server:

- `register_agent`: Register with capabilities
- `claim_task`: Pull next available task
- `update_task_progress`: Report progress
- `complete_task`: Submit results
- `fail_task`: Report errors
- `send_heartbeat`: Maintain status
- `submit_goal`: Create new goal (advanced)
- `request_dependency`: Get dependency results

## Architecture

The server implements:

1. **Actor Model**: No direct agent-to-agent communication
2. **Event Sourcing**: All state changes logged to JSONL
3. **Supervisor Pattern**: Health monitoring and failure handling
4. **State Machine**: Deterministic task state transitions

See [ARCHITECTURE.md](ARCHITECTURE.md) for details.

## Agent Integration

See [AGENTS.md](AGENTS.md) for agent implementation guide.

## Development

```bash
# Run tests
pytest

# Type checking
mypy src

# Linting
ruff check src
```

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and patterns
- [PROTOCOL.md](PROTOCOL.md) - MCP protocol specification
- [AGENTS.md](AGENTS.md) - Agent integration guide
- [ROADMAP.md](ROADMAP.md) - Future enhancements

## License

MIT License - see LICENSE file for details.
