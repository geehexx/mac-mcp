# Roadmap

Future enhancements for MAC MCP Server, prioritized by impact and implementation effort.

---

## Current Status (v0.1.0)

✅ **Production-ready foundation** with event sourcing, autonomous coordination, and MCP compliance.

See [CHANGELOG.md](CHANGELOG.md) for detailed release history.

---

## In Progress (v0.2.0 - Target: Q1 2026)

### Context Engineering for Goal Decomposition
**Priority**: Critical | **Effort**: High

Upgrade from static prompts to dynamic context engineering:
- Retrieve relevant past decompositions via embedding similarity
- Include domain-specific patterns and constraints
- Adapt context based on goal complexity
- Reduce hallucination and improve DAG quality

**Why**: 2025 standard for LLM applications (per research)

### Event Store Snapshotting
**Priority**: High | **Effort**: Medium

Automated snapshots every 1000 events for faster recovery:
- Current: O(N) replay where N = total events
- Target: O(M) where M = events since last snapshot
- Reduces startup time from minutes to seconds for large logs

**Implementation**: Already defined in base class, needs orchestrator integration

---

## Q1 2026 - Performance & Observability (v0.3.0)

### OpenTelemetry Distributed Tracing
**Priority**: High | **Effort**: Medium

Production-grade observability for multi-agent systems:
- Trace goal submission, decomposition, task execution
- Track LLM API calls with token counts
- Instrument agent heartbeats and dependency resolution
- Export to Jaeger, Zipkin, or cloud providers

**Dependencies**: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp`

### Performance Metrics in TUI
**Priority**: High | **Effort**: Low

Add metrics panel to dashboard:
- Task throughput and completion times
- Agent utilization rates (active/idle/failed)
- Goal statistics (avg, p95, p99 completion time)
- Error rates and retry counts
- Event log growth and memory usage

### Event-based Task Notifications
**Priority**: Medium | **Effort**: Medium

Replace polling with WebSocket notifications:
- Reduces task assignment latency from ~1s to ~50ms
- Improves agent responsiveness
- Lower CPU usage

---

## Q2 2026 - Security & Production (v0.4.0)

### Agent Authentication (JWT)
**Priority**: Critical | **Effort**: Medium

Prevent agent impersonation:
- Short-lived tokens (1 hour) with refresh capability
- Token claims: agent_id, capabilities, issued_at
- All MCP tool calls require valid JWT
- Configurable signing keys

### Event Log Signing (HMAC)
**Priority**: High | **Effort**: Low

Detect tampering and corruption:
- HMAC-SHA256 signatures on events
- Verification during replay
- Configurable secret rotation

### Rate Limiting & Quotas
**Priority**: High | **Effort**: Medium

Protect against resource exhaustion:
- Max concurrent tasks per agent: 5 (configurable)
- Max event payload: 1 MB
- Max task runtime: 1 hour (configurable)
- Max failed tasks: 10/hour per agent
- Max API calls: 1000/hour per agent

### Web Dashboard
**Priority**: Medium | **Effort**: High

Browser-based monitoring UI:
- Real-time goal/task/agent status (WebSocket)
- Interactive dependency graph visualization (D3.js)
- Historical analytics and trends
- Event stream viewer with filtering
- Export capabilities (JSON, CSV, PDF)

**Tech Stack**: React/Vue.js, D3.js, FastAPI backend

---

## Q3 2026 - Extensibility (v0.5.0)

### Additional LLM Providers
**Priority**: Medium | **Effort**: Medium

Expand beyond Anthropic and AWS Bedrock:
- **Azure OpenAI** - Enterprise customers
- **Google Vertex AI** - Claude on GCP
- **Ollama** - Local deployment
- **LM Studio** - Development/testing

### Template-based Decomposition
**Priority**: Medium | **Effort**: Medium

Pattern matching for common workflows:
- "Implement REST API" → Standard CRUD pattern
- "Add feature X" → Design → Implement → Test → Document
- "Fix bug in Y" → Reproduce → Fix → Test → Verify

**Benefits**: 10x faster + cheaper than LLM for known patterns

### Pluggable Storage Backends
**Priority**: Medium | **Effort**: High

Support alternative event stores:
- **PostgreSQL** - Relational with rich querying
- **MongoDB** - Complex event payloads
- **Apache Kafka** - High-throughput streaming
- **S3 + DynamoDB** - Serverless AWS deployment

### Monitoring Integrations
**Priority**: Medium | **Effort**: Low

Standard observability exports:
- Prometheus metrics endpoint
- Grafana dashboard templates
- Datadog APM integration
- CloudWatch integration (AWS)

---

## Q4 2026 - Production Hardening (v1.0.0)

### Hybrid Decomposition Strategy
**Priority**: Low | **Effort**: High

Combine templates and LLM intelligently:
1. Check if goal matches known pattern (embedding similarity)
2. If yes → Use template (fast, cheap, consistent)
3. If no → Use LLM (flexible)
4. Store successful LLM decompositions as new templates

### CI/CD & Deployment Tooling
**Priority**: Medium | **Effort**: Medium

Production deployment support:
- Official Docker images (multi-arch)
- Kubernetes Helm charts
- Terraform modules (AWS, GCP, Azure)
- GitHub Actions workflows
- Health check endpoints

### Documentation Completeness
**Priority**: High | **Effort**: Medium

Production-grade documentation:
- Complete API reference (auto-generated)
- Deployment guides (Docker, K8s, serverless)
- Troubleshooting playbooks
- Performance tuning guide
- Security hardening checklist

---

## 2027 - Distributed & Multi-Tenant (v2.0.0)

### Distributed Orchestrator
**Priority**: Low | **Complexity**: Very High

Horizontal scalability with multiple orchestrator instances:
- Coordination via Redis or etcd
- Distributed locks for task assignment
- Event log partitioning by goal_id or tenant_id
- Leader election for decomposition

**Use Cases**: >1000 tasks/hour, high availability, multi-region deployment

### Multi-Tenancy
**Priority**: Low | **Complexity**: High

Isolate goals and agents per tenant:
- Namespace isolation: `{tenant_id}:{goal_id}`
- Per-tenant event logs and agent pools
- Per-tenant resource quotas and rate limits
- Tenant-specific LLM configurations

---

## 2027+ - Intelligence & Learning (v3.0.0)

### Cross-Goal Learning
**Priority**: Low | **Complexity**: Very High

Learn from execution history:
- Store successful task DAGs as templates
- Embedding-based similarity search for goal matching
- Recommend decompositions for similar goals
- A/B testing of decomposition strategies
- Continuous improvement loop

### Adversarial Agent Detection
**Priority**: Low | **Complexity**: High

Detect malicious or compromised agents:
- Reputation scoring (success rate, latency, quality)
- Anomaly detection (unusual task patterns)
- Multi-agent verification for critical tasks
- Automatic quarantine of suspicious agents
- Manual review workflows

### Dynamic Re-planning
**Priority**: Low | **Complexity**: Very High

Adaptive DAG rewriting during execution:
- Agents propose DAG modifications based on runtime insights
- LLM evaluates proposed changes for validity
- Orchestrator applies approved modifications
- Full history preserved in event log (event sourcing FTW)

**Use Cases**: Long-running goals, changing requirements, unexpected blockers

---

## Version Timeline

| Version | Target | Theme | Key Features |
|---------|--------|-------|--------------|
| v0.2.0 | Q1 2026 | Performance | Context engineering, snapshotting, metrics |
| v0.3.0 | Q2 2026 | Observability | OpenTelemetry, notifications |
| v0.4.0 | Q2 2026 | Security | JWT auth, HMAC signing, rate limiting, web UI |
| v0.5.0 | Q3 2026 | Extensibility | Multi-provider LLM, templates, pluggable storage |
| v1.0.0 | Q4 2026 | Production | Hybrid decomposition, CI/CD, complete docs |
| v2.0.0 | 2027 | Scale | Distributed orchestrator, multi-tenancy |
| v3.0.0 | 2027+ | Intelligence | Learning, adversarial detection, dynamic planning |

---

## Contributing to the Roadmap

Have ideas for new features? We'd love to hear from you!

1. Check existing [GitHub Issues](../../issues)
2. Open a new issue with the `enhancement` label
3. Include use case, expected behavior, and implementation ideas
4. Join the discussion!

**Priority Criteria**:
- **Critical**: Blocks production use or major user pain point
- **High**: Significant value to many users
- **Medium**: Valuable to some users or nice-to-have
- **Low**: Future exploration or niche use case

**Effort Estimates**:
- **Low**: 1-2 days
- **Medium**: 1-2 weeks
- **High**: 2-4 weeks
- **Very High**: 1-3 months

---

*Last updated: November 16, 2025*
