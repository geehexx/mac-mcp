# MCP Protocol Patterns

## Core Principles

1. **Tools are functions** - Agents call tools to perform actions
2. **Resources are data** - Agents read resources to get information
3. **Prompts are templates** - Agents use prompts for guidance
4. **Stdio transport** - Communication via stdin/stdout JSON-RPC

## MCP Server Pattern

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, Resource, TextContent

app = Server("mac-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="submit_goal",
            description="Submit a high-level goal for decomposition",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "context": {"type": "object"},
                },
                "required": ["description"],
            },
        ),
        Tool(
            name="claim_task",
            description="Claim a pending task for execution",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "format": "uuid"},
                    "task_id": {"type": "string", "format": "uuid"},
                },
                "required": ["agent_id", "task_id"],
            },
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "submit_goal":
        goal_id = await orchestrator.submit_goal(
            description=arguments["description"],
            context=arguments.get("context", {}),
        )
        return [TextContent(
            type="text",
            text=f"Goal submitted: {goal_id}",
        )]
    
    elif name == "claim_task":
        success = await orchestrator.claim_task(
            agent_id=UUID(arguments["agent_id"]),
            task_id=UUID(arguments["task_id"]),
        )
        return [TextContent(
            type="text",
            text=f"Task claimed: {success}",
        )]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())
```

**Key Points**:
- `@app.list_tools()` declares available tools
- `@app.call_tool()` handles tool execution
- `inputSchema` uses JSON Schema for validation
- Return `list[TextContent]` for results
- Use `stdio_server()` for stdio transport

## Tool Schema Pattern

```python
# Simple tool with required fields
Tool(
    name="register_agent",
    description="Register agent with capabilities",
    inputSchema={
        "type": "object",
        "properties": {
            "agent_id": {"type": "string", "format": "uuid"},
            "capabilities": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["agent_id", "capabilities"],
    },
)

# Tool with optional fields and defaults
Tool(
    name="report_progress",
    description="Report task progress",
    inputSchema={
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "format": "uuid"},
            "progress": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "message": {"type": "string"},
        },
        "required": ["task_id", "progress"],
    },
)

# Tool with enum constraints
Tool(
    name="fail_task",
    description="Mark task as failed",
    inputSchema={
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "format": "uuid"},
            "reason": {
                "type": "string",
                "enum": ["timeout", "error", "blocked", "cancelled"],
            },
            "error_message": {"type": "string"},
        },
        "required": ["task_id", "reason"],
    },
)
```

**Key Points**:
- Use JSON Schema for validation
- `format: "uuid"` for UUID fields
- `enum` for constrained values
- `minimum`/`maximum` for numeric bounds
- `required` array for mandatory fields

## Resource Pattern

```python
@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="coordination://tasks",
            name="Available Tasks",
            description="List of pending tasks",
            mimeType="application/json",
        ),
        Resource(
            uri="coordination://agents",
            name="Registered Agents",
            description="List of active agents",
            mimeType="application/json",
        ),
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    if uri == "coordination://tasks":
        tasks = await orchestrator.get_pending_tasks()
        return json.dumps([task.model_dump() for task in tasks], indent=2)
    
    elif uri == "coordination://agents":
        agents = await orchestrator.get_active_agents()
        return json.dumps([agent.model_dump() for agent in agents], indent=2)
    
    raise ValueError(f"Unknown resource: {uri}")
```

**Key Points**:
- Resources are read-only data
- Use custom URI scheme (e.g., `coordination://`)
- Return JSON string for structured data
- `mimeType` indicates content type

## Error Handling Pattern

```python
from mcp.types import TextContent

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls with error handling."""
    try:
        if name == "claim_task":
            agent_id = UUID(arguments["agent_id"])
            task_id = UUID(arguments["task_id"])
            
            success = await orchestrator.claim_task(agent_id, task_id)
            
            if not success:
                return [TextContent(
                    type="text",
                    text=f"Failed to claim task {task_id}. "
                         f"Task may be already claimed or not found.",
                )]
            
            return [TextContent(
                type="text",
                text=f"Successfully claimed task {task_id}",
            )]
    
    except ValueError as e:
        return [TextContent(
            type="text",
            text=f"Invalid input: {e}",
        )]
    
    except Exception as e:
        logger.exception("Tool execution failed", tool=name)
        return [TextContent(
            type="text",
            text=f"Internal error: {e}",
        )]
```

**Key Points**:
- Catch exceptions and return error messages
- Don't raise exceptions from tool handlers
- Log errors for debugging
- Return descriptive error messages

## Async Pattern

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """All tool handlers are async."""
    if name == "submit_goal":
        # Async orchestrator call
        goal_id = await orchestrator.submit_goal(
            description=arguments["description"],
        )
        
        # Async decomposition (may take time)
        await orchestrator.decompose_goal(goal_id)
        
        return [TextContent(
            type="text",
            text=f"Goal {goal_id} submitted and decomposed",
        )]
```

**Key Points**:
- All MCP handlers are async
- Use `await` for I/O operations
- Don't block the event loop

## Testing Pattern

```python
import pytest
from mcp.types import TextContent

@pytest.mark.integration
async def test_submit_goal_tool():
    """Test submit_goal tool."""
    # Setup
    orchestrator = Orchestrator(event_store=InMemoryEventStore())
    
    # Call tool
    result = await call_tool(
        name="submit_goal",
        arguments={"description": "Build REST API"},
    )
    
    # Verify
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "Goal submitted" in result[0].text

@pytest.mark.integration
async def test_claim_task_not_found():
    """Test claim_task with non-existent task."""
    orchestrator = Orchestrator(event_store=InMemoryEventStore())
    
    result = await call_tool(
        name="claim_task",
        arguments={
            "agent_id": str(uuid4()),
            "task_id": str(uuid4()),  # Non-existent
        },
    )
    
    assert "Failed to claim" in result[0].text
```

**Key Points**:
- Test tool handlers directly
- Use in-memory storage for tests
- Verify return types and messages
- Test error cases

## Anti-Patterns

❌ **Blocking I/O in Tool Handler**
```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # NEVER use blocking I/O
    with open("file.txt") as f:  # ❌ Blocking!
        data = f.read()
```

✅ **Use Async I/O**
```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    async with aiofiles.open("file.txt") as f:
        data = await f.read()
```

❌ **Raising Exceptions from Tool Handler**
```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "unknown":
        raise ValueError("Unknown tool")  # ❌ Don't raise!
```

✅ **Return Error Message**
```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "unknown":
        return [TextContent(type="text", text="Unknown tool")]
```

❌ **Missing Input Validation**
```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # Missing validation - may crash on invalid UUID
    task_id = UUID(arguments["task_id"])
```

✅ **Validate and Handle Errors**
```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        task_id = UUID(arguments["task_id"])
    except ValueError:
        return [TextContent(type="text", text="Invalid task_id format")]
```

## Related Patterns

- Event Sourcing: `.amazonq/rules/reference/event-sourcing-patterns.md`
- Actor Model: `.amazonq/rules/reference/actor-model-patterns.md`
- Code Patterns: `.amazonq/rules/reference/code-patterns.md`
