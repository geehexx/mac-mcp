# Project Context

## Product
**MAC MCP**: Multi-Agent Coordination MCP Server. Event-sourced orchestrator for autonomous LLM agent teams. Value: Protocol-sound coordination, complete audit trail, fault tolerance, capability-based routing. Scope: Single orchestrator, multiple agents, MCP protocol compliance.

## Architecture
**Storage**: JSONL event store (append-only) | In-memory (dev/test) | Snapshots for optimization
**Coordination**: Goal decomposer (LLM-powered) | Task DAG (dependency management) | Agent supervisor (heartbeat monitoring) | Pull-based assignment (backpressure)
**Protocol**: MCP June 2025 (stdio transport) | 8 tools (submit_goal, register_agent, claim_task, report_progress, complete_task, fail_task, request_dependency, heartbeat) | 3 resources (tasks, agents, events)
**LLM**: Anthropic Claude Sonnet 4.5 | AWS Bedrock | Factory pattern for providers

## Structure
```
src/mac_mcp/: domain/ core/ storage/ mcp/ cli.py
  domain/: events.py tasks.py agents.py goals.py
  core/: orchestrator.py supervisor.py decomposer.py
  storage/: base.py memory.py jsonl.py
  mcp/: server.py
tests/: unit/ integration/ property/
docs/: reference/ examples/ guides/ getting-started/
```

## Tech Stack
**Core**: Python 3.12+, MCP SDK 1.2+, Pydantic 2.9+, aiofiles, uvloop (non-Windows)
**LLM**: anthropic 0.39+, boto3 1.35+
**UI**: rich 13.9+ (TUI dashboard)
**Dev**: pytest 8.3+, pytest-asyncio 0.24+, pytest-cov 6.0+, hypothesis 6.115+ (property tests), ruff 0.7+, mypy 1.13+ (strict)

## Config
**config.yaml**: LLM provider (anthropic/bedrock) | Model IDs | Storage backend (memory/jsonl) | Paths | Heartbeat timeout (90s) | Snapshot interval (use config.example.yaml as template)
**.env**: ANTHROPIC_API_KEY | AWS credentials (for Bedrock)
**pyproject.toml**: ruff (100 chars), mypy (strict), pytest (≥90%, markers: unit/integration/property/slow)

## Critical Rules
- NEVER: *SUMMARY*.md, *HANDOFF*.md, *TODO*.md
- ALWAYS: Event immutability (frozen Pydantic models), async I/O (no blocking), state machine validation, MCP protocol compliance
- Type safety: str | None not Optional[str], dict[str, Any] not Dict
- Testing: ≥90% coverage, property tests for invariants
- Logging: Structured logging with context
- Error handling: Graceful degradation, retry with backoff

## Key Decisions
**Event sourcing**: Complete audit trail, time-travel debugging, state reconstruction vs storage overhead
**Actor model**: Agent isolation, supervisor pattern, no shared state vs coordination complexity
**Pull-based**: Backpressure handling, agent autonomy vs potential idle time
**MCP protocol**: Standardized interface, tool discoverability vs protocol constraints
**LLM decomposition**: Autonomous goal breakdown vs LLM cost/latency
**JSONL storage**: Simple, append-only, human-readable vs no transactions

## Domain Models
**Goal**: SUBMITTED → DECOMPOSING → READY → EXECUTING → COMPLETED/FAILED
**Task**: PENDING → RUNNING → AWAITING → SUCCESS/ERROR/BLOCKED
**Agent**: ACTIVE/INACTIVE/FAILED/QUARANTINED
**Event**: 18 types (GoalSubmitted, TaskCreated, TaskClaimed, TaskCompleted, etc.)
