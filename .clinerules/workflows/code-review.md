# Code Review Workflow

This workflow guides you through a comprehensive code review process.

## Step 1: Understand the Changes

First, identify what needs to be reviewed:

```xml
<ask_followup_question>
<question>What would you like me to review?

Please provide:
- File paths or directories to review
- PR number (if applicable)
- Specific concerns or focus areas
- Context about the changes</question>
<options>["Review specific files", "Review entire PR", "Review recent changes", "Security-focused review"]</options>
</ask_followup_question>
```

## Step 2: Examine the Code

Use appropriate tools to gather context:

```xml
<read_file>
<path>path/to/file.py</path>
</read_file>
```

For pattern searches:

```xml
<search_files>
<path>src/</path>
<regex>pattern to find</regex>
<file_pattern>*.py</file_pattern>
</search_files>
```

## Step 3: Convene Expert Review Panel

For significant changes, use the expert review protocol:

### Generate Domain Experts (2-5)

Create personas with specific expertise relevant to the changes:

**Example for security review:**
```
Experts:
- Dr. Sarah Mitchell, Security Engineer at AWS (15 years in application security, OWASP expert)
- Marcus Chen, DevSecOps Lead at Stripe (specializes in secure Python patterns)
- Aisha Patel, Cryptography Specialist at Google (PhD in applied cryptography)
```

### Ground with Research

For each expert, provide 1-3 sentence briefing from web search:

```xml
<use_mcp_tool>
<server_name>BraveSearch</server_name>
<tool_name>brave_web_search</tool_name>
<arguments>
{
  "query": "Python async security best practices 2024",
  "count": 5
}
</arguments>
</use_mcp_tool>
```

### Multi-Round Debate

Have each expert provide feedback, then synthesize and continue until consensus.

## Step 4: Check Against Quality Standards

Verify the code meets project standards:

**Code Patterns:**
- [ ] Imports organized (stdlib → third-party → local)
- [ ] Type hints use modern syntax (str | None, not Optional[str])
- [ ] Async patterns correct (no blocking I/O)
- [ ] Docstrings present (Google style)

**Event Sourcing (if applicable):**
- [ ] Events are immutable (frozen=True)
- [ ] No side effects in apply_event
- [ ] Append-only pattern maintained

**Testing:**
- [ ] Unit tests present
- [ ] Integration tests for interactions
- [ ] Coverage ≥90%

**Security:**
- [ ] No hardcoded credentials
- [ ] Input validation present
- [ ] No sensitive data in logs

## Step 5: Provide Structured Feedback

Organize feedback into categories:

### Critical Issues
List any blocking issues that must be fixed before merge.

### Suggestions
List improvements that would enhance code quality.

### Positive Observations
Highlight what was done well.

### Questions
List any clarifying questions.

## Step 6: Summary and Recommendation

Provide clear recommendation:

```xml
<attempt_completion>
<result>
## Code Review Summary

**Overall Assessment:** [Approve/Request Changes/Needs Discussion]

**Critical Issues:** [count]
- Issue 1: Description and fix
- Issue 2: Description and fix

**Suggestions:** [count]
- Suggestion 1
- Suggestion 2

**Positive Observations:**
- Well-structured code
- Good test coverage
- Clear documentation

**Recommendation:** [Detailed recommendation with next steps]
</result>
</attempt_completion>
```

## Tips for Effective Reviews

1. **Start broad, then narrow**: Understand overall architecture before diving into details
2. **Use sub-agents for large changes**: Delegate research to Cline CLI if reviewing >10 files
3. **Focus on impact**: Prioritize critical issues over style preferences
4. **Be constructive**: Always explain why changes are recommended
5. **Test hypotheses**: If unsure about something, test it or research it

## Related Documentation

- Expert Review Panel: `.clinerules/rules/core/expert-review-panel.md`
- Quality Procedures: `.clinerules/rules/core/quality-procedures.md`
- Code Patterns: `.clinerules/rules/reference/code-patterns.md`
