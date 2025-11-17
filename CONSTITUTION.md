# MAC MCP Constitution

## Core Principles

### 1. Event Sourcing is Sacred
- **All state changes are events** - No direct state mutation
- **Events are immutable** - Use `frozen=True` in Pydantic models
- **Append-only log** - Never modify or delete events
- **State reconstruction** - Current state derived from event replay

### 2. Actor Model Isolation
- **Agents are isolated actors** - No shared state between agents
- **Communication via orchestrator** - All agent interactions through MCP tools
- **Supervisor pattern** - Orchestrator manages agent lifecycle and failures
- **No side channels** - Agents cannot communicate directly

### 3. Async First
- **All I/O is async** - Use `async`/`await` for all I/O operations
- **No blocking calls** - Use `aiofiles`, `asyncio.sleep`, etc.
- **Concurrency control** - Use semaphores for rate limiting
- **Graceful timeouts** - All operations have timeout bounds

### 4. Type Safety
- **Strict mypy** - All code passes mypy strict mode
- **Modern syntax** - Use `str | None` not `Optional[str]`
- **Pydantic validation** - Use Pydantic for all domain models
- **No `Any` escape hatches** - Explicit types everywhere

### 5. MCP Protocol Compliance
- **Follow MCP June 2025 spec** - Implement all required features
- **Tool discoverability** - All tools have complete schemas
- **Error handling** - Return error messages, don't raise exceptions
- **Stdio transport** - Use stdio for communication

### 6. Testing Rigor
- **≥90% coverage** - All new code must meet coverage target
- **Property tests** - Use Hypothesis for invariant testing
- **Integration tests** - Test full workflows end-to-end
- **Fast unit tests** - Unit tests run in <1s

### 7. Quality Gates
- **Pre-commit hooks** - Never bypass with `--no-verify`
- **Ruff formatting** - Consistent code style (100 char lines)
- **Mypy strict** - No type errors allowed
- **All tests pass** - No broken tests in commits

### 8. Documentation
- **Google-style docstrings** - All public APIs documented
- **Architecture docs** - Keep ARCHITECTURE.md current
- **CHANGELOG updates** - Document all user-facing changes
- **Code comments** - Explain "why" not "what"

## Anti-Patterns (Never Do This)

### ❌ Mutable Events
```python
class TaskEvent(BaseModel):
    # Missing frozen=True - FORBIDDEN
    task_id: UUID
```

### ❌ Blocking I/O in Async
```python
async def load_data():
    with open("file.txt") as f:  # FORBIDDEN - use aiofiles
        return f.read()
```

### ❌ Direct Agent Communication
```python
# FORBIDDEN - agents must go through orchestrator
agent1.send_message(agent2, "hello")
```

### ❌ Bypassing Pre-commit
```bash
# FORBIDDEN - defeats quality gates
git commit --no-verify -m "quick fix"
```

### ❌ Modifying Past Events
```python
# FORBIDDEN - breaks event sourcing
await store.update_event(event_id, new_data)
```

### ❌ Side Effects in Event Application
```python
def apply_event(self, event):
    # FORBIDDEN - no I/O in apply_event
    await notify_user(event.result)
```

## Enforcement

These principles are enforced by:
- **Pre-commit hooks** - Automated checks before commit
- **Validation scripts** - `check_async_patterns.py`, `check_event_immutability.py`
- **CI/CD pipeline** - GitHub Actions runs all checks
- **Code review** - Human review for architectural compliance
- **Expert panels** - Multi-agent review for complex changes

## Exceptions

Exceptions to these principles require:
1. **Explicit justification** in commit message
2. **Follow-up issue** to fix properly
3. **Documentation** of why exception was necessary
4. **Time-bound** - Must be fixed within 1 week

Exceptions should be <1% of all commits. If higher, the principle needs revision.

## Evolution

This constitution evolves with the project:
- **Propose changes** via PR with rationale
- **Discuss in issues** before major changes
- **Document decisions** in ADRs (if we add them)
- **Update patterns** in `.amazonq/rules/reference/`

## Related Documentation

- Project Context: `.amazonq/rules/core/project-context.md`
- Development Workflow: `.amazonq/rules/core/development-workflow.md`
- Quality Procedures: `.amazonq/rules/core/quality-procedures.md`
- Event Sourcing Patterns: `.amazonq/rules/reference/event-sourcing-patterns.md`
- MCP Protocol Patterns: `.amazonq/rules/reference/mcp-protocol-patterns.md`
