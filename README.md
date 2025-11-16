<div align="center">

# 🤖 MAC MCP Server

**Multi-Agent Coordination via Model Context Protocol**

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![MCP](https://img.shields.io/badge/MCP-June%202025-purple)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-alpha-orange)

*Event-sourced orchestration for autonomous LLM agent collaboration*

[Quick Start](#-quick-start) • [Documentation](docs/) • [Examples](examples/) • [Roadmap](ROADMAP.md)

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎯 Autonomous Coordination
- **LLM-powered goal decomposition** into executable task DAGs
- **Dependency-aware scheduling** with automatic topological sorting
- **Capability-based task matching** to specialized agents

</td>
<td width="50%">

### 🔄 Event Sourcing
- **Complete audit trail** of all system actions
- **Time-travel debugging** via event replay
- **State reconstruction** from append-only log

</td>
</tr>
<tr>
<td>

### 🤝 Agent Management
- **Pull-based assignment** prevents agent overload
- **Heartbeat monitoring** with automatic timeout detection
- **Capability matching** routes tasks to qualified agents

</td>
<td>

### 🛡️ Production Ready
- **MCP June 2025 compliant** with typed outputSchema
- **Multi-provider LLM** (Anthropic, AWS Bedrock)
- **Real-time TUI dashboard** for monitoring

</td>
</tr>
</table>

---

## 🏗 Architecture

```
┌─────────────┐
│   Claude    │ ← MCP Client (stdio, SSE, or HTTP transport)
│  (any LLM)  │
└──────┬──────┘
       │
       │ MCP Protocol (8 tools)
       │
┌──────▼────────────────────────────────────────────────┐
│              MAC MCP Server                           │
│  ┌────────────────────────────────────────────────┐   │
│  │           Orchestrator (Coordinator)           │   │
│  │  • Goal decomposition (LLM-powered)            │   │
│  │  • Task DAG management                         │   │
│  │  • Dependency resolution                       │   │
│  │  • Event sourcing (JSONL append-only log)      │   │
│  └────────────────────────────────────────────────┘   │
│                                                        │
│  ┌────────────────────────────────────────────────┐   │
│  │           Supervisor (Agent Manager)           │   │
│  │  • Agent registration & capabilities           │   │
│  │  • Heartbeat monitoring (90s timeout)          │   │
│  │  • Health status tracking                      │   │
│  └────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
       │
       │ MCP Tool Calls (claim_task, complete_task, etc.)
       │
┌──────┴──────┬──────────┬──────────┬──────────┐
│  Agent 1    │ Agent 2  │ Agent 3  │ Agent N  │
│  (Python)   │ (Testing)│  (Docs)  │  (...)   │
│             │          │          │          │
│ Capabilities│ pytest   │ markdown │ Custom   │
│ python, api │ coverage │ diagrams │ skills   │
└─────────────┴──────────┴──────────┴──────────┘
```

---

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install mac-mcp

# Or install from source
git clone https://github.com/yourusername/mac-mcp.git
cd mac-mcp
pip install -e .
```

### Configuration

```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Edit configuration with your API keys
# Required: Anthropic API key OR AWS Bedrock access
```

Example `config.yaml`:
```yaml
llm:
  provider: anthropic  # or 'bedrock'
  model: claude-sonnet-4-5-20250929
  api_key: ${ANTHROPIC_API_KEY}  # From environment

storage:
  type: jsonl
  path: ./data/events.jsonl

orchestrator:
  max_retries: 3
  timeout_seconds: 300
```

### Running the Server

```bash
# Start server with TUI dashboard
mac-mcp --config config.yaml --ui tui

# Or start in headless mode
mac-mcp --config config.yaml
```

### Submit Your First Goal

```python
from mcp import Client

async def main():
    client = Client("stdio")  # Connect to MAC MCP Server
    await client.connect()

    # Submit a goal
    result = await client.call_tool("submit_goal", {
        "goal_id": "auth_system",
        "description": "Build user authentication system with JWT",
        "context": {
            "language": "python",
            "framework": "fastapi",
            "requirements": ["registration", "login", "token refresh"]
        }
    })

    print(result)  # Goal decomposed into tasks

asyncio.run(main())
```

**Next**: Follow the [10-minute tutorial](docs/getting-started/quickstart.md) to build your first agent.

---

## 📖 Documentation

| Category | Description | Links |
|----------|-------------|-------|
| **Getting Started** | New to MAC MCP? Start here. | [Quick Start](docs/getting-started/quickstart.md) |
| **Guides** | How-to guides for common tasks | [Agent Integration](docs/guides/agent-integration.md) |
| **Reference** | Technical specifications | [Protocol Spec](docs/reference/protocol.md) • [Architecture](docs/reference/architecture.md) |
| **Examples** | Working code examples | [Simple Agent](docs/examples/README.md) • [Code Samples](examples/) |

---

## 🔧 MCP Tools

MAC MCP Server implements 8 tools via the Model Context Protocol:

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `submit_goal` | Submit high-level goal for decomposition | goal_id, description, context | Goal with task DAG |
| `register_agent` | Register agent with capabilities | agent_id, capabilities | Registration confirmation |
| `claim_task` | Claim next available task | agent_id, capabilities | Task or null |
| `report_progress` | Update task progress | task_id, progress, message | Acknowledgment |
| `complete_task` | Mark task complete | task_id, result | Completion + unblocked tasks |
| `fail_task` | Report task failure | task_id, error | Retry decision |
| `request_dependency` | Get dependency result | task_id, dependency_id | Dependency output |
| `heartbeat` | Maintain agent liveness | agent_id, status | Acknowledgment |

See [Protocol Reference](docs/reference/protocol.md) for detailed schemas.

---

## 🧪 Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/mac_mcp --cov-report=html

# Lint and format
ruff check src/
ruff format src/

# Type checking
mypy src/
```

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📊 Project Status

**Current Version**: v0.1.0 (Alpha)

**Known Limitations**:
- Single orchestrator instance (distributed in v2.0)
- JSONL storage only (pluggable backends in v1.0)
- No authentication (JWT in v0.3.0)
- No web dashboard (planned v0.4.0)

See [ROADMAP.md](ROADMAP.md) and [CHANGELOG.md](CHANGELOG.md) for details.

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ using Claude and the Model Context Protocol**

⭐ Star us on GitHub • 🐛 Report issues • 💡 Request features

</div>
