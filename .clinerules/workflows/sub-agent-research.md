# Sub-Agent Research Workflow

Delegate large-scale research and exploration to focused Cline CLI agents.

## When to Use Sub-Agents

**Use sub-agents when you need to:**
- Explore >10 files across the codebase
- Perform pattern searches and analysis
- Research dependencies and their usage
- Trace execution flows through multiple modules
- Gather context before making changes
- Analyze architecture and relationships

**Do NOT use sub-agents for:**
- Code editing (use main agent for this)
- Single file operations
- Simple searches (<5 files)
- Tasks requiring tool execution

## Sub-Agent Command Syntax

```bash
cline "your focused research prompt here"
```

## Effective Sub-Agent Prompts

### Pattern: Focused Research Question

**Good:**
```bash
cline "Find all async functions that use blocking I/O (open, requests, time.sleep) and list the file paths and function names"
```

**Bad:**
```bash
cline "Look at the code"  # Too vague
```

### Pattern: Architectural Investigation

**Good:**
```bash
cline "Reverse trace the event flow from TaskCreatedEvent through the orchestrator to agent registration. List all classes and methods involved with their file paths"
```

**Bad:**
```bash
cline "How does the orchestrator work?"  # Too broad
```

### Pattern: Dependency Analysis

**Good:**
```bash
cline "Find all usages of the Decomposer class. For each usage, show the file path, line number, and immediate context (3 lines before/after)"
```

**Bad:**
```bash
cline "Where is Decomposer used?"  # Lacks specificity on what output format is needed
```

### Pattern: Code Quality Audit

**Good:**
```bash
cline "Find all Pydantic models without frozen=True. List model name, file path, and whether they're used in event sourcing (check for BaseEvent inheritance)"
```

**Bad:**
```bash
cline "Check for mutable models"  # Missing context about what to check and why
```

## Workflow Steps

### Step 1: Define Research Objective

Be crystal clear about what you need to know:

```xml
<ask_followup_question>
<question>What specific information are you looking for?

Good research objectives:
- "Find all functions that could benefit from async conversion"
- "Map all dependencies of the Orchestrator class"
- "List all TODO/FIXME comments with context"
- "Identify all places where error handling could be improved"</question>
</ask_followup_question>
```

### Step 2: Craft Specific Prompt

**Template:**
```
Action: [Find/List/Trace/Analyze/Identify]
Target: [What you're looking for]
Scope: [Where to look]
Output Format: [How to present findings]
Context: [Why this matters (optional)]
```

**Example:**
```bash
cline "Find all class methods in src/mac_mcp/core/ that are longer than 50 lines. List class name, method name, file path, and line count. Sort by line count descending"
```

### Step 3: Execute Research

Run the cline command and wait for results:

```xml
<execute_command>
<command>cline "your research prompt"</command>
<requires_approval>false</requires_approval>
</execute_command>
```

### Step 4: Analyze Results

Review sub-agent findings and synthesize insights:

**Ask yourself:**
- Does this answer my research question?
- Do I need more specific information?
- Should I refine the prompt and re-run?
- What actions should I take based on findings?

### Step 5: Take Action

Based on sub-agent research, proceed with main task:

```xml
<read_file>
<path>file/identified/by/subagent.py</path>
</read_file>
```

Or make informed edits:

```xml
<replace_in_file>
<path>file/path.py</path>
<diff>...</diff>
</replace_in_file>
```

## Example Workflows

### Research Before Refactoring

**Goal:** Understand all usages before refactoring a function

```bash
# Step 1: Find all call sites
cline "Find all calls to process_event() in the codebase. For each call, show file path, function name where it's called, and the 2 lines before and after the call"

# Step 2: Analyze patterns
cline "In the previous results, identify common patterns in how process_event() is called. Are there any error handling patterns? Any common parameter combinations?"

# Step 3: Check test coverage
cline "Find all tests that call process_event(). List test file, test function name, and what aspects they're testing"
```

### Dependency Impact Analysis

**Goal:** Understand impact of changing an interface

```bash
# Step 1: Map direct dependencies
cline "Find all classes that import or use EventStore. List class name, file path, and which EventStore methods they call"

# Step 2: Find transitive dependencies
cline "For each class from the previous results, find what other classes depend on them. Create a dependency tree"

# Step 3: Identify breaking changes
cline "Review the dependency tree and identify which components would be affected if EventStore.append() signature changed"
```

### Code Quality Audit

**Goal:** Find areas needing improvement

```bash
# Step 1: Find complexity hotspots
cline "Find all functions with cyclomatic complexity >10 using mental analysis of nested conditionals and loops. List function name, file path, estimated complexity score, and brief description of what makes it complex"

# Step 2: Find missing tests
cline "Compare src/ directory structure with tests/ directory. List all modules in src/ that don't have corresponding test files"

# Step 3: Find TODO/FIXME items
cline "Find all TODO, FIXME, HACK, or XXX comments in src/. For each, show file path, line number, full comment text, and brief context of surrounding code"
```

### Architecture Investigation

**Goal:** Understand system design

```bash
# Step 1: Map main components
cline "List all classes in src/mac_mcp/core/ with their primary responsibilities based on class docstrings and main methods"

# Step 2: Identify communication patterns
cline "Find how Orchestrator, Supervisor, and Decomposer communicate. Show all method calls between these classes with their parameters"

# Step 3: Trace data flow
cline "Trace how a TaskCreatedEvent flows through the system from creation to storage. List each handler, method, and transformation it goes through"
```

## Tips for Effective Sub-Agent Use

### 1. Be Specific About Output Format

**Good:**
```bash
cline "Find async functions in src/core/. Output format:
- File: path/to/file.py
- Function: function_name
- Line: 123
- Has await: Yes/No"
```

**Bad:**
```bash
cline "Find async functions"  # Unclear what format you want
```

### 2. Request Summary and Details

```bash
cline "Find all database queries in src/. First provide a summary (total count, most common patterns). Then list each query with file path and context"
```

### 3. Ask for Prioritization

```bash
cline "Find security issues in src/. Rank by severity (Critical/High/Medium/Low) and for each show file path, issue description, and recommended fix"
```

### 4. Provide Context for Better Analysis

```bash
cline "Find all mutable Pydantic models in src/domain/. Context: We use event sourcing, so domain models should be immutable (frozen=True). List models that violate this and explain why it's problematic"
```

### 5. Chain Multiple Sub-Agents

For complex research, use multiple focused agents:

```bash
# Agent 1: Broad sweep
cline "List all .py files in src/ with their primary purpose (1 sentence each)"

# Agent 2: Deep dive based on Agent 1 results
cline "For the event handling files identified, analyze the error handling patterns used"

# Agent 3: Recommendations based on Agent 2
cline "Based on the error handling analysis, what inconsistencies exist and what standard pattern should we adopt?"
```

## Integration with Main Workflow

Sub-agents complement main agent workflow:

```
[User Request]
    ↓
[Main Agent: Understand request]
    ↓
[Decision: Need research?]
    ↓ Yes
[Sub-Agent: Focused research]
    ↓
[Sub-Agent: Returns findings]
    ↓
[Main Agent: Analyze findings]
    ↓
[Main Agent: Take action]
    ↓
[Main Agent: Validate results]
```

## Common Sub-Agent Patterns

### 1. The Explorer
Broad investigation to understand unknown territory:
```bash
cline "Explore src/mcp/ directory. For each file, provide: file purpose, main classes/functions, dependencies, and how it fits into the overall MCP architecture"
```

### 2. The Validator
Check for specific patterns or violations:
```bash
cline "Validate that all async functions in src/ use only async I/O operations. Flag any that use blocking operations like open(), requests.get(), or time.sleep()"
```

### 3. The Tracer
Follow execution paths:
```bash
cline "Trace the complete lifecycle of a Goal from submission to completion. Show each state transition, which components are involved, and what events are emitted"
```

### 4. The Auditor
Review code for quality issues:
```bash
cline "Audit error handling in src/core/. Check: 1) Are exceptions logged? 2) Are resources cleaned up? 3) Are errors propagated appropriately? Provide findings with examples"
```

### 5. The Mapper
Create comprehensive overviews:
```bash
cline "Create a map of all external dependencies in src/. For each dependency (aiofiles, pydantic, etc.), list which modules use it and for what purpose"
```

## Troubleshooting Sub-Agents

### Sub-agent returns incomplete results

**Solution:** Make prompt more specific:
```bash
# Before
cline "Find errors"

# After  
cline "Find all try/except blocks in src/. For each, show file path, line number, exception type caught, and whether it's logged"
```

### Sub-agent takes too long

**Solution:** Narrow the scope:
```bash
# Before
cline "Analyze all code"

# After
cline "Analyze only src/core/orchestrator.py"
```

### Sub-agent provides irrelevant information

**Solution:** Add constraints:
```bash
cline "Find TODO comments in src/ (exclude tests/ and docs/). Only show TODOs related to performance or security"
```

## Related Documentation

- Code Patterns: `.clinerules/rules/reference/code-patterns.md`
- Quality Procedures: `.clinerules/rules/core/quality-procedures.md`
- Cline CLI: [Cline CLI Documentation](https://docs.cline.bot/cline-cli/overview)
