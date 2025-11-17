# Quality Procedures

## Core Principle

**Understand deeply, implement correctly, review thoroughly. Catch issues internally rather than requiring user feedback cycles.**

## Deep Understanding Phase

**Before writing any code:**

- [ ] Requirement crystal clear (**use HITL immediately if not**)
- [ ] Study 2-3 similar implementations for patterns
- [ ] Check for existing solutions (patterns, libraries)
- [ ] **Use thinking to structure reasoning** (use `thinking` tool if ≥3 approaches or complex trade-offs)
- [ ] Validate approach aligns with architecture (**use HITL to confirm if uncertain**)
- [ ] **Create todo list for multi-step tasks** (MANDATORY if >2 tool calls OR >1 file OR requires planning)

**Time investment**: 20-30% of total time. Deep understanding prevents rework.

## Batch Questions (MANDATORY)

**Before implementation or commit, batch 3-10 questions**:

- Ask once, not incrementally
- Include context for each question
- Wait for responses before proceeding
- Format:
  ```
  ## Batched Questions

  1. **[Architecture]**: Question with context
  2. **[Security]**: Question with context
  3. **[Performance]**: Question with context

  Waiting for responses before proceeding.
  ```

**NEVER make breaking changes without explicit user authorization**:
- Breaking changes: API changes, config format changes, data migration required, backward incompatibility

## Todo List Requirements

**MANDATORY for ALL multi-step tasks**:
- Task requires >2 tool calls, OR
- Task modifies >1 file, OR
- Task requires planning/thinking about approach

**Multi-step examples**:
- ✓ "Add goal decomposition" - requires planning (LLM integration, state machine, tests)
- ✓ "Implement MCP server" - multiple files (server, tools, resources)
- ✗ "Fix typo in README" - single file, no planning
- ✗ "Update dependency version" - single file, straightforward

**When to create**: At task start, when multi-step detected. Output: "This appears to be a multi-step task. Creating todo list..."

**Progress updates**: After completing 200+ lines OR mid-implementation checkpoint, MUST mark todo items complete. Output: "✓ Completed: [task description]"

**Scope creep prevention**: If todo list grows >50% beyond original, STOP and use `request_confirmation` for scope change approval.

## Implementation Review Checkpoints

**Trigger review after:**
- Completing function/method (>20 lines)
- Completing class
- Accumulating 200+ lines of changes
- Before using fsWrite or fsReplace

**Comprehensive checklist:**

### A. Plan Alignment
- [ ] Solves stated problem completely
- [ ] Matches implementation plan
- [ ] All requirements addressed
- [ ] Scope appropriate (not over/under-engineered)
- [ ] Handles all edge cases

### B. Contextual Integrity
- [ ] Imports organized (stdlib → third-party → local)
- [ ] Type hints use modern syntax (str | None, not Optional[str])
- [ ] Naming follows conventions (snake_case, PascalCase, UPPER_SNAKE_CASE)
- [ ] File location appropriate (domain/, core/, storage/, mcp/)
- [ ] Follows established patterns (event sourcing, actor model, async/await)

### C. Quality
- [ ] No obvious bugs
- [ ] Edge cases handled
- [ ] Error handling appropriate
- [ ] No code duplication
- [ ] Performance acceptable
- [ ] Resource cleanup

### D. Style
- [ ] Line length ≤100 characters
- [ ] Module/class/function docstrings present (Google style)
- [ ] Type hints on all function signatures
- [ ] No commented-out code
- [ ] Structured logging with context

### E. Testing
- [ ] Test strategy clear
- [ ] Unit tests for public functions
- [ ] Integration tests for interactions
- [ ] Property tests for invariants
- [ ] Edge cases and errors covered
- [ ] Target: ≥90% coverage

### F. Future Impact
- [ ] No breaking changes
- [ ] No technical debt
- [ ] Backward compatible

**If any check fails**: Fix immediately before proceeding.

## Pre-Commit Review

**Before presenting code:**

1. **Re-read all changes with fresh eyes:**
   - Read every changed file completely
   - Verify all review checkpoints passed
   - Check for inconsistencies across files
   - Validate test coverage

2. **Simulate user perspective:**
   - Is change clear and understandable?
   - Obvious questions user will ask?
   - Documentation sufficient?
   - CHANGELOG updated?
   - README updated?

3. **Verify completeness:**
   - [ ] All files created/modified
   - [ ] All imports added
   - [ ] All dependencies documented (pyproject.toml)
   - [ ] All edge cases handled
   - [ ] All tests written and passing
   - [ ] All quality checks pass (ruff, mypy)
   - [ ] Git status clean (no unstaged deletions, no prohibited files)

4. **Check documentation:**
   - [ ] CHANGELOG.md updated (user-facing changes)
   - [ ] README updated (if new features/commands)

**If issues found**: Fix before presenting. Never present work with known issues.

## Self-Correction Protocol

**When discovering issues:**

1. **Assess severity:**
   - **Critical**: Logic error, security issue, data loss risk, breaking change
   - **Major**: Missing functionality, poor performance, breaks conventions
   - **Minor**: Style issue, suboptimal approach, missing edge case

2. **Fix immediately if:**
   - Critical or major severity
   - Fix straightforward (<10 min)
   - Doesn't require user input

3. **Use HITL if:**
   - Fix requires architectural decision (request_selection)
   - Multiple valid approaches (request_selection)
   - Trade-offs need user input (request_selection)
   - Scope change needed (request_confirmation)

4. **Document if deferring:**
   - Add TODO comment with explanation
   - Note in commit message
   - Add to question queue if blocks progress

5. **Learn from mistakes:**
   - What context was missing?
   - What pattern was misunderstood?
   - How to avoid similar issues?

## Pattern Consistency

**Before implementing new patterns:**
- Search for existing patterns (examine 2-3 usages)
- Validate consistency with `.amazonq/rules/reference/code-patterns.md`
- **Use HITL to confirm if multiple valid options**
- Document new patterns, get user approval via HITL if significant

## Test Coverage

- Aim for 100% on new functions, ≥90% overall
- Tests: independent, deterministic, fast (<1s), clear assertions
- Organization: tests/unit/, tests/integration/, tests/property/
- Naming: test_<functionality>_<scenario>

## Documentation

- [ ] Code: Module/class/function docstrings (Google style), type hints
- [ ] User: README, CHANGELOG
- [ ] Developer: Architecture docs for design changes

## Performance Review

- [ ] Algorithmic complexity acceptable (no O(n²) where O(n) possible)
- [ ] I/O operations async and batched where appropriate
- [ ] No memory leaks (resources closed, context managers used)

**If issues found**: Optimize before presenting (unless premature optimization).

## Security Review

- [ ] No hardcoded credentials (use environment variables)
- [ ] Input validated (user input, API responses, file paths)
- [ ] No sensitive data in error messages

**If issues found**: Fix immediately (critical priority). Never present code with known security issues.

## Integration Review

- [ ] Imports resolve, type hints compatible, no circular dependencies
- [ ] Configuration updated (config.yaml, pyproject.toml)
- [ ] Backward compatibility maintained

## Pre-Commit Hook Compliance

**Mandate**: All commits MUST pass pre-commit hooks before being committed.

**Rationale**: Pre-commit hooks enforce:
- Code formatting (ruff format)
- Linting (ruff check)
- Type checking (mypy)
- Tests (pytest)

**Workflow for Auto-Fixable Issues**:
1. Pre-commit hooks auto-fix files (trailing whitespace, formatting)
2. Commit fails with "Files were modified by this hook"
3. Stage the auto-fixed files: `git add -u`
4. Retry the commit with same message
5. Hooks pass, commit succeeds

**Workflow for Non-Auto-Fixable Issues**:
1. Pre-commit hooks report errors (mypy, pytest, etc.)
2. Commit fails with specific error messages
3. Fix the code manually to address the errors
4. Stage the fixes: `git add <files>`
5. Retry the commit
6. Hooks pass, commit succeeds

**NEVER**: Use `--no-verify` to bypass hooks (defeats quality gates)

## Final Quality Gate

**Before presenting:**

1. **Check git status and prohibited files:**
   ```bash
   git status
   # Verify:
   # - No unstaged deletions
   # - No untracked transient files
   # - All file moves properly staged (git mv)
   # - NO prohibited files (*SUMMARY*.md, *HANDOFF*.md, *TODO*.md)
   ```

2. **Run quality checks:**
   ```bash
   pytest  # All tests pass
   mypy src/  # No type errors
   ruff check .  # No linting errors
   ruff format --check .  # Formatting correct
   ```

3. **Verify coverage:**
   ```bash
   pytest --cov=src --cov-report=term-missing
   # New code ≥90% coverage
   ```

4. **Manual verification:**
   - [ ] All changed files reviewed
   - [ ] All tests pass
   - [ ] No obvious issues
   - [ ] Documentation complete
   - [ ] Git status clean
   - [ ] Ready for user review

**If any check fails**: Fix before presenting. Never present work that fails quality checks.

## Exception Handling

**When to skip review**: Never.

**When to use HITL during review**: Complex architectural decisions, trade-offs, unclear requirements, high-risk changes, ANY uncertainty.
