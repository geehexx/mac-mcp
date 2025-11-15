"""MCP server implementation for MAC protocol.

This module implements the Model Context Protocol server exposing
tools and resources for agent coordination.
"""

from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

from mac_mcp.core.orchestrator import Orchestrator
from mac_mcp.storage.base import EventStore


def create_server(
    orchestrator: Orchestrator,
    event_store: EventStore,
) -> Server:
    """Create MCP server with MAC protocol tools and resources.

    Args:
        orchestrator: The main orchestrator instance
        event_store: Event store for reading events

    Returns:
        Configured MCP server
    """
    server = Server("mac-mcp")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="submit_goal",
                description="Submit a high-level goal for autonomous decomposition and execution",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "goal_id": {"type": "string", "description": "Unique goal identifier"},
                        "description": {
                            "type": "string",
                            "description": "High-level goal description",
                        },
                        "context": {
                            "type": "object",
                            "description": "Additional context (language, framework, domain, etc.)",
                        },
                        "constraints": {
                            "type": "object",
                            "description": "Constraints (deadline, max_agents, etc.)",
                        },
                    },
                    "required": ["goal_id", "description"],
                },
            ),
            Tool(
                name="register_agent",
                description="Register agent with orchestrator",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string", "description": "Unique agent identifier"},
                        "capabilities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of capability tags",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Optional agent metadata",
                        },
                    },
                    "required": ["agent_id", "capabilities"],
                },
            ),
            Tool(
                name="claim_task",
                description="Request task assignment matching capabilities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "capabilities": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["agent_id", "capabilities"],
                },
            ),
            Tool(
                name="report_progress",
                description="Report task progress update",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "progress": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                        "message": {"type": "string"},
                        "artifacts": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["task_id", "agent_id", "progress"],
                },
            ),
            Tool(
                name="complete_task",
                description="Mark task as successfully completed",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "result": {
                            "type": "object",
                            "properties": {
                                "artifacts": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "summary": {"type": "string"},
                                "metrics": {"type": "object"},
                            },
                            "required": ["artifacts", "summary"],
                        },
                    },
                    "required": ["task_id", "agent_id", "result"],
                },
            ),
            Tool(
                name="fail_task",
                description="Report task failure",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "error": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "message": {"type": "string"},
                                "retryable": {"type": "boolean"},
                                "context": {"type": "object"},
                            },
                            "required": ["type", "message", "retryable"],
                        },
                    },
                    "required": ["task_id", "agent_id", "error"],
                },
            ),
            Tool(
                name="request_dependency",
                description="Request the result of a completed dependency task",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "task_id": {
                            "type": "string",
                            "description": "ID of the dependency task",
                        },
                    },
                    "required": ["agent_id", "task_id"],
                },
            ),
            Tool(
                name="heartbeat",
                description="Agent liveness signal",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["healthy", "degraded", "shutting_down"],
                        },
                        "current_tasks": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "load": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 1.0,
                        },
                    },
                    "required": ["agent_id", "status"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        if name == "submit_goal":
            goal = await orchestrator.submit_goal(
                goal_id=arguments["goal_id"],
                description=arguments["description"],
                context=arguments.get("context"),
                constraints=arguments.get("constraints"),
            )
            return [
                TextContent(
                    type="text",
                    text=f"Goal {goal.id} submitted and decomposed into {len(goal.task_ids)} tasks",
                )
            ]

        if name == "register_agent":
            agent = await orchestrator.supervisor.register_agent(
                agent_id=arguments["agent_id"],
                capabilities=arguments["capabilities"],
                metadata=arguments.get("metadata"),
            )
            return [
                TextContent(
                    type="text",
                    text=f"Agent {agent.id} registered successfully with capabilities: {agent.capabilities}",
                )
            ]

        if name == "claim_task":
            task = await orchestrator.claim_task(
                agent_id=arguments["agent_id"],
                capabilities=arguments["capabilities"],
            )
            if task is None:
                return [TextContent(type="text", text="No matching tasks available")]

            return [
                TextContent(
                    type="text",
                    text=f"Task {task.id} assigned: {task.description}",
                )
            ]

        if name == "report_progress":
            await orchestrator.update_task_progress(
                task_id=arguments["task_id"],
                agent_id=arguments["agent_id"],
                progress=arguments["progress"],
                message=arguments.get("message"),
                artifacts=arguments.get("artifacts"),
            )
            return [
                TextContent(
                    type="text",
                    text=f"Progress updated for task {arguments['task_id']}: {arguments['progress']}",
                )
            ]

        if name == "complete_task":
            await orchestrator.complete_task(
                task_id=arguments["task_id"],
                agent_id=arguments["agent_id"],
                result=arguments["result"],
            )
            return [
                TextContent(
                    type="text",
                    text=f"Task {arguments['task_id']} completed successfully",
                )
            ]

        if name == "fail_task":
            action = await orchestrator.fail_task(
                task_id=arguments["task_id"],
                agent_id=arguments["agent_id"],
                error=arguments["error"],
            )
            return [
                TextContent(
                    type="text",
                    text=f"Task {arguments['task_id']} failed. Action: {action}",
                )
            ]

        if name == "request_dependency":
            result = orchestrator.get_dependency_result(arguments["task_id"])
            if result is None:
                return [
                    TextContent(
                        type="text",
                        text=f"Dependency task {arguments['task_id']} not found or not completed",
                    )
                ]

            import json

            return [
                TextContent(
                    type="text",
                    text=f"Dependency result: {json.dumps(result, indent=2)}",
                )
            ]

        if name == "heartbeat":
            await orchestrator.supervisor.update_heartbeat(
                agent_id=arguments["agent_id"],
                status=arguments["status"],
                current_tasks=arguments.get("current_tasks"),
                load=arguments.get("load"),
            )
            return [
                TextContent(
                    type="text",
                    text=f"Heartbeat received from agent {arguments['agent_id']}",
                )
            ]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    # Resources
    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List available resources."""
        return [
            Resource(
                uri="coordination://tasks",
                name="All Tasks",
                mimeType="application/json",
                description="List of all tasks in the system",
            ),
            Resource(
                uri="coordination://agents",
                name="All Agents",
                mimeType="application/json",
                description="List of all registered agents",
            ),
            Resource(
                uri="coordination://events",
                name="Event Stream",
                mimeType="application/x-ndjson",
                description="Append-only event log",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> str:
        """Read a resource."""
        if uri == "coordination://tasks":
            tasks = [
                {
                    "id": task.id,
                    "goal_id": task.goal_id,
                    "description": task.description,
                    "state": task.state.value,
                    "assigned_agent": task.assigned_agent,
                    "progress": task.progress,
                }
                for task in orchestrator._tasks.values()
            ]
            import json

            return json.dumps(tasks, indent=2)

        if uri == "coordination://agents":
            agents = [
                {
                    "id": agent.id,
                    "capabilities": agent.capabilities,
                    "status": agent.status.value,
                    "current_tasks": agent.current_tasks,
                    "success_rate": agent.success_rate(),
                }
                for agent in orchestrator.supervisor.get_all_agents()
            ]
            import json

            return json.dumps(agents, indent=2)

        if uri == "coordination://events":
            events = []
            async for event in event_store.read():
                events.append(event.model_dump_json())
            return "\n".join(events)

        return f"Unknown resource: {uri}"

    return server


async def run_stdio_server(
    event_store: EventStore,
    orchestrator: Orchestrator | None = None,
) -> None:
    """Run the MCP server with stdio transport.

    Args:
        event_store: Event store for persistence
        orchestrator: Optional orchestrator instance
    """
    if orchestrator is None:
        from mac_mcp.core.orchestrator import Orchestrator
        from mac_mcp.core.supervisor import AgentSupervisor

        supervisor = AgentSupervisor(event_store)
        orchestrator = Orchestrator(event_store, supervisor)

    server = create_server(orchestrator, event_store)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
