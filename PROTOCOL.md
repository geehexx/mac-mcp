# Multi-Agent Coordination Protocol Specification

## Version 1.0.0

## Abstract

This document specifies the Multi-Agent Coordination (MAC) Protocol, a JSON-RPC 2.0 based protocol for orchestrating autonomous LLM-based agents. The protocol defines message formats, state transitions, and behavioral requirements for both orchestrators and agents.

## Table of Contents

1. [Terminology](#terminology)
2. [Protocol Foundations](#protocol-foundations)
3. [Message Transport](#message-transport)
4. [MCP Integration](#mcp-integration)
5. [Core Message Types](#core-message-types)
6. [State Transition Rules](#state-transition-rules)
7. [Error Handling](#error-handling)
8. [Security Requirements](#security-requirements)
9. [Compliance](#compliance)

---

## 1. Terminology

### Key Terms

- **Orchestrator**: The central coordination server (MUST be singular per deployment)
- **Agent**: An autonomous LLM-based worker (MAY be multiple instances)
- **Task**: An atomic unit of work with defined inputs, outputs, and success criteria
- **Goal**: A high-level objective decomposed into multiple tasks
- **Task DAG**: Directed Acyclic Graph of tasks with dependency edges
- **Capability**: A declared skill or domain expertise (e.g., "python", "testing")
- **Event**: An immutable state change record in the event log

### RFC 2119 Keywords

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

---

## 2. Protocol Foundations

### 2.1 Design Principles

The MAC Protocol is built on four foundational principles:

1. **Actor Isolation**: Agents MUST NOT communicate directly; all communication MUST flow through the orchestrator
2. **Event Immutability**: State changes MUST be append-only; historical events MUST NOT be modified
3. **Deterministic State**: Task state MUST be derivable from event log replay
4. **Human Primacy**: HITL requests MUST take precedence over agent autonomy

### 2.2 Protocol Layers

```
┌─────────────────────────────────────┐
│   Application Layer (Goals/Tasks)   │
├─────────────────────────────────────┤
│   Coordination Layer (State/Events) │
├─────────────────────────────────────┤
│   MCP Layer (Tools/Resources)       │
├─────────────────────────────────────┤
│   Transport Layer (JSON-RPC 2.0)    │
└─────────────────────────────────────┘
```

### 2.3 Conformance Classes

Implementations MUST declare conformance to one of these classes:

- **Class A**: Full orchestrator (all features)
- **Class B**: Minimal orchestrator (core features only, no HITL)
- **Class C**: Agent client (worker implementation)

---

## 3. Message Transport

### 3.1 JSON-RPC 2.0

All protocol messages MUST use JSON-RPC 2.0 format as defined in the [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification).

#### Request Format
```json
{
  "jsonrpc": "2.0",
  "method": "claim_task",
  "params": {
    "agent_id": "a1",
    "capabilities": ["python", "testing"]
  },
  "id": 1
}
```

#### Response Format
```json
{
  "jsonrpc": "2.0",
  "result": {
    "task_id": "t123",
    "description": "Write unit tests for auth module",
    "context": {...}
  },
  "id": 1
}
```

#### Error Format
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid capability format",
    "data": {"field": "capabilities", "expected": "array"}
  },
  "id": 1
}
```

### 3.2 Event Stream Format

Event logs MUST use line-delimited JSON (JSONL) format:

```jsonl
{"type":"agent_registered","agent_id":"a1","timestamp":"2025-11-15T20:00:00Z","sequence":1}
{"type":"task_created","task_id":"t1","timestamp":"2025-11-15T20:00:01Z","sequence":2}
```

#### Requirements

- Each line MUST be a valid JSON object
- Lines MUST be separated by `\n` (LF)
- Lines MUST NOT exceed 1 MB in size
- Files MUST use UTF-8 encoding
- Sequence numbers MUST be monotonically increasing

---

## 4. MCP Integration

### 4.1 MCP Server Requirements

The orchestrator MUST implement an MCP server exposing:

- **Tools**: 8 required tools (see section 4.2)
- **Resources**: 4 required resources (see section 4.3)
- **Transport**: stdio or SSE (server-sent events)

### 4.2 Required Tools

#### 4.2.1 `register_agent`

**Purpose**: Register agent with orchestrator

**Parameters**:
```typescript
{
  agent_id: string;        // REQUIRED: Unique agent identifier
  capabilities: string[];  // REQUIRED: List of capability tags
  metadata?: {             // OPTIONAL
    model?: string;
    version?: string;
    [key: string]: any;
  }
}
```

**Returns**:
```typescript
{
  registered: boolean;
  config: {
    heartbeat_interval_ms: number;
    event_stream_uri: string;
    max_concurrent_tasks: number;
  }
}
```

**Errors**:
- `-32001`: Agent ID already registered
- `-32002`: Invalid capability format
- `-32003`: Agent quota exceeded

#### 4.2.2 `claim_task`

**Purpose**: Request task assignment

**Parameters**:
```typescript
{
  agent_id: string;
  capabilities: string[];  // Filter tasks by capabilities
}
```

**Returns**:
```typescript
{
  task_id: string;
  description: string;
  required_capabilities: string[];
  context: {
    goal_id: string;
    dependencies: Array<{task_id: string, result: any}>;
    [key: string]: any;
  }
} | null  // null if no matching tasks available
```

**Errors**:
- `-32010`: Agent not registered
- `-32011`: Agent at max concurrent task limit

#### 4.2.3 `report_progress`

**Purpose**: Stream task progress update

**Parameters**:
```typescript
{
  task_id: string;
  agent_id: string;
  progress: number;        // REQUIRED: 0.0 to 1.0
  message?: string;        // OPTIONAL: Human-readable status
  artifacts?: string[];    // OPTIONAL: Intermediate outputs
}
```

**Returns**:
```typescript
{
  acknowledged: boolean;
}
```

**Errors**:
- `-32020`: Task not assigned to agent
- `-32021`: Invalid progress value (must be 0.0-1.0)

#### 4.2.4 `complete_task`

**Purpose**: Mark task as successfully completed

**Parameters**:
```typescript
{
  task_id: string;
  agent_id: string;
  result: {
    artifacts: string[];   // REQUIRED: Output files/data
    summary: string;       // REQUIRED: Completion summary
    metrics?: {            // OPTIONAL
      duration_ms?: number;
      [key: string]: any;
    }
  }
}
```

**Returns**:
```typescript
{
  completed: boolean;
  next_task?: {            // OPTIONAL: Suggest next task
    task_id: string;
    description: string;
  }
}
```

**Errors**:
- `-32030`: Task not in RUNNING state
- `-32031`: Result validation failed

#### 4.2.5 `fail_task`

**Purpose**: Report task failure

**Parameters**:
```typescript
{
  task_id: string;
  agent_id: string;
  error: {
    type: string;          // REQUIRED: Error category
    message: string;       // REQUIRED: Error description
    retryable: boolean;    // REQUIRED: Can task be retried?
    context?: any;         // OPTIONAL: Debug info
  }
}
```

**Returns**:
```typescript
{
  acknowledged: boolean;
  action: "retry" | "reassign" | "escalate" | "fail";
  retry_delay_ms?: number;
}
```

**Error Types** (standardized):
- `dependency_error`: Required dependency failed
- `resource_error`: Insufficient resources (memory, API quota)
- `capability_error`: Task requires unavailable capability
- `timeout_error`: Task exceeded time limit
- `logic_error`: Implementation bug or incorrect approach

#### 4.2.6 `request_dependency`

**Purpose**: Request output from dependent task

**Parameters**:
```typescript
{
  task_id: string;           // Current task
  dependency_task_id: string; // Required task
}
```

**Returns**:
```typescript
{
  status: "ready" | "pending" | "failed";
  result?: any;              // Present if status == "ready"
  estimated_completion_ms?: number; // Present if status == "pending"
}
```

**Errors**:
- `-32040`: Dependency not found
- `-32041`: Circular dependency detected

#### 4.2.7 `heartbeat`

**Purpose**: Agent liveness signal

**Parameters**:
```typescript
{
  agent_id: string;
  status: "healthy" | "degraded" | "shutting_down";
  current_tasks: string[];   // Task IDs currently executing
  load?: number;             // OPTIONAL: 0.0 to 1.0
}
```

**Returns**:
```typescript
{
  acknowledged: boolean;
  timestamp: string;         // ISO 8601 server time
}
```

**Requirements**:
- Agents MUST send heartbeat at configured interval (default: 30s)
- Orchestrator MUST consider agent failed after 3 missed heartbeats
- Agents SHOULD send "shutting_down" before graceful termination

#### 4.2.8 `request_human_input`

**Purpose**: Request human intervention

**Parameters**:
```typescript
{
  task_id: string;
  agent_id: string;
  question: string;          // REQUIRED: Human-readable question
  context: object;           // REQUIRED: Background information
  options?: string[];        // OPTIONAL: Predefined choices
  urgency: "low" | "medium" | "high";
  timeout_ms?: number;       // OPTIONAL: Response deadline
}
```

**Returns**:
```typescript
{
  response: string;          // Human's answer
  timestamp: string;
  responder: string;         // Human identifier
}
```

**Behavior**:
- This is a BLOCKING call; agent MUST wait for response
- Orchestrator MUST transition task to AWAITING state
- If timeout expires, orchestrator MAY return default/conservative choice
- In headless mode, orchestrator SHOULD use configured default strategy

**Errors**:
- `-32050`: HITL not available (headless mode with urgency=high)
- `-32051`: Timeout exceeded with no default
- `-32052`: Human explicitly rejected the request

### 4.3 Required Resources

#### 4.3.1 `coordination://tasks/{task_id}`

**Description**: Task details and current state

**URI Template**: `coordination://tasks/{task_id}`

**MIME Type**: `application/json`

**Schema**:
```typescript
{
  task_id: string;
  goal_id: string;
  description: string;
  state: "PENDING" | "RUNNING" | "AWAITING" | "SUCCESS" | "ERROR" | "BLOCKED";
  assigned_agent?: string;
  created_at: string;      // ISO 8601
  updated_at: string;
  progress: number;        // 0.0 to 1.0
  dependencies: string[];  // Task IDs
  required_capabilities: string[];
  result?: any;            // Present if state == SUCCESS
  error?: any;             // Present if state == ERROR
}
```

#### 4.3.2 `coordination://agents/{agent_id}`

**Description**: Agent status and capabilities

**URI Template**: `coordination://agents/{agent_id}`

**MIME Type**: `application/json`

**Schema**:
```typescript
{
  agent_id: string;
  capabilities: string[];
  metadata: object;
  registered_at: string;
  last_heartbeat: string;
  status: "active" | "inactive" | "failed" | "quarantined";
  current_tasks: string[];
  task_history: {
    total: number;
    successful: number;
    failed: number;
    success_rate: number;
  }
}
```

#### 4.3.3 `coordination://goals/{goal_id}`

**Description**: Goal and task decomposition

**URI Template**: `coordination://goals/{goal_id}`

**MIME Type**: `application/json`

**Schema**:
```typescript
{
  goal_id: string;
  description: string;
  state: "decomposing" | "pending_approval" | "executing" | "completed" | "failed";
  task_dag: {
    tasks: Array<{id: string, description: string}>;
    edges: Array<{from: string, to: string}>;
  };
  created_at: string;
  completed_at?: string;
  progress: {
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    percentage: number;
  }
}
```

#### 4.3.4 `coordination://events?since={sequence}`

**Description**: Event stream (JSONL format)

**URI Template**: `coordination://events?since={sequence}`

**MIME Type**: `application/x-ndjson`

**Query Parameters**:
- `since`: (optional) Sequence number to start from (default: 0)
- `limit`: (optional) Max events to return (default: 1000)
- `filter`: (optional) Event type filter (comma-separated)

**Format**: Each line is a JSON event object (see section 5)

---

## 5. Core Message Types

### 5.1 Event Envelope

All events MUST conform to this envelope:

```typescript
{
  type: string;            // REQUIRED: Event type identifier
  timestamp: string;       // REQUIRED: ISO 8601 timestamp
  sequence: number;        // REQUIRED: Monotonic sequence number
  task_id?: string;        // OPTIONAL: Related task
  agent_id?: string;       // OPTIONAL: Related agent
  goal_id?: string;        // OPTIONAL: Related goal
  payload: object;         // REQUIRED: Type-specific data
}
```

### 5.2 Event Type Catalog

#### Goal Events

##### `goal_submitted`
```typescript
{
  type: "goal_submitted",
  goal_id: string,
  description: string,
  constraints?: object,
  requester: string,
  timestamp: string,
  sequence: number,
  payload: {
    priority?: "low" | "medium" | "high",
    deadline?: string
  }
}
```

##### `goal_decomposed`
```typescript
{
  type: "goal_decomposed",
  goal_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    task_dag: {
      tasks: Array<{id: string, description: string, required_capabilities: string[]}>,
      edges: Array<{from: string, to: string}>
    },
    estimated_duration_ms: number
  }
}
```

##### `goal_approved`
```typescript
{
  type: "goal_approved",
  goal_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    approver: string,
    modifications?: object
  }
}
```

##### `goal_rejected`
```typescript
{
  type: "goal_rejected",
  goal_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    approver: string,
    reason: string
  }
}
```

#### Task Events

##### `task_created`
```typescript
{
  type: "task_created",
  task_id: string,
  goal_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    description: string,
    required_capabilities: string[],
    dependencies: string[],
    context: object
  }
}
```

##### `task_assigned`
```typescript
{
  type: "task_assigned",
  task_id: string,
  agent_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    assignment_reason: "capability_match" | "load_balancing" | "retry"
  }
}
```

##### `task_progress`
```typescript
{
  type: "task_progress",
  task_id: string,
  agent_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    progress: number,      // 0.0 to 1.0
    message?: string,
    artifacts?: string[]
  }
}
```

##### `task_completed`
```typescript
{
  type: "task_completed",
  task_id: string,
  agent_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    result: {
      artifacts: string[],
      summary: string,
      metrics?: object
    }
  }
}
```

##### `task_failed`
```typescript
{
  type: "task_failed",
  task_id: string,
  agent_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    error: {
      type: string,
      message: string,
      retryable: boolean,
      context?: any
    },
    retry_count: number
  }
}
```

#### Agent Events

##### `agent_registered`
```typescript
{
  type: "agent_registered",
  agent_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    capabilities: string[],
    metadata: object
  }
}
```

##### `agent_heartbeat`
```typescript
{
  type: "agent_heartbeat",
  agent_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    status: "healthy" | "degraded" | "shutting_down",
    current_tasks: string[],
    load?: number
  }
}
```

##### `agent_failed`
```typescript
{
  type: "agent_failed",
  agent_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    reason: "missed_heartbeats" | "error" | "quarantine",
    last_heartbeat: string,
    in_progress_tasks: string[]
  }
}
```

#### HITL Events

##### `hitl_request`
```typescript
{
  type: "hitl_request",
  task_id: string,
  agent_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    request_id: string,
    question: string,
    context: object,
    options?: string[],
    urgency: "low" | "medium" | "high"
  }
}
```

##### `hitl_response`
```typescript
{
  type: "hitl_response",
  task_id: string,
  timestamp: string,
  sequence: number,
  payload: {
    request_id: string,
    response: string,
    responder: string
  }
}
```

---

## 6. State Transition Rules

### 6.1 Task State Machine

The following state transitions are MANDATORY:

| From State | Event | To State | Conditions |
|------------|-------|----------|------------|
| - | `task_created` | PENDING | Initial state |
| PENDING | `task_assigned` | RUNNING | Agent claimed task |
| PENDING | - | BLOCKED | Dependencies not satisfied |
| BLOCKED | - | PENDING | All dependencies satisfied |
| RUNNING | `task_progress` | RUNNING | Progress update only |
| RUNNING | `task_completed` | SUCCESS | Terminal state |
| RUNNING | `task_failed` | ERROR | retryable=false |
| RUNNING | `task_failed` | PENDING | retryable=true, retry approved |
| RUNNING | `hitl_request` | AWAITING | Waiting for human input |
| AWAITING | `hitl_response` | RUNNING | Human provided input |
| AWAITING | `dependency_resolved` | RUNNING | Dependency became available |

### 6.2 Invariants

The orchestrator MUST enforce these invariants:

1. **Single Assignment**: A task MUST NOT be assigned to multiple agents simultaneously
2. **Acyclic Dependencies**: Task DAG MUST NOT contain cycles
3. **Monotonic Progress**: Task progress MUST NOT decrease (except on reset)
4. **Terminal Finality**: Tasks in SUCCESS or ERROR states MUST NOT transition (except explicit retry)
5. **Agent Liveness**: Tasks assigned to failed agents MUST be reassigned within 5 minutes

---

## 7. Error Handling

### 7.1 Error Codes

The protocol defines these standard JSON-RPC error codes:

| Code | Message | Description |
|------|---------|-------------|
| -32000 | Server error | Generic orchestrator error |
| -32001 | Agent already registered | Duplicate agent_id |
| -32002 | Invalid capability format | Malformed capability string |
| -32010 | Agent not registered | Unknown agent_id |
| -32011 | Task limit exceeded | Max concurrent tasks reached |
| -32020 | Task not assigned | Agent not assigned to task |
| -32030 | Invalid state transition | Illegal state change |
| -32040 | Dependency not found | Unknown dependency_task_id |
| -32050 | HITL unavailable | Headless mode with high urgency |

### 7.2 Retry Semantics

Agents SHOULD implement exponential backoff for retryable errors:

```
delay = min(initial_delay * 2^attempt, max_delay)
```

Recommended values:
- `initial_delay`: 1000ms
- `max_delay`: 60000ms
- `max_attempts`: 5

### 7.3 Failure Recovery

When an agent fails, the orchestrator MUST:

1. Emit `agent_failed` event
2. For each in-progress task:
   - Emit `task_failed` event with `retryable=true`
   - Transition task to PENDING
   - Make task available for reassignment
3. Remove agent from assignment pool

---

## 8. Security Requirements

### 8.1 Authentication

Orchestrators SHOULD implement authentication:

**Recommended**: JWT-based authentication
- Agents receive token on registration
- Token includes `agent_id` claim
- Token expires after 1 hour (refresh required)
- All subsequent requests include `Authorization: Bearer <token>` header

### 8.2 Message Integrity

For production deployments, orchestrators SHOULD sign events:

**Algorithm**: HMAC-SHA256
```typescript
signature = HMAC_SHA256(secret_key, canonical_event_json)
```

Events include signature:
```json
{"type":"task_completed","task_id":"t1","signature":"a1b2c3...","..."}
```

### 8.3 Resource Limits

Orchestrators MUST enforce these limits:

- **Max concurrent tasks per agent**: 5 (configurable)
- **Max event payload size**: 1 MB
- **Max task runtime**: 1 hour (configurable)
- **Max failed tasks per agent per hour**: 10

### 8.4 Access Control

Agents MUST only access:
- Tasks assigned to them
- Results of their dependency tasks
- Public agent registry (capabilities only)

Agents MUST NOT access:
- Other agents' task details
- HITL responses directly
- Event log modification

---

## 9. Compliance

### 9.1 Orchestrator Requirements

A compliant Class A orchestrator MUST:

- [ ] Implement all 8 required MCP tools
- [ ] Expose all 4 required MCP resources
- [ ] Enforce task state machine transitions
- [ ] Maintain append-only event log
- [ ] Support HITL integration
- [ ] Implement heartbeat monitoring
- [ ] Handle agent failures gracefully
- [ ] Validate all message schemas

### 9.2 Agent Requirements

A compliant Class C agent MUST:

- [ ] Register with valid capabilities
- [ ] Send heartbeats at configured interval
- [ ] Claim tasks matching capabilities
- [ ] Report progress during task execution
- [ ] Complete or fail tasks explicitly
- [ ] Request dependencies via orchestrator
- [ ] Respect HITL responses
- [ ] Handle errors gracefully

### 9.3 Interoperability

Implementations MUST support:

- JSON-RPC 2.0 over stdio transport
- ISO 8601 timestamps (UTC)
- UTF-8 encoding
- JSONL event format

Implementations SHOULD support:
- JSON-RPC 2.0 over SSE (server-sent events)
- Message compression (gzip)
- Event filtering by type

---

## 10. Versioning

This specification uses Semantic Versioning (SemVer):

- **MAJOR**: Incompatible protocol changes
- **MINOR**: Backward-compatible additions (new event types, optional fields)
- **PATCH**: Clarifications and bug fixes

Current version: **1.0.0**

Implementations MUST include protocol version in registration:
```json
{
  "agent_id": "a1",
  "protocol_version": "1.0.0",
  "capabilities": [...]
}
```

---

## Appendix A: Complete Example Flow

See `ARCHITECTURE.md` section "Example Workflow" for a comprehensive end-to-end example.

## Appendix B: Event Type Registry

All event types are registered in this specification. Custom implementations MAY add proprietary event types prefixed with `x-`:

```jsonl
{"type":"x-custom-metric","agent_id":"a1","payload":{"gpu_usage":0.8}}
```

Standard event types MUST NOT be modified or extended.

## Appendix C: Capability Naming Conventions

Capabilities SHOULD follow these conventions:

- Lowercase with underscores: `code_generation`, `unit_testing`
- Language tags: `python`, `javascript`, `rust`
- Framework tags: `fastapi`, `react`, `tensorflow`
- Domain tags: `security`, `database`, `devops`

Avoid:
- Versioned capabilities: `python3.11` (use metadata instead)
- Overly specific: `fastapi_with_postgres` (use multiple tags)
- Ambiguous: `backend` (prefer specific capabilities)

---

## References

- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [RFC 2119: Key words for use in RFCs](https://www.rfc-editor.org/rfc/rfc2119)
- [ISO 8601: Date and time format](https://www.iso.org/iso-8601-date-and-time-format.html)
- [NDJSON Specification](http://ndjson.org/)
