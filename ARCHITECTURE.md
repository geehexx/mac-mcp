---
title: Multi-Agent Coordination MCP Server - Architecture Design
description: Comprehensive system architecture and design patterns
version: 1.1.0
status: complete
type: technical-specification
category: architecture
keywords: [architecture, design-patterns, supervisor-worker, actor-model, state-machine, event-sourcing, autonomous-agents]
authors: [geehexx]
created: 2025-11-15
updated: 2025-11-15
related_docs: [PROTOCOL.md, DESIGN_RATIONALE.md, README.md]
machine_readable: true
schema_version: 1.0.0
components:
  - goal_decomposer
  - agent_supervisor
  - dependency_manager
  - task_state_machine
  - event_log
  - llm_provider
  - configuration_system
  - tui_dashboard
patterns: [actor-model, supervisor-worker, event-sourcing, state-machine, autonomous-operation]
---

# Multi-Agent Coordination MCP Server - Architecture Design

## Executive Summary

The Multi-Agent Coordination (MAC) MCP Server is a protocol-sound orchestrator for fully autonomous LLM-based agent teams. It implements a **Supervisor/Worker** pattern with **Actor model** messaging, **state machine-based** task lifecycle management, and **LLM-powered autonomous goal decomposition**. The architecture prioritizes protocol correctness, fault tolerance, autonomous operation, and efficient communication over specific technology choices.

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

### 4. Autonomous Operation
- **LLM-based Decomposition**: Goals autonomously decomposed into task DAGs using Claude
- **No Human Intervention**: Pure agent-to-agent coordination
- **Dependency Resolution**: Agents coordinate via orchestrator-mediated dependency requests
- **Audit Trail**: All operations logged in event stream

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
│  │   Goal      │  │    Agent     │  │  Dependency    │ │
│  │ Decomposer  │  │  Supervisor  │  │   Manager      │ │
│  │  (Claude)   │  │              │  │                │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
│  ┌─────────────────────────────────────────────────────┤ │
│  │         Task State Machine & Event Log              │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────┤ │
│  │     Configuration System & LLM Provider             │ │
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
**Purpose**: Transform complex goals into executable task DAGs (Directed Acyclic Graphs) autonomously

**Operations**:
- Parse natural language goals into structured task definitions
- Build dependency graph (topological ordering)
- Identify parallelizable vs sequential tasks
- Generate capability requirements for each task

**LLM Integration**:
- Uses configured LLM provider (Anthropic API or AWS Bedrock)
- Structured prompts for consistent decomposition
- Validates acyclic property of generated DAG

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
- **Quarantine**: For repeated failures (circuit breaker activation)

#### 3. Dependency Manager
**Purpose**: Mediate task-to-task dependencies

**Operations**:
- Track task completion states
- Provide dependency results to requesting agents
- Manage AWAITING state transitions
- Ensure task order respects dependency graph

**Interface**: MCP tool `request_dependency` for agents

#### 4. Task State Machine & Event Log
**Purpose**: Authoritative source of truth for all state

**Storage**: JSONL append-only log (event sourcing)

**State Transitions**: See [Task Lifecycle](#task-lifecycle) section

#### 5. Configuration System
**Purpose**: Centralized, validated configuration management

**Features**:
- YAML configuration files
- Environment variable support
- Pydantic-based validation
- Multi-provider LLM configuration

**Configuration Domains**:
- LLM Provider (Anthropic or Bedrock)
- Server settings (transport, storage, heartbeat)
- UI mode (TUI or headless)
- Logging configuration

#### 6. LLM Provider Abstraction
**Purpose**: Support multiple LLM backends for goal decomposition

**Implementations**:
- **AnthropicProvider**: Direct Anthropic API integration
- **BedrockProvider**: AWS Bedrock integration with boto3

**Interface**: Abstract `LLMProvider` base class with `generate()` method

#### 7. TUI Dashboard
**Purpose**: Real-time monitoring and observability (optional)

**Features**:
- Live display of goals, tasks, and agents
- Color-coded state indicators
- Configurable refresh rate
- Headless mode for production

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
    requires_depend │          │         │ agent_failed
                    │          │ completed│
                    ▼          ▼         ▼
              ┌──────────┐ ┌─────────┐ ┌───────┐
              │ AWAITING │ │ SUCCESS │ │ ERROR │ (Terminal states)
              └────┬─────┘ └─────────┘ └───┬───┘
                   │                        │
                   │ dependency_resolved    │ retry_approved
                   ▼                        ▼
              ┌──────────┐            ┌──────────┐
              │  RUNNING │            │ PENDING  │
              └──────────┘            └──────────┘
```

### State Definitions

| State | Description | Transitions |
|-------|-------------|-------------|
| **PENDING** | Task created, waiting for capable agent | → RUNNING (agent claims), → BLOCKED (dependency) |
| **RUNNING** | Agent actively executing task | → AWAITING (needs dependency), → SUCCESS, → ERROR |
| **AWAITING** | Blocked on dependency task | → RUNNING (dependency resolved) |
| **SUCCESS** | Task completed successfully | Terminal |
| **ERROR** | Task failed permanently | → PENDING (retry), Terminal |
| **BLOCKED** | Dependencies not met | → PENDING (dependencies ready) |

### Event Types

All state transitions are recorded as JSONL events:

```jsonl
{"type":"goal_submitted","goal_id":"g1","description":"Build REST API","sequence":1}
{"type":"goal_decomposed","goal_id":"g1","payload":{"task_ids":["t1","t2","t3"],"reasoning":"..."},"sequence":2}
{"type":"task_created","task_id":"t1","goal":"Implement auth","dependencies":[],"sequence":3}
{"type":"task_assigned","task_id":"t1","agent_id":"a1","sequence":4}
{"type":"task_progress","task_id":"t1","agent_id":"a1","progress":0.3,"message":"Generated schema","sequence":5}
{"type":"dependency_requested","task_id":"t2","dependency_task_id":"t1","sequence":6}
{"type":"task_completed","task_id":"t1","agent_id":"a1","result":{"artifacts":["auth.py"]},"sequence":7}
{"type":"dependency_resolved","task_id":"t2","dependency_task_id":"t1","result":{...},"sequence":8}
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

#### 1. `submit_goal`
**Purpose**: Submit a high-level goal for autonomous decomposition

**Parameters**:
```json
{
  "goal_id": "unique-goal-identifier",
  "description": "Build a REST API for user management",
  "context": {
    "language": "Python",
    "framework": "FastAPI"
  },
  "constraints": {
    "max_agents": 5,
    "deadline": "2025-11-20"
  }
}
```

**Returns**: Goal confirmation with decomposition status

#### 2. `register_agent`
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

#### 3. `claim_task`
**Purpose**: Agent requests work matching capabilities (pull model)

**Parameters**:
```json
{
  "agent_id": "agent-123",
  "capabilities": ["code_generation", "python"]
}
```

**Returns**: Task assignment or null if no matching work

#### 4. `report_progress`
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

#### 5. `request_dependency`
**Purpose**: Request output from dependent task

**Parameters**:
```json
{
  "agent_id": "agent-123",
  "task_id": "prerequisite-task-id"
}
```

**Returns**: Dependency task result or null if not completed

#### 6. `complete_task`
**Purpose**: Mark task as successfully completed

**Parameters**:
```json
{
  "task_id": "task-456",
  "agent_id": "agent-123",
  "result": {
    "artifacts": ["src/auth.py", "tests/test_auth.py"],
    "summary": "Implemented OAuth2 authentication",
    "metrics": {"coverage": 0.95}
  }
}
```

**Returns**: Confirmation

#### 7. `fail_task`
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

**Returns**: Orchestrator decision (retry, reassign, fail)

#### 8. `heartbeat`
**Purpose**: Liveness signal from agent

**Parameters**:
```json
{
  "agent_id": "agent-123",
  "status": "healthy",
  "current_tasks": ["task-456"],
  "load": 0.6
}
```

**Returns**: Acknowledgment

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
  │<───result OR null────────────────│                              │
  │                                  │                              │
  [If null, Agent B transitions               [Agent A completes]
   to AWAITING state and waits]                                    │
  │                                  │<──complete_task─────────────│
  │                                  │                              │
  │<───dependency_resolved event─────│                              │
  │                                  │                              │
  │──claim_task() [resume work]─────>│                              │
```

**Key Property**: Agents never communicate directly. Orchestrator mediates all data flow.

### 5. Goal Submission & Decomposition

```
Client                    Orchestrator                    LLM Provider
  │                            │                                │
  │──submit_goal──────────────>│                                │
  │                            │                                │
  │              [Create goal, start decomposition]             │
  │                            │                                │
  │                            │──decompose(goal)──────────────>│
  │                            │                                │
  │                            │<──task DAG─────────────────────│
  │                            │                                │
  │           [Create tasks from DAG, validate acyclic]         │
  │                            │                                │
  │<───goal_submitted──────────│                                │
  │    (with task_ids)         │                                │
  │                            │                                │
```

**Autonomous Operation**: No human approval required. LLM decomposes and tasks are created immediately.

---

## Fault Tolerance Mechanisms

### 1. Heartbeat Protocol

**Configuration**:
- **Interval**: 30 seconds (configurable via `MAC_SERVER_HEARTBEAT_INTERVAL`)
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
| Logic error | No | Mark as ERROR (terminal) |
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
2. Continue executing non-dependent tasks
3. Mark dependent tasks as BLOCKED
4. Log degraded state for monitoring

---

## Configuration System

### Configuration Sources

**Priority Order** (highest to lowest):
1. Command-line arguments (e.g., `mac-mcp config.yaml`)
2. Environment variables (MAC_* prefix)
3. Configuration file (YAML)
4. Default values

### Configuration Domains

#### LLM Provider Configuration

```yaml
llm:
  provider: "anthropic"  # or "bedrock"
  model: "claude-sonnet-4-5-20250929"
  api_key: "sk-..."  # For Anthropic
  # Or for Bedrock:
  # aws_region: "us-east-1"
  # aws_profile: "default"
  max_tokens: 4096
  temperature: 0.7
```

**Environment Variables**:
```bash
MAC_LLM_PROVIDER=anthropic
MAC_LLM_MODEL=claude-sonnet-4-5-20250929
MAC_LLM_API_KEY=sk-...
```

#### Server Configuration

```yaml
server:
  transport: "stdio"  # MCP transport mode
  event_store_path: "data/events.jsonl"
  max_agents: 100
  heartbeat_interval: 30  # seconds
  heartbeat_timeout: 90   # seconds
```

#### UI Configuration

```yaml
ui:
  mode: "tui"  # or "headless"
  refresh_interval: 1.0  # seconds
  theme: "dark"
  show_events: true
  show_metrics: true
```

#### Logging Configuration

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/mac-mcp.log"
  console: true
```

---

## LLM Provider Architecture

### Provider Abstraction

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate text completion from LLM."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get model identifier."""
        pass
```

### Anthropic Provider

**Features**:
- Direct Anthropic API integration
- Uses `anthropic` Python SDK
- Supports all Claude models

**Configuration**:
```python
llm_config = LLMConfig(
    provider="anthropic",
    model="claude-sonnet-4-5-20250929",
    api_key="sk-..."
)
```

### AWS Bedrock Provider

**Features**:
- AWS Bedrock integration via boto3
- Supports AWS credential chain (keys, profile, IAM role)
- Regional deployment

**Configuration**:
```python
llm_config = LLMConfig(
    provider="bedrock",
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    aws_region="us-east-1",
    aws_profile="default"  # Or use aws_access_key_id/aws_secret_access_key
)
```

**Credential Chain** (in order):
1. Explicit `aws_access_key_id` and `aws_secret_access_key`
2. AWS profile (`aws_profile`)
3. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
4. AWS credentials file (`~/.aws/credentials`)
5. IAM role (for EC2/ECS/Lambda)

---

## TUI Dashboard

### Features

**Real-time Monitoring**:
- Goals: ID, description, state, task count, progress
- Tasks: ID, description, state, assigned agent, progress
- Agents: ID, status, active tasks, success rate, capabilities
- Events: Recent system events (optional)

**Visual Design**:
```
┌────────────────────────────────────────────────────────┐
│ Multi-Agent Coordination Server │ MAC MCP Dashboard │
├────────────────┬───────────────────────────────────────┤
│     Goals      │           Agents                       │
│  ID │ State   │  ID  │ Status │ Tasks │ Success Rate   │
│  g1 │EXECUTING│  a1  │ACTIVE  │   2   │    95%         │
├────────────────┤───────────────────────────────────────┤
│     Tasks      │          Events (Optional)             │
│  ID │ State   │  Recent system events...               │
│  t1 │SUCCESS  │                                        │
│  t2 │RUNNING  │                                        │
└────────────────┴───────────────────────────────────────┘
│ Press Ctrl+C to exit  •  Refresh: 1.0s                 │
└────────────────────────────────────────────────────────┘
```

**Color Coding**:
- Green: SUCCESS, COMPLETED, ACTIVE states
- Yellow: RUNNING, EXECUTING, BUSY states
- Red: ERROR, FAILED, QUARANTINED states
- Cyan: PENDING, SUBMITTED states
- Magenta: AWAITING states

### Modes

**TUI Mode**: Full terminal UI with live updates
```bash
export MAC_UI_MODE=tui
mac-mcp
```

**Headless Mode**: No UI (for production/CI)
```bash
export MAC_UI_MODE=headless
mac-mcp
```

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
- **Mitigation**: Event-based notifications (future enhancement)
  - Agents maintain persistent connection
  - Orchestrator pushes "task_available" events
  - Agents respond with `claim_task` call

**Comparison**:
| Model | Latency | Scalability | Backpressure |
|-------|---------|-------------|--------------|
| Push | Low (~10ms) | Medium | Poor |
| Pull (polling) | High (~1s) | High | Excellent |
| Pull (events) | Low (~50ms) | High | Excellent |

**Recommendation**: Pull with event notifications (future)

### 3. Dependency Graph Traversal

**Algorithm**: Topological sort with Kahn's algorithm (O(V + E))

**Optimization**: Pre-compute "ready tasks" (all dependencies satisfied)
- Maintain priority queue sorted by priority/creation time
- Update on task completion (O(log N) recomputation)

### 4. State Reconstruction

**Event Sourcing Trade-off**:
- **Benefit**: Complete audit trail, time-travel debugging
- **Cost**: State reconstruction requires replay (O(N) events)

**Mitigation**: Snapshot Strategy (future enhancement)
- Periodic snapshots of current state (every 1000 events)
- Reconstruction = Load snapshot + Replay recent events
- **Formula**: `reconstruction_time = snapshot_load + (events_since_snapshot * avg_event_process_time)`

---

## Security Considerations

### 1. Agent Authentication

**Problem**: Prevent agent impersonation (spoofing `agent_id`)

**Solution**: API Key or JWT-based authentication (future enhancement)
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

**Solution**: Message signing with HMAC-SHA256 (future enhancement)
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
  - Directly communicate with other agents

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
    async def append(self, event: Event) -> None
    async def read(self, since: int = 0) -> AsyncIterator[Event]
    async def get_latest_sequence(self) -> int
```

**Implementations**:
- `InMemoryEventStore`: For development/testing
- `JSONLEventStore`: JSONL file (default, implemented)
- `DatabaseEventStore`: PostgreSQL, SQLite (future)
- `StreamEventStore`: Kafka, Kinesis (future)

### 3. Goal Decomposition Strategies

**Interface**:
```python
class GoalDecomposer(Protocol):
    async def decompose(self, goal_id: str, description: str, context: dict, constraints: dict) -> TaskDAG
```

**Implementations**:
- `LLMDecomposer`: Use Claude to generate task breakdown (implemented)
- `TemplateDecomposer`: Pattern-based (e.g., "implement feature X" → standard tasks) (future)
- `HybridDecomposer`: LLM + templates (future)

### 4. LLM Providers

**Interface**:
```python
class LLMProvider(Protocol):
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> str
    def get_model_name(self) -> str
```

**Implementations**:
- `AnthropicProvider`: Anthropic API (implemented)
- `BedrockProvider`: AWS Bedrock (implemented)
- `AzureProvider`: Azure OpenAI (future)
- `LocalProvider`: Ollama, LM Studio (future)

---

## Deployment Modes

### 1. Development Mode (TUI)
```bash
export MAC_LLM_API_KEY=sk-...
export MAC_UI_MODE=tui
mac-mcp
```
- In-memory or file-based storage
- TUI dashboard for monitoring
- Verbose logging
- No authentication

### 2. Production Mode (Headless)
```bash
mac-mcp config.yaml
```

**config.yaml**:
```yaml
llm:
  provider: "bedrock"
  aws_region: "us-east-1"
  aws_profile: "production"
server:
  event_store_path: "/var/lib/mac-mcp/events.jsonl"
ui:
  mode: "headless"
logging:
  level: "WARNING"
  file: "/var/log/mac-mcp/server.log"
```

- File-based event store (JSONL)
- Headless mode (no UI)
- Structured logging (JSON)
- Authentication (future enhancement)

### 3. Distributed Mode (Future Enhancement)
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

```bash
# Via MCP tool
submit_goal(
  goal_id="g1",
  description="Build a REST API for user management with CRUD operations",
  context={
    "language": "Python",
    "framework": "FastAPI",
    "database": "PostgreSQL"
  }
)
```

#### 2. Goal Decomposition (LLM-based, Autonomous)

**Orchestrator calls LLM**:
```python
task_dag = await decomposer.decompose(
    goal_id="g1",
    description="Build a REST API for user management with CRUD operations",
    context={"language": "Python", "framework": "FastAPI", "database": "PostgreSQL"},
    constraints={}
)
```

**LLM Returns**:
```json
{
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
  ],
  "edges": [["t1","t2"], ["t2","t3"], ["t3","t4"], ["t3","t5"]]
}
```

**No approval needed** - tasks created immediately.

#### 3. Agent Registration

```jsonl
{"type":"agent_registered","agent_id":"db_agent","capabilities":["database","postgresql","sql"],"sequence":1}
{"type":"agent_registered","agent_id":"py_agent_1","capabilities":["python","fastapi","sqlalchemy"],"sequence":2}
{"type":"agent_registered","agent_id":"py_agent_2","capabilities":["python","fastapi","pytest"],"sequence":3}
{"type":"agent_registered","agent_id":"doc_agent","capabilities":["documentation","openapi"],"sequence":4}
```

#### 4. Task Execution (Event Stream)

```jsonl
{"type":"goal_submitted","goal_id":"g1","description":"Build REST API...","sequence":5}
{"type":"goal_decomposed","goal_id":"g1","payload":{"task_ids":["t1","t2","t3","t4","t5"],"reasoning":"..."},"sequence":6}
{"type":"task_created","task_id":"t1","description":"Design database schema","state":"PENDING","sequence":7}
{"type":"task_assigned","task_id":"t1","agent_id":"db_agent","sequence":8}
{"type":"task_progress","task_id":"t1","progress":0.5,"message":"Created users table definition","sequence":9}
{"type":"task_completed","task_id":"t1","result":{"artifact":"schema.sql"},"sequence":10}

{"type":"task_created","task_id":"t2","state":"PENDING","sequence":11}
{"type":"task_assigned","task_id":"t2","agent_id":"py_agent_1","sequence":12}
{"type":"dependency_requested","agent_id":"py_agent_1","task_id":"t1","sequence":13}
{"type":"dependency_resolved","task_id":"t2","dependency_task_id":"t1","result":{"artifact":"schema.sql"},"sequence":14}
{"type":"task_progress","task_id":"t2","progress":0.7,"message":"Generated Pydantic models","sequence":15}
{"type":"task_completed","task_id":"t2","result":{"artifacts":["models.py","schemas.py"]},"sequence":16}

{"type":"task_created","task_id":"t3","state":"PENDING","sequence":17}
{"type":"task_assigned","task_id":"t3","agent_id":"py_agent_1","sequence":18}
{"type":"task_progress","task_id":"t3","progress":1.0,"message":"Implemented all CRUD endpoints","sequence":19}
{"type":"task_completed","task_id":"t3","result":{"artifacts":["routes.py"]},"sequence":20}

{"type":"task_created","task_id":"t4","state":"PENDING","sequence":21}
{"type":"task_created","task_id":"t5","state":"PENDING","sequence":22}
{"type":"task_assigned","task_id":"t4","agent_id":"py_agent_2","sequence":23}
{"type":"task_assigned","task_id":"t5","agent_id":"doc_agent","sequence":24}

[Both t4 and t5 execute in parallel]

{"type":"task_completed","task_id":"t4","result":{"artifacts":["test_routes.py"],"test_coverage":0.95},"sequence":25}
{"type":"task_completed","task_id":"t5","result":{"artifacts":["README.md","openapi.yaml"]},"sequence":26}

{"type":"goal_completed","goal_id":"g1","success":true,"total_time":"2.5h","sequence":27}
```

#### 5. Final Result

```json
{
  "goal_id": "g1",
  "status": "SUCCESS",
  "artifacts": [
    "schema.sql",
    "models.py",
    "schemas.py",
    "routes.py",
    "test_routes.py",
    "README.md",
    "openapi.yaml"
  ],
  "metrics": {
    "total_time": "2.5 hours",
    "tasks_completed": 5,
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
| **Dependency Management** | Single point | Multiple points |
| **Debugging** | Complete audit trail | Partial logs |
| **Fault Tolerance** | Supervisor handles | Peer recovery |
| **Complexity** | O(N) connections | O(N²) connections |

**Verdict**: Orchestration is superior for dependency management and debuggability.

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
| **LLM Integration** | Built-in | Plugin required |
| **Autonomous Operation** | Native | Not designed for |

**Verdict**: MAC is purpose-built for autonomous LLM agents; workflow engines are general-purpose.

---

## Future Enhancements

### 1. Web-based Dashboard
**Description**: Browser-based monitoring UI

**Features**:
- Real-time WebSocket updates
- Interactive goal/task visualization
- Agent health dashboards
- Historical metrics and analytics

**Status**: Documented for future implementation

### 2. Multi-Tenancy
**Description**: Isolate goals from different users

**Proposal**: Namespace isolation
- Goal IDs prefixed with tenant: `{tenant_id}:{goal_id}`
- Agents register per-tenant
- Event streams partitioned by tenant

### 3. Agent Pricing & Cost Optimization
**Description**: Allocate expensive LLM calls efficiently

**Proposal**: Cost-aware scheduling
- Agents declare cost per task (e.g., API credits)
- Orchestrator optimizes for cost + time trade-off
- Cheaper agents preferred for low-priority tasks

### 4. Cross-Goal Learning
**Description**: Learn from past goal executions

**Proposal**: Decomposition templates
- Successful DAGs stored as templates
- Similar goals reuse templates (faster decomposition)
- Embedding-based similarity search

### 5. Performance Metrics in TUI
**Description**: Display system performance metrics

**Features**:
- Task throughput (tasks/hour)
- Agent utilization (% busy)
- Goal completion time (avg, p50, p99)
- Error rates and retry counts

---

## Implementation Status

### Completed Features
- ✅ Event store (JSONL file backend)
- ✅ Task state machine
- ✅ Agent registration and heartbeat
- ✅ Task assignment (pull model)
- ✅ MCP server implementation
- ✅ Goal domain model
- ✅ Autonomous goal decomposition (LLM-based)
- ✅ Dependency resolution
- ✅ Configuration system (YAML + env vars)
- ✅ LLM provider abstraction
- ✅ Anthropic provider
- ✅ AWS Bedrock provider
- ✅ TUI dashboard (Rich-based)

### Future Enhancements
- ⏳ Web-based dashboard
- ⏳ Agent authentication (JWT)
- ⏳ Message signing (HMAC)
- ⏳ Rate limiting and quotas
- ⏳ Monitoring and metrics
- ⏳ Distributed orchestrator (Redis coordination)
- ⏳ Pluggable storage backends (PostgreSQL, Kafka)
- ⏳ Multi-tenancy support
- ⏳ Performance metrics in TUI

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
3. **Autonomous operation** through LLM-powered decomposition
4. **Operational transparency** via JSONL event streams
5. **Flexibility** through configuration and provider abstraction

This architecture provides a **robust, scalable, and debuggable** foundation for building multi-agent AI systems that are autonomous, efficient, and maintainable.
