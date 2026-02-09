#!/bin/bash
# Context7 Proactive Preloader — SessionStart hook
# Runs in background so it doesn't block session startup

python3 ~/.claude/hooks/context7-preloader.py \
    --project-path "$PWD" \
    --max-preload 5 \
    --timeout 10 \
    >> ~/.logs/context7-preload.log 2>&1 &
