#!/bin/bash
# Show uncommitted changes (conditional)

# Ensure we're in the project directory
[ -n "$PWD" ] && cd "$PWD" 2>/dev/null


f=$(git status --porcelain)
if [ -n "$f" ]; then
    echo "⚠️  Uncommitted: $(echo "$f" | wc -l) files"
    echo "📝 Last Commit: $(git log -1 --pretty=format:'%h - %s (%cr)')"
fi
