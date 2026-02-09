# .claude/hooks/lib/context7_fingerprint.py
import re
from typing import Optional

# Intent keyword mappings (expand as needed)
INTENT_KEYWORDS = {
    'authentication': ['auth', 'authenticate', 'login', 'signup', 'sign up', 'session', 'oauth'],
    'routing': ['route', 'routing', 'navigation', 'navigate', 'url', 'path'],
    'hooks': ['hook', 'useeffect', 'usestate', 'usememo', 'usecallback'],
    'forms': ['form', 'input', 'validation', 'submit'],
    'database': ['db', 'database', 'query', 'sql', 'migration', 'model'],
    'testing': ['test', 'testing', 'spec', 'jest', 'pytest', 'rspec'],
    'styling': ['css', 'style', 'styling', 'theme', 'design'],
    'api': ['api', 'rest', 'graphql', 'endpoint', 'request', 'response'],
    'state': ['state', 'redux', 'context', 'store'],
    'performance': ['performance', 'optimize', 'optimization', 'cache', 'caching'],
}

def extract_intent(query: str) -> str:
    """
    Extract main intent from query using keyword matching.

    Returns most specific matching intent or 'general' if no match.
    """
    query_lower = query.lower()

    # Check each intent category
    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                return intent

    # Fall back to first significant word (3+ chars)
    words = re.findall(r'\b\w{3,}\b', query_lower)
    if words:
        # Filter out common words
        common_words = {'how', 'what', 'when', 'where', 'why', 'the', 'and', 'for', 'with'}
        significant = [w for w in words if w not in common_words]
        if significant:
            return significant[0]

    return 'general'

def generate_fingerprint(library: str, major_version: str, query: str) -> str:
    """
    Generate cache fingerprint for Context7 query.

    Format: {library}-{major_version}:{intent}
    Example: rails-7:authentication
    """
    intent = extract_intent(query)
    return f"{library}-{major_version}:{intent}"

def parse_fingerprint(fingerprint: str) -> Optional[dict]:
    """
    Parse fingerprint back into components.

    Returns: {'library': str, 'version': str, 'intent': str} or None
    """
    match = re.match(r'^([^-]+)-(\d+):(.+)$', fingerprint)
    if match:
        return {
            'library': match.group(1),
            'version': match.group(2),
            'intent': match.group(3)
        }
    return None
