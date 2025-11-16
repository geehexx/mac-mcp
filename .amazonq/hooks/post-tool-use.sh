#!/bin/bash
# Track tool calls and re-print prompt after threshold
# Detect git commit failures from pre-commit hooks

SESSION_ID="${Q_SESSION_ID:-$$}"
COUNTER_FILE="/tmp/q-tool-counter-$USER-$SESSION_ID"
GIT_FAILURE_FILE="/tmp/q-git-failure-$USER-$SESSION_ID"
THRESHOLD=50  # Re-print prompt every 50 tool calls

# Increment counter
count=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
count=$((count + 1))
echo "$count" > "$COUNTER_FILE"

# Check threshold
if [ $((count % THRESHOLD)) -eq 0 ]; then
    echo ""
    echo "📋 Prompt Refresh (after $count tool calls)"
    echo "   Re-reading: .amazonq/cli-agents/cli-agent-prompt.md"
    echo "   Reason: Long session - refresh core workflows and patterns"
fi

# Detect git commit failures from pre-commit hooks
# Check if last command was git commit and if it failed
if [ -n "$Q_LAST_COMMAND" ] && echo "$Q_LAST_COMMAND" | grep -q "git commit"; then
    # Check git status for uncommitted changes (indicates commit failed)
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        # Check if pre-commit hooks ran (look for hook output patterns)
        if git log -1 --pretty=%B 2>/dev/null | grep -q "Files were modified by this hook\|hook failed"; then
            echo ""
            echo "⚠️  PRE-COMMIT HOOK FAILURE DETECTED"
            echo ""
            echo "Pre-commit hooks auto-fixed files or reported errors."
            echo ""
            echo "PROPER WORKFLOW:"
            echo "  1. If hooks auto-fixed files:"
            echo "     git add -u"
            echo "     git commit -m \"<same message>\""
            echo ""
            echo "  2. If hooks reported errors (mypy, xenon, etc.):"
            echo "     # Fix the code manually"
            echo "     git add <fixed-files>"
            echo "     git commit -m \"<same message>\""
            echo ""
            echo "NEVER use --no-verify to bypass hooks!"
            echo ""

            # Log for tracking
            echo "$(date): Pre-commit hook failure detected" >> "$GIT_FAILURE_FILE"
        fi
    fi
fi
