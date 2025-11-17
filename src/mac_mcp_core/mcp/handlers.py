"""MCP tool handlers for MAC orchestration.

This module implements the Handler/Strategy pattern to eliminate the massive
if-elif chain in call_tool(). Each tool has a dedicated handler function,
making the code more maintainable and extensible.

2025 Best Practice: Use handler registries instead of giant conditional chains.
"""

import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from mcp.types import TextContent

from mac_mcp_core.orchestrator import Orchestrator
from mac_mcp_core.domain.tasks import Task


# Type alias for handler functions
ToolHandler = Callable[[Orchestrator, dict[str, Any]], Awaitable[list[TextContent]]]


# Authorization helpers


def check_agent_authorization(
    authenticated_agent_id: str,
    requested_agent_id: str,
    operation: str,
) -> TextContent | None:
    """Check if agent is authorized to perform operation.

    Args:
        authenticated_agent_id: Agent ID from authentication
        requested_agent_id: Agent ID in request
        operation: Description of operation for error message

    Returns:
        Error TextContent if unauthorized, None if authorized
    """
    if authenticated_agent_id != requested_agent_id:
        return TextContent(
            type="text",
            text=f"❌ Authorization error: Cannot {operation} for another agent. "
            f"Authenticated as '{authenticated_agent_id}', "
            f"but tried to act as '{requested_agent_id}'.",
        )
    return None


def check_task_ownership(
    task: Task | None,
    agent_id: str,
    task_id: str,
    operation: str,
) -> TextContent | None:
    """Check if agent owns the task.

    Args:
        task: Task to check
        agent_id: Agent ID to validate
        task_id: Task ID for error messages
        operation: Description of operation for error message

    Returns:
        Error TextContent if unauthorized/not found, None if authorized
    """
    if task is None:
        return TextContent(
            type="text",
            text=f"❌ Task '{task_id}' not found.",
        )

    if task.assigned_agent != agent_id:
        return TextContent(
            type="text",
            text=f"❌ Authorization error: Cannot {operation} task '{task_id}'. "
            f"Task is assigned to '{task.assigned_agent}', not you.",
        )

    return None


async def handle_submit_goal(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle submit_goal tool call.

    Supports dry-run mode for previewing decomposition before persistence.
    """
    dry_run = arguments.get("dry_run", False)
    result = await orchestrator.submit_goal(
        goal_id=arguments["goal_id"],
        description=arguments["description"],
        context=arguments.get("context"),
        constraints=arguments.get("constraints"),
        dry_run=dry_run,
    )

    # Handle dry-run preview
    if dry_run:
        task_dag = result
        preview_data = {
            "goal_id": arguments["goal_id"],
            "state": "PREVIEW",
            "is_preview": True,
            "task_count": len(task_dag.tasks),
            "task_ids": [t.id for t in task_dag.tasks],
            "tasks": [
                {
                    "id": t.id,
                    "description": t.description,
                    "required_capabilities": t.required_capabilities,
                    "dependencies": t.dependencies,
                }
                for t in task_dag.tasks
            ],
        }
        return [
            TextContent(
                type="text",
                text=f"🔍 DRY-RUN PREVIEW for goal {arguments['goal_id']}:\n\n"
                f"Would create {len(task_dag.tasks)} tasks:\n"
                + "\n".join([f"  - {t.id}: {t.description}" for t in task_dag.tasks])
                + f"\n\nTo execute, call submit_goal again with dry_run=false\n\n"
                f"Full preview:\n{json.dumps(preview_data, indent=2)}",
            )
        ]

    # Handle actual submission
    goal = result
    return [
        TextContent(
            type="text",
            text=f"✅ Goal {goal.id} submitted and decomposed into {len(goal.task_ids)} tasks",
        )
    ]


async def handle_register_agent(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle register_agent tool call with authorization."""
    agent_id = arguments["agent_id"]

    # Authorization check: agent_id must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "register",
        )
        if auth_error:
            return [auth_error]

    agent = await orchestrator.supervisor.register_agent(
        agent_id=agent_id,
        capabilities=arguments["capabilities"],
        metadata=arguments.get("metadata"),
    )
    return [
        TextContent(
            type="text",
            text=f"✅ Agent {agent.id} registered with capabilities: {', '.join(agent.capabilities)}",
        )
    ]


async def handle_claim_task(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle claim_task tool call with authorization."""
    agent_id = arguments["agent_id"]
    capabilities = arguments["capabilities"]

    # Authorization check: agent_id must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "claim tasks",
        )
        if auth_error:
            return [auth_error]

    # Use orchestrator's claim_task method (pull-based assignment)
    task = await orchestrator.claim_task(
        agent_id=agent_id,
        capabilities=capabilities,
    )

    if task is None:
        return [
            TextContent(
                type="text",
                text="[i] No matching tasks available",
            )
        ]

    return [
        TextContent(
            type="text",
            text=f"✅ Claimed task {task.id}: {task.description}\n"
            f"Dependencies: {', '.join(task.dependencies) if task.dependencies else 'none'}",
        )
    ]


async def handle_report_progress(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle report_progress tool call with authorization."""
    task_id = arguments["task_id"]
    agent_id = arguments["agent_id"]
    progress = arguments["progress"]
    message = arguments.get("message")
    artifacts = arguments.get("artifacts")

    # Authorization check 1: agent_id must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "report progress",
        )
        if auth_error:
            return [auth_error]

    # Authorization check 2: agent must own the task
    task = orchestrator.get_task(task_id)
    ownership_error = check_task_ownership(task, agent_id, task_id, "report progress on")
    if ownership_error:
        return [ownership_error]

    await orchestrator.update_task_progress(
        task_id=task_id,
        agent_id=agent_id,
        progress=progress,
        message=message,
        artifacts=artifacts,
    )

    return [
        TextContent(
            type="text",
            text=f"✅ Progress updated: {task_id} at {progress:.0%}"
            + (f" - {message}" if message else ""),
        )
    ]


async def handle_complete_task(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle complete_task tool call with authorization."""
    task_id = arguments["task_id"]
    agent_id = arguments["agent_id"]
    result = arguments["result"]

    # Authorization check 1: agent_id must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "complete task",
        )
        if auth_error:
            return [auth_error]

    # Authorization check 2: agent must own the task
    task = orchestrator.get_task(task_id)
    ownership_error = check_task_ownership(task, agent_id, task_id, "complete")
    if ownership_error:
        return [ownership_error]

    await orchestrator.complete_task(
        task_id=task_id,
        agent_id=agent_id,
        result=result,
    )

    # Check for unblocked tasks
    task = orchestrator.get_task(task_id)
    if task:
        # Find tasks that were waiting on this one
        unblocked = [
            t.id
            for t in orchestrator._tasks.values()
            if task_id in t.dependencies and t.state.value == "PENDING"
        ]

        if unblocked:
            return [
                TextContent(
                    type="text",
                    text=f"✅ Task {task_id} completed!\nUnblocked tasks: {', '.join(unblocked)}",
                )
            ]

    return [
        TextContent(
            type="text",
            text=f"✅ Task {task_id} completed successfully",
        )
    ]


async def handle_fail_task(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle fail_task tool call with authorization."""
    task_id = arguments["task_id"]
    agent_id = arguments["agent_id"]
    error = arguments["error"]

    # Authorization check 1: agent_id must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "fail task",
        )
        if auth_error:
            return [auth_error]

    # Authorization check 2: agent must own the task
    task = orchestrator.get_task(task_id)
    ownership_error = check_task_ownership(task, agent_id, task_id, "fail")
    if ownership_error:
        return [ownership_error]

    action = await orchestrator.fail_task(
        task_id=task_id,
        agent_id=agent_id,
        error=error,
    )

    if action == "retry":
        task = orchestrator.get_task(task_id)
        retry_count = task.metadata.get("retry_count", 0) if task else 0
        return [
            TextContent(
                type="text",
                text=f"⚠️ Task {task_id} failed but will retry (attempt {retry_count}/3)\n"
                f"Error: {error.get('message', 'Unknown error')}",
            )
        ]
    return [
        TextContent(
            type="text",
            text=f"❌ Task {task_id} failed permanently\n"
            f"Error: {error.get('message', 'Unknown error')}",
        )
    ]


async def handle_request_dependency(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle request_dependency tool call with authorization."""
    agent_id = arguments["agent_id"]
    dependency_task_id = arguments["task_id"]

    # Authorization check 1: agent_id must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "request dependency",
        )
        if auth_error:
            return [auth_error]

    # Authorization check 2: Verify agent has a task that depends on this
    agent_tasks = [t for t in orchestrator._tasks.values() if t.assigned_agent == agent_id]

    # Find the dependent task and verify it belongs to same goal (prevent cross-goal leakage)
    dependent_task = None
    for task in agent_tasks:
        if dependency_task_id in task.dependencies:
            dependent_task = task
            break

    if not dependent_task:
        return [
            TextContent(
                type="text",
                text=f"❌ Authorization error: You don't have any tasks that depend on '{dependency_task_id}'.",
            )
        ]

    # Verify dependency task exists and belongs to same goal
    dependency_task = orchestrator.get_task(dependency_task_id)
    if dependency_task and dependency_task.goal_id != dependent_task.goal_id:
        return [
            TextContent(
                type="text",
                text="❌ Authorization error: Cross-goal dependency access denied.",
            )
        ]

    # Use orchestrator's get_dependency_result method
    result = orchestrator.get_dependency_result(dependency_task_id)

    if result is None:
        return [
            TextContent(
                type="text",
                text=f"❌ Dependency task {dependency_task_id} not found or not completed",
            )
        ]

    # Return dependency result
    result_json = json.dumps(result, indent=2)
    return [
        TextContent(
            type="text",
            text=f"✅ Dependency {dependency_task_id} result:\n{result_json}",
        )
    ]


async def handle_heartbeat(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    """Handle heartbeat tool call with authorization."""
    agent_id = arguments["agent_id"]
    status = arguments.get("status", "healthy")
    current_tasks = arguments.get("current_tasks")
    load = arguments.get("load")

    # Authorization check: agent_id must match authenticated agent
    if "_authenticated_agent_id" in arguments:
        auth_error = check_agent_authorization(
            arguments["_authenticated_agent_id"],
            agent_id,
            "send heartbeat",
        )
        if auth_error:
            return [auth_error]

    try:
        await orchestrator.supervisor.update_heartbeat(
            agent_id=agent_id,
            status=status,
            current_tasks=current_tasks,
            load=load,
        )

        # Calculate timeout
        agent = orchestrator.supervisor.get_agent(agent_id)
        if agent:
            timeout_seconds = orchestrator.supervisor.heartbeat_timeout
            last_heartbeat = agent.last_heartbeat
            elapsed = (datetime.now(UTC) - last_heartbeat).total_seconds()
            remaining = max(0, timeout_seconds - elapsed)

            return [
                TextContent(
                    type="text",
                    text=f"💓 Heartbeat acknowledged for {agent_id} (timeout in {int(remaining)}s)",
                )
            ]

        return [
            TextContent(
                type="text",
                text=f"💓 Heartbeat acknowledged for {agent_id}",
            )
        ]

    except KeyError:
        return [
            TextContent(
                type="text",
                text=f"❌ Agent {agent_id} not registered. Please register first.",
            )
        ]


# Tool handler registry - maps tool names to handler functions
TOOL_HANDLERS: dict[str, ToolHandler] = {
    "submit_goal": handle_submit_goal,
    "register_agent": handle_register_agent,
    "claim_task": handle_claim_task,
    "report_progress": handle_report_progress,
    "complete_task": handle_complete_task,
    "fail_task": handle_fail_task,
    "request_dependency": handle_request_dependency,
    "heartbeat": handle_heartbeat,
}


def get_handler(tool_name: str) -> ToolHandler | None:
    """Get handler function for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Handler function if found, None otherwise
    """
    return TOOL_HANDLERS.get(tool_name)
