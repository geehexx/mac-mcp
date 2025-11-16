#!/bin/bash
# Remind to update knowledge base after source changes

cd "$PWD" 2>/dev/null || exit 0

if git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null | grep -q "^src/"; then
    echo ""
    echo "🔄 Update knowledge base:"
    echo "   knowledge(command=\"update\", context_id=\"505a7641-9686-4ff0-bdc3-6104fc3924d0\", path=\"$PWD/src\")"
    echo ""
fi
