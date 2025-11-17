# Architecture

System design and implementation patterns for the MAC MCP Server.

## System Overview

The MAC MCP Server coordinates autonomous LLM agent teams using the Model Context Protocol. It provides goal decomposition, task orchestration, state management, and fault tolerance.

## Core Patterns

1. **Actor Model**: Agents communicate only through orchestrator, never directly
2. **Event Sourcing**: Append-only JSONL event log as source of truth
3. **Supervisor/Worker**: Orchestrator supervises agent health and handles failures
4. **Pull-based Dispatch**: Agents request work rather than receiving pushed assignments
5. **State Machine**: Deterministic task state transitions with event-driven updates

## Architecture Decision Records

### ADR-001: Event Sourcing for State Management

**Decision**: Use append-only JSONL event log as authoritative state store

**Rationale**:
- Complete audit trail of all operations
- State reconstruction after crashes
- Time-travel debugging
- Distributed deployment support

**Implementation**: `EventStore` writes events before state mutations

### ADR-002: Pull-based Task Assignment

**Decision**: Agents claim tasks via `claim_task` rather than receiving pushed assignments

**Rationale**:
- Backpressure control (agents request work when ready)
- No orchestrator queuing complexity
- Agent autonomy in workload management
- Natural load balancing

**Implementation**: Orchestrator maintains available task queue, agents poll

### ADR-003: Actor Model for Agent Isolation

**Decision**: Agents communicate only through orchestrator, never peer-to-peer

**Rationale**:
- Simplified coordination (no consensus protocols)
- Centralized observability
- Easier fault isolation
- Supervisor pattern enforcement

**Implementation**: Dependency results mediated via `request_dependency` tool

### ADR-004: LLM-based Goal Decomposition

**Decision**: Use Claude to decompose goals into task DAGs autonomously

**Rationale**:
- Handles complex, unstructured goals
- Adapts to context and constraints
- No manual workflow definition
- Leverages LLM reasoning capabilities

**Implementation**: `GoalDecomposer` sends structured prompt to Claude API/Bedrock

## Component Overview

```
┌─────────────────────────────────────────────┐
│           MAC MCP Server                    │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │        Orchestrator                  │   │
│  │  - Goal management                   │   │
│  │  - Task state machine                │   │
│  │  - Dependency resolution             │   │
│  └─────────────────────────────────────┘   │
│                   │                         │
│       ┌───────────┼───────────┐             │
│       ▼           ▼           ▼             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │  Goal   │ │  Agent  │ │  Event  │       │
│  │Decomp.  │ │ Super.  │ │  Store  │       │
│  └─────────┘ └─────────┘ └─────────┘       │
│                                             │
└─────────────────────────────────────────────┘
                   │
           ┌───────┼───────┐
           ▼       ▼       ▼
      ┌────────┐ ┌────────┐ ┌────────┐
      │Agent A │ │Agent B │ │Agent C │
      └────────┘ └────────┘ └────────┘
```

## Data Flow

### Goal Submission

```
Agent → submit_goal → Orchestrator → GoalDecomposer → Claude
                                           │
                    ┌──────────────────────┘
                    ▼
              Task DAG Created
                    │
                    ▼
            Tasks → PENDING State
```

### Task Execution

```
Agent → claim_task → Orchestrator
           │              │
           │     Finds matching task
           │              │
           ▼              ▼
     Task assigned → RUNNING
           │
           ├─→ report_progress
           │
           ├─→ request_dependency (if needed)
           │
           └─→ complete_task → SUCCESS
                 OR
               fail_task → ERROR/PENDING
```

## Task State Machine

```
PENDING ──────────────┐
   │                  │
   │ claim_task      │ assign_task
   ▼                  │
RUNNING ──────────────┘
   │
   ├─→ complete_task ──→ SUCCESS
   │
   ├─→ fail_task ──────→ ERROR (retryable=false)
   │
   └─→ fail_task ──────→ PENDING (retryable=true, retry_count++)
```

## Event Types

- `goal_submitted`: New goal created
- `goal_decomposed`: Tasks generated from goal
- `agent_registered`: Agent joined system
- `task_created`: Task added to system
- `task_assigned`: Task assigned to agent
- `task_progress`: Progress update
- `task_completed`: Task finished successfully
- `task_failed`: Task encountered error
- `heartbeat_received`: Agent liveness signal
- `heartbeat_timeout`: Agent unresponsive

## Fault Tolerance

### Heartbeat Monitoring

- Agents send heartbeat every 30 seconds
- Timeout after 90 seconds without heartbeat
- Automatic task reassignment on timeout

### Retry Logic

- Tasks marked `retryable: true` reset to PENDING
- Max 3 retry attempts
- Exponential backoff for transient failures

### Circuit Breaker

- Agent disabled after 3 consecutive failures
- Prevents cascading failures
- Manual re-enable or auto-recovery after timeout

## Technology Stack

- **Language**: Python 3.12+
- **Protocol**: Model Context Protocol (MCP)
- **LLM**: Anthropic API or AWS Bedrock
- **Storage**: JSONL event log
- **Validation**: Pydantic v2
- **UI**: Rich TUI library
- **Config**: YAML + environment variables

## Security

- **Authentication**: JWT tokens (future)
- **Event Integrity**: HMAC-SHA256 signatures (future)
- **Rate Limiting**: Per-agent quotas (future)
- **Input Validation**: Pydantic models prevent injection

## Performance

- **Event Append**: O(1) write to JSONL
- **State Rebuild**: O(N) event replay (snapshot optimization planned)
- **Task Claim**: O(M) scan of available tasks (M = pending tasks)
- **Heartbeat**: O(K) check of K registered agents

## Monitoring

- **Event Log**: Complete audit trail in JSONL
- **TUI Dashboard**: Real-time goal/task/agent status
- **Metrics**: Task throughput, agent utilization, success rates
- **Tracing**: Future OpenTelemetry integration
