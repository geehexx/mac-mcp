# Refactoring Workflow

This workflow guides safe refactoring with comprehensive testing and validation.

## Step 1: Understand Current Implementation

Before refactoring, thoroughly understand the existing code:

```xml
<read_file>
<path>path/to/file.py</path>
</read_file>
```

Search for all usages:

```xml
<search_files>
<path>src/</path>
<regex>function_or_class_name</regex>
<file_pattern>*.py</file_pattern>
</search_files>
```

## Step 2: Identify Refactoring Goals

Clarify what you're improving and why:

```xml
<ask_followup_question>
<question>What is the goal of this refactoring?

Please specify:
- What needs to be improved (performance, maintainability, structure)
- Current pain points
- Desired end state
- Any constraints or requirements</question>
<options>["Improve performance", "Better maintainability", "Reduce complexity", "Extract reusable components"]</options>
</ask_followup_question>
```

## Step 3: Create Safety Net

**CRITICAL: Ensure comprehensive test coverage BEFORE refactoring**

Check existing test coverage:

```bash
pytest --cov=src/path/to/module --cov-report=term-missing
```

If coverage <90%, add tests first:

1. **Unit tests** for each function/method
2. **Integration tests** for component interactions
3. **Property tests** for invariants

Example test structure:

```python
@pytest.mark.unit
def test_original_behavior():
    """Document current behavior before refactoring."""
    result = original_function(input_data)
    assert result == expected_output
    assert some_invariant_holds(result)
```

## Step 4: Plan Refactoring Strategy

Choose appropriate strategy:

### Small Refactoring (<100 lines)
- Direct replacement in single commit
- Run tests immediately after

### Medium Refactoring (100-500 lines)
- Break into 2-3 commits
- Test after each commit
- Use feature flags if needed

### Large Refactoring (>500 lines)
- **Use Strangler Fig Pattern**:
  1. Create new implementation alongside old
  2. Gradually migrate callers
  3. Remove old implementation when complete
- Consider creating temporary branch
- Multiple commits with tests at each step

## Step 5: Convene Expert Review (for complex refactorings)

For non-trivial refactorings, get expert input:

```
Experts:
- Senior Software Architect (specializes in Python architecture patterns)
- Performance Engineer (expert in optimization strategies)
- Technical Debt Specialist (focuses on maintainability)
```

Ground each expert with research on best practices.

## Step 6: Execute Refactoring

### Use replace_in_file for Targeted Changes

Prefer `replace_in_file` over `write_to_file` for refactoring:

```xml
<replace_in_file>
<path>src/module.py</path>
<diff>
------- SEARCH
def old_implementation(param):
    # ... existing code ...
=======
def new_implementation(param):
    # ... improved code ...
+++++++ REPLACE
</diff>
</replace_in_file>
```

### Maintain Backwards Compatibility

If breaking changes are necessary:

1. Add deprecation warnings first
2. Provide migration guide
3. Update all internal usages
4. Document in CHANGELOG.md

## Step 7: Validate Refactoring

Run comprehensive test suite:

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=term-missing

# Type checking
mypy src/

# Linting
ruff check .
```

### Verify No Behavior Changes

Critical checks:

- [ ] All existing tests pass
- [ ] Coverage maintained or improved (≥90%)
- [ ] No new type errors
- [ ] No new linting issues
- [ ] Performance not degraded (run benchmarks if applicable)

## Step 8: Update Documentation

Update all affected documentation:

- [ ] Function/class docstrings
- [ ] README.md (if public API changed)
- [ ] Architecture docs (if structure changed)
- [ ] CHANGELOG.md (if user-facing)
- [ ] Migration guide (if breaking changes)

## Step 9: Code Review

For significant refactorings:

1. Self-review all changes
2. Use expert review panel if complex
3. Verify all quality gates pass
4. Check for potential side effects

## Step 10: Commit and Monitor

Commit with clear message:

```bash
git add <files>
git commit -m "refactor(module): improve X for better Y

- Specific change 1
- Specific change 2
- Why this improves the codebase

Refs: #123"
```

Monitor after merge:

- Watch for regression reports
- Monitor performance metrics
- Be ready to roll back if issues arise

## Common Refactoring Patterns

### Extract Function

Before:
```python
def process_data(data):
    # Long function with multiple responsibilities
    # 50+ lines...
```

After:
```python
def process_data(data):
    validated = _validate_data(data)
    transformed = _transform_data(validated)
    return _save_result(transformed)

def _validate_data(data): ...
def _transform_data(data): ...
def _save_result(data): ...
```

### Replace Conditional with Polymorphism

Before:
```python
def process(item, type):
    if type == "A":
        # Process type A
    elif type == "B":
        # Process type B
```

After:
```python
class ProcessorA:
    def process(self, item): ...

class ProcessorB:
    def process(self, item): ...

processors = {"A": ProcessorA(), "B": ProcessorB()}
processors[type].process(item)
```

### Introduce Parameter Object

Before:
```python
def create_task(task_id, description, priority, assignee, deadline):
    ...
```

After:
```python
@dataclass(frozen=True)
class TaskRequest:
    task_id: UUID
    description: str
    priority: int
    assignee: str
    deadline: datetime

def create_task(request: TaskRequest):
    ...
```

## Rollback Plan

If issues arise:

1. **Immediate**: Revert the commit
2. **Short-term**: Fix forward with hot patch
3. **Long-term**: Re-evaluate refactoring approach

Always have rollback plan before major refactorings.

## Related Documentation

- Code Patterns: `.clinerules/rules/reference/code-patterns.md`
- Quality Procedures: `.clinerules/rules/core/quality-procedures.md`
- Development Workflow: `.clinerules/rules/core/development-workflow.md`
