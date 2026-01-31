#!/usr/bin/env python3
"""
Show current project context.
Auto-detects project from cwd and shows state.
"""

import sys
import json
import os

# Add ninja-assist src to path
sys.path.insert(0, "/home/ndninja/clawd/projects/ninja-assist")

from src.state_manager import StateManager


def main():
    # Optional: specify a path to detect from
    start_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    sm = StateManager(auto_detect=False)
    
    if start_path:
        project = sm.detect_project(start_path)
    else:
        project = sm.detect_project()
    
    ctx = sm.get_context_summary()
    
    if not ctx["has_project"]:
        print(json.dumps({
            "status": "no_project",
            "message": "No project detected in current directory tree",
            "hint": "Navigate to a project directory or specify a path"
        }, indent=2))
        return
    
    # Build detailed output
    result = {
        "project": ctx["project_name"],
        "path": sm.project_state.project_path if sm.project_state else None,
        "phase": ctx["current_phase"],
        "task": ctx["current_task"],
        "pending_count": ctx["pending_count"],
        "tools": ctx["tools_detected"],
        "last_action": ctx["last_action"],
    }
    
    # Add pending tasks if any
    if sm.project_state and sm.project_state.pending_tasks:
        result["pending_tasks"] = sm.project_state.pending_tasks[:5]
    
    # Add recent projects
    recent = sm.get_recent_projects(5)
    if recent:
        result["recent_projects"] = recent
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
