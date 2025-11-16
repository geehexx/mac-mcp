# Roadmap

Future enhancements for MAC MCP Server, prioritized by user value and implementation complexity.

## Current Status (v0.1.0)

**Completed**:
- Core orchestrator with event sourcing
- Autonomous goal decomposition (LLM-based)
- Agent registration and heartbeat monitoring
- Pull-based task assignment with dependency resolution
- MCP server (stdio transport)
- Configuration system (YAML + environment)
- Multi-provider LLM (Anthropic API, AWS Bedrock)
- TUI dashboard (Rich-based terminal UI)

---

## Q4 2025 - Performance & Metrics

### Performance Metrics in TUI
**Priority**: High

Add performance metrics panel showing:
- Task throughput and completion times
- Agent utilization rates
- Goal completion statistics (avg, p95, p99)
- Error rates and retry counts
- Event log growth and resource usage

### Event-based Task Notifications
**Priority**: Medium

Replace polling with WebSocket-based notifications to reduce task assignment latency from ~1s to ~50ms.

### State Snapshot System
**Priority**: Medium

Periodic snapshots every 1000 events for faster recovery. Reduces startup time from minutes to seconds for large event logs.

---

## Q1 2026 - Security & Production

### Agent Authentication (JWT)
**Priority**: High

Prevent agent impersonation with JWT tokens:
- Short-lived tokens (1 hour) with refresh
- Token includes agent_id and capabilities claims
- All MCP tool calls require valid JWT

### Event Log Signing (HMAC)
**Priority**: Medium

Sign events with HMAC-SHA256 to detect tampering or corruption.

### Rate Limiting & Quotas
**Priority**: Medium

Protect against resource exhaustion:
- Max concurrent tasks per agent: 5
- Max event payload: 1 MB
- Max task runtime: 1 hour (configurable)
- Max failed tasks per agent: 10/hour
- Max API calls per agent: 1000/hour

### Web Dashboard
**Priority**: Medium

Browser-based monitoring UI with:
- Real-time goal/task/agent status (WebSocket)
- Interactive dependency graphs
- Historical analytics and trends
- Event stream viewer with filtering
- Export capabilities (JSON, CSV, PDF)

**Tech**: React/Vue.js, D3.js visualization, FastAPI backend

---

## Q2 2026 - Advanced LLM & Integrations

### Additional LLM Providers
**Priority**: Medium

- Azure OpenAI (enterprise customers)
- Google Vertex AI (Claude on GCP)
- Ollama (local deployment)
- LM Studio (development)

### Template-based Decomposition
**Priority**: Low

Pattern-based decomposition for common workflows:
- "Implement REST API" → Standard CRUD pattern
- "Add feature X" → Design → Implement → Test → Document
- "Fix bug in Y" → Reproduce → Fix → Test → Verify

Benefits: Faster, cheaper, more consistent than LLM for known patterns.

### Monitoring Integrations
**Priority**: Medium

- Prometheus metrics export
- Grafana dashboards
- OpenTelemetry distributed tracing
- Datadog APM integration

---

## Q3 2026 - Extensibility

### Pluggable Storage Backends
**Priority**: Medium

Support alternative event stores:
- PostgreSQL (relational with indexing)
- MongoDB (complex event payloads)
- Kafka (high-throughput streaming)
- S3 + DynamoDB (serverless AWS)

### Hybrid Decomposition
**Priority**: Low

Combine templates and LLM:
1. Check if goal matches known pattern
2. If yes, use template (fast, cheap)
3. If no, use LLM (flexible)
4. Store successful LLM decompositions as templates

### CI/CD & Deployment
**Priority**: Low

- Docker image
- Helm chart for Kubernetes
- Terraform modules
- GitHub Actions workflows

---

## Q4 2026 - Distributed & Multi-Tenant

### Distributed Orchestrator
**Priority**: Low
**Complexity**: Very High

Horizontal scalability with multiple orchestrator instances:
- Coordination via Redis or etcd
- Distributed locks for task assignment
- Event log partitioning by goal or tenant

**Use cases**: >1000 tasks/hour, high availability, multi-region

### Multi-Tenancy
**Priority**: Low
**Complexity**: High

Isolate goals and agents per tenant:
- Namespace isolation (`{tenant_id}:{goal_id}`)
- Per-tenant event logs and agent pools
- Per-tenant resource quotas

---

## 2027 - Intelligence & Learning

### Cross-Goal Learning
**Priority**: Low
**Complexity**: Very High

Learn from past executions:
- Store successful task DAGs as templates
- Embedding-based similarity search
- Recommend decompositions for similar goals
- A/B testing of strategies

### Adversarial Agent Detection
**Priority**: Low
**Complexity**: High

Detect malicious or compromised agents:
- Reputation scoring (success rate, completion time)
- Anomaly detection (unusual patterns)
- Multi-agent verification for critical tasks
- Automatic quarantine

### Dynamic Re-planning
**Priority**: Low
**Complexity**: Very High

Adaptive DAG rewriting during execution:
- Agents propose DAG modifications
- LLM evaluates proposed changes
- Orchestrator applies approved changes
- Full history preserved in event log

---

## Version Milestones

- **v0.2.0** (Q4 2025): Performance metrics, notifications, snapshots
- **v0.3.0** (Q1 2026): Security (JWT, HMAC, rate limiting)
- **v0.4.0** (Q1 2026): Web dashboard
- **v0.5.0** (Q2 2026): Additional LLM providers, templates, monitoring
- **v1.0.0** (Q3 2026): Pluggable storage, complete docs, production-ready
- **v2.0.0** (Q4 2026): Distributed orchestrator, multi-tenancy
- **v3.0.0** (2027): Intelligence, learning, dynamic planning
