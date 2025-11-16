# Production Deployment Guide

Guide for deploying MAC MCP Server in production environments with best practices for security, reliability, and scalability.

---

## 📋 Prerequisites

### System Requirements

- **Python**: 3.12+ (required)
- **Memory**: Minimum 512MB, recommended 2GB+
- **Storage**: 1GB+ for event logs (JSONL)
- **CPU**: 1+ cores (2+ recommended for concurrent operations)

### External Dependencies

- **LLM Provider**: Anthropic API key OR AWS Bedrock access
- **Event Storage**: Local filesystem OR compatible storage backend
- **Network**: Stable connection for LLM API calls

---

## 🔐 Security Configuration

### 1. API Key Management

**Environment Variables** (Recommended):
```bash
# Set in production environment
export ANTHROPIC_API_KEY="your-key-here"
export MAC_MCP_EVENT_STORE_PATH="/var/lib/mac-mcp/events.jsonl"
```

**Secrets Management**:
```yaml
# config.yaml - Use environment variable substitution
llm:
  provider: anthropic
  api_key: ${ANTHROPIC_API_KEY}  # Read from environment
  model: claude-sonnet-4-5-20250929
```

**AWS Secrets Manager** (for Bedrock):
```python
import boto3
import json

def get_bedrock_config():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    secret = client.get_secret_value(SecretId='mac-mcp/bedrock')
    return json.loads(secret['SecretString'])
```

### 2. File Permissions

**Event Log Security**:
```bash
# Create restricted directory for event logs
sudo mkdir -p /var/lib/mac-mcp
sudo chown mac-mcp:mac-mcp /var/lib/mac-mcp
sudo chmod 700 /var/lib/mac-mcp

# Secure event log file
sudo touch /var/lib/mac-mcp/events.jsonl
sudo chmod 600 /var/lib/mac-mcp/events.jsonl
```

### 3. Network Security

**Firewall Rules** (if using HTTP transport):
```bash
# Allow only specific IPs to connect
sudo ufw allow from 10.0.0.0/24 to any port 3000
sudo ufw deny 3000
```

---

## 🚀 Deployment Methods

### Method 1: Systemd Service (Linux)

**1. Create Service File**:
```bash
sudo nano /etc/systemd/system/mac-mcp.service
```

**Service Configuration**:
```ini
[Unit]
Description=MAC MCP Server
After=network.target

[Service]
Type=simple
User=mac-mcp
Group=mac-mcp
WorkingDirectory=/opt/mac-mcp
Environment="ANTHROPIC_API_KEY=your-key-here"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/mac-mcp/venv/bin/mac-mcp --config /etc/mac-mcp/config.yaml --ui headless
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
MemoryMax=2G
CPUQuota=200%

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/mac-mcp

[Install]
WantedBy=multi-user.target
```

**2. Enable and Start**:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable on boot
sudo systemctl enable mac-mcp

# Start service
sudo systemctl start mac-mcp

# Check status
sudo systemctl status mac-mcp

# View logs
sudo journalctl -u mac-mcp -f
```

---

### Method 2: Docker Container

**1. Create Dockerfile**:
```dockerfile
FROM python:3.12-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 mac-mcp

# Set working directory
WORKDIR /app

# Copy requirements
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy application
COPY src/ ./src/
COPY config.example.yaml /etc/mac-mcp/config.yaml

# Create data directory
RUN mkdir -p /var/lib/mac-mcp && \
    chown -R mac-mcp:mac-mcp /var/lib/mac-mcp

# Switch to app user
USER mac-mcp

# Expose port (if using HTTP transport)
# EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run server
CMD ["mac-mcp", "--config", "/etc/mac-mcp/config.yaml", "--ui", "headless"]
```

**2. Build and Run**:
```bash
# Build image
docker build -t mac-mcp:latest .

# Run container
docker run -d \
    --name mac-mcp \
    --restart unless-stopped \
    -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
    -v /var/lib/mac-mcp:/var/lib/mac-mcp \
    -v /etc/mac-mcp/config.yaml:/etc/mac-mcp/config.yaml:ro \
    mac-mcp:latest

# View logs
docker logs -f mac-mcp

# Stop container
docker stop mac-mcp
```

**3. Docker Compose**:
```yaml
version: '3.8'

services:
  mac-mcp:
    image: mac-mcp:latest
    container_name: mac-mcp
    restart: unless-stopped
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - PYTHONUNBUFFERED=1
    volumes:
      - /var/lib/mac-mcp:/var/lib/mac-mcp
      - /etc/mac-mcp/config.yaml:/etc/mac-mcp/config.yaml:ro
    # ports:  # Only if using HTTP transport
    #   - "3000:3000"
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

---

### Method 3: Kubernetes Deployment

**1. ConfigMap for Configuration**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mac-mcp-config
  namespace: production
data:
  config.yaml: |
    llm:
      provider: anthropic
      model: claude-sonnet-4-5-20250929
      api_key: ${ANTHROPIC_API_KEY}
    storage:
      type: jsonl
      path: /var/lib/mac-mcp/events.jsonl
    orchestrator:
      max_retries: 3
      timeout_seconds: 300
```

**2. Secret for API Key**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mac-mcp-secrets
  namespace: production
type: Opaque
stringData:
  anthropic-api-key: "your-key-here"
```

**3. Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mac-mcp
  namespace: production
spec:
  replicas: 1  # Single instance (distributed in v2.0)
  selector:
    matchLabels:
      app: mac-mcp
  template:
    metadata:
      labels:
        app: mac-mcp
    spec:
      containers:
      - name: mac-mcp
        image: mac-mcp:latest
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: mac-mcp-secrets
              key: anthropic-api-key
        - name: PYTHONUNBUFFERED
          value: "1"
        volumeMounts:
        - name: config
          mountPath: /etc/mac-mcp
          readOnly: true
        - name: data
          mountPath: /var/lib/mac-mcp
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "import sys; sys.exit(0)"
          initialDelaySeconds: 10
          periodSeconds: 30
      volumes:
      - name: config
        configMap:
          name: mac-mcp-config
      - name: data
        persistentVolumeClaim:
          claimName: mac-mcp-data
```

**4. Persistent Volume Claim**:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mac-mcp-data
  namespace: production
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
```

---

## 📊 Monitoring & Observability

### Logging

**Structured Logging Configuration**:
```yaml
# config.yaml
logging:
  level: INFO
  format: json  # For log aggregation
  output: stdout
```

**Log Rotation** (systemd):
```bash
# /etc/systemd/journald.conf
[Journal]
SystemMaxUse=1G
SystemMaxFileSize=100M
MaxRetentionSec=7day
```

### Health Checks

**HTTP Health Endpoint** (future feature):
```bash
# Check server health
curl http://localhost:3000/health

# Expected response
{"status": "healthy", "uptime": 3600, "event_count": 1234}
```

**Manual Health Check**:
```bash
# Check if process is running
systemctl status mac-mcp

# Check event log is growing
ls -lh /var/lib/mac-mcp/events.jsonl

# Monitor resource usage
top -p $(pgrep -f mac-mcp)
```

---

## 🔧 Performance Tuning

### Event Store Optimization

**Periodic Snapshotting** (v0.2.0+):
```yaml
# config.yaml
storage:
  type: jsonl
  path: /var/lib/mac-mcp/events.jsonl
  snapshot_interval: 1000  # Create snapshot every 1000 events
  snapshot_retention: 5     # Keep last 5 snapshots
```

**Log Rotation**:
```bash
# Rotate large event logs
logrotate -f /etc/logrotate.d/mac-mcp
```

**Logrotate Configuration**:
```
/var/lib/mac-mcp/events.jsonl {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0600 mac-mcp mac-mcp
    postrotate
        systemctl reload mac-mcp
    endscript
}
```

### Resource Limits

**Memory Tuning**:
```yaml
# config.yaml
orchestrator:
  max_goals: 100        # Limit concurrent goals
  max_tasks_per_goal: 50  # Limit task DAG size
  event_buffer_size: 1000  # In-memory event buffer
```

**LLM Rate Limiting**:
```yaml
llm:
  provider: anthropic
  rate_limit:
    requests_per_minute: 50
    retry_on_429: true
    backoff_multiplier: 2
```

---

## 🚨 Error Handling & Recovery

### Automatic Restart

**Systemd Restart Policy**:
```ini
[Service]
Restart=always
RestartSec=10
StartLimitInterval=5min
StartLimitBurst=5
```

### Backup Strategy

**Event Log Backups**:
```bash
#!/bin/bash
# /usr/local/bin/backup-mac-mcp.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/mac-mcp"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup event log
cp /var/lib/mac-mcp/events.jsonl "$BACKUP_DIR/events_$DATE.jsonl"

# Compress old backups
find "$BACKUP_DIR" -name "*.jsonl" -mtime +7 -exec gzip {} \;

# Delete backups older than 30 days
find "$BACKUP_DIR" -name "*.jsonl.gz" -mtime +30 -delete
```

**Cron Job**:
```bash
# Backup every 6 hours
0 */6 * * * /usr/local/bin/backup-mac-mcp.sh
```

---

## 📈 Scalability Considerations

### Current Limitations (v0.1.0)

- ❌ Single orchestrator instance
- ❌ JSONL storage only
- ❌ No horizontal scaling

### Future Scaling (v2.0.0+)

- ✅ Distributed orchestrator (Redis/etcd coordination)
- ✅ Pluggable storage (PostgreSQL, MongoDB, Kafka)
- ✅ Multi-region deployment
- ✅ Load balancing across instances

### Vertical Scaling Guidance

| Workload | CPU | Memory | Storage |
|----------|-----|--------|---------|
| Light (<10 goals/hour) | 1 core | 512MB | 1GB |
| Medium (10-50 goals/hour) | 2 cores | 2GB | 10GB |
| Heavy (50-100 goals/hour) | 4 cores | 4GB | 50GB |
| Very Heavy (100+ goals/hour) | 8+ cores | 8GB+ | 100GB+ |

---

## 🔍 Troubleshooting

### Common Issues

**1. LLM API Failures**:
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Test API connectivity
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

**2. Event Store Corruption**:
```bash
# Validate event log
python -c "
import json
with open('/var/lib/mac-mcp/events.jsonl') as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            print(f'Line {i}: {e}')
"
```

**3. High Memory Usage**:
```bash
# Check event count
wc -l /var/lib/mac-mcp/events.jsonl

# If >10,000 events, consider snapshotting
# (Feature coming in v0.2.0)
```

---

## 📚 Additional Resources

- [Configuration Reference](../reference/configuration.md) (future)
- [Security Hardening Checklist](../reference/security.md) (future)
- [Performance Tuning Guide](../reference/performance.md) (future)
- [Disaster Recovery Plan](../reference/disaster-recovery.md) (future)

---

**Last Updated**: November 16, 2025
**Version**: v0.1.0
**Status**: Production-ready for single-instance deployments
