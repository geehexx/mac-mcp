# Expert Review Panel Protocol

## Core Principle
Multi-agent debate improves factuality and reasoning. 2-3 rounds typically achieve consensus. Sparse communication enables deeper deliberation.

## When to Convene
**Mandatory**: Before implementation | Every 200+ lines | Before commit | Integration | Security/performance
**Skip**: Trivial (<10 lines, formatting, typos) | Documentation-only

## Protocol

### 1. Generate Experts (2-5)
**Include**: Name + Industry/Company + 1-2 sentence background (23% specificity increase)

**Example**:
```
Task: Implement caching
Experts:
- Dr. Sarah Chen, Performance Engineer at Netflix (12 years optimizing caching at scale)
- Marcus Rodriguez, Security Specialist at AWS (expert in cache poisoning prevention)
- Aisha Patel, Database Architect at Stripe (designed Redis infrastructure)
```

**Requirements**: Specific titles, domain expertise, diverse perspectives, include skeptic for complex decisions, rotate 1-2 between sessions

### 2. Ground with Research
Each expert receives 1-3 sentence briefing from web search:

```python
brave_web_search(
    query="Redis vs Memcached performance benchmarks",
    goggles=["https://gist.githubusercontent.com/.../ai-coding-agent-goggle.txt"],
    count=5
)
# Synthesize: "Redis 20% faster for complex structures. LRU eviction standard. TTL-based invalidation reduces stale data 80%."
```

**Output**: `Performance Engineer (Briefing: Redis 20% faster...)`

### 3. Multi-Round Debate
1. Each expert provides feedback from their perspective
2. Identify disagreements and critical issues
3. Agent synthesizes and provides context
4. Experts respond to synthesis and each other
5. Repeat until consensus

**Consensus**: All approve OR no new critical issues for 2 rounds OR max 3 rounds (standard) / unlimited (comprehensive)

### 4. Rotate Experts
Rotate 1-2 experts between sessions for fresh perspective. Replace non-productive or overly agreeable experts mid-debate.

## Output Format

**Standard Mode** (3 rounds max):
```markdown
### Expert Review Panel (Session X, Round Y / Max 3)

**Task**: [1-sentence description]

**Panelists**:
- Performance Engineer (Briefing: Redis 20% faster for complex structures)
- Security Specialist (Briefing: Cache poisoning via timing attacks. Require auth + TLS)

#### Performance Engineer's Feedback
Use Redis with LRU eviction policy.
* Action: Set maxmemory-policy=allkeys-lru

#### Security Specialist's Feedback
CRITICAL - No authentication configured.
* Action: Add requirepass and enable TLS

**Agent Synthesis**: Will add Redis auth and TLS. Performance config approved. TTL strategy concerns?

**Status**: Proceeding to Round 2
```

**Unlimited Mode** (comprehensive review):
```markdown
### Expert Review Panel - Unlimited Debate (Round X)

**Critical Issues** (require action):
1. Issue description + specific action
2. Issue description + specific action

**Consensus Items** (approved):
✅ Item 1, Item 2, Item 3

**Status**: [Continuing | Consensus Reached | Diminishing Returns]
```

## Best Practices
- Specific titles and domains
- Rotate experts between sessions
- Include diverse perspectives
- Current sources (2023+) for briefings
- Actionable recommendations (1-3 sentences)
- Concise summaries for consensus
- Detail only for critical issues/disagreements
- Stop at consensus (not perfection)

## Common Pitfalls
- Too many experts (>5): diminishing returns
- Generic experts without domain specificity
- No research briefings (generic advice)
- Ignoring feedback
- Endless debate (3 rounds max for standard, stop at diminishing returns for unlimited)
