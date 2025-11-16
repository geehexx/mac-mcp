# Expert Panel Review - Round 2
## Deep Dive: Critical Issues and Architecture Design

**Date**: November 16, 2025  
**Review Type**: Unlimited Rounds - Deep Dive  
**Focus**: Authentication, Security, Snapshot Automation, Agent Failover

---

## Panel Members (Round 2)

**Retained** (5 experts):
1. **Dr. Sarah Chen** - Multi-Agent Systems (Agent failover, load balancing)
2. **Marcus Rodriguez** - Event Sourcing (Snapshot automation, schema versioning)
3. **Dr. Aisha Patel** - MCP Protocol (Auth architecture, consent flows)
4. **Dr. Robert Chang** - Security (Auth/authz implementation)
5. **Yuki Tanaka** - Performance (Snapshot optimization)

**Rotated IN** (2 new experts):
6. **Dr. Li Wei** - Distributed Systems Architect (Google Cloud, consensus protocols)
   - *Briefing*: Agent coordination at scale requires consensus protocols (Raft, Paxos), circuit breakers, timeout strategies
7. **Maria Santos** - Auth/Identity Engineer (Okta, OAuth 2.1 implementation expert)
   - *Briefing*: OAuth 2.1 best practices 2025: PKCE required, refresh token rotation, JWT short-lived (1hr), Resource Indicators (RFC 8707)

**Rotated OUT**: James Kim (Python), Elena Kowalski (DX) - issues addressed, will return for final review

---

## Round 2 Agenda

1. **Authentication Architecture Design** (P0)
2. **Snapshot Automation Implementation** (P1)
3. **Agent Failover Mechanism** (P1)
4. **Event Schema Versioning Strategy** (P2)
5. **Performance Optimization Plan** (P2)

---

## Issue 1: Authentication Architecture Design

### Current State
- **No authentication whatsoever**
- Anyone can call any MCP tool
- No agent identity verification
- No access control

### Expert Discussion

**Dr. Robert Chang (Security)**:
"We need a pragmatic approach. For alpha/v0.1.0, I recommend API key authentication as interim solution. Full OAuth 2.1 can wait for v0.2.0."

**Proposed Alpha Solution (v0.1.0)**:
```python
# Simple API key auth for alpha
class APIKeyAuth:
    def __init__(self, valid_keys: dict[str, str]):
        self.valid_keys = valid_keys  # key → agent_id
    
    async def validate(self, api_key: str) -> str | None:
        """Return agent_id if valid, None otherwise."""
        return self.valid_keys.get(api_key)

# In MCP server middleware
@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    api_key = arguments.get("api_key")
    if not api_key:
        return [TextContent(type="text", text="❌ Missing api_key")]
    
    agent_id = await auth.validate(api_key)
    if not agent_id:
        return [TextContent(type="text", text="❌ Invalid api_key")]
    
    # Store authenticated agent_id in context
    arguments["_authenticated_agent_id"] = agent_id
    
    handler = get_handler(name)
    return await handler(orchestrator, arguments)
```

**Maria Santos (Auth Expert)**:
"API keys are acceptable for alpha IF:
1. Generated with sufficient entropy (32+ bytes)
2. Stored securely (hashed with bcrypt)
3. Clearly documented as temporary solution
4. Migration path to OAuth 2.1 planned"

**Proposed v0.2.0 Solution (OAuth 2.1)**:
```python
# JWT-based OAuth 2.1 with Resource Indicators
class OAuth21Auth:
    def __init__(self, jwks_url: str, audience: str):
        self.jwks_url = jwks_url
        self.audience = audience  # Resource Indicator (RFC 8707)
    
    async def validate_token(self, token: str) -> dict[str, Any]:
        """Validate JWT and return claims."""
        # 1. Verify signature using JWKS
        # 2. Verify expiration (max 1hr)
        # 3. Verify audience matches this MCP server
        # 4. Verify issuer is trusted
        # 5. Return claims: {agent_id, capabilities, scope}
        pass
```

**Architecture Decision**:
```
Phase 1 (v0.1.0 - Alpha):
├── API Key Authentication
├── Keys stored in config.yaml (hashed)
├── Per-tool authorization checks
└── Clear documentation: "Alpha security only"

Phase 2 (v0.2.0 - Beta):
├── JWT Bearer tokens (OAuth 2.1)
├── Resource Indicators (RFC 8707)
├── PKCE for public clients
├── Refresh token rotation
└── 1hr access token expiry

Phase 3 (v0.3.0 - Production):
├── Full OAuth 2.1 server integration
├── Rate limiting per agent
├── Audit logging
└── HMAC request signing
```

### Implementation Plan (v0.1.0)

**Files to Create**:
- `src/mac_mcp/auth/__init__.py`
- `src/mac_mcp/auth/api_key.py` - APIKeyAuth class
- `src/mac_mcp/auth/middleware.py` - Auth middleware

**Files to Modify**:
- `src/mac_mcp/mcp/server.py` - Add auth middleware
- `src/mac_mcp/mcp/handlers.py` - Add authorization checks
- `src/mac_mcp/config.py` - Add auth config section

**Testing**:
- `tests/unit/test_auth.py` - API key validation
- `tests/integration/test_auth_flow.py` - End-to-end auth

**Documentation**:
- Add "Security" section to README warning about alpha auth
- Update ROADMAP with OAuth 2.1 timeline

**Panel Consensus**: ✅ **APPROVED** - API key auth sufficient for alpha

---

## Issue 2: Authorization (Access Control)

### Current State
- Any authenticated agent can do anything
- Agent A can complete Agent B's tasks
- No permission boundaries

### Expert Discussion

**Dr. Robert Chang**:
"Authorization is simpler than authentication. Agent-scoped permissions: agent can only act on tasks assigned to them."

**Proposed Solution**:
```python
# In handlers.py
async def handle_complete_task(
    orchestrator: Orchestrator,
    arguments: dict[str, Any],
) -> list[TextContent]:
    task_id = arguments["task_id"]
    agent_id_from_request = arguments["agent_id"]
    authenticated_agent_id = arguments["_authenticated_agent_id"]
    
    # Authorization check: agent can only complete own tasks
    if agent_id_from_request != authenticated_agent_id:
        return [TextContent(
            type="text",
            text=f"❌ Authorization error: Agent {authenticated_agent_id} "
                 f"cannot act as agent {agent_id_from_request}"
        )]
    
    task = orchestrator.get_task(task_id)
    if task.assigned_agent != authenticated_agent_id:
        return [TextContent(
            type="text",
            text=f"❌ Authorization error: Task {task_id} is not assigned to you"
        )]
    
    # Proceed with completion
    await orchestrator.complete_task(task_id, authenticated_agent_id, ...)
```

**Authorization Matrix**:
| Tool | Authorization Rule |
|------|-------------------|
| `submit_goal` | Any authenticated user (for now) |
| `register_agent` | agent_id in request must match authenticated agent |
| `claim_task` | agent_id must match authenticated agent |
| `report_progress` | Task must be assigned to authenticated agent |
| `complete_task` | Task must be assigned to authenticated agent |
| `fail_task` | Task must be assigned to authenticated agent |
| `request_dependency` | Task requesting dependency must be assigned to authenticated agent |
| `heartbeat` | agent_id must match authenticated agent |

**Panel Consensus**: ✅ **APPROVED** - Implement agent-scoped permissions

---

## Issue 3: Snapshot Automation

### Current State
- Snapshot base class exists
- Methods defined but never called
- Event log grows unbounded
- Startup time O(N) where N = total events

### Expert Discussion

**Marcus Rodriguez (Event Sourcing)**:
"Standard pattern: snapshot every 1000 events. Store latest snapshot + events since snapshot. Startup becomes O(M) where M < 1000."

**Yuki Tanaka (Performance)**:
"Snapshot overhead is minimal. Serializing 10K tasks takes ~50ms. Worth it for 30s → 1s startup time improvement."

**Implementation Design**:
```python
# In jsonl.py
class JSONLEventStore(EventStore):
    def __init__(self, path: Path, snapshot_interval: int = 1000):
        self.path = path
        self.snapshot_path = path.parent / f"{path.stem}.snapshot"
        self.snapshot_interval = snapshot_interval
        self._events_since_snapshot = 0
    
    async def append(self, event: Event) -> None:
        # Write event
        async with aiofiles.open(self.path, "a") as f:
            await f.write(event.model_dump_json() + "\n")
        
        self._events_since_snapshot += 1
        
        # Check if snapshot needed
        if self._events_since_snapshot >= self.snapshot_interval:
            await self._create_snapshot()
    
    async def _create_snapshot(self) -> None:
        """Create snapshot of current state."""
        # Collect current state from orchestrator
        state = {
            "sequence": self._sequence,
            "timestamp": datetime.now(UTC).isoformat(),
            "tasks": {id: task.model_dump() for id, task in orchestrator._tasks.items()},
            "goals": {id: goal.model_dump() for id, goal in orchestrator._goals.items()},
            "agents": {id: agent.model_dump() for id, agent in supervisor.agents.items()},
        }
        
        # Write snapshot atomically
        temp_path = self.snapshot_path.with_suffix(".tmp")
        async with aiofiles.open(temp_path, "w") as f:
            await f.write(json.dumps(state))
        
        # Atomic rename
        temp_path.rename(self.snapshot_path)
        
        self._events_since_snapshot = 0
    
    async def load_snapshot(self) -> dict[str, Any] | None:
        """Load latest snapshot if exists."""
        if not self.snapshot_path.exists():
            return None
        
        async with aiofiles.open(self.snapshot_path) as f:
            content = await f.read()
            return json.loads(content)
    
    async def read(self) -> AsyncIterator[Event]:
        """Read events, starting from snapshot if available."""
        # Load snapshot first
        snapshot = await self.load_snapshot()
        if snapshot:
            # Yield synthetic "snapshot loaded" event
            yield SnapshotLoadedEvent(
                sequence=snapshot["sequence"],
                timestamp=snapshot["timestamp"],
                payload=snapshot,
            )
        
        # Then yield events since snapshot
        snapshot_seq = snapshot["sequence"] if snapshot else -1
        async with aiofiles.open(self.path) as f:
            async for line in f:
                event = Event.model_validate_json(line)
                if event.sequence > snapshot_seq:
                    yield event
```

**Orchestrator Integration**:
```python
# In orchestrator.py
async def rebuild_from_events(self) -> None:
    """Rebuild state from snapshot + events."""
    self._tasks.clear()
    self._goals.clear()
    
    async for event in self.event_store.read():
        if event.type == EventType.SNAPSHOT_LOADED:
            # Restore state from snapshot
            self._load_from_snapshot(event.payload)
        else:
            # Apply incremental event
            await self._apply_event(event)

def _load_from_snapshot(self, snapshot: dict[str, Any]) -> None:
    """Load state from snapshot."""
    for task_data in snapshot["tasks"].values():
        task = Task.model_validate(task_data)
        self._tasks[task.id] = task
    
    for goal_data in snapshot["goals"].values():
        goal = Goal.model_validate(goal_data)
        self._goals[goal.id] = goal
    
    # Restore supervisor state
    for agent_data in snapshot["agents"].values():
        agent = Agent.model_validate(agent_data)
        self.supervisor.agents[agent.id] = agent
```

**Performance Impact**:
- **Before**: Startup reads all 10K events = ~30 seconds
- **After**: Startup reads 1 snapshot + <1000 events = ~1 second
- **30x improvement** ✅

**Panel Consensus**: ✅ **APPROVED** - Implement snapshot automation in v0.2.0

---

## Issue 4: Agent Failover Mechanism

### Current State
- Agent timeout detected (90s since last heartbeat)
- Task stuck in RUNNING state forever
- No automatic recovery

### Expert Discussion

**Dr. Sarah Chen (Multi-Agent)**:
"Failover is critical for reliability. When agent times out, task should be reset to PENDING for reassignment."

**Dr. Li Wei (Distributed Systems)**:
"Need circuit breaker pattern. After 3 consecutive failures, agent quarantined. Exponential backoff before allowing back."

**Implementation Design**:
```python
# In supervisor.py
class AgentSupervisor:
    async def check_timeouts(self) -> list[str]:
        """Check for timed-out agents, return list of timed-out agent IDs."""
        now = datetime.now(UTC)
        timed_out = []
        
        for agent in self.agents.values():
            if agent.status == AgentStatus.ACTIVE:
                time_since_heartbeat = (now - agent.last_heartbeat).total_seconds()
                
                if time_since_heartbeat > self.heartbeat_timeout:
                    # Agent timed out
                    timed_out.append(agent.id)
                    
                    # Mark agent as failed
                    agent.status = AgentStatus.FAILED
                    agent.failure_count += 1
                    
                    # Circuit breaker: quarantine after 3 failures
                    if agent.failure_count >= 3:
                        agent.status = AgentStatus.QUARANTINED
                    
                    # Emit event
                    await self.event_publisher.publish(
                        AgentFailedEvent,
                        agent_id=agent.id,
                        payload={
                            "reason": "heartbeat_timeout",
                            "last_heartbeat": agent.last_heartbeat.isoformat(),
                        },
                    )
        
        return timed_out

# In orchestrator.py
async def handle_agent_timeout(self, agent_id: str) -> None:
    """Handle agent timeout by reassigning tasks."""
    # Find all tasks assigned to failed agent
    failed_tasks = [
        task for task in self._tasks.values()
        if task.assigned_agent == agent_id and task.state == TaskState.RUNNING
    ]
    
    for task in failed_tasks:
        # Reset task to PENDING
        task.state = TaskState.PENDING
        task.assigned_agent = None
        task.metadata["retry_count"] = task.metadata.get("retry_count", 0) + 1
        task.metadata["previous_agent"] = agent_id
        
        # Emit event
        await self.event_publisher.publish(
            TaskFailedEvent,
            task_id=task.id,
            agent_id=agent_id,
            payload={
                "error": {
                    "type": "agent_timeout",
                    "message": f"Agent {agent_id} timed out",
                    "retryable": True,
                },
                "retry_count": task.metadata["retry_count"],
            },
        )

# Background task to check timeouts
async def timeout_checker_loop(orchestrator: Orchestrator, interval: int = 30):
    """Background task to check for agent timeouts."""
    while True:
        await asyncio.sleep(interval)
        
        timed_out_agents = await orchestrator.supervisor.check_timeouts()
        
        for agent_id in timed_out_agents:
            await orchestrator.handle_agent_timeout(agent_id)
```

**Circuit Breaker Logic**:
```python
class Agent(BaseModel):
    failure_count: int = 0
    quarantine_until: datetime | None = None
    
    def is_quarantined(self) -> bool:
        """Check if agent is currently quarantined."""
        if self.status != AgentStatus.QUARANTINED:
            return False
        
        if self.quarantine_until and datetime.now(UTC) > self.quarantine_until:
            # Quarantine period over
            self.status = AgentStatus.INACTIVE
            self.failure_count = 0
            return False
        
        return True
    
    def quarantine(self, duration_seconds: int = 300) -> None:
        """Quarantine agent for specified duration."""
        self.status = AgentStatus.QUARANTINED
        self.quarantine_until = datetime.now(UTC) + timedelta(seconds=duration_seconds)
```

**Exponential Backoff**:
- 1st failure: 5 min quarantine
- 2nd failure: 15 min quarantine
- 3rd+ failure: 60 min quarantine

**Panel Consensus**: ✅ **APPROVED** - Implement agent failover in v0.2.0

---

## Issue 5: Event Schema Versioning

### Current State
- No version field in events
- Schema changes will break event replay
- No migration strategy

### Expert Discussion

**Marcus Rodriguez**:
"Add schema_version field NOW (v0.1.0) even if we only have version 1. Easier to add field when log is small than migrate millions of events later."

**Implementation**:
```python
# In events.py
class Event(BaseModel):
    type: EventType
    schema_version: int = 1  # Add now
    timestamp: datetime
    sequence: int
    # ... rest of fields

# Event upcasters for future migrations
class EventUpcaster:
    """Migrate events from older schema versions."""
    
    @staticmethod
    def upcast(event_dict: dict[str, Any]) -> dict[str, Any]:
        """Upcast event to latest schema version."""
        version = event_dict.get("schema_version", 1)
        
        # Apply migrations sequentially
        if version < 2:
            event_dict = EventUpcaster._v1_to_v2(event_dict)
        if version < 3:
            event_dict = EventUpcaster._v2_to_v3(event_dict)
        
        return event_dict
    
    @staticmethod
    def _v1_to_v2(event_dict: dict[str, Any]) -> dict[str, Any]:
        """Migrate v1 → v2 (example for future use)."""
        # Example: rename field
        # event_dict["new_field"] = event_dict.pop("old_field")
        event_dict["schema_version"] = 2
        return event_dict
```

**Panel Consensus**: ✅ **APPROVED** - Add schema_version in v0.1.0

---

## Issue 6: Rate Limiting

### Current State
- No rate limits
- Agent can spam requests
- DoS attack vector

### Expert Discussion

**Dr. Robert Chang**:
"Rate limiting is essential for security and cost control. Per-agent limits prevent abuse."

**Maria Santos**:
"Standard practice: 1000 req/hr per agent for normal ops. Burst allowance of 100 req/min."

**Implementation**:
```python
# In auth/rate_limiter.py
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(
        self,
        requests_per_hour: int = 1000,
        requests_per_minute: int = 100,
    ):
        self.requests_per_hour = requests_per_hour
        self.requests_per_minute = requests_per_minute
        
        # Track requests per agent
        self._hourly_counts: dict[str, list[datetime]] = defaultdict(list)
        self._minute_counts: dict[str, list[datetime]] = defaultdict(list)
    
    async def check_limit(self, agent_id: str) -> tuple[bool, str]:
        """Check if agent is within rate limits.
        
        Returns:
            (allowed, reason) tuple
        """
        now = datetime.now(UTC)
        
        # Clean old timestamps
        hour_ago = now - timedelta(hours=1)
        minute_ago = now - timedelta(minutes=1)
        
        self._hourly_counts[agent_id] = [
            ts for ts in self._hourly_counts[agent_id] if ts > hour_ago
        ]
        self._minute_counts[agent_id] = [
            ts for ts in self._minute_counts[agent_id] if ts > minute_ago
        ]
        
        # Check limits
        if len(self._hourly_counts[agent_id]) >= self.requests_per_hour:
            return False, f"Hourly limit exceeded ({self.requests_per_hour} req/hr)"
        
        if len(self._minute_counts[agent_id]) >= self.requests_per_minute:
            return False, f"Burst limit exceeded ({self.requests_per_minute} req/min)"
        
        # Record this request
        self._hourly_counts[agent_id].append(now)
        self._minute_counts[agent_id].append(now)
        
        return True, ""

# In MCP server middleware
rate_limiter = RateLimiter()

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    # ... auth checks ...
    
    # Rate limit check
    allowed, reason = await rate_limiter.check_limit(authenticated_agent_id)
    if not allowed:
        return [TextContent(
            type="text",
            text=f"❌ Rate limit exceeded: {reason}. Try again later."
        )]
    
    # ... proceed with tool call ...
```

**Panel Consensus**: ✅ **APPROVED** - Implement rate limiting in v0.2.0

---

## Round 2 Summary

### Decisions Made

**v0.1.0 (Alpha) - Immediate**:
1. ✅ API key authentication (interim solution)
2. ✅ Agent-scoped authorization
3. ✅ Add schema_version field to events
4. ✅ Clear security disclaimers in README
5. ✅ Update ROADMAP with security timeline

**v0.2.0 (Beta) - Q1 2026**:
6. ✅ Snapshot automation (every 1000 events)
7. ✅ Agent failover with circuit breaker
8. ✅ Rate limiting (1000/hr, 100/min)
9. ✅ Event upcaster framework
10. ✅ OAuth 2.1 preparation

**Implementation Priority**:
- **P0**: API key auth, agent authorization, security docs
- **P1**: Snapshot automation, agent failover, rate limiting
- **P2**: OAuth 2.1, upcasters, advanced monitoring

### Metrics for Success

**Security**:
- Zero unauthorized access (with API keys)
- 100% of tool calls authenticated
- Agent-scoped permissions enforced

**Performance**:
- Startup <5s for 10K events (with snapshots)
- Event persistence <100ms p95
- Task assignment <200ms p95

**Reliability**:
- Agent failure detected within 90s
- Task reassignment within 120s of failure
- 99.9% uptime SLA

---

## Next Round: Implementation Review

For Round 3, we'll:
1. Review concrete implementation PRs
2. Validate security architecture
3. Performance benchmarks
4. Integration testing results

**Panel will continue with same members** for implementation review.
