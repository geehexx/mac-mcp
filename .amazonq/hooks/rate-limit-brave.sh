#!/bin/bash
# Rate limiting for brave_web_search (1 req/sec)

f=/tmp/q-brave-last-call-$USER
while [ -f "$f" ] && [ $(($(date +%s%3N) - $(stat -c %Y000 "$f" 2>/dev/null || echo 0))) -lt 1000 ]; do
    sleep 0.$(printf '%03d' $((100 + RANDOM % 100)))
done
touch "$f"
