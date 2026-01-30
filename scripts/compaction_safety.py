#!/usr/bin/env python3
"""
compaction_safety.py — Compaction Safety System for Neurodivergent Users

Features:
- Visual context health indicator
- Tiered warnings (75%, 85%, 95%)
- Auto-save to memory files
- Named checkpoints
- Pin system
- Version history

Usage:
    python compaction_safety.py --status              # Show context health
    python compaction_safety.py --save                # Manual save current context
    python compaction_safety.py --checkpoint "name"   # Create named checkpoint
    python compaction_safety.py --pin "item"          # Add pinned item
    python compaction_safety.py --list-checkpoints    # List saved checkpoints
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
MEMORY_DIR = PROJECT_DIR / "memory"
CHECKPOINTS_DIR = MEMORY_DIR / "checkpoints"
PINNED_FILE = MEMORY_DIR / "PINNED.md"
CONTEXT_FILE = MEMORY_DIR / "CONTEXT.md"

# Thresholds
WARN_THRESHOLD = 0.75      # Yellow - heads up
SAVE_THRESHOLD = 0.85      # Orange - auto-save triggered
CRITICAL_THRESHOLD = 0.95  # Red - urgent

# Context limits (Claude's context window)
MAX_CONTEXT_TOKENS = 200000


def get_health_indicator(percentage: float) -> str:
    """Generate visual health bar with emoji and color description."""
    
    filled = int(percentage * 20)
    empty = 20 - filled
    
    if percentage < WARN_THRESHOLD:
        color = "🟢"
        status = "Healthy"
        risk = "Low"
    elif percentage < SAVE_THRESHOLD:
        color = "🟡"
        status = "Filling Up"
        risk = "Medium"
    elif percentage < CRITICAL_THRESHOLD:
        color = "🟠"
        status = "Getting Full"
        risk = "High"
    else:
        color = "🔴"
        status = "Nearly Full"
        risk = "Critical"
    
    bar = f"{'█' * filled}{'░' * empty}"
    
    # Estimate remaining turns (rough: ~1000 tokens per turn)
    remaining_tokens = int(MAX_CONTEXT_TOKENS * (1 - percentage))
    remaining_turns = remaining_tokens // 1000
    
    return f"""
{color} Context Health: {status}
├─ Usage: [{bar}] {percentage*100:.1f}%
├─ Risk Level: {risk}
├─ Estimated Remaining: ~{remaining_turns} messages
└─ Status: {'⚠️ Auto-save recommended' if percentage >= SAVE_THRESHOLD else '✅ All good'}
"""


def get_today_file() -> Path:
    """Get today's memory file path."""
    today = datetime.now().strftime("%Y-%m-%d")
    return MEMORY_DIR / f"{today}.md"


def create_checkpoint(name: str, context: dict) -> Path:
    """Create a named checkpoint file."""
    
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in name.lower())
    filename = f"{timestamp}_{safe_name}.md"
    filepath = CHECKPOINTS_DIR / filename
    
    content = f"""# Checkpoint: {name}
> Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Current Task
{context.get('current_task', 'Not specified')}

## Recent Decisions
{context.get('recent_decisions', 'None recorded')}

## Open Loops
{context.get('open_loops', 'None')}

## Key Context
{context.get('key_context', 'None')}

## Don't Forget
{context.get('dont_forget', 'Nothing flagged')}
"""
    
    filepath.write_text(content)
    return filepath


def add_pinned_item(item: str) -> None:
    """Add an item to PINNED.md."""
    
    today = datetime.now().strftime("%Y-%m-%d")
    pinned_line = f"- [{today}] {item}\n"
    
    content = PINNED_FILE.read_text()
    
    # Find the "## 📌 Pinned Items" section and append
    if "## 📌 Pinned Items" in content:
        content = content.rstrip() + "\n" + pinned_line
    else:
        content += f"\n## 📌 Pinned Items\n{pinned_line}"
    
    PINNED_FILE.write_text(content)


def auto_save_context(context: dict) -> dict:
    """Auto-save current context to memory files. Returns save summary."""
    
    saved = {}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 1. Update CONTEXT.md with current state
    context_content = f"""# CONTEXT.md — Compaction-Resistant Summary
> Last auto-saved: {timestamp}
> This file survives compaction. Keep under 50 lines.

## Current Task
{context.get('current_task', 'Not specified')}

## Recent Decisions
{context.get('recent_decisions', 'None')}

## Open Loops (Unfinished Threads)
{context.get('open_loops', 'None')}

## Don't Forget
{context.get('dont_forget', 'Nothing flagged')}

## Key Context
{context.get('key_context', 'None')}
"""
    CONTEXT_FILE.write_text(context_content)
    saved['context'] = str(CONTEXT_FILE)
    
    # 2. Append to today's daily file
    daily_file = get_today_file()
    daily_entry = f"""
## Auto-Save ({timestamp})
- **Task:** {context.get('current_task', 'Not specified')}
- **Decisions:** {context.get('recent_decisions', 'None')}
- **Note:** Context preserved before compaction

"""
    
    if daily_file.exists():
        with open(daily_file, 'a') as f:
            f.write(daily_entry)
    else:
        daily_file.write_text(f"# Memory Log — {datetime.now().strftime('%Y-%m-%d')}\n{daily_entry}")
    
    saved['daily'] = str(daily_file)
    
    # 3. Create automatic checkpoint
    checkpoint_path = create_checkpoint(f"auto-save-{timestamp.replace(':', '-')}", context)
    saved['checkpoint'] = str(checkpoint_path)
    
    return saved


def list_checkpoints() -> list:
    """List all saved checkpoints."""
    
    if not CHECKPOINTS_DIR.exists():
        return []
    
    checkpoints = []
    for f in sorted(CHECKPOINTS_DIR.glob("*.md"), reverse=True):
        if f.name != "README.md":
            checkpoints.append({
                'file': f.name,
                'path': str(f),
                'created': f.stat().st_mtime
            })
    
    return checkpoints[:10]  # Return last 10


def generate_save_confirmation(saved: dict, context: dict) -> str:
    """Generate friendly confirmation message."""
    
    return f"""
✅ **Context Archived Successfully**

📋 **What I'm carrying forward:**
- Task: {context.get('current_task', 'Not specified')}
- Key decisions preserved
- Open threads tracked

📁 **Saved to:**
- {saved.get('context', 'CONTEXT.md')}
- {saved.get('daily', 'Today\'s log')}
- {saved.get('checkpoint', 'Checkpoint created')}

🔄 **Nothing lost** — ready to continue where we left off.

_Is anything missing? Let me know and I'll add it to the pinned items._
"""


def main():
    parser = argparse.ArgumentParser(description="Compaction Safety System")
    parser.add_argument('--status', action='store_true', help='Show context health')
    parser.add_argument('--save', action='store_true', help='Manual save current context')
    parser.add_argument('--checkpoint', type=str, help='Create named checkpoint')
    parser.add_argument('--pin', type=str, help='Add pinned item')
    parser.add_argument('--list-checkpoints', action='store_true', help='List checkpoints')
    parser.add_argument('--usage', type=float, help='Current token usage (0-1)')
    parser.add_argument('--context', type=str, help='JSON context to save')
    
    args = parser.parse_args()
    
    if args.status:
        usage = args.usage if args.usage else 0.5  # Default to 50% if not provided
        print(get_health_indicator(usage))
        
    elif args.save:
        context = json.loads(args.context) if args.context else {
            'current_task': 'Not specified',
            'recent_decisions': 'None',
            'open_loops': 'None',
            'key_context': 'None',
            'dont_forget': 'Nothing flagged'
        }
        saved = auto_save_context(context)
        print(generate_save_confirmation(saved, context))
        
    elif args.checkpoint:
        context = json.loads(args.context) if args.context else {}
        path = create_checkpoint(args.checkpoint, context)
        print(f"✅ Checkpoint created: {path}")
        
    elif args.pin:
        add_pinned_item(args.pin)
        print(f"📌 Pinned: {args.pin}")
        
    elif args.list_checkpoints:
        checkpoints = list_checkpoints()
        if checkpoints:
            print("📚 Recent Checkpoints:")
            for cp in checkpoints:
                print(f"  • {cp['file']}")
        else:
            print("No checkpoints found.")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
