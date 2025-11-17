# Example Agents

Production-ready agent templates demonstrating MAC MCP Server integration.

## `simple_agent.py`

Complete agent implementation with all best practices:

- Agent registration with capabilities
- Heartbeat loop (30s interval, <90s timeout)
- Pull-based task claiming with backpressure
- Progress reporting and error handling
- Concurrent task execution
- Graceful shutdown (SIGINT)

**Usage**:
```bash
python examples/simple_agent.py --agent-id my_agent \
    --capabilities python,testing,docs \
    --max-concurrent-tasks 5
```

## Customization

The `do_work()` method contains placeholder logic. Replace with:
- **LLM integration**: Call Anthropic/OpenAI APIs
- **Tool execution**: Run pytest, linters, code generators
- **Data processing**: ETL pipelines, analysis tasks

See [Agent Integration Guide](../guides/agent-integration.md) for complete customization examples.

## Troubleshooting

**Agent not receiving tasks**:
- Verify capabilities match task requirements (check TUI)
- Confirm heartbeats are being sent (check logs)

**Heartbeat timeout**:
- Interval must be <90s
- Check for blocking operations in main loop

**Task failures**:
- Mark transient errors as `retryable: true`
- Review logs in server TUI

## Documentation

- **Tutorial**: [Build Your First Agent](../getting-started/quickstart.md) (10 minutes)
- **Integration**: [Agent Integration Guide](../guides/agent-integration.md) (complete reference)
- **Protocol**: [MCP Specification](../reference/protocol.md) (tool schemas)

---

**Note**: Example uses pseudocode for MCP calls. Replace with actual MCP SDK when deploying.
