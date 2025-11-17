# Cline Advanced Workflow Activation Guide

This guide will walk you through activating all advanced Cline features for this project.

## Prerequisites

- VSCode with Cline extension installed
- Project workspace opened in VSCode
- Cline configured with Claude Sonnet 4.5 via AWS Bedrock (or your preferred model)

## Step 1: Enable Hooks (REQUIRED)

Hooks are the foundation of the advanced workflow system.

### Enable in Cline Settings

1. **Open Cline Panel** in VSCode (click Cline icon in sidebar)
2. **Click Settings** button (top right corner of Cline panel)
3. **Navigate to "Features"** section in left navigation
4. **Scroll down** to find "Enable Hooks" checkbox
5. **Check the box** labeled "Enable Hooks"
6. **Restart VSCode** if prompted (recommended)

### Verify Hooks are Enabled

Open VSCode Output panel and select "Cline" channel:
- Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
- Type "Output: Show Output Channels"
- Select "Cline" from dropdown

Look for messages about hooks when starting a task.

### Verify Hooks are Executable

The hooks were made executable during setup, but verify:

```bash
ls -l .clinerules/hooks/
```

Expected output: All hook files should show `rwxr-xr-x` permissions.

If not executable:
```bash
chmod +x .clinerules/hooks/*
```

## Step 2: Verify Hook Functionality

Test that hooks are working:

### Test TaskStart Hook

1. Start a new task in Cline
2. Type a simple request like "list the files in the src directory"
3. Look for hook context injection in the Cline response

Expected: You should see context about project initialization, quality gates, and core principles.

### Test PreToolUse Hook

1. Try to create a prohibited file:
   - Type: "Create a file called SUMMARY.md"
2. Hook should block this action

Expected: Error message explaining prohibited files.

### Test PostToolUse Hook

1. Run tests:
   - Type: "Run pytest"
2. Check for hook feedback after command completes

Expected: Context about test results and best practices.

### Test UserPromptSubmit Hook

1. Type a message with keywords like "commit" or "test"
2. Look for relevant guidance in response

Expected: Contextual reminders about git workflow or testing standards.

## Step 3: Verify Workflows

Workflows should be automatically available:

1. In Cline chat, type `/`
2. You should see workflow suggestions:
   - `/code-review.md`
   - `/refactoring.md`
   - `/sub-agent-research.md`

If workflows don't appear:
- Verify files exist in `.clinerules/workflows/`
- Verify files have `.md` extension
- Try restarting Cline

## Step 4: Test Sub-Agent CLI (Optional)

Sub-agents require Cline CLI to be installed:

### Check if Cline CLI is Available

```bash
which cline
# OR
cline --version
```

### If Not Installed

Install globally:
```bash
npm install -g @cline/cli
```

Or use VSCode extension's built-in CLI (usually available automatically).

### Test Sub-Agent

Try a simple research task:

```bash
cline "list all .py files in src/ directory"
```

Expected: List of Python files with brief descriptions.

## Step 5: Test Expert Review Panel

The expert review panel is a powerful feature for complex decisions.

### Simple Test

In Cline chat:
```
I'm about to implement Redis caching for the task queue. Can you convene an expert review panel to evaluate this approach?
```

Expected: Cline should:
1. Generate 2-5 domain experts
2. Ground each with research
3. Present multi-round debate
4. Provide consensus recommendation

## Troubleshooting

### Issue: Hooks Not Running

**Symptoms:**
- No hook context appears in responses
- TaskStart doesn't inject initialization context

**Solutions:**
1. Verify "Enable Hooks" is checked in Cline settings
2. Check hook files are executable: `ls -l .clinerules/hooks/`
3. Check VSCode Output panel (Cline channel) for errors
4. Restart VSCode
5. Verify hook files have proper shebang: `#!/usr/bin/env bash`

### Issue: Hooks Produce Errors

**Symptoms:**
- Error messages in Cline Output panel
- Hooks timeout or fail silently

**Solutions:**
1. Verify `jq` is installed: `which jq`
   - Install if missing: `sudo apt install jq` (Linux) or `brew install jq` (Mac)
2. Check hook syntax: `bash -n .clinerules/hooks/TaskStart`
3. Test hook manually:
   ```bash
   echo '{"taskId":"test","taskStart":{"taskMetadata":{"initialTask":"test"}}}' | .clinerules/hooks/TaskStart
   ```
4. Check Output panel for specific error messages

### Issue: Workflows Not Appearing

**Symptoms:**
- Typing `/` doesn't show workflow suggestions
- Cannot invoke workflows by name

**Solutions:**
1. Verify files exist: `ls -l .clinerules/workflows/`
2. Verify `.md` extension on all workflow files
3. Restart Cline (click Cline Settings → Close → Reopen Cline panel)
4. Try invoking directly: `/code-review.md`

### Issue: Sub-Agents Not Working

**Symptoms:**
- `cline` command not found
- Sub-agent doesn't respond or errors

**Solutions:**
1. Install Cline CLI: `npm install -g @cline/cli`
2. Verify workspace is open in VSCode
3. Check you have an active Cline task
4. Try simpler prompt: `cline "list files in current directory"`
5. Check if VSCode extension has built-in CLI enabled

### Issue: ask_followup_question Not Working (HITL)

**Symptoms:**
- Questions don't appear in Cline chat
- No response options shown
- Cline proceeds without waiting for answer

**Possible Causes:**
1. **Model Context Limitations**: If conversation is very long, questions may be truncated
2. **Tool Response Parsing**: Rare edge case where tool response isn't parsed correctly
3. **UI State**: Cline UI may be in incorrect state

**Solutions:**

1. **Check Tool Call Format**:
   - Verify `<ask_followup_question>` tags are properly closed
   - Ensure `<question>` parameter is present
   - Options are optional but must be valid JSON array if present

2. **Try Simpler Question**:
   ```xml
   <ask_followup_question>
   <question>What would you like me to do next?</question>
   </ask_followup_question>
   ```

3. **Check Cline Output Panel**:
   - Look for tool execution errors
   - Check for JSON parsing issues

4. **Restart Cline Task**:
   - Cancel current task
   - Start fresh with simpler request
   - Build up complexity gradually

5. **Verify Model Configuration**:
   - Ensure you're using supported model (Claude Sonnet 3.5/4+)
   - Check API connection is stable
   - Verify sufficient token budget

6. **Clear Conversation Context**:
   - Start a new task if conversation is very long
   - Use checkpoints feature to save progress
   - Resume with fresh context

### Issue: Context Too Large

**Symptoms:**
- Slow responses
- Truncated messages
- "Context limit exceeded" errors

**Solutions:**
1. Use `new_task` tool to start fresh with relevant context
2. Use sub-agents for research instead of loading all files
3. Enable auto-compact in Cline settings
4. Break large tasks into smaller chunks

### Issue: Expert Review Panel Too Verbose

**Symptoms:**
- Very long responses
- Too much detail in debates

**Solutions:**
1. Request "standard mode" (3 rounds max)
2. Ask for "concise summary with critical issues only"
3. Limit experts to 2-3 instead of 4-5
4. Skip briefings for simple topics

## Advanced Configuration

### Customize Hook Behavior

Edit hook files in `.clinerules/hooks/` to customize behavior:

**Example: Adjust PreToolUse validation**

Edit `.clinerules/hooks/PreToolUse`:
```bash
# Add custom validation rules
if [ "$tool_name" = "execute_command" ]; then
    command=$(echo "$parameters" | jq -r '.command // ""')
    
    # Block dangerous commands
    if echo "$command" | grep -qE 'rm -rf /'; then
        cancel=true
        error_message="Dangerous command blocked"
    fi
fi
```

### Customize Workflows

Create custom workflows in `.clinerules/workflows/`:

1. Create new `.md` file with workflow name
2. Use XML tool syntax in examples
3. Provide clear step-by-step guidance
4. Include tips and common pitfalls
5. Invoke with `/your-workflow-name.md`

### Extend Rules

Add project-specific rules in `.clinerules/rules/`:

- Core rules: `.clinerules/rules/core/`
- Reference patterns: `.clinerules/rules/reference/`

Rules are automatically available to hooks and can be referenced in workflows.

## Verification Checklist

Mark each item as you verify it works:

- [ ] Hooks enabled in Cline settings
- [ ] Hooks are executable (`chmod +x`)
- [ ] TaskStart hook injects context
- [ ] PreToolUse hook blocks prohibited files
- [ ] PostToolUse hook provides feedback
- [ ] UserPromptSubmit hook detects keywords
- [ ] Workflows appear when typing `/`
- [ ] Can invoke workflows by name
- [ ] Sub-agent CLI installed and working
- [ ] Expert review panel generates experts
- [ ] ask_followup_question tool works
- [ ] No errors in Cline Output panel

## Next Steps

Once everything is activated:

1. **Read Core Documentation**:
   - `.clinerules/rules/core/development-workflow.md`
   - `.clinerules/rules/core/expert-review-panel.md`
   - `.clinerules/rules/core/quality-procedures.md`

2. **Try a Workflow**:
   - Type `/code-review.md` to review code
   - Type `/refactoring.md` to refactor safely
   - Type `/sub-agent-research.md` to delegate research

3. **Use Expert Review**:
   - For complex decisions, request expert panel
   - Let experts debate and reach consensus
   - Use their recommendations

4. **Leverage Sub-Agents**:
   - Delegate large-scale research
   - Use for code exploration
   - Keep main agent focused on implementation

## Getting Help

If you encounter issues:

1. Check Cline Output panel for errors
2. Review this troubleshooting guide
3. Check hook execution with manual tests
4. Verify all dependencies (jq, bash, etc.)
5. Restart VSCode if needed

## Success Indicators

You'll know everything is working when:

✅ Task initialization shows project context
✅ Prohibited file creation is blocked
✅ Git commit failures trigger helpful guidance
✅ Workflows are accessible via `/`
✅ Sub-agents can be invoked via CLI
✅ Expert panels provide multi-perspective analysis
✅ No errors appear in Output panel

## Additional Resources

- **Cline Documentation**: https://docs.cline.bot
- **Cline Hooks**: https://docs.cline.bot/features/hooks
- **Cline Workflows**: https://docs.cline.bot/features/slash-commands/workflows
- **Cline CLI**: https://docs.cline.bot/cline-cli/overview
- **Project README**: `.clinerules/README.md`

---

**You're now ready to use Cline with advanced workflows, hooks, expert review panels, and sub-agent orchestration!**
