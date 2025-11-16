# Development Workflow

## Commit Messages

**Format**: `<type>(<scope>): <subject>`

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**Example**: `feat(orchestrator): add goal decomposition with Claude Sonnet`

**Body**: Reference issues/PRs: `Refs: #1`

**Commit Scope Guidelines**:
- **Single Responsibility**: Each commit should address ONE logical change
- **Accurate Scope**: Commit message must accurately reflect ALL changes
- **Avoid Mixed Concerns**: Don't combine feature additions with refactoring
- **Split Large Changes**: If commit touches >10 files or >500 lines, consider splitting

## Pre-Commit Hook Mandate

**NEVER use `--no-verify` or `--no-hooks` flags to bypass pre-commit hooks**

Pre-commit hooks enforce quality gates (formatting, linting, type checking). Bypassing them:
- Introduces technical debt
- Defeats the only quality gate (no CI/CD to catch issues)
- Violates code quality standards

### Proper Workflow When Hooks Auto-Fix Files

```bash
# 1. Attempt commit
git commit -m "feat(module): add feature"

# 2. Pre-commit hooks run and auto-fix files
# Output: "Files were modified by this hook"
# Commit FAILS (expected behavior)

# 3. Stage the auto-fixed files
git add -u  # Stage all modified tracked files

# 4. Retry the commit with same message
git commit -m "feat(module): add feature"

# 5. Hooks run again, pass (no changes needed)
# Commit SUCCEEDS
```

### Proper Workflow When Hooks Report Errors

```bash
# 1. Attempt commit
git commit -m "feat(module): add feature"

# 2. Pre-commit hooks report errors
# Example: "mypy: error: Incompatible types in assignment"
# Commit FAILS (expected behavior)

# 3. Fix the code manually
# Address the reported errors in your code

# 4. Stage the fixes
git add <fixed-files>

# 5. Retry the commit
git commit -m "feat(module): add feature"

# 6. Hooks pass
# Commit SUCCEEDS
```

## Branch Naming

- Feature: `feature/<id>-description`
- Bugfix: `fix/<id>-description`
- Docs: `docs/<topic>`
- Refactor: `refactor/<component>`

## CHANGELOG Updates

**ALWAYS update CHANGELOG.md under `[Unreleased]` for user-facing changes**

**Categories**: Added, Changed, Deprecated, Removed, Fixed, Security

**Style**: Use present tense ("Add feature" not "Added feature")

**Example**:
```markdown
## [Unreleased]

### Added
- Add goal decomposition with Claude Sonnet 4.5
- Add heartbeat monitoring with 90s timeout

### Changed
- Migrate storage from in-memory to JSONL for persistence

### Fixed
- Fix race condition in concurrent task claiming
```

**On Release**:
1. Update version in `pyproject.toml`: `version = "X.Y.Z"`
2. Move `[Unreleased]` content to new version section: `## [X.Y.Z] - YYYY-MM-DD`
3. Clear `[Unreleased]` section
4. Update comparison links at bottom

**Version Numbering (Semantic Versioning)**:
- **MAJOR (X.0.0)**: Breaking changes, incompatible API changes
- **MINOR (0.X.0)**: New features, backward compatible
- **PATCH (0.0.X)**: Bug fixes, backward compatible

## Pre-Commit Requirements

**ALWAYS run pre-commit hooks before committing**

**Required checks**: ruff (format + lint), mypy (strict), pytest

**Install**: `pre-commit install`

**Run manually**: `pre-commit run --all-files`

## Testing Standards

**Test organization**: Mirror source structure
```text
src/mac_mcp/domain/events.py → tests/unit/domain/test_events.py
src/mac_mcp/core/orchestrator.py → tests/integration/test_orchestrator.py
```

**Test markers**:
```python
@pytest.mark.unit
def test_task_state_transition():
    """Test task state machine."""

@pytest.mark.integration
async def test_full_task_lifecycle():
    """Test complete task workflow."""

@pytest.mark.property
def test_event_sequence_preservation():
    """Property test for event ordering."""

@pytest.mark.slow
def test_stress_test():
    """Stress test with 1000 tasks."""
```

**Markers defined in pyproject.toml**:
- `unit`: Fast, isolated, no external dependencies
- `integration`: Slower, tests component interactions
- `property`: Hypothesis property-based tests
- `slow`: Excluded from pre-commit

**Coverage target**: Minimum 90% coverage for new code

**Run tests**:
```bash
pytest                    # All tests with coverage
pytest tests/unit/        # Unit tests only
pytest tests/integration/ # Integration tests only
pytest --no-cov           # Without coverage
pytest -m "not slow"      # Exclude slow tests
```

## PR Checklist

Before marking PR ready for review:

- [ ] Pre-commit hooks pass
- [ ] Tests added (unit + integration + property where applicable)
- [ ] Documentation updated (docstrings, README if needed)
- [ ] No secrets or credentials in code
- [ ] CHANGELOG.md updated with user-facing changes
- [ ] Coverage ≥90% for new code
- [ ] Git status clean (no unstaged deletions, no prohibited files)

## Code Quality Gates

**All commits must pass**:
- ruff format (formatting, line-length=100)
- ruff check (linting, comprehensive rule set)
- mypy (type checking, strict=true)
- pytest (tests pass)

**Run quality checks**:
```bash
ruff format .
ruff check .
mypy src/
pytest
```

## Prohibited Files

**NEVER create these files in the repository**:
- `*SUMMARY*.md` (e.g., SESSION_SUMMARY.md, PROJECT_SUMMARY.md)
- `*HANDOFF*.md` (e.g., HANDOFF.md, SESSION_HANDOFF.md)
- `*TODO*.md` (e.g., TODO.md, NEXT_STEPS.md)

**Rationale**: Clutter repository, become stale immediately. Use CHANGELOG.md or issue tracker instead.

## Git Operations

**File moves**: ALWAYS use `git mv`, NEVER filesystem `mv`
```bash
# GOOD
git mv old/path/file.py new/path/file.py

# BAD (leaves unstaged deletion)
mv old/path/file.py new/path/file.py
```

**After file operations**: Check git status
```bash
git status  # Verify no unstaged deletions or untracked files
```

## Session Completion Protocol

When completing a work session:

1. **Update Core Documentation**:
   - README.md: Update project status, version, next steps
   - CHANGELOG.md: Document all user-facing changes
   - ROADMAP.md: Mark completed milestones

2. **Commit and Document**:
   - Commit all changes with proper references
   - Verify git status shows no prohibited files

3. **Verify Quality**:
   - All tests pass
   - Code quality checks pass (mypy, ruff)
   - NO prohibited files exist

4. **Provide Session-End Suggestions (MANDATORY)**:
   - **MUST provide unless user explicitly requests no suggestions**
   - Suggest next work based on: incomplete features, technical debt, dependencies

   **Template**:
   ```
   Based on this session's work, I suggest continuing with:

   1. **[Feature/Task Name]** (Priority: High/Medium/Low)
      - Rationale: [Why this is next logical step]
      - Dependencies: [What's blocking or unblocking this]
      - Estimated effort: [Time estimate]

   2. **[Alternative Option]**
      - Rationale: [Why this could be valuable]
      - Trade-offs: [Pros/cons vs option 1]
   ```

5. **Provide Handoff in Conversation**:
   - Print completion summary directly in conversation
   - Provide optimized prompt for next agent in conversation
   - NEVER create summary or handoff files

## Related Documentation

- Code patterns: `.clinerules/rules/reference/code-patterns.md`
- Event sourcing patterns: `.clinerules/rules/reference/event-sourcing-patterns.md`
- MCP protocol: `.clinerules/rules/reference/mcp-protocol-patterns.md`
- Project context: `.clinerules/rules/core/project-context.md`
