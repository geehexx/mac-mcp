#!/bin/bash
# Session initialization + knowledge base check

# Ensure we're in the project directory
[ -n "$PWD" ] && cd "$PWD" 2>/dev/null

# Session info
echo "🕐 Session: $(date --iso-8601=seconds) | Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"

# Knowledge base check
current=$(git rev-parse HEAD 2>/dev/null)
last=$(cat /tmp/q-knowledge-last-head-$USER 2>/dev/null)
if [ -n "$current" ] && [ "$current" != "$last" ]; then
    echo ""
    echo "🔄 Knowledge Base Update Available"
    if [ -n "$last" ]; then
        echo "   Previous: ${last:0:7}"
    else
        echo "   Previous: none"
    fi
    echo "   Current:  ${current:0:7}"
    echo "   Action: Update 'uke-codebase' context before searching"
fi

# Uncommitted changes
f=$(git status --porcelain)
if [ -n "$f" ]; then
    echo ""
    echo "⚠️  Uncommitted Changes:"
    echo "$f"
fi

# Token usage tracking stub
# Note: Amazon Q CLI doesn't expose token usage in hooks yet
# Use manual logging at session end:
#   uv run python scripts/tools/log_session.py
#
# Future: When token usage becomes available, uncomment:
# SESSION_ID="${Q_SESSION_ID:-$$}"
# echo "{\"session_id\": \"$SESSION_ID\", \"started_at\": \"$(date -Iseconds)\"}" >> ~/.uke/session_metrics.jsonl
