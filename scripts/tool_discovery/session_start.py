"""
SessionStartDiscovery - Get relevant tools based on recent conversation topics

This module queries recent conversations from the database, extracts topics,
and ranks tools using the ToolScorer. Used at session start to suggest
relevant tools based on conversation history.
"""

import sys
from typing import List, Dict, Tuple
from database import ToolDatabase
from scorer import ToolScorer


class SessionStartDiscovery:
    """Discover relevant tools at session start based on conversation history"""

    def __init__(self):
        """Initialize discovery components"""
        self.db = ToolDatabase()
        self.scorer = ToolScorer()

    def extract_topics(self, conversations: List[Dict]) -> List[str]:
        """
        Extract topics from conversation list

        Args:
            conversations: List of conversation dicts with 'topics_discussed' field

        Returns:
            Flat list of all topics from all conversations
        """
        topics = []

        for conversation in conversations:
            conversation_topics = conversation.get('topics_discussed')

            # Handle None/null topics
            if conversation_topics is None:
                continue

            # Handle both list and JSONB array
            if isinstance(conversation_topics, list):
                topics.extend(conversation_topics)
            elif isinstance(conversation_topics, str):
                # In case it's a JSON string
                import json
                try:
                    parsed = json.loads(conversation_topics)
                    if isinstance(parsed, list):
                        topics.extend(parsed)
                except json.JSONDecodeError:
                    pass

        return topics

    def get_relevant_tools(self, limit: int = 5) -> List[Tuple[Dict, int]]:
        """
        Query DB for recent conversations, extract topics, and rank tools

        Args:
            limit: Maximum number of tools to return

        Returns:
            List of (tool, score) tuples, sorted by score descending
        """
        try:
            # Connect to database
            if not self.db.connect():
                print("Failed to connect to database", file=sys.stderr)
                return []

            try:
                # Get recent conversations (last 5)
                cursor = self.db.conn.cursor()
                try:
                    cursor.execute("""
                        SELECT topics_discussed
                        FROM conversation_summaries
                        ORDER BY created_at DESC
                        LIMIT 5
                    """)

                    rows = cursor.fetchall()

                    # Extract topics from rows, handling NULL values
                    conversations = []
                    for row in rows:
                        topics_discussed = row[0] if row[0] else []
                        conversations.append({
                            'topics_discussed': topics_discussed
                        })

                    # Extract all topics
                    topics = self.extract_topics(conversations)

                    # If no topics found, return empty list
                    if not topics:
                        return []

                    # Get all tools
                    tools = self.db.get_all_tools()

                    if not tools:
                        return []

                    # Rank tools using scorer
                    ranked = self.scorer.rank_tools(tools, topics, limit=limit)

                    return ranked

                finally:
                    cursor.close()

            finally:
                self.db.close()

        except Exception as e:
            print(f"Error getting relevant tools: {e}", file=sys.stderr)
            return []

    def format_suggestions(self, tools: List[Tuple[Dict, int]]) -> str:
        """
        Format tool suggestions for display

        Args:
            tools: List of (tool, score) tuples

        Returns:
            Formatted string with tool names, commands, and scores
        """
        if not tools:
            return "No relevant tools found based on recent conversations."

        lines = ["Suggested tools based on recent conversations:\n"]

        for i, (tool, score) in enumerate(tools, 1):
            tool_data = tool.get('data', {})
            name = tool_data.get('name', 'Unknown')
            command = tool_data.get('command', 'N/A')
            description = tool_data.get('description', 'No description')

            lines.append(f"{i}. {name} (score: {score})")
            lines.append(f"   Command: {command}")
            lines.append(f"   {description}\n")

        return "\n".join(lines)


def main():
    """Example usage"""
    discovery = SessionStartDiscovery()

    # Get relevant tools
    tools = discovery.get_relevant_tools(limit=5)

    # Format and print suggestions
    suggestions = discovery.format_suggestions(tools)
    print(suggestions)


if __name__ == '__main__':
    main()
