# .claude/hooks/lib/test_context7_fingerprint.py
import pytest
from context7_fingerprint import generate_fingerprint, extract_intent

def test_extract_intent_basic():
    """Test basic intent extraction."""
    assert extract_intent("How do I implement Rails authentication?") == "authentication"
    assert extract_intent("Next.js dynamic routing guide") == "routing"
    assert extract_intent("React useEffect hook examples") == "hooks"

def test_extract_intent_normalization():
    """Test intent normalization (similar queries → same intent)."""
    # All should map to "authentication"
    queries = [
        "Rails authentication",
        "Rails auth",
        "Rails login system",
        "How to authenticate users in Rails"
    ]
    intents = [extract_intent(q) for q in queries]
    assert len(set(intents)) == 1, f"Expected same intent, got: {intents}"

def test_generate_fingerprint():
    """Test fingerprint generation."""
    fp = generate_fingerprint("rails", "7", "How do I implement Rails authentication?")
    assert fp == "rails-7:authentication"

    fp = generate_fingerprint("react", "18", "React hooks tutorial")
    assert fp == "react-18:hooks"

def test_fingerprint_deduplication():
    """Test that similar queries generate same fingerprint."""
    queries = [
        "Rails authentication",
        "Rails auth system",
        "How to add authentication to Rails"
    ]

    fingerprints = [generate_fingerprint("rails", "7", q) for q in queries]
    assert len(set(fingerprints)) == 1, f"Expected same fingerprint, got: {fingerprints}"
