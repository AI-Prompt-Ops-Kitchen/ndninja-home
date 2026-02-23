---
name: eza-modern-ls
domain: CLI/Files
level: 1-tomoe
description: Modern ls replacement with icons, color coding, git status integration, tree views, and directory grouping. Zero-friction upgrade aliased to ls.
sources:
  - type: youtube
    title: "10 CLI tools I use with Claude Code"
    url: "https://youtu.be/3NzCBIcIqD0"
    date: "2026-02-23"
    confidence: high
  - type: web
    title: "Eza GitHub"
    url: "https://github.com/eza-community/eza"
    date: "2026-02-23"
    confidence: high
sources_count: 2
last_updated: 2026-02-23
can_do_from_cli: true
---

# Eza — Modern ls Replacement

## Mental Model
Drop-in replacement for `ls` with icons, colors, git awareness, and tree view. Aliased to `ls` so it's zero friction — just better output everywhere.

## Installation & Aliases
```bash
# Already installed + aliased in ~/.bashrc:
alias ls='eza --icons --group-directories-first'
alias ll='eza --icons --group-directories-first -la'
alias lt='eza --icons --group-directories-first --tree --level=2'
```

## Useful Flags
| Flag | Purpose |
|------|---------|
| `--icons` | File type icons (requires Nerd Font) |
| `--group-directories-first` | Dirs before files |
| `-la` | Long format + hidden files |
| `--tree` | Tree view |
| `--level=N` | Tree depth limit |
| `--git` | Show git status per file |
| `--git-ignore` | Respect .gitignore |
| `--sort=modified` | Sort by modification time |
| `--sort=size` | Sort by file size |
| `-r` | Reverse sort |
| `--no-permissions` | Hide permissions column |
| `--no-user` | Hide user column |
| `--time-style=relative` | "2 hours ago" instead of dates |
| `--header` | Column headers in long view |
| `-1` | One file per line |

## Handy Combos
```bash
# Recently modified files
eza -la --sort=modified --reverse output/thumbnails/

# Tree with git status
eza --tree --level=2 --git projects/ninja-dashboard/

# Just directories
eza -D projects/

# Size-sorted (find big files)
eza -la --sort=size --reverse output/
```

## Nerd Font Requirement
Icons require a Nerd Font in your terminal. If you see boxes instead of icons:
- Install a Nerd Font: https://www.nerdfonts.com/
- Or remove `--icons` from aliases

## Integration Points — Ninja Ecosystem
- `ls output/` — instantly see thumbnails, videos, approved/rejected files with icons
- `lt projects/` — tree view of all project directories
- `ll --git` — see which files are staged/modified/untracked at a glance
