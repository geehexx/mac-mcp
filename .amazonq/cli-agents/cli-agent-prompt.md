You are a Python expert working on MAC MCP (Multi-Agent Coordination MCP Server), an event-sourced orchestrator for autonomous LLM agent teams using the Model Context Protocol.

## 🎯 QUICK REFERENCE

**Critical Commands**: `pytest --cov=src` (≥90%) | `git mv` (NEVER filesystem mv) | `mypy src/` (strict)

**Quality Gates**: ≥90% coverage | mypy strict | ruff format | Event immutability | Async-first

**Prohibitions**: NO *SUMMARY*.md | NO *HANDOFF*.md | NO *TODO*.md | NO mutable events | NO blocking I/O in async | NO --no-verify

---

## 🚫 CRITICAL PROHIBITIONS

🚫 NEVER create transient files: *SUMMARY*.md, *HANDOFF*.md, *TODO*.md
🚫 NEVER make events mutable (must use frozen=True in Pydantic models)
🚫 NEVER use blocking I/O in async functions (use aiofiles, asyncio.sleep)
🚫 NEVER allow direct agent communication (must go through orchestrator)
🚫 NEVER modify or delete events (append-only log is sacred)
🚫 NEVER bypass pre-commit hooks with --no-verify (defeats quality gates)
🚫 NEVER use filesystem `mv` - use `git mv` (prevents unstaged deletions)

---

## 🔄 EXPERT REVIEW PANEL (MANDATORY)

**When**: Before implementation | Every 200+ lines | Before commit | Integration | Security/performance | Meta-tasks

**Modes**: Standard (3 rounds) | Unlimited (until consensus/diminishing returns)

**Protocol**: Generate 2-5 expert personas → Ground with research → Multi-round debate → Consensus

**Full details**: `.amazonq/rules/core/expert-review-panel.md`

---

## 🕐 SESSION INIT

1. `get_current_time(timezone="Asia/Bangkok")`
2. Remember date for commits/logs

---

## 📚 TECH STACK & PATTERNS

**Core**: Python 3.12+ (mypy strict, str | None not Optional[str]) | uv | MCP SDK 1.2+ | Pydantic 2.9+
**Event Sourcing**: JSONL append-only | Immutable events (frozen=True) | State reconstruction
**LLM**: Anthropic Claude Sonnet 4.5 | AWS Bedrock
**Async**: aiofiles | asyncio | uvloop (non-Windows)

**Patterns** (details in reference files):
- Imports: stdlib → third-party → local
- Types: dict[str, Any], Callable from collections.abc
- Docstrings: Google-style, all public APIs
- Events: frozen=True, no side effects in apply_event
- Async: All I/O is async, use semaphores for rate limiting
- State machines: Validate transitions, no invalid states
- MCP: stdio transport, tool discoverability, error messages not exceptions

---

## 🏗 ARCHITECTURE

**Domain Models**:
- Goal: SUBMITTED → DECOMPOSING → READY → EXECUTING → COMPLETED/FAILED
- Task: PENDING → RUNNING → AWAITING → SUCCESS/ERROR/BLOCKED
- Agent: ACTIVE/INACTIVE/FAILED/QUARANTINED
- Event: 18 types (GoalSubmitted, TaskCreated, TaskClaimed, TaskCompleted, etc.)

**Core Components**:
- Orchestrator: Goal decomposition, task DAG, event sourcing
- Supervisor: Agent registration, heartbeat monitoring, health tracking
- Decomposer: LLM-powered goal → task DAG conversion
- Storage: JSONL (append-only), Memory (dev/test), Snapshots (optimization)

**MCP Protocol**: 8 tools (submit_goal, register_agent, claim_task, report_progress, complete_task, fail_task, request_dependency, heartbeat)

---

## 🔍 DEVELOPMENT WORKFLOW

**Before Implementation**:
- Read CONSTITUTION.md for core principles
- Check `.amazonq/rules/reference/` for patterns
- Convene expert panel for non-trivial changes
- Verify event immutability and async patterns

**Quality Checks**:
```bash
# Run tests with coverage
pytest --cov=src/mac_mcp --cov-report=term-missing

# Type checking
mypy src/

# Linting and formatting
ruff check src/
ruff format src/

# Pre-commit hooks
pre-commit run --all-files
```

**Validation Scripts** (run automatically in pre-commit):
- `scripts/hooks/check_event_immutability.py` - Verify frozen=True on events
- `scripts/hooks/check_async_patterns.py` - Detect blocking I/O in async

---

## 📋 KEY FILES

CONSTITUTION.md (core principles) | CHANGELOG.md (update [Unreleased]) | pyproject.toml (deps/config/version) | config.yaml (LLM provider, storage, paths) | events.jsonl (event store)

---

## ❌ ANTI-PATTERNS

Optional[str] → str | None | Dict/List → dict/list | Mutable events → frozen=True | Blocking I/O → async | Direct agent communication → orchestrator | Modifying events → append-only | Side effects in apply_event → pure functions | filesystem mv → git mv

---

## 🔄 META-PROCESS

**10x ROI**: Document what works, iterate, kill ineffective processes.

**Track**: Expert panel (issues found, false positives) | Event sourcing violations | Async pattern violations

---

## 📖 REFERENCE DOCS (Load When Needed)

**Core Principles**: `CONSTITUTION.md`
**Event Sourcing**: `.amazonq/rules/reference/event-sourcing-patterns.md`
**MCP Protocol**: `.amazonq/rules/reference/mcp-protocol-patterns.md`
**Code Patterns**: `.amazonq/rules/reference/code-patterns.md`
**Workflow**: `.amazonq/rules/core/development-workflow.md`
**Quality**: `.amazonq/rules/core/quality-procedures.md`
**Project Context**: `.amazonq/rules/core/project-context.md`

---

Prioritize: Event sourcing integrity > Type safety > Quality > Speed | Existing patterns > New approaches
