# Changelog

All notable changes to MAC MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Fix Pydantic Field syntax for mypy compatibility (removed Annotated wrapper, use Field as default value)
- Fix imports in mac_mcp_core/storage to reference mac_mcp_core instead of legacy mac_mcp package
- Fix datetime.now() to use UTC timezone in dashboard
- Fix loop variable overwrite in JSONL event store (PLW2901)
- Fix unused import warnings (TaskDAG added to __all__)
- Add Pydantic mypy plugin for proper type checking
- Auto-fix 63 linting errors (import sorting, whitespace, unnecessary pass statements)
- Add noqa comments for intentional patterns (lazy imports in entry points, stylistic choices)
- Prefix unused method arguments with underscore (matcher/scheduler context parameters)

### Security
- Fix authorization bypass in claim_task: now uses registered agent capabilities instead of caller-provided
- Add PII redaction for error objects to prevent sensitive data leakage in event logs
- Strengthen request_dependency authorization with same-goal verification to prevent cross-goal data access
- Add structured error handling with context in goal decomposition
- Add actor_id field to Event model for audit trail compliance (optional for backward compatibility)
- Document resource endpoint authentication limitations and v0.2.0 security roadmap (event signing, rate limiting)

### Changed
- Improve try-except-else patterns for better error handling (TRY300 compliance)
- Replace ambiguous Unicode characters with ASCII equivalents (RUF001 compliance)

### Added
- **Domain Models**: Event-sourced domain models (Goal, Task, Agent, Event)
- **Event Sourcing**: 18 event types with immutable frozen models
- **Storage**: In-memory and JSONL event stores with snapshot support
- **Core Orchestration**: Goal decomposition, task DAG management, agent supervision
- **LLM Integration**: Anthropic Claude Sonnet 4.5 and AWS Bedrock support
- **Goal Decomposer**: Autonomous LLM-powered goal → task DAG conversion
- **Agent Supervisor**: Heartbeat monitoring (90s timeout), health tracking, quarantine
- **Authentication**: API key authentication (alpha - suitable for development)
- **MCP Server**: stdio transport with 8 tools and 3 resources
- **MCP Tools**: submit_goal, register_agent, claim_task, report_progress, complete_task, fail_task, request_dependency, heartbeat
- **MCP Resources**: coordination://tasks, coordination://agents, coordination://events
- **CLI**: Command-line interface with headless mode
- **TUI Dashboard**: Rich-based real-time monitoring with live updates
- **Configuration**: Type-safe YAML + environment variable support
- **Testing**: 55 tests (unit, integration, property-based) with 43% coverage
- **Documentation**: Comprehensive README, quickstart guide, architecture docs, examples
- **Production Agent Example**: Complete reference implementation

### Changed
- Project infrastructure and development tooling
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks (ruff, mypy, pytest)
- Makefile for development automation
- Python 3.12+ support with comprehensive tooling

### Security
- **ALPHA WARNING**: API key authentication is suitable for development only
- OAuth 2.1 planned for v0.2.0
- Agent-scoped permissions (agents can only act on own tasks)
- Task ownership validation
- Dependency access control

---

## Release History

Future releases will be documented here.
