---
name: lazygit-tui
domain: CLI/Git
level: 2-tomoe
description: Terminal UI for git — visual staging, diff viewer, branch management, commit history, stash management. Replaces walls of git status output with an interactive TUI.
sources:
  - type: youtube
    title: "10 CLI tools I use with Claude Code"
    url: "https://youtu.be/3NzCBIcIqD0"
    date: "2026-02-23"
    confidence: high
  - type: web
    title: "Lazygit GitHub"
    url: "https://github.com/jesseduffield/lazygit"
    date: "2026-02-23"
    confidence: high
sources_count: 2
last_updated: 2026-02-23
can_do_from_cli: true
---

# Lazygit — Terminal Git UI

## Mental Model
Lazygit is a full-screen terminal UI for git. Instead of typing `git status`, `git diff`, `git add`, `git commit` etc., you get a persistent dashboard showing files, staging area, branches, commits, and stashes — all navigable with keyboard shortcuts. Think of it as "htop for git."

## Installation
```bash
# Already installed at /usr/local/bin/lazygit (v0.59.0)
lazygit --version
```

## Core Panels (left to right)
| Panel | Key | Purpose |
|-------|-----|---------|
| Status | `1` | Repo name, branch, upstream status |
| Files | `2` | Working tree changes (stage/unstage) |
| Branches | `3` | Local + remote branches, checkout, merge |
| Commits | `4` | Commit log with inline diffs |
| Stash | `5` | Stash entries, apply/pop/drop |

## Essential Keybindings
| Action | Key |
|--------|-----|
| Launch | `lazygit` (or alias `lg`) |
| Stage file | `space` |
| Stage all | `a` |
| Commit | `c` |
| Push | `P` (shift) |
| Pull | `p` |
| Checkout branch | `space` on branch |
| New branch | `n` on branches panel |
| View diff | `enter` on any file |
| Scroll diff | `↑/↓` or `j/k` |
| Switch panels | `tab` or `h/l` |
| Quit | `q` |
| Amend last commit | `A` (shift) |
| Interactive rebase | `e` on commit |
| Cherry pick | `C` (shift) on commit |
| Stash | `s` on files panel |
| Discard changes | `d` on file |
| Filter files | `/` |

## Suggested Alias
```bash
alias lg='lazygit'
```

## Workflow: Claude Code + Lazygit Side-by-Side
1. Run Claude Code in one terminal pane
2. Run `lazygit` in a second pane
3. Watch files change in real-time as Claude writes code
4. Stage selectively, review diffs visually, commit when ready
5. No more scrolling through massive `git status` output

## Custom Config (optional)
Config lives at `~/.config/lazygit/config.yml`:
```yaml
gui:
  theme:
    activeBorderColor:
      - green
      - bold
  showFileTree: true
  showRandomTip: false
git:
  paging:
    colorArg: always
    pager: delta  # if delta is installed
```

## Integration Points — Ninja Ecosystem
- **Massive working tree:** The home repo has 100+ untracked/modified files — lazygit makes selective staging manageable
- **Multi-project changes:** When Claude modifies files across `scripts/`, `projects/ninja-dashboard/`, `sage_mode/` — see all changes at a glance
- **Rasengan git hooks:** `post-commit` and `pre-push` hooks fire events — lazygit shows hook output inline

## Tips
- Press `?` in any panel for context-specific help
- `x` opens the command log (see what git commands lazygit ran)
- Works over SSH — great for headless server workflow
- Supports mouse if your terminal supports it
