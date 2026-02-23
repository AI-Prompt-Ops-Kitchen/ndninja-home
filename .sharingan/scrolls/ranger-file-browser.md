---
name: ranger-file-browser
domain: CLI/Files
level: 1-tomoe
description: Terminal file browser with vim-style navigation, directory preview, and file operations. Essential GUI file manager replacement for headless Linux servers.
sources:
  - type: youtube
    title: "10 CLI tools I use with Claude Code"
    url: "https://youtu.be/3NzCBIcIqD0"
    date: "2026-02-23"
    confidence: high
  - type: web
    title: "Ranger GitHub"
    url: "https://github.com/ranger/ranger"
    date: "2026-02-23"
    confidence: high
sources_count: 2
last_updated: 2026-02-23
can_do_from_cli: true
---

# Ranger — Terminal File Browser

## Mental Model
Ranger is a 3-column file manager for the terminal. Left column shows parent directory, middle shows current directory, right shows preview of selected file. Navigate with vim keys. It's the closest thing to Finder/Nautilus you can get on a headless server.

## Installation
```bash
# Already installed (v1.9.4)
ranger
```

## Navigation
| Key | Action |
|-----|--------|
| `h` | Go to parent directory |
| `l` or `enter` | Open / enter directory |
| `j/k` | Move down/up |
| `gg` | Jump to top |
| `G` | Jump to bottom |
| `H` | Back in history |
| `L` | Forward in history |
| `gh` | Go to ~ (home) |
| `gd` | Go to /dev |
| `ge` | Go to /etc |
| `/` | Search |
| `n/N` | Next/prev search result |
| `f` | Quick find (type to filter) |
| `q` | Quit |

## File Operations
| Key | Action |
|-----|--------|
| `yy` | Copy (yank) selected files |
| `dd` | Cut selected files |
| `pp` | Paste files |
| `dD` | Delete (confirm prompt) |
| `cw` | Rename |
| `A` | Rename (append to name) |
| `space` | Toggle selection |
| `V` | Visual select mode |
| `uv` | Unselect all |
| `:mkdir <name>` | Create directory |
| `:touch <name>` | Create file |
| `S` | Open shell in current directory |

## View Modes
| Key | Action |
|-----|--------|
| `zh` | Toggle hidden files |
| `zf` | Toggle filter |
| `os` | Sort by size |
| `om` | Sort by modification time |
| `on` | Sort by name |
| `or` | Reverse sort |
| `i` | Inspect file (full preview) |
| `w` | Open task manager |

## Config
Generate default config: `ranger --copy-config=all`
Config at `~/.config/ranger/rc.conf`:
```
set preview_images true
set preview_images_method kitty  # or sixel, w3m
set show_hidden true
set sort natural
set sort_directories_first true
```

## Integration Points — Ninja Ecosystem
- **Browse output/:** Visually scan thumbnails, videos, approved/rejected renders
- **Browse assets/:** Find avatar references, B-roll clips
- **Browse .sharingan/scrolls/:** Quick-read scroll files with preview
- **Pairs with zoxide:** Navigate in ranger, `z` jumps back to frequently visited dirs later
- **Shell out (`S`):** Drop into a shell in current dir, run ffprobe/mediainfo on files

## Tips
- `S` (capital S) opens a shell in the current directory — incredibly handy
- Preview column shows file contents for text, and file info for binaries
- For image preview in terminal, set `preview_images_method` to `kitty` (if using Kitty terminal) or `sixel`
- Ranger remembers your last position in each directory
