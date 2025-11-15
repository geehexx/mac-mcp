---
title: Contributing Guide
description: Guidelines for contributing to MAC MCP Server
version: 1.0.0
type: documentation
category: contributing
machine_readable: true
---

# Contributing to MAC MCP Server

Thank you for your interest in contributing to the Multi-Agent Coordination MCP Server! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- uv (recommended) or pip
- Git

### Setup Steps

```bash
# Clone the repository
git clone https://github.com/geehexx/mac-mcp.git
cd mac-mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies with uv (recommended)
uv pip install -e ".[dev]"

# Or with pip
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow the code style guidelines (see below)
- Add tests for new functionality
- Update documentation as needed
- Run tests locally before committing

### 3. Run Quality Checks

```bash
# Linting and formatting
ruff check src tests
ruff format src tests

# Type checking
mypy src

# Run tests
pytest

# Run all pre-commit hooks
pre-commit run --all-files
```

### 4. Commit Changes

We use conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Build/tooling changes

Example:
```bash
git commit -m "feat(orchestrator): add task priority scheduling

Implement priority-based task assignment to optimize
agent utilization for high-priority goals.

Closes #123"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style Guidelines

### Python Style

- Follow PEP 8 (enforced by ruff)
- Use type hints for all functions (enforced by mypy strict mode)
- Maximum line length: 100 characters
- Use descriptive variable names
- Write docstrings for all public APIs (Google style)

Example:
```python
async def create_task(
    self,
    task_id: str,
    description: str,
    required_capabilities: list[str],
) -> Task:
    """Create a new task.

    Args:
        task_id: Unique task identifier
        description: Human-readable task description
        required_capabilities: List of required capability tags

    Returns:
        Created task instance

    Raises:
        ValueError: If task_id already exists
    """
    ...
```

### Testing Guidelines

- **Unit tests**: Fast, isolated tests for single functions/classes
- **Integration tests**: Test component interactions
- **Property tests**: Use Hypothesis for invariant testing
- All tests must be async-compatible
- Aim for >90% code coverage
- Use descriptive test names

Example:
```python
async def test_task_assignment_updates_agent_state(
    orchestrator: Orchestrator,
) -> None:
    """Test that assigning a task updates agent's current_tasks."""
    agent = await orchestrator.supervisor.register_agent("a1", ["python"])
    task = await orchestrator.create_task("t1", "g1", "Test", ["python"])

    await orchestrator.assign_task("t1", "a1")

    assert "t1" in agent.current_tasks
```

### Documentation Guidelines

- All documentation files must have YAML frontmatter
- Update README.md for user-facing changes
- Update ARCHITECTURE.md for design changes
- Add examples for new features
- Use clear, concise language

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_tasks.py

# Run with coverage
pytest --cov --cov-report=html

# Run only unit tests
pytest tests/unit

# Run only integration tests
pytest tests/integration -m integration

# Run property-based tests
pytest tests/property -m property
```

### Writing Tests

Place tests in the appropriate directory:
- `tests/unit/`: Unit tests
- `tests/integration/`: Integration tests
- `tests/property/`: Property-based tests

Use fixtures from `tests/conftest.py`:
```python
async def test_something(
    event_store: InMemoryEventStore,
    orchestrator: Orchestrator,
) -> None:
    ...
```

## Architecture Decisions

Before making significant architectural changes:

1. Review ARCHITECTURE.md and DESIGN_RATIONALE.md
2. Discuss the change in an issue
3. Get consensus from maintainers
4. Update documentation to reflect the decision

## Submitting Pull Requests

### PR Checklist

- [ ] Tests pass (`pytest`)
- [ ] Linting passes (`ruff check`)
- [ ] Type checking passes (`mypy src`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (for significant changes)
- [ ] Commit messages follow conventional commits
- [ ] Branch is up to date with main

### PR Description Template

```markdown
## Description
Brief description of the changes

## Motivation
Why is this change needed?

## Changes
- Bullet list of changes

## Testing
How was this tested?

## Breaking Changes
Any breaking changes?

## Related Issues
Closes #123
```

## Releases

Maintainers will handle releases. The process:

1. Update version in `src/mac_mcp/__init__.py`
2. Update CHANGELOG.md
3. Create git tag
4. GitHub Actions will build and publish

## Getting Help

- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Documentation**: See README.md, ARCHITECTURE.md, PROTOCOL.md

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
