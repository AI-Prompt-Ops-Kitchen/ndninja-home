"""
Keyword detector for action item completion tracking.

This module analyzes tool output for completion keywords and calculates
confidence scores to determine whether an action item has been completed.
"""

import re
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class DetectionResult:
    """Result of keyword detection analysis"""
    keyword_found: Optional[str]
    confidence: int  # 0-100
    category: str   # commit-related, deployment, test-success, bug-fixed, build-success, file-created
    context_snippet: str  # surrounding context


class KeywordDetector:
    """Detects completion keywords in tool output and calculates confidence scores"""

    # Define completion keywords organized by category
    KEYWORDS = {
        "commit-related": [
            "git commit",
            "committed",
            "commit complete",
            "commit -m",
        ],
        "deployment": [
            "deployed",
            "pushed to",
            "live on",
            "deployment successful",
        ],
        "test-success": [
            "all tests passed",
            "tests passing",
            "test suite passed",
            "passed",
            "✅ passing",
        ],
        "bug-fixed": [
            "fixed",
            "resolved",
            "bug resolved",
            "patch applied",
        ],
        "build-success": [
            "build successful",
            "build complete",
            "compiled",
        ],
        "file-created": [
            "created",
            "written to",
            "saved",
        ],
    }

    # Keywords that indicate failure/error context
    FAILURE_INDICATORS = [
        "failed",
        "error",
        "failed to",
        "unable to",
        "could not",
        "connection timeout",
        "unauthorized",
        "403",
        "404",
    ]

    def __init__(self):
        """Initialize the keyword detector"""
        self._compiled_keywords = self._compile_keywords()

    def _compile_keywords(self) -> Dict[str, List[re.Pattern]]:
        """Compile keyword patterns for efficient matching"""
        compiled = {}
        for category, keywords in self.KEYWORDS.items():
            compiled[category] = [
                re.compile(re.escape(kw), re.IGNORECASE)
                for kw in keywords
            ]
        return compiled

    def detect(self, tool_output: str) -> Optional[DetectionResult]:
        """
        Analyze tool output for completion keywords and calculate confidence.

        Args:
            tool_output: The output string from a tool execution

        Returns:
            DetectionResult if keyword(s) found with reasonable confidence, None otherwise
        """
        if not tool_output or not isinstance(tool_output, str):
            return None

        # Search for all matching keywords and their positions
        matches = self._find_all_matches(tool_output)

        if not matches:
            return None

        # Score each match and return the highest confidence one
        scored_matches = [self._score_match(match, tool_output) for match in matches]
        scored_matches.sort(key=lambda x: x[1], reverse=True)  # Sort by confidence

        if scored_matches and scored_matches[0][1] >= 60:  # Minimum 60% confidence
            match_info, confidence = scored_matches[0]
            category, keyword, start, end = match_info

            context_snippet = self._extract_context(tool_output, start, end)

            return DetectionResult(
                keyword_found=keyword,
                confidence=confidence,
                category=category,
                context_snippet=context_snippet,
            )

        return None

    def _find_all_matches(self, tool_output: str) -> List[Tuple[str, str, int, int]]:
        """
        Find all keyword matches in the tool output.

        Returns:
            List of (category, keyword, start_pos, end_pos) tuples
        """
        matches = []

        for category, patterns in self._compiled_keywords.items():
            for pattern in patterns:
                for match in pattern.finditer(tool_output):
                    # Get the original (unescaped) keyword for display
                    matched_text = match.group(0)
                    matches.append((category, matched_text, match.start(), match.end()))

        return matches

    def _score_match(
        self, match: Tuple[str, str, int, int], tool_output: str
    ) -> Tuple[Tuple[str, str, int, int], int]:
        """
        Score a keyword match based on context analysis.

        Args:
            match: (category, keyword, start_pos, end_pos)
            tool_output: The full tool output

        Returns:
            (match_info, confidence_score) tuple
        """
        category, keyword, start, end = match
        base_confidence = 85  # Base confidence for keyword match

        # Extract surrounding context (500 chars before and after)
        context_start = max(0, start - 500)
        context_end = min(len(tool_output), end + 500)
        context = tool_output[context_start:context_end]

        # Penalize if failure indicators are nearby
        failure_penalty = 0
        for failure_indicator in self.FAILURE_INDICATORS:
            if failure_indicator.lower() in context.lower():
                # Check if failure indicator is close to keyword
                failure_pos = context.lower().find(failure_indicator.lower())
                keyword_pos = context.lower().find(keyword.lower())

                if failure_pos != -1 and keyword_pos != -1:
                    distance = abs(failure_pos - keyword_pos)
                    # Strong penalty if failure indicator is within 50 chars
                    if distance < 50:
                        failure_penalty = 40
                    # Moderate penalty if within 150 chars
                    elif distance < 150:
                        failure_penalty = 20

        confidence = max(0, base_confidence - failure_penalty)

        # Boost confidence if certain positive indicators are present
        if self._has_positive_indicators(context, category):
            confidence = min(100, confidence + 10)

        return (match, confidence)

    def _has_positive_indicators(self, context: str, category: str) -> bool:
        """
        Check if context has positive indicators for the category.

        Args:
            context: The surrounding context text
            category: The keyword category

        Returns:
            True if positive indicators found
        """
        positive_indicators = {
            "commit-related": [
                "success",
                "complete",
                "done",
                "all done",
                "changed",
                "file changed",
            ],
            "deployment": [
                "success",
                "live",
                "available",
                "working",
                "production",
                "staging",
            ],
            "test-success": [
                "success",
                "all",
                "passed",
                "passing",
                "✅",
                "okay",
            ],
            "bug-fixed": [
                "success",
                "resolved",
                "fixed",
                "complete",
                "working",
            ],
            "build-success": [
                "success",
                "complete",
                "done",
                "built",
            ],
            "file-created": [
                "success",
                "complete",
                "written",
                "created",
                "new",
            ],
        }

        indicators = positive_indicators.get(category, [])
        context_lower = context.lower()

        return any(indicator.lower() in context_lower for indicator in indicators)

    def _extract_context(self, tool_output: str, start: int, end: int, max_length: int = 200) -> str:
        """
        Extract a reasonable snippet of context around the keyword match.

        Args:
            tool_output: The full tool output
            start: Start position of the keyword
            end: End position of the keyword
            max_length: Maximum length of context snippet

        Returns:
            Context snippet containing the keyword
        """
        # Try to include some context before and after
        context_before = max(0, start - 50)
        context_after = min(len(tool_output), end + 50)

        snippet = tool_output[context_before:context_after]

        # Truncate if too long
        if len(snippet) > max_length:
            # Try to keep the keyword in view
            keyword_pos = start - context_before
            start_trim = max(0, keyword_pos - (max_length // 2))
            end_trim = start_trim + max_length
            snippet = snippet[start_trim:end_trim]
            if start_trim > 0:
                snippet = "..." + snippet
            if end_trim < len(tool_output) - context_before:
                snippet = snippet + "..."

        return snippet.strip()
