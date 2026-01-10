"""
Git Manager - Handles git commits for reflection updates
"""

import subprocess
from typing import Optional
from pathlib import Path
from analyzer import Reflection
from config import GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL, HOME_DIR


class GitManager:
    """Manages git commits for skill reflection updates"""

    def __init__(self):
        self.repo_dir = HOME_DIR
        self.author_name = GIT_AUTHOR_NAME
        self.author_email = GIT_AUTHOR_EMAIL

    def commit_reflection(self, skill_name: str, reflection: Reflection) -> Optional[str]:
        """
        Commits skill file update with structured message.

        Args:
            skill_name: Name of the skill that was updated
            reflection: Reflection object with update details

        Returns:
            Commit SHA if successful, None otherwise
        """
        skill_file = f".claude/skills/{skill_name}.md"

        try:
            # Add the skill file (force add even if in .gitignore)
            self._run_git(['add', '-f', skill_file])

            # Build commit message
            commit_msg = self._build_commit_message(skill_name, reflection)

            # Commit with author info
            self._run_git([
                'commit',
                '-m', commit_msg,
                '--author', f'{self.author_name} <{self.author_email}>'
            ])

            # Get commit SHA
            result = self._run_git(['rev-parse', 'HEAD'])
            return result.strip() if result else None

        except subprocess.CalledProcessError as e:
            print(f"Git error: {e}")
            return None

    def _build_commit_message(self, skill_name: str, reflection: Reflection) -> str:
        """Build structured commit message for reflection"""
        # First line: summary
        summary = f"Reflect: Update {skill_name}"

        # Body: details
        body_lines = [
            '',  # Blank line after summary
            f"Signal: {reflection.signal_type}",
            f"Confidence: {reflection.confidence}",
            f"Session: {reflection.source_session}",
            '',
            reflection.what_changed,
            '',
            f'Co-Authored-By: {self.author_name} <{self.author_email}>'
        ]

        return summary + '\n' + '\n'.join(body_lines)

    def _run_git(self, args: list) -> Optional[str]:
        """
        Run git command in the repository directory.

        Args:
            args: Git command arguments (e.g., ['status', '--short'])

        Returns:
            Command output as string, or None on error
        """
        try:
            result = subprocess.run(
                ['git'] + args,
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: git {' '.join(args)}")
            print(f"Error: {e.stderr}")
            raise

    def get_skill_history(self, skill_name: str, limit: int = 10) -> list:
        """
        Get git history for a skill file.

        Args:
            skill_name: Name of the skill
            limit: Number of commits to retrieve

        Returns:
            List of commit info dicts
        """
        skill_file = f".claude/skills/{skill_name}.md"

        try:
            output = self._run_git([
                'log',
                f'-{limit}',
                '--pretty=format:%H|%an|%ae|%ad|%s',
                '--date=short',
                '--',
                skill_file
            ])

            if not output:
                return []

            commits = []
            for line in output.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        'sha': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4]
                    })

            return commits

        except subprocess.CalledProcessError:
            return []

    def show_diff(self, skill_name: str, commit_sha: Optional[str] = None) -> str:
        """
        Show diff for a skill file.

        Args:
            skill_name: Name of the skill
            commit_sha: Specific commit SHA, or None for uncommitted changes

        Returns:
            Diff output as string
        """
        skill_file = f".claude/skills/{skill_name}.md"

        try:
            if commit_sha:
                # Show diff for specific commit
                output = self._run_git(['show', f'{commit_sha}', '--', skill_file])
            else:
                # Show uncommitted changes
                output = self._run_git(['diff', 'HEAD', '--', skill_file])

            return output or "No changes"

        except subprocess.CalledProcessError:
            return "Error retrieving diff"

    def rollback_reflection(self, commit_sha: str) -> bool:
        """
        Rollback a reflection commit.

        Args:
            commit_sha: SHA of the commit to revert

        Returns:
            True if successful, False otherwise
        """
        try:
            self._run_git(['revert', '--no-edit', commit_sha])
            return True
        except subprocess.CalledProcessError:
            return False

    def is_repo_clean(self) -> bool:
        """Check if repository has uncommitted changes"""
        try:
            output = self._run_git(['status', '--short'])
            return not output or len(output.strip()) == 0
        except subprocess.CalledProcessError:
            return False

    def get_current_branch(self) -> Optional[str]:
        """Get current git branch name"""
        try:
            output = self._run_git(['branch', '--show-current'])
            return output.strip() if output else None
        except subprocess.CalledProcessError:
            return None
