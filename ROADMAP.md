# Roadmap

Future enhancements prioritized by impact and effort.

## Current (v0.1.0)

✅ Production-ready foundation with event sourcing, autonomous coordination, MCP June 2025 compliance.

See [CHANGELOG.md](CHANGELOG.md) for complete feature list.

---

## Next Release (v0.2.0 - Q1 2026)

### MCP Output Schema Compliance
**Priority**: High | **Effort**: Low

Fix tool handlers to return structured data:
- Handlers currently return TextContent causing validation warnings
- Refactor to return dict matching outputSchema
- Tools work but produce "Output validation error" messages

### LLM Rate Limiting
**Priority**: Critical | **Effort**: Medium

Production-grade rate limiting for LLM providers:
- Token bucket algorithm with exponential backoff
- Request queuing for concurrent goals
- Per-provider rate limits (Bedrock: 1 req/5s, Anthropic: configurable)
- Monitoring and alerting for throttling events
- **Status**: Required before high-volume production use

### Decomposition Caching
**Priority**: High | **Effort**: Low

Cache LLM decompositions for similar goals:
- Hash-based lookup (goal description + context)
- 30-50% reduction in LLM calls
- Configurable TTL and cache size
- Cost savings: ~$8-$860/month depending on volume

### MCP Health Check Tool
**Priority**: Medium | **Effort**: Low

Add health/status tool:
- Server status and uptime
- LLM provider availability
- Storage backend info
- Active agents/tasks count
- Memory usage

### Context Engineering
**Priority**: High | **Effort**: High

Dynamic LLM context vs static prompts:
- Retrieve similar past decompositions (embedding search)
- Include domain patterns and constraints
- Reduce hallucination, improve DAG quality
- Optimize prompts (20-30% token reduction)

### Event Snapshotting
**Priority**: High | **Effort**: Medium

Snapshots every 1000 events:
- Reduces startup from O(N) to O(M) events
- Minutes → seconds for large logs
- Base class already defined, needs integration

### Performance Metrics
**Priority**: Medium | **Effort**: Low

TUI dashboard enhancements:
- Task throughput, completion times
- Agent utilization (active/idle/failed)
- Goal statistics (avg, p95, p99)
- Error rates, memory usage
- LLM cost tracking

---

## v0.3.0 - Observability (Q2 2026)

### OpenTelemetry Tracing
Production observability:
- Trace goal submission → task execution
- Track LLM API calls + token counts
- Export to Jaeger/Zipkin/cloud

### Event Notifications
WebSocket-based vs polling:
- Task assignment latency: 1s → 50ms
- Lower CPU usage

---

## v0.4.0 - Security (Q2 2026)

### OAuth 2.1 Authentication
Production-grade authentication:
- Replace alpha API key auth
- Short-lived tokens (1hr) with refresh
- Claims: agent_id, capabilities, issued_at
- Required for all MCP tool calls

### Event Log Signing (HMAC)
- HMAC-SHA256 signatures
- Tamper detection on replay

### Agent Rate Limiting
Per-agent resource limits:
- Max concurrent tasks/agent: 5
- Max failed tasks: 10/hr
- Prevent resource exhaustion

### Web Dashboard
Browser UI with real-time updates:
- Goal/task/agent status (WebSocket)
- Dependency graph visualization (D3.js)
- Historical analytics
- Event stream viewer

---

## v1.0.0 - Production (Q4 2026)

### Additional LLM Providers
- Azure OpenAI, Google Vertex AI
- Ollama (local), LM Studio (dev)

### Template Decomposition
Pattern matching for common workflows:
- 10x faster than LLM for known patterns
- Auto-learn from successful decompositions

### Pluggable Storage
- PostgreSQL, MongoDB, Kafka
- S3 + DynamoDB (serverless)

### Monitoring Integrations
- Prometheus/Grafana
- Datadog, CloudWatch

### Complete Documentation
- Auto-generated API reference
- Cloud deployment guides (AWS/GCP/Azure)
- Performance tuning guide
- Security hardening checklist

---

## v2.0.0+ - Scale (2027)

### Distributed Orchestrator
Multiple instances with coordination (Redis/etcd):
- High availability, multi-region
- Horizontal scalability
- Use case: >1000 tasks/hour

### Multi-Tenancy
Per-tenant isolation:
- Separate event logs, agent pools
- Resource quotas, rate limits
- Custom LLM configurations

---

## Contributing

Ideas for new features? [Open an issue](../../issues) with:
- Use case and expected behavior
- Implementation suggestions
- Priority justification

**Priority Levels**:
- **Critical**: Blocks production use
- **High**: Significant value
- **Medium**: Nice-to-have
- **Low**: Future exploration

**Effort Estimates**:
- **Low**: 1-2 days
- **Medium**: 1-2 weeks
- **High**: 2-4 weeks

---

**Last Updated**: November 16, 2025
