from datetime import datetime, timedelta
from typing import List, Dict

class ToolScorer:
    """Score tools against conversation topics"""

    EXACT_MATCH = 10
    PARTIAL_MATCH = 5
    RECENT_BONUS = 3  # Used in last 7 days
    HIGH_USAGE_BONUS = 2  # Use count > 10

    def score_tool(self, tool: Dict, topics: List[str]) -> int:
        """
        Score a tool against conversation topics

        Args:
            tool: Tool dict with 'data' containing keywords, last_used, use_count
            topics: List of topic strings from conversation

        Returns:
            Total score for this tool
        """
        score = 0
        tool_data = tool.get('data', {})
        keywords = tool_data.get('keywords', [])

        # Tokenize topics
        topic_tokens = []
        for topic in topics:
            topic_tokens.extend(topic.lower().split())

        # Keyword matching
        for keyword in keywords:
            keyword_lower = keyword.lower()

            # Exact match
            if keyword_lower in topic_tokens:
                score += self.EXACT_MATCH
                continue

            # Partial match (substring)
            for token in topic_tokens:
                if keyword_lower in token or token in keyword_lower:
                    score += self.PARTIAL_MATCH
                    break

        # Recent usage bonus
        last_used = tool_data.get('last_used')
        if last_used:
            try:
                last_used_date = datetime.strptime(last_used, '%Y-%m-%d')
                days_ago = (datetime.now() - last_used_date).days
                if days_ago <= 7:
                    score += self.RECENT_BONUS
            except ValueError:
                pass

        # High usage bonus
        use_count = tool_data.get('use_count', 0)
        if use_count > 10:
            score += self.HIGH_USAGE_BONUS

        return score

    def rank_tools(self, tools: List[Dict], topics: List[str], limit: int = 5) -> List[Dict]:
        """
        Rank tools by score and return top N

        Args:
            tools: List of tool dicts
            topics: Conversation topics
            limit: Maximum tools to return

        Returns:
            List of (tool, score) tuples, sorted by score descending
        """
        scored = []
        for tool in tools:
            score = self.score_tool(tool, topics)
            if score > 0:  # Only include tools with matches
                scored.append((tool, score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[:limit]
