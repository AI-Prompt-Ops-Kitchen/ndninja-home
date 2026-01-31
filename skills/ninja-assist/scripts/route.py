#!/usr/bin/env python3
"""
Route a plain-language request to the appropriate tool.
Uses pattern matching (0 LLM tokens) with fallback to unknown.
Logs routes for learning and checks learned patterns.
"""

import sys
import json

# Add ninja-assist src to path
sys.path.insert(0, "/home/ndninja/clawd/projects/ninja-assist")

from src.intent_router import classify_intent, route_request
from src.state_manager import get_manager, record_action
from src.learning import get_learner


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: route.py <request> [--correct <category>] [--stats]",
            "example": "route.py 'help me code a parser'"
        }))
        sys.exit(1)
    
    # Handle --stats flag
    if sys.argv[1] == "--stats":
        learner = get_learner()
        stats = learner.get_stats()
        stats["accuracy"] = learner.get_accuracy()
        print(json.dumps(stats, indent=2))
        return
    
    # Handle --correct flag
    if "--correct" in sys.argv:
        idx = sys.argv.index("--correct")
        if idx + 1 < len(sys.argv):
            actual = sys.argv[idx + 1]
            learner = get_learner()
            pattern = learner.correct_last(actual)
            print(json.dumps({
                "corrected": True,
                "actual_category": actual,
                "learned_pattern": pattern.pattern if pattern else None
            }, indent=2))
            return
    
    text = " ".join(sys.argv[1:])
    learner = get_learner()
    
    # First check learned patterns (from corrections)
    learned = learner.check_learned_patterns(text)
    if learned:
        category, confidence = learned
        result = {
            "category": category,
            "confidence": confidence,
            "tool": None,  # Will be filled below
            "original": text,
            "source": "learned_pattern",
        }
    else:
        # Use built-in intent router
        intent = classify_intent(text)
        result = {
            "category": intent.category,
            "confidence": intent.confidence,
            "tool": intent.suggested_tool,
            "original": text,
            "source": "pattern_match",
        }
        category = intent.category
    
    # Log the route
    learner.log_route(text, result["category"], result["confidence"], result.get("tool"))
    
    # Record the intent in state
    try:
        sm = get_manager()
        sm.record_intent(result["category"])
    except Exception:
        pass  # Don't fail if state manager has issues
    
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
