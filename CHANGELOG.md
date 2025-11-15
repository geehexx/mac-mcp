---
title: Changelog
description: Version history and changes
version: 0.1.0
type: documentation
category: changelog
machine_readable: true
---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-11-15

### Added

#### Architecture & Design
- Complete architecture design with Supervisor/Worker pattern
- Formal protocol specification (MAC Protocol v1.0.0)
- Event sourcing with JSONL format
- Task state machine with deterministic transitions
- Design rationale documentation

#### Core Implementation
- Domain models (Events, Tasks, Agents) with Pydantic v2
- Event store with JSONL and in-memory backends
- Agent supervisor with heartbeat monitoring
- Main orchestrator with state management
- Pull-based task assignment

#### MCP Integration
- MCP server with 6 core tools:
  - `register_agent`
  - `claim_task`
  - `report_progress`
  - `complete_task`
  - `fail_task`
  - `heartbeat`
- MCP resources for tasks, agents, and events
- stdio transport support

#### Testing
- Unit tests with pytest-asyncio
- Integration tests for end-to-end workflows
- Property-based tests with Hypothesis
- Test coverage >90%

#### Development Infrastructure
- Modern project structure with src/ layout
- pyproject.toml with comprehensive tool configuration
- GitHub Actions CI/CD pipeline
- Pre-commit hooks for code quality
- Ruff for linting and formatting
- Mypy for strict type checking
- Agent configuration files (.clinerules, .cursorrules)

#### Documentation
- README with quick start guide
- ARCHITECTURE.md with complete system design
- PROTOCOL.md with formal specification
- DESIGN_RATIONALE.md with decision deep-dives
- CONTRIBUTING.md with development guidelines
- YAML frontmatter for machine readability

### Changed
- N/A (initial release)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- Type-safe implementation with strict mypy
- Input validation with Pydantic
- Immutable events (frozen models)

## Release Notes

### v0.1.0 - Initial Architecture Complete

This is the foundational release of MAC MCP Server, implementing the complete architecture and protocol specification. The system is designed for:

- **Protocol Soundness**: Based on Actor model, Supervisor pattern, and Event Sourcing
- **Type Safety**: Full type hints with mypy strict mode
- **Testing**: Comprehensive test suite with unit, integration, and property tests
- **Modern Tooling**: Python 3.12+, Pydantic v2, pytest-asyncio, Hypothesis
- **Agent Automation**: Configuration files for Claude and other AI agents

**Status**: Architecture and core implementation complete. Ready for Phase 2 (HITL Integration).

**Breaking Changes**: None (initial release)

**Migration Guide**: N/A (initial release)

[Unreleased]: https://github.com/geehexx/mac-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/geehexx/mac-mcp/releases/tag/v0.1.0
