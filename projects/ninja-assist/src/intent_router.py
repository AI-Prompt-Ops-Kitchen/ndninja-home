"""
Ninja Assist - Intent Router
============================
Classifies plain language requests into actionable intents using pattern matching.
ZERO LLM tokens used - pure regex/keyword matching.

Categories:
- code: Programming, debugging, implementation tasks
- research: Information gathering, lookups, analysis
- install: Package installation, updates, dependencies
- design: Brainstorming, planning, architecture discussions
- unknown: Ambiguous requests that need LLM handling
"""

import re
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class IntentCategory(Enum):
    CODE = "code"
    RESEARCH = "research"
    INSTALL = "install"
    DESIGN = "design"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Structured intent classification result."""
    category: str
    confidence: float  # 0.0 - 1.0
    suggested_tool: Optional[str]
    original_text: str
    matched_pattern: Optional[str] = None  # For debugging


# Tool mappings per category
TOOL_MAP = {
    IntentCategory.CODE: "claude_code",
    IntentCategory.RESEARCH: "web_search",
    IntentCategory.INSTALL: "exec",
    IntentCategory.DESIGN: "shadow_council",
    IntentCategory.UNKNOWN: None,
}


# Pattern definitions with confidence scores
# Higher specificity = higher confidence
PATTERNS = {
    IntentCategory.CODE: [
        # High confidence - explicit coding keywords
        (r'\b(write|create|code|implement|build|develop|program)\b.*\b(function|class|script|module|api|endpoint|component)\b', 0.95),
        (r'\bfix\b.*\b(bug|error|issue|crash|exception)\b', 0.95),
        (r'\bdebug\b', 0.90),
        (r'\brefactor\b', 0.90),
        (r'\badd\b.*\b(feature|function|method|endpoint)\b', 0.90),
        
        # Medium confidence - action + code context
        (r'\b(write|create|make|build)\b.*\b(python|javascript|typescript|rust|go|java|ruby|php|bash|shell)\b', 0.85),
        (r'\bhelp\s+(me\s+)?(with\s+)?(the\s+)?cod(e|ing)\b', 0.85),
        (r'\b(parse|serialize|deserialize|validate|transform)\b.*\bdata\b', 0.85),
        (r'\bunit\s*test', 0.85),
        (r'\btest\s+case', 0.85),
        
        # Programming language mentions with action context
        (r'\b(in|using|with)\s+(python|javascript|typescript|rust|go)\b', 0.75),
        
        # Lower confidence - general coding terms
        (r'\b(function|method|class|module|script|api)\b', 0.70),
        (r'\bhow\s+(do\s+i|to)\s+(code|implement|write)\b', 0.70),
        (r'\bcode\s+(this|that|it)\b', 0.80),
        (r'\blet\'?s?\s+code\b', 0.85),
        
        # Error/fix context
        (r'\b(error|exception|traceback|stack\s*trace)\b', 0.65),
        (r'\b(doesn\'t|does\s*n[o\']t|won\'t|isn\'t)\s+work', 0.60),
    ],
    
    IntentCategory.RESEARCH: [
        # High confidence - explicit research intent
        (r'\b(research|look\s*up|find\s+(out|info|information))\b', 0.95),
        (r'\bwhat\s+is\b.*\?', 0.85),
        (r'\bhow\s+does\b.*\bwork\b', 0.85),
        (r'\bwhat\s+are\s+the\b.*\b(best|top|popular)\b', 0.90),
        
        # Search intent
        (r'\bsearch\s+(for|about)\b', 0.90),
        (r'\blook\s+into\b', 0.85),
        (r'\bfind\s+(me\s+)?(articles?|info|resources?|docs?|documentation)\b', 0.90),
        
        # Comparison/analysis
        (r'\bcompare\b.*\b(vs|versus|and|with)\b', 0.85),
        (r'\b(pros?\s*(and|&)?\s*cons?|advantages|disadvantages)\b', 0.85),
        (r'\bwhat\'?s?\s+the\s+difference\s+between\b', 0.90),
        
        # Learning intent
        (r'\blearn\s+(about|more)\b', 0.80),
        (r'\bexplain\b.*\bto\s+me\b', 0.80),
        (r'\bcan\s+you\s+explain\b', 0.80),
        (r'\btell\s+me\s+about\b', 0.85),
        
        # General queries
        (r'\bhow\s+(do|can|should)\s+(i|we|you)\b', 0.60),  # Lower - could be code
        (r'\bwhy\s+(does|is|do|are)\b', 0.75),
    ],
    
    IntentCategory.INSTALL: [
        # High confidence - explicit install/update
        (r'\b(install|uninstall|reinstall)\b', 0.95),
        (r'\b(update|upgrade|downgrade)\b.*\b(package|library|dependency|dep|tool|cli)\b', 0.95),
        (r'\b(npm|pip|cargo|brew|apt|yum|pacman|yarn|pnpm)\s+(install|update|upgrade|add|remove)\b', 0.98),
        
        # Package management
        (r'\badd\b.*\b(package|dependency|lib|library)\b', 0.90),
        (r'\bremove\b.*\b(package|dependency|lib|library)\b', 0.90),
        (r'\b(setup|configure)\s+(my\s+)?(environment|dev\s*env|project)\b', 0.85),
        
        # Version management
        (r'\b(update|upgrade)\s+(all|everything|packages?|deps?|dependencies)\b', 0.90),
        (r'\bpin\b.*\bversion\b', 0.85),
        (r'\block\b.*\b(file|version)\b', 0.85),
        
        # Tool installation
        (r'\bget\s+(me\s+)?(\w+)\s+(installed|set\s*up|running)\b', 0.85),
        (r'\bset\s*up\b.*(environment|env|project|workspace)\b', 0.85),
        (r'\bset\s*up\b', 0.70),  # Lower - could be design
        (r'\bneed\s+(to\s+)?(install|update)\b', 0.90),
    ],
    
    IntentCategory.DESIGN: [
        # High confidence - explicit design/brainstorm
        (r'\b(brainstorm|ideate|spitball)\b', 0.95),
        (r'\bdesign\b.*\b(system|architecture|solution|approach)\b', 0.95),
        (r'\barchitect(ure)?\b', 0.90),
        
        # Planning intent
        (r'\b(plan|planning)\b.*\b(project|feature|sprint)\b', 0.90),
        (r'\bhow\s+should\s+(we|i)\s+(approach|design|structure|architect)\b', 0.90),
        (r'\bwhat\'?s?\s+the\s+best\s+(way|approach|strategy)\s+to\b', 0.85),
        
        # Discussion/exploration
        (r'\blet\'?s?\s+(think|discuss|talk)\s+about\b', 0.85),
        (r'\bi\s+need\s+(ideas?|suggestions?|options?)\b', 0.85),
        (r'\bhelp\s+me\s+think\s+through\b', 0.90),
        (r'\bshould\s+(i|we)\b.*\bor\b', 0.80),  # Decision making
        
        # Strategy/approach
        (r'\bwhat\s+do\s+you\s+think\s+about\b', 0.75),
        (r'\b(strategy|roadmap|plan)\b', 0.80),
        (r'\bweigh\s+(in|options?)\b', 0.85),
        
        # RFC/Proposal
        (r'\b(rfc|proposal|spec|specification)\b', 0.85),
        (r'\btrade\s*off', 0.85),
    ],
}


def classify_intent(text: str) -> Intent:
    """
    Classify plain language text into an intent category.
    
    Uses pattern matching with confidence scoring.
    Returns 'unknown' for ambiguous requests that need LLM handling.
    
    Args:
        text: Plain language request from user
        
    Returns:
        Intent object with category, confidence, suggested tool, and original text
    """
    text_lower = text.lower().strip()
    
    best_match: Optional[tuple[IntentCategory, float, str]] = None
    
    # Check all patterns, keep highest confidence match
    for category, patterns in PATTERNS.items():
        for pattern, base_confidence in patterns:
            match = re.search(pattern, text_lower)
            if match:
                # Adjust confidence based on match quality
                # Longer matches = higher confidence
                match_len = len(match.group(0))
                text_len = len(text_lower)
                length_bonus = min(0.1, match_len / text_len * 0.1)
                
                confidence = min(1.0, base_confidence + length_bonus)
                
                if best_match is None or confidence > best_match[1]:
                    best_match = (category, confidence, pattern)
    
    # Handle results
    if best_match is None or best_match[1] < 0.5:
        # No match or too low confidence - needs LLM
        return Intent(
            category=IntentCategory.UNKNOWN.value,
            confidence=0.0 if best_match is None else best_match[1],
            suggested_tool=None,
            original_text=text,
            matched_pattern=None if best_match is None else best_match[2],
        )
    
    category, confidence, pattern = best_match
    
    return Intent(
        category=category.value,
        confidence=round(confidence, 2),
        suggested_tool=TOOL_MAP[category],
        original_text=text,
        matched_pattern=pattern,
    )


def route_request(text: str) -> dict:
    """
    Convenience function that returns intent as a dictionary.
    Useful for JSON serialization.
    """
    intent = classify_intent(text)
    return {
        "category": intent.category,
        "confidence": intent.confidence,
        "suggested_tool": intent.suggested_tool,
        "original_text": intent.original_text,
    }


# =============================================================================
# TEST CASES
# =============================================================================
def run_tests():
    """Run test cases to verify pattern matching."""
    
    test_cases = [
        # CODE tests
        ("help me code a function to parse JSON", "code", 0.80),
        ("write a Python script to scrape websites", "code", 0.80),
        ("fix the bug in the login handler", "code", 0.90),
        ("debug this error", "code", 0.85),
        ("create a REST API endpoint", "code", 0.90),
        ("refactor the database module", "code", 0.85),
        ("let's code", "code", 0.80),
        ("add unit tests for the parser", "code", 0.80),
        
        # RESEARCH tests
        ("research the best JavaScript frameworks", "research", 0.80),
        ("what is the difference between REST and GraphQL?", "research", 0.80),
        ("look up how Kubernetes works", "research", 0.80),
        ("compare React vs Vue", "research", 0.80),
        ("find me articles about machine learning", "research", 0.85),
        ("what are the pros and cons of microservices?", "research", 0.80),
        ("tell me about WebSockets", "research", 0.80),
        
        # INSTALL tests
        ("install numpy", "install", 0.90),
        ("npm install react", "install", 0.95),
        ("update all my packages", "install", 0.85),
        ("pip install -r requirements.txt", "install", 0.95),
        ("add the axios dependency", "install", 0.85),
        ("set up my development environment", "install", 0.80),
        ("I need to install Docker", "install", 0.85),
        
        # DESIGN tests
        ("let's brainstorm the architecture", "design", 0.90),
        ("how should we approach the caching layer?", "design", 0.85),
        ("I need ideas for the onboarding flow", "design", 0.80),
        ("help me think through the database schema", "design", 0.85),
        ("what's the best strategy for scaling?", "design", 0.80),
        ("design a system for user authentication", "design", 0.90),
        ("should I use SQL or NoSQL?", "design", 0.75),
        
        # UNKNOWN tests - ambiguous requests
        ("hello", "unknown", 0.0),
        ("thanks", "unknown", 0.0),
        ("hmm", "unknown", 0.0),
        ("do the thing", "unknown", 0.0),
    ]
    
    print("=" * 70)
    print("NINJA ASSIST - INTENT ROUTER TESTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for text, expected_category, min_confidence in test_cases:
        intent = classify_intent(text)
        
        category_match = intent.category == expected_category
        confidence_match = intent.confidence >= min_confidence
        
        if category_match and confidence_match:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"\n{status}")
        print(f"  Input: {text!r}")
        print(f"  Expected: {expected_category} (≥{min_confidence})")
        print(f"  Got: {intent.category} ({intent.confidence})")
        print(f"  Tool: {intent.suggested_tool}")
        if intent.matched_pattern:
            print(f"  Pattern: {intent.matched_pattern[:50]}...")
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{passed + failed} passed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    
    # If arguments provided, classify them
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        intent = classify_intent(text)
        print(f"\nInput: {text}")
        print(f"Category: {intent.category}")
        print(f"Confidence: {intent.confidence}")
        print(f"Tool: {intent.suggested_tool}")
    else:
        # Run tests
        success = run_tests()
        sys.exit(0 if success else 1)
