#!/usr/bin/env python3
"""
Show Ninja Assist learning statistics.
Token savings, accuracy, learned patterns.
"""

import sys
import json

# Add ninja-assist src to path
sys.path.insert(0, "/home/ndninja/clawd/projects/ninja-assist")

from src.learning import LearningSystem


def main():
    learner = LearningSystem()
    
    stats = learner.get_stats()
    accuracy = learner.get_accuracy()
    patterns = learner.get_learned_patterns()
    
    output = {
        "routing": {
            "total_routes": stats["total_routes"],
            "tokens_saved": stats["total_tokens_saved"],
            "cost_saved": stats["estimated_cost_saved"],
            "by_category": stats["routes_by_category"],
        },
        "accuracy": accuracy,
        "learning": {
            "patterns_learned": len(patterns),
            "patterns": [
                {"pattern": p.pattern[:50], "category": p.category, "matches": p.times_matched}
                for p in patterns[:10]  # Show top 10
            ]
        }
    }
    
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
