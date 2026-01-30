# Improved Memory System Design

## Problem
Context loss after compaction causes:
- Forgetting project details
- Re-asking questions user already answered
- Losing track of decisions and rationale
- Frustration (especially for neurodivergent users who hate repeating themselves)

## Solution: Multi-Layer Memory

### Layer 1: MEMORY.md (Long-term, Curated)
- Core facts about the user
- Preferences, boundaries, communication style
- Key relationships and context
- **Loaded in main sessions only**

### Layer 2: memory/YYYY-MM-DD.md (Daily Logs)
- Raw session notes
- Tasks completed
- Decisions made
- Technical details

### Layer 3: memory/projects/*.md (Project State) [NEW]
- One file per active project
- Current state, not history
- Key files, APIs, credentials
- Next steps
- **Always load relevant project file when working on that project**

### Layer 4: memory/CONTEXT.md (Compaction-Resistant) [NEW]
- Critical context that MUST survive compaction
- Active project summaries (2-3 lines each)
- Recent important decisions
- "Don't forget" items
- **Loaded on every session start**

## File Structure
```
memory/
├── MEMORY.md              # Long-term (main session only)
├── CONTEXT.md             # Compaction-resistant summary [NEW]
├── YYYY-MM-DD.md          # Daily logs
├── projects/              # Project state files [NEW]
│   ├── ninja-content.md   # Content pipeline project
│   └── ...
└── heartbeat-state.json   # Heartbeat tracking
```

## Rules
1. Update CONTEXT.md when something important happens
2. Create/update project files when working on projects
3. Before answering questions about prior work, check project files
4. Keep CONTEXT.md under 50 lines (distilled, not verbose)
