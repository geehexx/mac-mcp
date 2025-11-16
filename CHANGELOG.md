# Changelog

All notable changes to MAC MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
