#!/usr/bin/env python3
"""Sharingan — GitHub repo deep-read extractor.

Shallow-clones a repo, intelligently selects high-value files by priority tier,
and produces a structured knowledge dump for scroll synthesis.

Usage:
    python3 extract_repo.py <github_url> [output_dir]

Output:
    repo_knowledge.json with repo metadata + selected file contents
"""

import re
import sys
import json
import shutil
import subprocess
from pathlib import Path

# ── File priority scoring ──────────────────────────────────────────────────────
# Lower score = higher priority = read first

ROOT_DOC_NAMES = {
    "readme", "readme.md", "readme.rst", "readme.txt",
    "changelog", "changelog.md", "changes.md", "history.md",
    "architecture.md", "design.md", "contributing.md",
    "hacking.md", "overview.md", "guide.md", "getting-started.md",
}

CONFIG_NAMES = {
    "pyproject.toml", "setup.py", "setup.cfg",
    "package.json", "cargo.toml", "go.mod", "go.sum",
}

ENTRY_POINT_NAMES = {
    "__init__.py", "index.ts", "index.js", "index.tsx",
    "main.py", "main.ts", "main.js", "main.go",
    "app.py", "app.ts", "lib.rs", "mod.rs",
}

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".next", "dist", "build",
    "target", ".cargo", "vendor", "venv", ".venv", "env", ".tox",
    "coverage", ".nyc_output", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", ".hypothesis",
}

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp",
    ".mp4", ".mp3", ".wav", ".ogg", ".pdf",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pyc", ".pyo", ".pyd", ".so", ".dylib", ".dll", ".exe",
    ".lock",  # lock files are noisy, low value
}

MAX_FILE_BYTES = 60_000    # 60KB per file (truncated if larger)
MAX_TOTAL_BYTES = 500_000  # 500KB total content budget
MAX_FILES = 60             # Maximum files to read


# ── URL parsing ────────────────────────────────────────────────────────────────

def parse_github_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL."""
    url = url.strip().rstrip("/")
    patterns = [
        r"github\.com[/:]([^/]+)/([^/\s]+?)(?:\.git)?(?:/.*)?$",
        r"^([^/]+)/([^/]+)$",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1), m.group(2).replace(".git", "")
    raise ValueError(f"Cannot parse GitHub URL: {url!r}")


# ── Repo metadata ──────────────────────────────────────────────────────────────

def get_repo_metadata(owner: str, repo: str) -> dict:
    """Fetch repo metadata via GitHub API (requires gh auth)."""
    result = subprocess.run(
        [
            "gh", "api", f"repos/{owner}/{repo}",
            "--jq",
            "{description:.description, language:.language, "
            "stars:.stargazers_count, topics:.topics, "
            "default_branch:.default_branch, license:.license.name, "
            "created_at:.created_at, pushed_at:.pushed_at}",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    return {}


# ── File selection ─────────────────────────────────────────────────────────────

def should_skip(path: Path) -> bool:
    """Return True if this path should not be read."""
    for part in path.parts:
        if part in SKIP_DIRS or part.endswith(".egg-info"):
            return True
    suffix = path.suffix.lower()
    if suffix in SKIP_EXTENSIONS:
        return True
    name = path.name
    if name.endswith(".min.js") or name.endswith(".min.css"):
        return True
    # Skip test fixtures / snapshots — usually not useful for learning
    if "__snapshots__" in str(path) or "fixtures" in path.parts:
        return True
    return False


def score_file(path: Path, repo_root: Path) -> int:
    """
    Assign a priority score to a file (lower = read sooner).

    Tiers:
      10  - Root-level documentation (README, CHANGELOG, ARCHITECTURE…)
      20  - Package config (pyproject.toml, package.json…)
      30  - Entry points (__init__.py, index.ts, main.py…)
      40  - docs/ directory markdown
      50  - examples/ / demo/ directory
      60  - Test files (show API usage patterns)
      70  - Source files — penalised by nesting depth
      90  - Everything else
    """
    rel = path.relative_to(repo_root)
    parts = rel.parts
    name_lower = path.name.lower()
    rel_str = str(rel).lower()

    # Tier 10: Root-level docs
    if len(parts) == 1 and name_lower in ROOT_DOC_NAMES:
        return 10

    # Tier 20: Package config
    if len(parts) == 1 and name_lower in CONFIG_NAMES:
        return 20

    # Tier 30: Entry points anywhere in the tree (closer to root = better)
    if name_lower in ENTRY_POINT_NAMES:
        return 30 + len(parts)

    # Tier 40: docs/ directory
    if parts[0] in {"docs", "doc", "documentation"}:
        return 40 + len(parts)

    # Tier 50: examples/ demo/
    if parts[0] in {"examples", "example", "demo", "demos", "samples"}:
        return 50 + len(parts)

    # Tier 60: Test files — they reveal actual API usage
    if parts[0] in {"tests", "test", "__tests__"} or "test" in name_lower:
        return 60 + len(parts)

    # Tier 70: Source files — penalise deeper nesting
    return 70 + len(parts) * 3


def collect_files(repo_root: Path) -> list[Path]:
    """Walk repo, skip noise, sort by priority score."""
    all_files = [
        p for p in repo_root.rglob("*")
        if p.is_file() and not should_skip(p)
    ]
    all_files.sort(key=lambda p: score_file(p, repo_root))
    return all_files


# ── File reading ───────────────────────────────────────────────────────────────

def read_files(files: list[Path], repo_root: Path) -> list[dict]:
    """Read files within budget limits."""
    results = []
    total_bytes = 0

    for path in files:
        if len(results) >= MAX_FILES:
            break
        if total_bytes >= MAX_TOTAL_BYTES:
            break

        file_size = path.stat().st_size
        truncated = False

        try:
            if file_size > MAX_FILE_BYTES:
                raw = path.read_bytes()[:MAX_FILE_BYTES]
                content = raw.decode("utf-8", errors="replace")
                truncated = True
            else:
                content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        content_bytes = len(content.encode("utf-8"))
        total_bytes += content_bytes

        results.append({
            "path": str(path.relative_to(repo_root)),
            "size_bytes": file_size,
            "truncated": truncated,
            "priority_score": score_file(path, repo_root),
            "content": content,
        })

    return results


# ── File tree summary ──────────────────────────────────────────────────────────

def build_tree_summary(repo_root: Path, max_entries: int = 300) -> list[str]:
    """Return a sorted list of relative file paths for structural overview."""
    paths = []
    for p in sorted(repo_root.rglob("*")):
        if p.is_file() and not should_skip(p):
            paths.append(str(p.relative_to(repo_root)))
        if len(paths) >= max_entries:
            break
    return paths


# ── Main extract function ──────────────────────────────────────────────────────

def extract(url: str, output_dir: str = "/tmp/sharingan") -> dict:
    """Deep-read a GitHub repo and produce a knowledge dump."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Parse
    owner, repo = parse_github_url(url)
    repo_name = f"{owner}/{repo}"
    print(f"Repo:    {repo_name}")

    # Metadata
    print("Fetching metadata via GitHub API...")
    meta = get_repo_metadata(owner, repo)
    if meta:
        print(f"  Language:    {meta.get('language', 'unknown')}")
        print(f"  Stars:       {meta.get('stars', '?'):,}")
        print(f"  Description: {meta.get('description') or '(none)'}")
        topics = meta.get("topics") or []
        if topics:
            print(f"  Topics:      {', '.join(topics)}")
    else:
        print("  (metadata unavailable — gh auth may be needed)")

    # Clone
    clone_dir = out / "clone"
    if clone_dir.exists():
        shutil.rmtree(clone_dir)

    print("Cloning (shallow, depth=1)...")
    clone_url = f"https://github.com/{owner}/{repo}.git"
    result = subprocess.run(
        ["git", "clone", "--depth", "1", "--single-branch", clone_url, str(clone_dir)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # Fallback: gh repo clone (handles auth for private repos)
        print("  git clone failed, trying gh repo clone...")
        result = subprocess.run(
            ["gh", "repo", "clone", repo_name, str(clone_dir), "--", "--depth", "1"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return {"error": f"Clone failed: {result.stderr.strip()}"}

    print("  Done.")

    # Walk + select files
    print("Scanning file tree...")
    all_files = collect_files(clone_dir)
    tree_summary = build_tree_summary(clone_dir)
    print(f"  Total readable files: {len(all_files)}")
    print(f"  Selecting up to {MAX_FILES} files within {MAX_TOTAL_BYTES // 1024}KB budget...")

    selected = read_files(all_files, clone_dir)
    total_kb = sum(len(f["content"].encode()) for f in selected) / 1024
    print(f"  Selected: {len(selected)} files ({total_kb:.1f}KB)")

    # Print what we selected (for transparency)
    for f in selected:
        trunc = " [truncated]" if f["truncated"] else ""
        print(f"    [{f['priority_score']:3d}] {f['path']}{trunc}")

    # Cleanup
    shutil.rmtree(clone_dir)
    print("  Clone cleaned up.")

    # Assemble output
    knowledge = {
        "source_type": "github",
        "repo": repo_name,
        "url": url,
        "owner": owner,
        "name": repo,
        "metadata": meta,
        "file_tree": tree_summary,
        "files_read": len(selected),
        "total_files": len(all_files),
        "files": selected,
    }

    output_path = out / "repo_knowledge.json"
    with open(output_path, "w") as f:
        json.dump(knowledge, f, indent=2)

    print(f"\nKnowledge dump: {output_path}")
    return knowledge


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <github_url> [output_dir]")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/tmp/sharingan"
    result = extract(url, output_dir)

    if "error" in result:
        print(f"\nERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"\nReady for scroll synthesis.")
