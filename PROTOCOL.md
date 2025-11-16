# Protocol Specification

MCP tool specifications and protocol requirements for the MAC MCP Server.

## MCP Tools

### register_agent

Register agent with capabilities.

**Parameters**:
- `agent_id` (string, required): Unique agent identifier
- `capabilities` (array, required): List of capability strings
- `max_concurrent_tasks` (integer, optional): Max concurrent tasks (default: 5)

**Returns**: `{"status": "registered", "agent_id": "..."}`

**Errors**:
- `DUPLICATE_AGENT_ID`: Agent ID already registered

### claim_task

Pull next available task matching agent capabilities.

**Parameters**:
- `agent_id` (string, required): Agent identifier
- `capabilities` (array, required): Agent capabilities

**Returns**: Task object or null if no tasks available

**Errors**:
- `AGENT_NOT_FOUND`: Agent not registered
- `AGENT_AT_CAPACITY`: Agent has max concurrent tasks

### update_task_progress

Report task progress.

**Parameters**:
- `task_id` (string, required): Task identifier
- `agent_id` (string, required): Agent identifier
- `progress` (number, required): Progress 0.0-1.0
- `message` (string, optional): Progress message

**Returns**: `{"status": "updated"}`

**Errors**:
- `TASK_NOT_FOUND`: Task does not exist
- `UNAUTHORIZED`: Agent not assigned to task
- `INVALID_STATE`: Task not in RUNNING state

### complete_task

Mark task as successfully completed.

**Parameters**:
- `task_id` (string, required): Task identifier
- `agent_id` (string, required): Agent identifier
- `result` (object, required): Task results

**Returns**: `{"status": "completed"}`

**Errors**:
- `TASK_NOT_FOUND`: Task does not exist
- `UNAUTHORIZED`: Agent not assigned to task
- `INVALID_STATE`: Task not in RUNNING state

### fail_task

Report task failure.

**Parameters**:
- `task_id` (string, required): Task identifier
- `agent_id` (string, required): Agent identifier
- `error` (object, required): Error details with `type`, `message`, `retryable` fields

**Returns**: `{"status": "failed", "action": "retry" | "error"}`

**Errors**:
- `TASK_NOT_FOUND`: Task does not exist
- `UNAUTHORIZED`: Agent not assigned to task

### send_heartbeat

Maintain agent liveness.

**Parameters**:
- `agent_id` (string, required): Agent identifier
- `status` (string, optional): Status message

**Returns**: `{"status": "alive"}`

**Errors**:
- `AGENT_NOT_FOUND`: Agent not registered

### request_dependency

Get results from completed dependency task.

**Parameters**:
- `task_id` (string, required): Requesting task ID
- `dependency_id` (string, required): Dependency task ID

**Returns**: Dependency task result object

**Errors**:
- `TASK_NOT_FOUND`: Task does not exist
- `DEPENDENCY_NOT_FOUND`: Dependency task does not exist
- `DEPENDENCY_NOT_COMPLETE`: Dependency not yet completed
- `INVALID_DEPENDENCY`: Task does not depend on specified dependency

### submit_goal

Submit new goal for decomposition.

**Parameters**:
- `goal_id` (string, required): Unique goal identifier
- `description` (string, required): Goal description
- `context` (object, optional): Additional context
- `constraints` (object, optional): Constraints

**Returns**: `{"status": "submitted", "goal_id": "..."}`

**Errors**:
- `DUPLICATE_GOAL_ID`: Goal ID already exists
- `DECOMPOSITION_FAILED`: LLM failed to decompose goal

## State Machine

### Task States

- **PENDING**: Task created, awaiting assignment
- **RUNNING**: Task assigned to agent, in progress
- **SUCCESS**: Task completed successfully
- **ERROR**: Task failed and not retryable

### Goal States

- **SUBMITTED**: Goal created, awaiting decomposition
- **EXECUTING**: Tasks being executed
- **COMPLETED**: All tasks successful
- **FAILED**: One or more tasks failed permanently

## Event Types

All events have: `type`, `timestamp`, `sequence`, `payload`

- `goal_submitted`: Goal created
- `goal_decomposed`: Tasks generated
- `agent_registered`: Agent joined
- `task_created`: Task added
- `task_assigned`: Task assigned to agent
- `task_progress`: Progress update
- `task_completed`: Task successful
- `task_failed`: Task error
- `heartbeat_received`: Agent alive
- `heartbeat_timeout`: Agent unresponsive

## Error Codes

- `AGENT_NOT_FOUND`: Agent ID not registered
- `TASK_NOT_FOUND`: Task ID does not exist
- `GOAL_NOT_FOUND`: Goal ID does not exist
- `DUPLICATE_AGENT_ID`: Agent ID already registered
- `DUPLICATE_GOAL_ID`: Goal ID already exists
- `INVALID_STATE`: Operation not allowed in current state
- `UNAUTHORIZED`: Agent not authorized for operation
- `AGENT_AT_CAPACITY`: Agent has max concurrent tasks
- `DEPENDENCY_NOT_FOUND`: Dependency task not found
- `DEPENDENCY_NOT_COMPLETE`: Dependency not yet completed
- `INVALID_DEPENDENCY`: Invalid dependency reference
- `DECOMPOSITION_FAILED`: LLM decomposition failed

## Heartbeat Protocol

- Agents send `send_heartbeat` every 30 seconds
- Server timeout after 90 seconds without heartbeat
- On timeout:
  1. Emit `heartbeat_timeout` event
  2. Mark agent as unresponsive
  3. Reassign running tasks to other agents

## Retry Logic

When `fail_task` is called with `retryable: true`:
1. Increment task retry count
2. If retry_count < 3, reset task to PENDING
3. If retry_count >= 3, mark task as ERROR
4. Return `{"action": "retry"}` or `{"action": "error"}`

## Security Requirements

- Validate all task IDs match `^[a-zA-Z0-9_-]+$` pattern
- Max event payload size: 1 MB
- Max task description length: 10,000 characters
- Max concurrent tasks per agent: 5
- Rate limit: 1000 API calls per agent per hour

## Conformance Requirements

Implementations must:
1. Persist events before state mutations
2. Implement all 8 MCP tools
3. Follow task state machine exactly
4. Enforce heartbeat timeout
5. Support retry logic with max 3 attempts
6. Validate all inputs with Pydantic models
7. Return errors with proper error codes
