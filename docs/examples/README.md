# MAC MCP Server - Example Agents

This directory contains example agents demonstrating best practices for integrating with the MAC MCP Server.

## Examples

### `simple_agent.py` - Basic Agent Template

A production-ready agent template demonstrating:

- ✅ Agent registration with capabilities
- ✅ Heartbeat loop for liveness monitoring
- ✅ Task claiming with capability matching
- ✅ Progress reporting during execution
- ✅ Proper error handling and retries
- ✅ Graceful shutdown on SIGINT
- ✅ Concurrent task execution
- ✅ Load-based status reporting

**Usage**:

```bash
# Basic usage
python examples/simple_agent.py

# Custom configuration
python examples/simple_agent.py \
    --agent-id my_python_agent \
    --capabilities python,testing,documentation \
    --max-concurrent-tasks 5
```

**Features Demonstrated**:

1. **Registration**: Registers with orchestrator and provides metadata
2. **Heartbeat**: Sends heartbeat every 30 seconds (required < 90s)
3. **Task Claiming**: Pull-based task assignment with backpressure control
4. **Progress Reporting**: Updates orchestrator at 10%, 50%, 90% completion
5. **Error Handling**: Distinguishes retryable vs permanent failures
6. **Concurrent Execution**: Handles multiple tasks up to max_concurrent_tasks
7. **Clean Shutdown**: Handles SIGINT gracefully, completes in-flight tasks

## Adapting for Your Use Case

### Adding LLM Integration

Replace the `do_work()` method with actual LLM calls:

```python
async def do_work(self, task: dict[str, Any]) -> dict[str, Any]:
    """Use Claude to complete the task."""
    from anthropic import Anthropic

    client = Anthropic(api_key="your-api-key")

    # Call Claude to generate code/tests/docs
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"Task: {task['description']}\n\nGenerate high-quality output."
        }]
    )

    return {
        "artifacts": ["generated_output.py"],
        "summary": response.content[0].text[:200],
        "metrics": {"tokens_used": response.usage.total_tokens},
    }
```

### Handling Dependencies

Request dependency results before starting work:

```python
async def execute_task(self, task: dict[str, Any]):
    """Execute task with dependency support."""
    task_id = task["task_id"]

    # Request dependencies first
    dependencies = {}
    for dep_id in task.get("dependencies", []):
        dep_result = await self.request_dependency(task_id, dep_id)
        dependencies[dep_id] = dep_result

    # Now execute with dependency data available
    result = await self.do_work(task, dependencies)
    await self.complete_task(task_id, result)

async def request_dependency(self, task_id: str, dependency_id: str):
    """Request dependency task result."""
    # Pseudocode
    # result = await self.mcp.call_tool(
    #     "request_dependency",
    #     {
    #         "agent_id": self.agent_id,
    #         "task_id": dependency_id,
    #     }
    # )
    # return result["result"]
    pass
```

### Specialized Agents

Create specialized agents for different task types:

```python
# Testing specialist agent
python_testing_agent = SimpleAgent(
    agent_id="testing_specialist",
    capabilities=["python", "testing", "pytest"],
    max_concurrent_tasks=5,
)

# Documentation specialist agent
docs_agent = SimpleAgent(
    agent_id="docs_specialist",
    capabilities=["documentation", "markdown"],
    max_concurrent_tasks=3,
)

# Code review agent
review_agent = SimpleAgent(
    agent_id="reviewer",
    capabilities=["code_review", "security", "best_practices"],
    max_concurrent_tasks=2,
)
```

## Connecting to MAC MCP Server

### Stdio Transport (Default)

The agent connects to the server via stdio:

```python
from mcp import Client

async def connect_to_server(self):
    self.mcp = Client("stdio")
    await self.mcp.connect()
```

### HTTP Transport

For HTTP-based connections:

```python
async def connect_to_server(self):
    self.mcp = Client("http://localhost:3000")
    await self.mcp.connect()
```

### Configuration

Update your `~/.config/mcp/config.json`:

```json
{
  "mcpServers": {
    "mac-coordination": {
      "command": "mac-mcp",
      "args": ["--config", "/path/to/config.yaml"]
    }
  }
}
```

## Testing Your Agent

### 1. Start MAC MCP Server

```bash
# Terminal 1: Start server with TUI
mac-mcp --config config.yaml --ui tui
```

### 2. Submit Test Goal

```bash
# Terminal 2: Submit a test goal
python -c "
import asyncio
from mcp import Client

async def submit():
    client = Client('stdio')
    await client.call_tool('submit_goal', {
        'goal_id': 'test_001',
        'description': 'Write unit tests for authentication module',
        'context': {'language': 'python', 'framework': 'pytest'},
    })

asyncio.run(submit())
"
```

### 3. Run Your Agent

```bash
# Terminal 3: Start agent
python examples/simple_agent.py --capabilities python,testing
```

You should see:
```
✅ Agent simple_agent_001 registered successfully
💓 Heartbeat sent (status=healthy, load=0.0%)
🔨 Executing task task_1: Write unit tests...
📊 Progress 50%: Processing...
✅ Task task_1 completed successfully
```

## Troubleshooting

**Agent not receiving tasks**:
- Check capabilities match task requirements in TUI
- Verify agent is sending heartbeats (check server logs)
- Ensure task is in PENDING state

**Heartbeat timeout**:
- Heartbeat interval must be < 90 seconds
- Check for network issues or blocking operations
- Review agent logs for exceptions in heartbeat loop

**Task failures**:
- Check error is marked as `retryable: true` for transient failures
- Review task logs in server TUI
- Verify LLM API keys are valid

## Best Practices (2025 Standards)

1. **Always send heartbeats** - Required every 30-90 seconds
2. **Report progress frequently** - At least at 25%, 50%, 75%, 100%
3. **Handle retries gracefully** - Distinguish transient vs permanent failures
4. **Validate dependencies** - Check all dependencies completed before starting
5. **Provide detailed results** - Include artifacts, summary, and metrics
6. **Clean shutdown** - Handle SIGINT/SIGTERM, complete in-flight tasks
7. **Concurrent execution** - Use asyncio for parallel task handling
8. **Structured logging** - Use Python logging module with appropriate levels

## Additional Resources

- [Tutorial: Build Your First Agent in 10 Minutes](../getting-started/quickstart.md)
- [Agent Integration Guide](../guides/agent-integration.md)
- [MCP Protocol Specification](../reference/protocol.md)
- [Architecture Overview](../reference/architecture.md)

---

**Note**: The example agent uses pseudocode for MCP tool calls. Replace with actual MCP SDK calls when integrating with a real server.
