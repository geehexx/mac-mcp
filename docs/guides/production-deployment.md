# Production Deployment

Deploy MAC MCP Server in production with security and reliability.

## Prerequisites

- **Python**: 3.12+
- **Memory**: 512MB minimum, 2GB+ recommended
- **Storage**: 1GB+ for event logs
- **LLM Provider**: Anthropic API key OR AWS Bedrock access

## Security

### API Keys

Use environment variables:
```bash
export ANTHROPIC_API_KEY="your-key-here"
export MAC_MCP_EVENT_STORE_PATH="/var/lib/mac-mcp/events.jsonl"
```

Config with substitution:
```yaml
llm:
  api_key: ${ANTHROPIC_API_KEY}
  model: claude-sonnet-4-5-20250929
```

### File Permissions

```bash
sudo mkdir -p /var/lib/mac-mcp
sudo chown mac-mcp:mac-mcp /var/lib/mac-mcp
sudo chmod 700 /var/lib/mac-mcp
```

## Systemd Service

**Service file** (`/etc/systemd/system/mac-mcp.service`):
```ini
[Unit]
Description=MAC MCP Server
After=network.target

[Service]
Type=simple
User=mac-mcp
WorkingDirectory=/opt/mac-mcp
Environment="ANTHROPIC_API_KEY=your-key-here"
ExecStart=/opt/mac-mcp/venv/bin/mac-mcp --config /etc/mac-mcp/config.yaml --ui headless
Restart=always
RestartSec=10

# Resource limits
MemoryMax=2G
CPUQuota=200%

# Security
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/var/lib/mac-mcp

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mac-mcp
sudo systemctl start mac-mcp
sudo journalctl -u mac-mcp -f  # View logs
```

## Docker Deployment

**Dockerfile**:
```dockerfile
FROM python:3.12-slim
RUN useradd -m mac-mcp
WORKDIR /app
COPY . .
RUN pip install .
USER mac-mcp
CMD ["mac-mcp", "--config", "/etc/mac-mcp/config.yaml", "--ui", "headless"]
```

**Run**:
```bash
docker build -t mac-mcp .
docker run -d \
    -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
    -v /var/lib/mac-mcp:/var/lib/mac-mcp \
    mac-mcp
```

## Monitoring

### Logging

Configure structured logging:
```yaml
logging:
  level: INFO
  format: json
  output: stdout
```

### Health Checks

```bash
systemctl status mac-mcp
ls -lh /var/lib/mac-mcp/events.jsonl
```

## Performance Tuning

### Resource Limits

> **Note**: These configuration options are planned for v0.2.0.

```yaml
# Planned for v0.2.0
orchestrator:
  max_goals: 100
  max_tasks_per_goal: 50
  event_buffer_size: 1000
```

### LLM Rate Limiting

> **Note**: Rate limiting configuration is planned for v0.2.0. Currently, rate limits are handled by the LLM provider's SDK (Anthropic/Bedrock).

For manual rate limiting in v0.1.0, control request frequency via `server.heartbeat_interval` and agent concurrency settings.

## Backups

**Backup script** (`/usr/local/bin/backup-mac-mcp.sh`):
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/mac-mcp"
mkdir -p "$BACKUP_DIR"
cp /var/lib/mac-mcp/events.jsonl "$BACKUP_DIR/events_$DATE.jsonl"
find "$BACKUP_DIR" -name "*.jsonl" -mtime +7 -exec gzip {} \;
find "$BACKUP_DIR" -name "*.jsonl.gz" -mtime +30 -delete
```

**Cron** (every 6 hours):
```bash
0 */6 * * * /usr/local/bin/backup-mac-mcp.sh
```

## Scaling

### Current Capacity (v0.1.0)

| Workload | CPU | Memory | Storage |
|----------|-----|--------|---------|
| Light (<10 goals/hr) | 1 core | 512MB | 1GB |
| Medium (10-50 goals/hr) | 2 cores | 2GB | 10GB |
| Heavy (50-100 goals/hr) | 4 cores | 4GB | 50GB |

**Limitations**: Single instance only (distributed in v2.0)

## Troubleshooting

**LLM API failures**:
```bash
curl https://api.anthropic.com/v1/messages -H "x-api-key: $ANTHROPIC_API_KEY"
```

**Event log corruption**:
```bash
python -c "import json; [json.loads(line) for line in open('/var/lib/mac-mcp/events.jsonl')]"
```

**High memory**: Check event count, consider snapshotting (v0.2.0+)

## Advanced Deployments

- **Kubernetes**: See [k8s-deployment](https://github.com/yourusername/mac-mcp/tree/main/deployments/kubernetes) (future)
- **AWS/GCP/Azure**: Cloud-specific guides (future)
- **High Availability**: Distributed orchestrator (v2.0)

---

**Version**: v0.1.0
**Status**: Production-ready for single-instance deployments
