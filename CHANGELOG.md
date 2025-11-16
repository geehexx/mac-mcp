# Changelog

All notable changes to MAC MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Event validation before persistence (prevents data corruption)
- MCP June 2025 compliance with outputSchema for all 8 tools
- Dry-run mode for submit_goal (human-in-the-loop preview)
- Production-ready example agent with best practices
- Comprehensive beginner tutorial (10 minutes)
- Examples documentation with LLM integration guides
- Structured output schemas for type-safe tool responses
- Event semantic validation (required fields per event type)

### Changed
- Documentation restructured into docs/ directory following Diátaxis framework
- README optimized with visual design and badges
- ROADMAP consolidated as single source of truth for future work

## [0.1.0] - 2025-11-15

### Added
- Core orchestrator with event sourcing (JSONL + in-memory)
- Autonomous goal decomposition using LLM
- Agent registration and heartbeat monitoring (90s timeout)
- Pull-based task assignment with capability matching
- Task DAG with dependency resolution
- MCP server implementation (stdio transport)
- Configuration system (YAML + environment variables)
- Multi-provider LLM support (Anthropic API, AWS Bedrock)
- TUI dashboard with real-time monitoring (Rich-based)
- Goal/Task/Agent state machines
- Retry logic with exponential backoff
- Event store snapshotting foundation

### Documentation
- Protocol specification (MCP tools)
- Architecture overview (event sourcing, actor model)
- Agent integration guide
- Example configuration
- Roadmap through 2027

### Infrastructure
- Python 3.12+ support
- Pydantic v2 domain models
- AsyncIO throughout
- Type hints and static typing
- Pre-commit hooks (ruff, mypy, pytest)
- Makefile for common tasks

---

## Release Notes

### v0.1.0 - Initial Release

**MAC MCP Server** provides event-sourced orchestration for autonomous multi-agent LLM collaboration via the Model Context Protocol (MCP).

**Key Features**:
- 🎯 **Autonomous Coordination**: LLM-powered goal decomposition into executable task DAGs
- 🔄 **Event Sourcing**: Complete audit trail with time-travel debugging and replay
- 🤝 **Agent Management**: Capability-based matching, heartbeat monitoring, pull-based assignment
- 🛡️ **Production Ready**: MCP June 2025 compliant, multi-provider LLM, TUI dashboard

**Getting Started**: See [Quick Start Guide](docs/getting-started/quickstart.md)

**Known Limitations**:
- Single orchestrator instance (distributed coordination planned for v2.0)
- JSONL storage only (pluggable backends planned for v1.0)
- No authentication (JWT planned for v0.3.0)
- No web dashboard (planned for v0.4.0)

**Next Release**: v0.2.0 (Q1 2026) - Performance metrics, event snapshotting, context engineering
