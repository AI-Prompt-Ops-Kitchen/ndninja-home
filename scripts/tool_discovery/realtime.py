"""
Real-time keyword detection for tool discovery.

Scans user prompts for high-value tool keywords and suggests relevant tools
with rate limiting to avoid overwhelming the user.
"""

from typing import Optional, Dict, List
import json
import os
import re
from database import ToolDatabase


class RealtimeDiscovery:
    """Real-time tool discovery through keyword detection"""

    # Keyword patterns mapping to tool names
    KEYWORD_PATTERNS = {
        r'multi-model|consensus|vpn analysis': 'llm-council',
        r'distributed|kage bunshin|72b': 'kage-bunshin',
        r'docker environment|container debug': 'docker-env-debugger'
    }

    RATE_LIMIT_MESSAGES = 5

    def __init__(self):
        """Initialize real-time discovery with state persistence"""
        self.state_file = f"/tmp/tool-discovery-session-{os.getpid()}.json"
        self.db = ToolDatabase()
        self._load_state()

    def _load_state(self):
        """Load session state from disk or initialize new state"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.state = self._init_state()
        else:
            self.state = self._init_state()

    def _init_state(self) -> Dict:
        """Initialize new state dict"""
        return {
            'message_count': 0,
            'last_suggestion': None,
            'suggested_tools': []
        }

    def _save_state(self):
        """Save state to disk"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f)
        except IOError:
            pass  # Silent fail for state persistence

    def reset(self):
        """Reset state for testing purposes"""
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
        self._load_state()

    def check_rate_limit(self) -> bool:
        """
        Returns True if suggestion allowed, False if rate-limited.

        Rate limit: 1 suggestion per RATE_LIMIT_MESSAGES messages.
        """
        return self.state['message_count'] < self.RATE_LIMIT_MESSAGES

    def match_keywords(self, prompt: str) -> Optional[Dict]:
        """
        Scan prompt for keyword matches, return tool data or None.

        Args:
            prompt: User prompt to scan for keywords

        Returns:
            Dict with tool data if match found, None otherwise
        """
        if not prompt:
            return None

        # Convert to lowercase for case-insensitive matching
        prompt_lower = prompt.lower()

        # Check each pattern
        for pattern, tool_name in self.KEYWORD_PATTERNS.items():
            if re.search(pattern, prompt_lower):
                # Found a match - return minimal tool data
                # In production, this would query the database for full tool info
                return {
                    'tool_name': tool_name,
                    'command': f'/{tool_name}',
                    'description': self._get_tool_description(tool_name),
                    'keywords': pattern.split('|')
                }

        return None

    def _get_tool_description(self, tool_name: str) -> str:
        """Get tool description from database or return placeholder"""
        # Map tool names to descriptions
        # In production, this would query the database
        descriptions = {
            'llm-council': 'Multi-model consensus analysis',
            'kage-bunshin': 'Distributed AI cluster processing',
            'docker-env-debugger': 'Docker environment debugging'
        }
        return descriptions.get(tool_name, 'No description available')

    def format_suggestion(self, tool: Dict) -> str:
        """
        Format real-time suggestion with emoji indicator.

        Args:
            tool: Tool dict with tool_name, command, description

        Returns:
            Formatted suggestion string
        """
        lines = [
            f"💡 Detected tool suggestion:",
            f"",
            f"Tool: {tool['tool_name']}",
            f"Command: {tool['command']}",
            f"Description: {tool['description']}",
        ]

        return "\n".join(lines)

    def suggest_tool(self, prompt: str) -> Optional[str]:
        """
        Main entry point - check rate limit, match keywords, format suggestion.

        Args:
            prompt: User prompt to analyze

        Returns:
            Formatted suggestion string or None if rate-limited or no match
        """
        # Check rate limit
        if not self.check_rate_limit():
            self.state['message_count'] += 1
            self._save_state()
            return None

        # Match keywords
        tool = self.match_keywords(prompt)
        if not tool:
            self.state['message_count'] += 1
            self._save_state()
            return None

        # Check if already suggested this tool
        if tool['tool_name'] in self.state['suggested_tools']:
            self.state['message_count'] += 1
            self._save_state()
            return None

        # Format and return suggestion
        suggestion = self.format_suggestion(tool)

        # Update state
        self.state['suggested_tools'].append(tool['tool_name'])
        self.state['last_suggestion'] = tool['tool_name']
        self.state['message_count'] = 0  # Reset counter after suggestion
        self._save_state()

        return suggestion


def main():
    """Example usage"""
    discovery = RealtimeDiscovery()

    # Test prompts
    prompts = [
        "I need multi-model consensus for this analysis",
        "What's the weather today?",
        "Can you use the distributed 72b model?",
        "How do I debug my docker environment?",
    ]

    for prompt in prompts:
        print(f"\nPrompt: {prompt}")
        suggestion = discovery.suggest_tool(prompt)
        if suggestion:
            print(suggestion)
        else:
            print("No suggestion (rate-limited or no match)")


if __name__ == '__main__':
    main()
