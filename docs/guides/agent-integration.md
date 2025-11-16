# Agent Integration Guide

How to build agents that connect to the MAC MCP Server.

## Agent Lifecycle

1. **Register** with capabilities using `register_agent`
2. **Heartbeat** loop to maintain liveness
3. **Claim tasks** that match capabilities
4. **Execute** task and report progress
5. **Complete** or fail task with results
6. **Repeat** steps 3-5

## MCP Tools

### register_agent

Register agent with capabilities.

**Parameters**:
- `agent_id` (string, required): Unique agent identifier
- `capabilities` (array, required): List of capability strings
- `metadata` (object, optional): Agent metadata (model, version, etc.)

**Example**:
```json
{
  "agent_id": "agent_001",
  "capabilities": ["python", "testing"],
  "metadata": {"model": "claude-sonnet-4", "version": "1.0.0"}
}
```

### claim_task

Pull next available task matching agent capabilities.

**Parameters**:
- `agent_id` (string, required): Agent identifier
- `capabilities` (array, required): Agent capabilities

**Returns**: Task object or null if no tasks available

**Example**:
```json
{
  "agent_id": "agent_001",
  "capabilities": ["python", "testing"]
}
```

### report_progress

Report task progress.

**Parameters**:
- `task_id` (string, required): Task identifier
- `agent_id` (string, required): Agent identifier
- `progress` (number, required): Progress 0.0-1.0
- `message` (string, optional): Progress message

**Example**:
```json
{
  "task_id": "task_123",
  "agent_id": "agent_001",
  "progress": 0.5,
  "message": "Completed analysis phase"
}
```

### complete_task

Mark task as successfully completed.

**Parameters**:
- `task_id` (string, required): Task identifier
- `agent_id` (string, required): Agent identifier
- `result` (object, required): Task results

**Example**:
```json
{
  "task_id": "task_123",
  "agent_id": "agent_001",
  "result": {
    "artifacts": ["test_suite.py"],
    "coverage": "95%",
    "summary": "All tests passing"
  }
}
```

### fail_task

Report task failure.

**Parameters**:
- `task_id` (string, required): Task identifier
- `agent_id` (string, required): Agent identifier
- `error` (object, required): Error details with `type`, `message`, `retryable`

**Example**:
```json
{
  "task_id": "task_123",
  "agent_id": "agent_001",
  "error": {
    "type": "network_error",
    "message": "API timeout",
    "retryable": true
  }
}
```

### heartbeat

Maintain agent liveness.

**Parameters**:
- `agent_id` (string, required): Agent identifier
- `status` (string, optional): Status message

**Example**:
```json
{
  "agent_id": "agent_001",
  "status": "healthy"
}
```

### request_dependency

Get results from completed dependency task.

**Parameters**:
- `task_id` (string, required): Requesting task ID
- `dependency_id` (string, required): Dependency task ID

**Returns**: Dependency task result object

**Example**:
```json
{
  "task_id": "task_456",
  "dependency_id": "task_123"
}
```

### submit_goal

Submit new goal for decomposition (advanced).

**Parameters**:
- `goal_id` (string, required): Unique goal identifier
- `description` (string, required): Goal description
- `context` (object, optional): Additional context
- `constraints` (object, optional): Constraints

**Example**:
```json
{
  "goal_id": "goal_001",
  "description": "Build user authentication system",
  "context": {"framework": "FastAPI"},
  "constraints": {"security": "high"}
}
```

## Example Agent

```python
import asyncio
from anthropic import Anthropic

class Agent:
    def __init__(self, agent_id, capabilities):
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.llm = Anthropic(api_key="...")

    async def run(self):
        await self.register()
        asyncio.create_task(self.heartbeat_loop())

        while True:
            task = await self.claim_task()
            if task:
                await self.execute(task)
            else:
                await asyncio.sleep(5)

    async def register(self):
        await self.mcp.call_tool("register_agent", {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities
        })

    async def heartbeat_loop(self):
        while True:
            await self.mcp.call_tool("heartbeat", {
                "agent_id": self.agent_id
            })
            await asyncio.sleep(30)

    async def claim_task(self):
        return await self.mcp.call_tool("claim_task", {
            "agent_id": self.agent_id,
            "capabilities": self.capabilities
        })

    async def execute(self, task):
        try:
            # Update progress
            await self.mcp.call_tool("report_progress", {
                "task_id": task["id"],
                "agent_id": self.agent_id,
                "progress": 0.5
            })

            # Do work
            result = await self.do_work(task)

            # Complete task
            await self.mcp.call_tool("complete_task", {
                "task_id": task["id"],
                "agent_id": self.agent_id,
                "result": result
            })
        except Exception as e:
            await self.mcp.call_tool("fail_task", {
                "task_id": task["id"],
                "agent_id": self.agent_id,
                "error": {"type": "error", "message": str(e)}
            })
```

## Capabilities

Common capability strings:

- **Languages**: `python`, `javascript`, `go`, `rust`
- **Domains**: `testing`, `documentation`, `deployment`, `security`
- **Tools**: `git`, `docker`, `kubernetes`, `terraform`
- **Skills**: `code_generation`, `code_review`, `debugging`, `research`

## Configuration

Connect to MAC MCP Server:

```json
{
  "mcpServers": {
    "mac-coordination": {
      "command": "mac-mcp",
      "args": ["--config", "config.yaml"]
    }
  }
}
```

## Best Practices

1. **Heartbeat regularly** (every 30 seconds) to maintain liveness
2. **Report progress** frequently for long-running tasks
3. **Handle retries** gracefully for transient failures
4. **Validate dependencies** before starting work
5. **Provide detailed results** for downstream tasks

## Troubleshooting

**Task not assigned**: Check capabilities match task requirements

**Heartbeat timeout**: Ensure heartbeat loop is running and interval < 90s

**Dependency not available**: Verify dependency task completed successfully
