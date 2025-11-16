#!/bin/bash
# Track modified file count (preToolUse)

# Ensure we're in the project directory
[ -n "$PWD" ] && cd "$PWD" 2>/dev/null


git ls-files -m | wc -l > /tmp/q-pre-modified-$USER-$$
