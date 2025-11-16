#!/bin/bash
# Check modifications (postToolUse)

# Ensure we're in the project directory
[ -n "$PWD" ] && cd "$PWD" 2>/dev/null


pre=$(cat /tmp/q-pre-modified-$USER-$$ 2>/dev/null || echo 0)
post=$(git ls-files -m | wc -l)
rm -f /tmp/q-pre-modified-$USER-$$

if [ $post -gt $pre ]; then
    echo "📝 Modified: \"$(git ls-files -m | paste -sd,)\""
fi
