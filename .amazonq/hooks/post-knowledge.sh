#!/bin/bash
# Post-knowledge hook: Auto-wait for update completion

set -euo pipefail

# Read hook event from STDIN
hook_event=$(cat)

# Extract tool info
tool_name=$(echo "$hook_event" | jq -r '.tool_name // empty')
command=$(echo "$hook_event" | jq -r '.tool_input.command // empty')
context_id=$(echo "$hook_event" | jq -r '.tool_input.context_id // empty')

# Only proceed for knowledge update operations
[ "$tool_name" != "knowledge" ] && exit 0
[ "$command" != "update" ] && exit 0
[ -z "$context_id" ] && exit 0

# Wait for update completion
readonly TIMEOUT=180
readonly INTERVAL=15
readonly CONTEXTS_FILE="$HOME/.aws/amazonq/knowledge_bases/developer_cli_enhanced_3c06addb18a25d31/contexts.json"

echo ""
echo "⏳ Waiting for knowledge base update (max ${TIMEOUT}s)..."

initial=$(jq -r ".\"$context_id\".updated_at // empty" "$CONTEXTS_FILE" 2>/dev/null)
[ -z "$initial" ] && { echo "❌ Context not found"; exit 0; }

elapsed=0
while [ $elapsed -lt $TIMEOUT ]; do
    sleep $INTERVAL
    elapsed=$((elapsed + INTERVAL))

    current=$(jq -r ".\"$context_id\".updated_at // empty" "$CONTEXTS_FILE" 2>/dev/null)

    if [ "$current" != "$initial" ]; then
        echo "✅ Complete (${elapsed}s)"
        echo ""
        exit 0
    fi

    echo "   Checking... (${elapsed}s/${TIMEOUT}s)"
done

echo "❌ Timeout after ${TIMEOUT}s"
echo ""
exit 0
