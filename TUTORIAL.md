# Tutorial: Build Your First Agent in 10 Minutes

Learn how to build and connect a working agent to the MAC MCP Server in 10 minutes.

## What You'll Build

A Python agent that:
- Registers with the MAC MCP Server
- Claims tasks matching its capabilities
- Executes tasks and reports progress
- Handles errors gracefully

## Prerequisites

- Python 3.12+
- MAC MCP Server running (see [README.md](../README.md) for installation)
- Basic Python knowledge

## Step 1: Create Agent File (2 minutes)

Create `my_agent.py`:

```python
import asyncio
import json
from anthropic import Anthropic

class SimpleAgent:
    def __init__(self, agent_id: str, capabilities: list[str], mcp_client):
        """Initialize agent with ID, capabilities, and MCP client.

        Args:
            agent_id: Unique identifier (e.g., "agent_001")
            capabilities: List of skills (e.g., ["python", "testing"])
            mcp_client: MCP client for server communication
        """
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.mcp = mcp_client
        self.running = True
```

## Step 2: Add Registration (1 minute)

Add the `register()` method:

```python
    async def register(self):
        """Register agent with the orchestrator."""
        result = await self.mcp.call_tool(
            "register_agent",
            {
                "agent_id": self.agent_id,
                "capabilities": self.capabilities,
            }
        )
        print(f"✅ Registered: {result}")
```

## Step 3: Add Heartbeat Loop (1 minute)

Keep the agent alive with periodic heartbeats:

```python
    async def heartbeat_loop(self):
        """Send heartbeat every 30 seconds."""
        while self.running:
            try:
                await self.mcp.call_tool(
                    "heartbeat",
                    {
                        "agent_id": self.agent_id,
                        "status": "healthy",
                    }
                )
                print("💓 Heartbeat sent")
            except Exception as e:
                print(f"⚠️ Heartbeat failed: {e}")

            await asyncio.sleep(30)
```

## Step 4: Implement Task Claiming (2 minutes)

Add task discovery and claiming:

```python
    async def claim_task(self):
        """Claim next available task matching capabilities."""
        result = await self.mcp.call_tool(
            "claim_task",
            {
                "agent_id": self.agent_id,
                "capabilities": self.capabilities,
            }
        )

        if "No matching tasks" in str(result):
            return None

        # Parse task from result
        # In production, use structured output schema
        return result
```

## Step 5: Execute Tasks (3 minutes)

Add task execution logic:

```python
    async def execute_task(self, task):
        """Execute a task and report progress."""
        task_id = task["task_id"]
        description = task["description"]

        print(f"🔨 Executing: {description}")

        try:
            # Report initial progress
            await self.mcp.call_tool(
                "report_progress",
                {
                    "task_id": task_id,
                    "agent_id": self.agent_id,
                    "progress": 0.3,
                    "message": "Starting work...",
                }
            )

            # Do actual work here
            # For this tutorial, simulate work
            await asyncio.sleep(2)
            result = {
                "artifacts": ["output.txt"],
                "summary": f"Completed: {description}",
            }

            # Report completion
            await self.mcp.call_tool(
                "complete_task",
                {
                    "task_id": task_id,
                    "agent_id": self.agent_id,
                    "result": result,
                }
            )

            print(f"✅ Completed: {task_id}")

        except Exception as e:
            # Report failure
            await self.mcp.call_tool(
                "fail_task",
                {
                    "task_id": task_id,
                    "agent_id": self.agent_id,
                    "error": {
                        "type": "execution_error",
                        "message": str(e),
                        "retryable": True,
                    },
                }
            )
            print(f"❌ Failed: {e}")
```

## Step 6: Add Main Loop (1 minute)

Tie it all together:

```python
    async def run(self):
        """Main agent loop."""
        # Register
        await self.register()

        # Start heartbeat in background
        asyncio.create_task(self.heartbeat_loop())

        # Main work loop
        print("🤖 Agent running. Press Ctrl+C to stop.")
        try:
            while self.running:
                # Try to claim a task
                task = await self.claim_task()

                if task:
                    await self.execute_task(task)
                else:
                    # No tasks available, wait before trying again
                    await asyncio.sleep(5)

        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            self.running = False
```

## Step 7: Create Main Entry Point

Add at the end of `my_agent.py`:

```python
async def main():
    """Entry point."""
    # Initialize MCP client (pseudocode - use actual MCP SDK)
    from mcp import Client
    mcp_client = Client("stdio")  # Connect via stdio

    # Create and run agent
    agent = SimpleAgent(
        agent_id="my_agent_001",
        capabilities=["python", "testing", "documentation"],
        mcp_client=mcp_client,
    )

    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 8: Test Your Agent (2 minutes)

### Terminal 1: Start MAC MCP Server

```bash
mac-mcp --config config.yaml --ui tui
```

### Terminal 2: Submit a Test Goal

```bash
python -c "
import asyncio
from mcp import Client

async def submit():
    client = Client('stdio')
    await client.call_tool('submit_goal', {
        'goal_id': 'test_goal_001',
        'description': 'Write unit tests for authentication module',
        'context': {'language': 'python', 'framework': 'pytest'},
    })

asyncio.run(submit())
"
```

### Terminal 3: Run Your Agent

```bash
python my_agent.py
```

You should see:
```
✅ Registered: Agent my_agent_001 registered...
💓 Heartbeat sent
🔨 Executing: Write unit tests for authentication module
✅ Completed: task_1
```

## What You Learned

✅ How to register an agent with capabilities
✅ How to maintain liveness with heartbeats
✅ How to claim tasks matching your agent's skills
✅ How to report progress during execution
✅ How to complete or fail tasks properly

## Next Steps

- **Add LLM Integration**: Use Anthropic API to generate code/tests
- **Handle Dependencies**: Request results from prerequisite tasks
- **Multiple Capabilities**: Build specialized agents for different task types
- **Error Handling**: Implement retries and better error recovery

## Troubleshooting

**Agent not receiving tasks**
- Check capabilities match task requirements
- Verify agent is sending heartbeats (check server logs)
- Ensure task is in PENDING state (not already assigned)

**Heartbeat timeout**
- Heartbeat interval must be < 90 seconds
- Check network connection to server
- Look for exceptions in heartbeat_loop

**Task assignment fails**
- Verify agent_id matches registration
- Check agent hasn't exceeded max_concurrent_tasks (default: 5)
- Ensure task hasn't been claimed by another agent

## Complete Code

The complete `my_agent.py` is available in `examples/simple_agent.py` in the repository.

## Resources

- [Agent Integration Guide](../AGENTS.md) - Detailed agent development guide
- [MCP Protocol Spec](../PROTOCOL.md) - Complete protocol reference
- [Architecture Overview](../ARCHITECTURE.md) - System design and patterns

---

**Time to complete**: ~10 minutes
**Difficulty**: Beginner
**Prerequisites**: Python 3.12+, MAC MCP Server running

Built with ❤️ by the MAC MCP community
