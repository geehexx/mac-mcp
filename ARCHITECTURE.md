# Multi-Agent Coordination MCP Server - Architecture Design

## Executive Summary

The Multi-Agent Coordination (MAC) MCP Server is a protocol-sound orchestrator for autonomous LLM-based agent teams. It implements a **Supervisor/Worker** pattern with **Actor model** messaging, **state machine-based** task lifecycle management, and centralized **Human-in-the-Loop** (HITL) intervention. The architecture prioritizes protocol correctness, fault tolerance, and efficient communication over specific technology choices.

## Design Principles

### 1. Protocol Soundness
- **Actor Model**: Agents are independent actors communicating via asynchronous messages
- **Supervisor Pattern**: Orchestrator supervises agent lifecycle with failure recovery strategies
- **State Machine**: Tasks follow deterministic state transitions (PENDING → RUNNING → AWAITING → SUCCESS/ERROR)
- **Event Sourcing**: All state changes are append-only events in JSONL format

### 2. Agent-Centric Design
- **Capability Registry**: Agents declare capabilities at registration
- **Pull-based Dispatch**: Agents request work matching their capabilities (vs push-based assignment)
- **Result Streaming**: Agents stream incremental progress, not just final results
- **Resource Negotiation**: Agents request dependencies from orchestrator, not direct peer access

### 3. Fault Tolerance
- **Heartbeat Protocol**: Periodic liveness checks with configurable timeout
- **Graceful Degradation**: Failed agents don't cascade failures
- **Task Replay**: Failed tasks can be reassigned with full context
- **Circuit Breaker**: Repeatedly failing agents are quarantined

### 4. Human Integration
- **Centralized HITL**: Only orchestrator requests human input
- **Approval Workflows**: Task decomposition, critical decisions, and conflicts require approval
- **Audit Trail**: All HITL interactions logged in event stream

---

## Core Architecture

### Layered Design

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client Layer                      │
│              (Claude Desktop, SDKs, etc.)                │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │ JSON-RPC 2.0
                           ▼
┌─────────────────────────────────────────────────────────┐
│              MAC Orchestrator (MCP Server)               │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   Goal      │  │    Agent     │  │      HITL      │ │
│  │ Decomposer  │  │  Supervisor  │  │   Integrator   │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
│  ┌─────────────────────────────────────────────────────┤ │
│  │         Task State Machine & Event Log              │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │ MCP Tools
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Agent Workers                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Agent A  │  │ Agent B  │  │ Agent C  │  ...         │
│  │(Code Gen)│  │(Research)│  │(Testing) │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### 1. Goal Decomposer
**Purpose**: Transform complex goals into executable task DAGs (Directed Acyclic Graphs)

**Operations**:
- Parse natural language goals into structured task definitions
- Build dependency graph (topological ordering)
- Identify parallelizable vs sequential tasks
- Request HITL approval for decomposition plan

**Output**: Task DAG with dependency edges

#### 2. Agent Supervisor
**Purpose**: Manage agent lifecycle and health

**Operations**:
- Agent registration with capability declarations
- Heartbeat monitoring (liveness detection)
- Failure recovery (restart strategies)
- Load balancing (task assignment to capable agents)

**Strategies**:
- **Restart**: For transient failures (network timeout)
- **Reassign**: For persistent failures (move task to different agent)
- **Escalate**: For systemic failures (request HITL intervention)

#### 3. HITL Integrator
**Purpose**: Centralized human intervention point

**Trigger Conditions**:
- Task decomposition approval (DAG review)
- Conflict resolution (agents disagree on approach)
- Critical decision points (flagged by agents)
- Security/safety validation (before execution)

**Interface**: MCP tool `request_human_input` with structured context

#### 4. Task State Machine & Event Log
**Purpose**: Authoritative source of truth for all state

**Storage**: JSONL append-only log (event sourcing)

**State Transitions**: See [Task Lifecycle](#task-lifecycle) section

---

## Task Lifecycle

### State Machine

```
                         ┌──────────┐
                         │  PENDING │ (Initial state)
                         └─────┬────┘
                               │ assigned_to_agent
                               ▼
                         ┌──────────┐
                    ┌────┤  RUNNING │────┐
                    │    └─────┬────┘    │
    requires_input  │          │         │ agent_failed
                    │          │ completed│
                    ▼          ▼         ▼
              ┌──────────┐ ┌─────────┐ ┌───────┐
              │ AWAITING │ │ SUCCESS │ │ ERROR │ (Terminal states)
              └────┬─────┘ └─────────┘ └───┬───┘
                   │                        │
                   │ input_provided         │ retry_approved
                   ▼                        ▼
              ┌──────────┐            ┌──────────┐
              │  RUNNING │            │ PENDING  │
              └──────────┘            └──────────┘
```

### State Definitions

| State | Description | Transitions |
|-------|-------------|-------------|
| **PENDING** | Task created, waiting for capable agent | → RUNNING (agent claims), → BLOCKED (dependency) |
| **RUNNING** | Agent actively executing task | → AWAITING (needs input), → SUCCESS, → ERROR |
| **AWAITING** | Blocked on dependency/input | → RUNNING (dependency resolved) |
| **SUCCESS** | Task completed successfully | Terminal |
| **ERROR** | Task failed permanently | → PENDING (retry), Terminal |
| **BLOCKED** | Dependencies not met | → PENDING (dependencies ready) |

### Event Types

All state transitions are recorded as JSONL events:

```jsonl
{"type":"task_created","task_id":"t1","goal":"Implement auth","dependencies":[],"timestamp":"2025-11-15T20:00:00Z"}
{"type":"task_assigned","task_id":"t1","agent_id":"a1","timestamp":"2025-11-15T20:00:05Z"}
{"type":"task_progress","task_id":"t1","agent_id":"a1","progress":0.3,"message":"Generated schema","timestamp":"2025-11-15T20:00:15Z"}
{"type":"task_awaiting_input","task_id":"t1","agent_id":"a1","reason":"Choose OAuth provider","options":["Auth0","Cognito"],"timestamp":"2025-11-15T20:00:20Z"}
{"type":"hitl_response","task_id":"t1","choice":"Auth0","timestamp":"2025-11-15T20:05:00Z"}
{"type":"task_completed","task_id":"t1","agent_id":"a1","result":{"status":"success","artifact":"auth_module.py"},"timestamp":"2025-11-15T20:10:00Z"}
```

---

## Protocol Specification

### MCP Resources

Expose coordination state via read-only MCP resources:

#### 1. `coordination://tasks/{task_id}`
- **Description**: Task details and current state
- **MIME Type**: `application/json`
- **Contents**: Task definition, state, assigned agent, progress, dependencies

#### 2. `coordination://agents/{agent_id}`
- **Description**: Agent status and capabilities
- **MIME Type**: `application/json`
- **Contents**: Agent metadata, registered capabilities, current tasks, health

#### 3. `coordination://goals/{goal_id}`
- **Description**: High-level goal and decomposition
- **MIME Type**: `application/json`
- **Contents**: Original goal, task DAG, overall progress

#### 4. `coordination://events?since={timestamp}`
- **Description**: Event stream (JSONL format)
- **MIME Type**: `application/x-ndjson`
- **Contents**: Append-only log of all state changes

### MCP Tools

Orchestrator provides these tools for agent operations:

#### 1. `register_agent`
**Purpose**: Agent joins coordination network

**Parameters**:
```json
{
  "agent_id": "unique-agent-identifier",
  "capabilities": ["code_generation", "python", "testing"],
  "metadata": {
    "model": "claude-sonnet-4",
    "version": "1.0.0"
  }
}
```

**Returns**: Registration confirmation with orchestrator config

#### 2. `claim_task`
**Purpose**: Agent requests work matching capabilities (pull model)

**Parameters**:
```json
{
  "agent_id": "agent-123",
  "capabilities": ["code_generation", "python"]
}
```

**Returns**: Task assignment or null if no matching work

#### 3. `report_progress`
**Purpose**: Stream incremental progress updates

**Parameters**:
```json
{
  "task_id": "task-456",
  "agent_id": "agent-123",
  "progress": 0.65,
  "message": "Generated test fixtures",
  "artifacts": ["tests/fixtures.py"]
}
```

**Returns**: Acknowledgment

#### 4. `request_dependency`
**Purpose**: Request output from dependent task

**Parameters**:
```json
{
  "task_id": "current-task",
  "dependency_task_id": "prerequisite-task"
}
```

**Returns**: Dependency task result or AWAITING status

#### 5. `complete_task`
**Purpose**: Mark task as successfully completed

**Parameters**:
```json
{
  "task_id": "task-456",
  "agent_id": "agent-123",
  "result": {
    "artifacts": ["src/auth.py", "tests/test_auth.py"],
    "summary": "Implemented OAuth2 authentication"
  }
}
```

**Returns**: Confirmation and next available task

#### 6. `fail_task`
**Purpose**: Report task failure with context

**Parameters**:
```json
{
  "task_id": "task-456",
  "agent_id": "agent-123",
  "error": {
    "type": "dependency_error",
    "message": "Missing database schema",
    "retryable": true
  }
}
```

**Returns**: Orchestrator decision (retry, reassign, escalate)

#### 7. `heartbeat`
**Purpose**: Liveness signal from agent

**Parameters**:
```json
{
  "agent_id": "agent-123",
  "status": "healthy",
  "current_tasks": ["task-456"]
}
```

**Returns**: Acknowledgment

#### 8. `request_human_input`
**Purpose**: Escalate decision to human (routed through orchestrator)

**Parameters**:
```json
{
  "task_id": "task-456",
  "agent_id": "agent-123",
  "question": "Should I use REST or GraphQL API?",
  "context": {
    "current_stack": "Node.js + PostgreSQL",
    "tradeoffs": "..."
  },
  "options": ["REST", "GraphQL"],
  "urgency": "medium"
}
```

**Returns**: Human response (blocking call with timeout)

---

## Message Schemas (JSONL)

### Event Stream Format

All events follow this envelope:

```typescript
{
  type: string;           // Event type identifier
  timestamp: string;      // ISO 8601 timestamp
  task_id?: string;       // Related task (if applicable)
  agent_id?: string;      // Related agent (if applicable)
  goal_id?: string;       // Related goal (if applicable)
  sequence: number;       // Monotonic sequence number
  payload: object;        // Type-specific data
}
```

### Core Event Types

#### 1. Goal Events
```jsonl
{"type":"goal_submitted","goal_id":"g1","description":"Build authentication system","requester":"user@example.com","timestamp":"...","sequence":1}
{"type":"goal_decomposed","goal_id":"g1","task_dag":{"nodes":[...],"edges":[...]},"timestamp":"...","sequence":2}
{"type":"goal_approved","goal_id":"g1","approver":"human","timestamp":"...","sequence":3}
```

#### 2. Task Events
```jsonl
{"type":"task_created","task_id":"t1","goal_id":"g1","description":"Design database schema","dependencies":[],"required_capabilities":["database","sql"],"timestamp":"...","sequence":4}
{"type":"task_assigned","task_id":"t1","agent_id":"a1","timestamp":"...","sequence":5}
{"type":"task_progress","task_id":"t1","agent_id":"a1","progress":0.5,"message":"Created users table","timestamp":"...","sequence":6}
{"type":"task_completed","task_id":"t1","agent_id":"a1","result":{...},"timestamp":"...","sequence":7}
```

#### 3. Agent Events
```jsonl
{"type":"agent_registered","agent_id":"a1","capabilities":["database","sql","postgresql"],"metadata":{...},"timestamp":"...","sequence":8}
{"type":"agent_heartbeat","agent_id":"a1","status":"healthy","load":0.6,"timestamp":"...","sequence":9}
{"type":"agent_failed","agent_id":"a1","reason":"timeout","timestamp":"...","sequence":10}
{"type":"agent_quarantined","agent_id":"a1","failure_count":3,"timestamp":"...","sequence":11}
```

#### 4. HITL Events
```jsonl
{"type":"hitl_request","request_id":"h1","task_id":"t1","agent_id":"a1","question":"Approve schema design?","context":{...},"timestamp":"...","sequence":12}
{"type":"hitl_response","request_id":"h1","response":"approved","details":{...},"timestamp":"...","sequence":13}
```

#### 5. Dependency Events
```jsonl
{"type":"dependency_requested","task_id":"t2","dependency_task_id":"t1","timestamp":"...","sequence":14}
{"type":"dependency_resolved","task_id":"t2","dependency_task_id":"t1","result":{...},"timestamp":"...","sequence":15}
```

---

## Agent Communication Patterns

### 1. Registration & Capability Discovery

```
Agent                           Orchestrator
  │                                  │
  │──register_agent(capabilities)──>│
  │                                  │
  │<───registration_config───────────│
  │    (heartbeat_interval,          │
  │     event_stream_uri)            │
  │                                  │
```

### 2. Task Claiming (Pull Model)

```
Agent                           Orchestrator
  │                                  │
  │──claim_task(capabilities)───────>│
  │                                  │
  │                    [Match pending tasks
  │                     to capabilities]
  │                                  │
  │<───task_assignment OR null───────│
  │                                  │
```

**Rationale**: Pull model prevents orchestrator overload and allows agents to self-regulate workload.

### 3. Progress Streaming

```
Agent                           Orchestrator                  Event Stream
  │                                  │                              │
  │──report_progress(30%)───────────>│                              │
  │                                  │──task_progress_event────────>│
  │                                  │                              │
  │──report_progress(65%)───────────>│                              │
  │                                  │──task_progress_event────────>│
  │                                  │                              │
```

### 4. Dependency Resolution

```
Agent B                         Orchestrator                  Agent A
  │                                  │                              │
  │──request_dependency(task_A)─────>│                              │
  │                                  │                              │
  │                     [Check task_A state]                        │
  │                                  │                              │
  │<───result OR AWAITING────────────│                              │
  │                                  │                              │
  [If AWAITING, Agent B transitions               [Agent A completes]
   to AWAITING state and waits]                                    │
  │                                  │<──complete_task─────────────│
  │                                  │                              │
  │<───dependency_resolved event─────│                              │
  │                                  │                              │
  │──claim_task() [resume work]─────>│                              │
```

**Key Property**: Agents never communicate directly. Orchestrator mediates all data flow.

### 5. HITL Escalation

```
Agent                   Orchestrator                Human
  │                          │                         │
  │──request_human_input────>│                         │
  │    (blocking call)       │                         │
  │                          │                         │
  │               [Transition task to                  │
  │                AWAITING state]                     │
  │                          │                         │
  │                          │──HITL request (MCP)────>│
  │                          │                         │
  │                          │<──response──────────────│
  │                          │                         │
  │<───response──────────────│                         │
  │                          │                         │
```

**Timeout Handling**: If human doesn't respond within timeout, orchestrator can:
- Use default/conservative choice
- Reassign task to different agent
- Mark task as ERROR with reason "hitl_timeout"

---

## Fault Tolerance Mechanisms

### 1. Heartbeat Protocol

**Configuration**:
- **Interval**: 30 seconds (configurable)
- **Timeout**: 3 missed heartbeats = 90 seconds
- **Failure Action**: Reassign in-progress tasks

**Implementation**:
```python
# Pseudo-code
class AgentSupervisor:
    def monitor_agent_health(self, agent_id: str):
        last_heartbeat = self.get_last_heartbeat(agent_id)
        if now() - last_heartbeat > HEARTBEAT_TIMEOUT:
            self.emit_event("agent_failed", agent_id=agent_id)
            tasks = self.get_agent_tasks(agent_id)
            for task in tasks:
                self.reassign_task(task.id)
```

### 2. Task Retry Strategy

**Retry Decision Matrix**:

| Error Type | Retryable? | Strategy |
|------------|------------|----------|
| Network timeout | Yes | Retry same agent (max 3) |
| Capability mismatch | No | Reassign to different agent |
| Resource exhaustion | Yes | Retry after delay (exponential backoff) |
| Logic error | No | Escalate to HITL |
| Dependency failure | Yes | Wait for dependency retry |

### 3. Circuit Breaker

**Purpose**: Prevent cascading failures from repeatedly failing agents

**Thresholds**:
- **Failure Count**: 3 failures within 10 minutes
- **Action**: Quarantine agent (remove from task assignment pool)
- **Recovery**: Manual intervention or time-based (24 hours)

### 4. Graceful Degradation

**Scenario**: Critical agent type unavailable (e.g., all "testing" agents failed)

**Response**:
1. Emit warning event
2. Request HITL notification
3. Continue executing non-dependent tasks
4. Suggest manual completion or alternate approach

---

## HITL Integration Design

### Integration Points

#### 1. Goal Approval
**Trigger**: After goal decomposition into task DAG
**Purpose**: Validate decomposition plan before execution
**Interface**: Visual DAG representation + task descriptions

**Example Request**:
```json
{
  "type": "goal_approval",
  "goal": "Build user authentication system",
  "proposed_dag": {
    "tasks": [
      {"id": "t1", "desc": "Design database schema"},
      {"id": "t2", "desc": "Implement OAuth2 flow", "depends_on": ["t1"]},
      {"id": "t3", "desc": "Add session management", "depends_on": ["t2"]},
      {"id": "t4", "desc": "Write integration tests", "depends_on": ["t2", "t3"]}
    ]
  },
  "estimated_time": "2 hours",
  "agent_allocation": {"code_gen": 2, "testing": 1}
}
```

#### 2. Conflict Resolution
**Trigger**: Multiple agents propose contradictory approaches
**Purpose**: Human decides between competing solutions

**Example**:
```json
{
  "type": "conflict_resolution",
  "task_id": "t2",
  "conflict": "API design approach",
  "proposals": [
    {"agent": "a1", "approach": "REST", "rationale": "..."},
    {"agent": "a2", "approach": "GraphQL", "rationale": "..."}
  ]
}
```

#### 3. Critical Decision
**Trigger**: Agent flags decision as requiring human judgment
**Purpose**: Security, compliance, or high-stakes choices

**Example**:
```json
{
  "type": "critical_decision",
  "task_id": "t5",
  "decision": "Store passwords using bcrypt or Argon2?",
  "security_implications": "...",
  "recommendations": [...]
}
```

#### 4. Error Escalation
**Trigger**: Task failed multiple retries
**Purpose**: Human diagnosis and intervention

**Example**:
```json
{
  "type": "error_escalation",
  "task_id": "t3",
  "failures": [
    {"attempt": 1, "agent": "a1", "error": "..."},
    {"attempt": 2, "agent": "a2", "error": "..."}
  ],
  "context": "All available agents failed on session storage implementation"
}
```

### HITL Response Format

```json
{
  "request_id": "h123",
  "decision": "approve|reject|modify",
  "details": {
    "selected_option": "...",
    "modifications": [...],
    "reasoning": "..."
  },
  "timestamp": "2025-11-15T20:30:00Z"
}
```

### Headless Mode

**Configuration**: `--headless` flag or `MAC_HEADLESS=true`

**Behavior**:
- HITL requests with `urgency: low` → Use default/conservative choice
- HITL requests with `urgency: medium` → Wait with timeout, then default
- HITL requests with `urgency: high` → Block indefinitely (log warning)

**Use Case**: CI/CD pipelines, automated workflows

---

## Performance Considerations

### 1. Event Stream Efficiency

**JSONL Benefits**:
- **Streamable**: Parse line-by-line without loading entire file
- **Appendable**: O(1) write operations
- **Debuggable**: Human-readable with standard tools (`jq`, `grep`)
- **Compressible**: Text compression (gzip) achieves ~10x reduction

**Trade-off**: No indexed queries (require secondary indexes)

### 2. Task Assignment Latency

**Pull Model Overhead**:
- Agents poll orchestrator (potential latency)
- **Mitigation**: WebSocket-based event notifications
  - Agents maintain persistent connection
  - Orchestrator pushes "task_available" events
  - Agents respond with `claim_task` call

**Comparison**:
| Model | Latency | Scalability | Backpressure |
|-------|---------|-------------|--------------|
| Push | Low (~10ms) | Medium | Poor |
| Pull (polling) | High (~1s) | High | Excellent |
| Pull (WebSocket) | Low (~50ms) | High | Excellent |

**Recommendation**: WebSocket-enhanced pull model

### 3. Dependency Graph Traversal

**Algorithm**: Topological sort with Kahn's algorithm (O(V + E))

**Optimization**: Pre-compute "ready tasks" (all dependencies satisfied)
- Maintain priority queue sorted by priority/creation time
- Update on task completion (O(log N) recomputation)

### 4. State Reconstruction

**Event Sourcing Trade-off**:
- **Benefit**: Complete audit trail, time-travel debugging
- **Cost**: State reconstruction requires replay (O(N) events)

**Mitigation**: Snapshot Strategy
- Periodic snapshots of current state (every 1000 events)
- Reconstruction = Load snapshot + Replay recent events
- **Formula**: `reconstruction_time = snapshot_load + (events_since_snapshot * avg_event_process_time)`

---

## Security Considerations

### 1. Agent Authentication

**Problem**: Prevent agent impersonation (spoofing `agent_id`)

**Solution**: API Key or JWT-based authentication
```json
{
  "agent_id": "a1",
  "auth_token": "jwt_token_here",
  "capabilities": [...]
}
```

**Token Generation**:
- Orchestrator issues tokens on registration
- Tokens include `agent_id` claim
- Short-lived (1 hour) with refresh mechanism

### 2. Message Integrity

**Problem**: Prevent event log tampering

**Solution**: Message signing with HMAC-SHA256
```jsonl
{"type":"task_completed","task_id":"t1","signature":"hmac_sha256_hex"}
```

**Verification**:
- Orchestrator signs all events with secret key
- Consumers verify signature before trusting event
- Detect tampering or corruption

### 3. Resource Limits

**Problem**: Malicious agents could exhaust resources

**Quotas**:
- Max concurrent tasks per agent: 5
- Max event payload size: 1 MB
- Max task runtime: 1 hour (configurable)
- Max failed tasks per agent: 10 per hour

**Enforcement**: Orchestrator rejects operations exceeding quotas

### 4. Principle of Least Privilege

**Access Control**:
- Agents can only access:
  - Tasks assigned to them
  - Results of their dependency tasks
  - Public agent registry (capabilities only, not task details)

- Agents CANNOT:
  - Access other agents' task details
  - Modify task definitions
  - Reassign tasks
  - Access HITL responses directly (orchestrator mediates)

---

## Extensibility Points

### 1. Custom Capability Matching

**Default**: Exact string match (`agent.capabilities ∩ task.required_capabilities ≠ ∅`)

**Extension**: Semantic matching
```python
class SemanticMatcher(CapabilityMatcher):
    def match(self, agent_caps: List[str], task_caps: List[str]) -> float:
        # Use embedding similarity
        return cosine_similarity(embed(agent_caps), embed(task_caps))
```

### 2. Pluggable Storage Backends

**Interface**:
```python
class EventStore(Protocol):
    def append(self, event: Event) -> None
    def read(self, since: int) -> Iterator[Event]
    def snapshot(self) -> State
```

**Implementations**:
- `InMemoryEventStore`: For development/testing
- `FileEventStore`: JSONL file (default)
- `DatabaseEventStore`: PostgreSQL, SQLite (custom)
- `StreamEventStore`: Kafka, Kinesis (high-throughput)

### 3. Goal Decomposition Strategies

**Interface**:
```python
class GoalDecomposer(Protocol):
    def decompose(self, goal: str) -> TaskDAG
```

**Implementations**:
- `LLMDecomposer`: Use Claude to generate task breakdown (default)
- `TemplateDecomposer`: Pattern-based (e.g., "implement feature X" → standard tasks)
- `InteractiveDecomposer`: Prompt human for decomposition

### 4. HITL Backends

**Interface**:
```python
class HITLBackend(Protocol):
    def request_input(self, context: dict) -> str
```

**Implementations**:
- `MCPHITLBackend`: Use existing hitl-mcp-cli server
- `CLIHITLBackend`: Terminal prompts
- `WebHITLBackend`: Web dashboard
- `SlackHITLBackend`: Slack bot notifications

---

## Deployment Modes

### 1. Development Mode
```bash
mac-mcp serve --mode dev --storage memory --hitl cli
```
- In-memory storage (no persistence)
- CLI-based HITL prompts
- Verbose logging
- No authentication

### 2. Production Mode
```bash
mac-mcp serve --mode prod --storage file --hitl mcp --auth enabled
```
- File-based event store (JSONL)
- MCP-based HITL integration
- Structured logging (JSON)
- JWT authentication required

### 3. Headless Mode
```bash
mac-mcp serve --headless --hitl-strategy conservative
```
- No human intervention
- Use defaults for HITL requests
- Suitable for CI/CD

### 4. Distributed Mode (Future)
```bash
mac-mcp serve --distributed --coordinator redis://...
```
- Multiple orchestrator instances
- Shared state via Redis/etcd
- Horizontal scalability

---

## Example Workflow

### Scenario: "Build a REST API for user management"

#### 1. Goal Submission
```json
{
  "goal": "Build a REST API for user management with CRUD operations",
  "constraints": {
    "language": "Python",
    "framework": "FastAPI",
    "database": "PostgreSQL"
  }
}
```

#### 2. Goal Decomposition (LLM-based)
```json
{
  "task_dag": {
    "tasks": [
      {
        "id": "t1",
        "description": "Design database schema for users table",
        "required_capabilities": ["database", "postgresql"],
        "dependencies": []
      },
      {
        "id": "t2",
        "description": "Implement FastAPI models and schemas",
        "required_capabilities": ["python", "fastapi"],
        "dependencies": ["t1"]
      },
      {
        "id": "t3",
        "description": "Implement CRUD endpoints",
        "required_capabilities": ["python", "fastapi"],
        "dependencies": ["t2"]
      },
      {
        "id": "t4",
        "description": "Write integration tests",
        "required_capabilities": ["python", "pytest"],
        "dependencies": ["t3"]
      },
      {
        "id": "t5",
        "description": "Add API documentation",
        "required_capabilities": ["documentation"],
        "dependencies": ["t3"]
      }
    ]
  }
}
```

#### 3. HITL Approval Request
```
╔═══════════════════════════════════════════════════════════╗
║  Goal Decomposition Approval Required                     ║
╠═══════════════════════════════════════════════════════════╣
║  Goal: Build REST API for user management                 ║
║  Proposed Tasks: 5                                         ║
║  Estimated Time: 3 hours                                   ║
║  Required Agents: database(1), python(2), documentation(1) ║
║                                                            ║
║  Task DAG:                                                 ║
║    t1 (Design schema)                                      ║
║     └─> t2 (FastAPI models)                                ║
║          └─> t3 (CRUD endpoints)                           ║
║               ├─> t4 (Tests)                               ║
║               └─> t5 (Docs)                                ║
║                                                            ║
║  Approve? [Y/n/modify]:                                    ║
╚═══════════════════════════════════════════════════════════╝
```

#### 4. Agent Registration
```jsonl
{"type":"agent_registered","agent_id":"db_agent","capabilities":["database","postgresql","sql"],"timestamp":"..."}
{"type":"agent_registered","agent_id":"py_agent_1","capabilities":["python","fastapi","sqlalchemy"],"timestamp":"..."}
{"type":"agent_registered","agent_id":"py_agent_2","capabilities":["python","fastapi","pytest"],"timestamp":"..."}
{"type":"agent_registered","agent_id":"doc_agent","capabilities":["documentation","openapi"],"timestamp":"..."}
```

#### 5. Task Execution (Event Stream)
```jsonl
{"type":"task_created","task_id":"t1","description":"Design database schema","state":"PENDING","timestamp":"..."}
{"type":"task_assigned","task_id":"t1","agent_id":"db_agent","timestamp":"..."}
{"type":"task_progress","task_id":"t1","progress":0.5,"message":"Created users table definition","timestamp":"..."}
{"type":"task_completed","task_id":"t1","result":{"artifact":"schema.sql"},"timestamp":"..."}

{"type":"task_created","task_id":"t2","state":"PENDING","timestamp":"..."}
{"type":"task_assigned","task_id":"t2","agent_id":"py_agent_1","timestamp":"..."}
{"type":"dependency_requested","task_id":"t2","dependency":"t1","timestamp":"..."}
{"type":"dependency_resolved","task_id":"t2","dependency":"t1","result":{"artifact":"schema.sql"},"timestamp":"..."}
{"type":"task_progress","task_id":"t2","progress":0.7,"message":"Generated Pydantic models","timestamp":"..."}
{"type":"task_completed","task_id":"t2","result":{"artifacts":["models.py","schemas.py"]},"timestamp":"..."}

{"type":"task_created","task_id":"t3","state":"PENDING","timestamp":"..."}
{"type":"task_assigned","task_id":"t3","agent_id":"py_agent_1","timestamp":"..."}
{"type":"task_awaiting_input","task_id":"t3","reason":"Endpoint authentication strategy","timestamp":"..."}
{"type":"hitl_request","request_id":"h1","question":"Use JWT or session-based auth?","options":["JWT","Session"],"timestamp":"..."}
{"type":"hitl_response","request_id":"h1","choice":"JWT","timestamp":"..."}
{"type":"task_progress","task_id":"t3","progress":1.0,"message":"Implemented all CRUD endpoints with JWT auth","timestamp":"..."}
{"type":"task_completed","task_id":"t3","result":{"artifacts":["routes.py","auth.py"]},"timestamp":"..."}

{"type":"task_created","task_id":"t4","state":"PENDING","timestamp":"..."}
{"type":"task_created","task_id":"t5","state":"PENDING","timestamp":"..."}
{"type":"task_assigned","task_id":"t4","agent_id":"py_agent_2","timestamp":"..."}
{"type":"task_assigned","task_id":"t5","agent_id":"doc_agent","timestamp":"..."}

[Both t4 and t5 execute in parallel]

{"type":"task_completed","task_id":"t4","result":{"artifacts":["test_routes.py"],"test_coverage":0.95},"timestamp":"..."}
{"type":"task_completed","task_id":"t5","result":{"artifacts":["README.md","openapi.yaml"]},"timestamp":"..."}

{"type":"goal_completed","goal_id":"g1","success":true,"total_time":"2.5h","timestamp":"..."}
```

#### 6. Final Result
```json
{
  "goal_id": "g1",
  "status": "SUCCESS",
  "artifacts": [
    "schema.sql",
    "models.py",
    "schemas.py",
    "routes.py",
    "auth.py",
    "test_routes.py",
    "README.md",
    "openapi.yaml"
  ],
  "metrics": {
    "total_time": "2.5 hours",
    "tasks_completed": 5,
    "hitl_interventions": 2,
    "agent_failures": 0
  }
}
```

---

## Comparison with Alternative Architectures

### vs. Direct Agent-to-Agent Communication (Choreography)

| Aspect | MAC (Orchestration) | Choreography |
|--------|---------------------|--------------|
| **Coordination** | Centralized | Distributed |
| **HITL Integration** | Single point | Multiple points |
| **Debugging** | Complete audit trail | Partial logs |
| **Fault Tolerance** | Supervisor handles | Peer recovery |
| **Complexity** | O(N) connections | O(N²) connections |

**Verdict**: Orchestration is superior for HITL integration and debuggability.

### vs. Shared Blackboard Architecture

| Aspect | MAC | Blackboard |
|--------|-----|------------|
| **State Management** | Explicit state machine | Implicit (knowledge sources) |
| **Task Assignment** | Pull-based with capabilities | Opportunistic (pattern matching) |
| **Determinism** | High | Low |
| **LLM Suitability** | High (clear prompts) | Medium (complex rules) |

**Verdict**: MAC is more suitable for LLM agents due to explicit task definitions.

### vs. Workflow Engines (Temporal, Airflow)

| Aspect | MAC | Workflow Engines |
|--------|-----|------------------|
| **Agent Dynamism** | Agents join/leave | Static workers |
| **Capability Matching** | First-class | Manual configuration |
| **HITL** | Built-in | Plugin required |
| **LLM-Centric** | Yes | No |

**Verdict**: MAC is purpose-built for LLM agents; workflow engines are general-purpose.

---

## Open Questions & Future Work

### 1. Multi-Tenancy
**Question**: How to isolate goals from different users?

**Proposal**: Namespace isolation
- Goal IDs prefixed with tenant: `{tenant_id}:{goal_id}`
- Agents register per-tenant
- Event streams partitioned by tenant

### 2. Agent Pricing & Cost Optimization
**Question**: How to allocate expensive LLM calls efficiently?

**Proposal**: Cost-aware scheduling
- Agents declare cost per task (e.g., API credits)
- Orchestrator optimizes for cost + time trade-off
- Cheaper agents preferred for low-priority tasks

### 3. Cross-Goal Learning
**Question**: Can agents learn from past goal executions?

**Proposal**: Decomposition templates
- Successful DAGs stored as templates
- Similar goals reuse templates (faster decomposition)
- Embedding-based similarity search

### 4. Adversarial Agents
**Question**: How to handle malicious or compromised agents?

**Proposal**: Reputation system
- Track success rate per agent
- Isolate low-reputation agents
- Multi-agent verification for critical tasks

### 5. Dynamic Re-planning
**Question**: What if initial task decomposition is wrong?

**Proposal**: Adaptive DAG rewriting
- Agents can propose DAG modifications
- Requires HITL approval
- Event log preserves history

---

## Implementation Roadmap

### Phase 1: Core Orchestrator (MVP)
- [ ] Event store (JSONL file backend)
- [ ] Task state machine
- [ ] Agent registration and heartbeat
- [ ] Basic task assignment (pull model)
- [ ] MCP server implementation

### Phase 2: HITL Integration
- [ ] CLI-based HITL backend
- [ ] MCP-based HITL integration
- [ ] Goal approval workflow
- [ ] Error escalation

### Phase 3: Advanced Features
- [ ] Dependency graph optimization
- [ ] WebSocket-based task notifications
- [ ] Agent capability matching (semantic)
- [ ] Snapshot-based state reconstruction

### Phase 4: Production Hardening
- [ ] Authentication (JWT)
- [ ] Message signing (HMAC)
- [ ] Rate limiting and quotas
- [ ] Monitoring and metrics

### Phase 5: Scalability
- [ ] Distributed orchestrator (Redis coordination)
- [ ] Pluggable storage backends (PostgreSQL, Kafka)
- [ ] Multi-tenancy support

---

## Conclusion

The Multi-Agent Coordination MCP Server architecture is grounded in proven distributed systems principles:

- **Actor Model** for isolated, message-passing agents
- **Supervisor Pattern** for fault-tolerant agent lifecycle management
- **State Machines** for deterministic task progression
- **Event Sourcing** for complete auditability

The design prioritizes:
1. **Protocol soundness** over implementation shortcuts
2. **Agent autonomy** within orchestrator guardrails
3. **Human agency** through centralized HITL integration
4. **Operational transparency** via JSONL event streams

This architecture provides a **robust, scalable, and debuggable** foundation for building multi-agent AI systems that are safe, efficient, and aligned with human intent.
