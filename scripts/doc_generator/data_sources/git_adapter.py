"""Git adapter - analyzes codebase from git repositories"""
import subprocess
import os
from pathlib import Path
from data_sources.base_adapter import BaseAdapter
from config import Config


class GitAdapter(BaseAdapter):
    """Adapter for analyzing git repositories"""

    def gather(self, project, args):
        """
        Gather codebase information from git repository

        Args:
            project: Project dict with metadata
            args: Command-line arguments

        Returns:
            dict: {'git': {repo_path, structure, languages, commits, dependencies}}
        """
        repo_path = self._find_repo(project)

        if not repo_path:
            return {'git': {
                'available': False,
                'message': f"No git repository found for '{project['title']}'"
            }}

        return {'git': {
            'available': True,
            'repo_path': repo_path,
            'structure': self._get_structure(repo_path),
            'languages': self._detect_languages(repo_path),
            'recent_commits': self._get_commits(repo_path, limit=10),
            'dependencies': self._get_dependencies(repo_path),
            'file_count': self._count_files(repo_path)
        }}

    def is_available(self, project, args):
        """Check if git repo exists for this project"""
        return self._find_repo(project) is not None

    def _find_repo(self, project):
        """
        Find git repository path for project

        Strategies:
        1. Check metadata.github_repo or metadata.repo_path
        2. Try /home/ndninja/projects/{repo-name}
        3. Try /home/ndninja/projects/{project-slug}
        """
        metadata = project.get('metadata', {}) or {}

        # Strategy 1: Check metadata for explicit path
        if 'repo_path' in metadata:
            path = metadata['repo_path']
            if os.path.exists(os.path.join(path, '.git')):
                return path

        # Strategy 2: Extract from github_repo
        if 'github_repo' in metadata:
            repo_name = metadata['github_repo'].split('/')[-1].replace('.git', '')
            path = os.path.join(Config.PROJECTS_DIR, repo_name)
            if os.path.exists(os.path.join(path, '.git')):
                return path

        # Strategy 3: Project slug (title converted to slug)
        project_slug = project['title'].lower().replace(' ', '-')
        path = os.path.join(Config.PROJECTS_DIR, project_slug)
        if os.path.exists(os.path.join(path, '.git')):
            return path

        return None

    def _get_structure(self, repo_path):
        """Get directory tree structure"""
        try:
            result = subprocess.run(
                ['tree', '-L', '2', '-I', 'node_modules|venv|__pycache__|.git|dist|build', repo_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return "Tree command not available or timed out"

    def _detect_languages(self, repo_path):
        """Detect programming languages used in repository"""
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React (JSX)',
            '.tsx': 'React (TSX)',
            '.go': 'Go',
            '.rs': 'Rust',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.sh': 'Shell',
            '.sql': 'SQL',
            '.html': 'HTML',
            '.css': 'CSS',
            '.md': 'Markdown'
        }

        found_languages = set()
        exclude_dirs = {'node_modules', 'venv', '__pycache__', '.git', 'dist', 'build'}

        for root, dirs, files in os.walk(repo_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                ext = Path(file).suffix.lower()
                if ext in extension_map:
                    found_languages.add(extension_map[ext])

        return sorted(list(found_languages))

    def _get_commits(self, repo_path, limit=10):
        """Get recent commit history"""
        try:
            result = subprocess.run(
                ['git', '-C', repo_path, 'log', f'-{limit}',
                 '--pretty=format:%h|%an|%ar|%s'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                commits = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split('|', 3)
                        if len(parts) == 4:
                            commits.append({
                                'hash': parts[0],
                                'author': parts[1],
                                'date': parts[2],
                                'message': parts[3]
                            })
                return commits
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return []

    def _get_dependencies(self, repo_path):
        """Extract dependency information from common files"""
        deps = {}

        # Python - requirements.txt
        req_file = os.path.join(repo_path, 'requirements.txt')
        if os.path.exists(req_file):
            try:
                with open(req_file, 'r') as f:
                    deps['python'] = [
                        line.strip()
                        for line in f
                        if line.strip() and not line.startswith('#')
                    ][:15]  # Limit to first 15
            except:
                pass

        # Node.js - package.json
        pkg_file = os.path.join(repo_path, 'package.json')
        if os.path.exists(pkg_file):
            try:
                import json
                with open(pkg_file, 'r') as f:
                    pkg_data = json.load(f)
                    deps['node'] = {
                        'dependencies': list(pkg_data.get('dependencies', {}).keys())[:15],
                        'devDependencies': list(pkg_data.get('devDependencies', {}).keys())[:10]
                    }
            except:
                pass

        # Go - go.mod
        go_file = os.path.join(repo_path, 'go.mod')
        if os.path.exists(go_file):
            try:
                with open(go_file, 'r') as f:
                    go_deps = []
                    for line in f:
                        if line.strip().startswith('require'):
                            continue
                        if '\t' in line or '    ' in line:  # Indented dependency
                            go_deps.append(line.strip().split()[0])
                    deps['go'] = go_deps[:15]
            except:
                pass

        return deps

    def _count_files(self, repo_path):
        """Count total files in repository"""
        count = 0
        exclude_dirs = {'node_modules', 'venv', '__pycache__', '.git', 'dist', 'build'}

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            count += len(files)

        return count
