#!/usr/bin/env python3
"""
Route a plain-language request to the appropriate tool.
Uses pattern matching (0 LLM tokens) with fallback to unknown.
"""

import sys
import json

# Add ninja-assist src to path
sys.path.insert(0, "/home/ndninja/clawd/projects/ninja-assist")

from src.intent_router import classify_intent, route_request
from src.state_manager import get_manager, record_action


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: route.py <request>",
            "example": "route.py 'help me code a parser'"
        }))
        sys.exit(1)
    
    text = " ".join(sys.argv[1:])
    intent = classify_intent(text)
    
    # Record the intent in state
    try:
        sm = get_manager()
        sm.record_intent(intent.category)
    except Exception:
        pass  # Don't fail if state manager has issues
    
    result = {
        "category": intent.category,
        "confidence": intent.confidence,
        "tool": intent.suggested_tool,
        "original": text,
    }
    
    # Add routing suggestions
    if intent.category == "code":
        result["suggestion"] = "Use Claude Code or GSD for implementation"
        result["commands"] = ["claude", "/gsd:execute-phase"]
    elif intent.category == "research":
        result["suggestion"] = "Use web_search tool"
        result["commands"] = ["web_search"]
    elif intent.category == "install":
        result["suggestion"] = "Run with exec tool"
        result["commands"] = ["pip install", "npm install", "apt install"]
    elif intent.category == "design":
        result["suggestion"] = "Use brainstorming or Shadow Council"
        result["commands"] = ["Think through options", "List pros/cons"]
    else:
        result["suggestion"] = "Ambiguous - use full LLM reasoning"
        result["commands"] = []
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
