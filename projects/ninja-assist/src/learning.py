"""
Ninja Assist - Learning System
==============================
Self-improving routing through usage logging and corrections.

Features:
- Log all routes with outcomes
- Accept user corrections for misclassifications
- Learn new patterns from corrections
- Track token savings metrics
"""

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from collections import Counter


@dataclass
class RouteLog:
    """A logged routing decision."""
    timestamp: str
    input_text: str
    predicted_category: str
    confidence: float
    actual_category: Optional[str] = None  # Set by correction
    was_correct: Optional[bool] = None     # True/False/None (unknown)
    tool_used: Optional[str] = None
    tokens_saved: int = 0  # Estimated tokens saved by pattern matching
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "RouteLog":
        return cls(**data)


@dataclass
class LearnedPattern:
    """A pattern learned from user corrections."""
    pattern: str
    category: str
    confidence: float
    source: str  # "correction" or "manual"
    created_at: str
    times_matched: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "LearnedPattern":
        return cls(**data)


class LearningSystem:
    """
    Tracks routing decisions and learns from corrections.
    
    Usage:
        learner = LearningSystem()
        
        # Log a route
        learner.log_route("help me code", "code", 0.85)
        
        # User says it was wrong
        learner.correct_last("research")
        
        # Check stats
        print(learner.get_stats())
    """
    
    DATA_DIR = Path.home() / ".ninja-assist"
    ROUTES_FILE = DATA_DIR / "route_logs.jsonl"
    PATTERNS_FILE = DATA_DIR / "learned_patterns.json"
    STATS_FILE = DATA_DIR / "stats.json"
    
    # Estimate: LLM classification would cost ~50 tokens
    TOKENS_PER_LLM_CLASSIFICATION = 50
    
    def __init__(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._last_log: Optional[RouteLog] = None
        self._learned_patterns: list[LearnedPattern] = self._load_patterns()
    
    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    
    def log_route(
        self,
        input_text: str,
        predicted_category: str,
        confidence: float,
        tool_used: Optional[str] = None,
    ) -> RouteLog:
        """Log a routing decision."""
        log = RouteLog(
            timestamp=datetime.now().isoformat(),
            input_text=input_text,
            predicted_category=predicted_category,
            confidence=confidence,
            tool_used=tool_used,
            tokens_saved=self.TOKENS_PER_LLM_CLASSIFICATION if confidence >= 0.5 else 0,
        )
        
        # Append to JSONL file
        with open(self.ROUTES_FILE, "a") as f:
            f.write(json.dumps(log.to_dict()) + "\n")
        
        self._last_log = log
        self._update_stats(log)
        
        return log
    
    def mark_correct(self, log_id: Optional[str] = None) -> None:
        """Mark the last (or specified) route as correct."""
        if self._last_log:
            self._last_log.was_correct = True
            self._last_log.actual_category = self._last_log.predicted_category
            # Update the log file
            self._update_last_log_in_file()
    
    def _update_last_log_in_file(self) -> None:
        """Update the last log entry in the JSONL file."""
        if not self._last_log or not self.ROUTES_FILE.exists():
            return
        
        # Read all logs, update last one, rewrite
        logs = []
        with open(self.ROUTES_FILE, "r") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        
        if logs:
            logs[-1] = self._last_log.to_dict()
            with open(self.ROUTES_FILE, "w") as f:
                for log in logs:
                    f.write(json.dumps(log) + "\n")
    
    def correct_last(self, actual_category: str) -> Optional[LearnedPattern]:
        """
        Correct the last routing decision and learn from it.
        
        Returns a new LearnedPattern if one was created.
        """
        if not self._last_log:
            return None
        
        self._last_log.was_correct = False
        self._last_log.actual_category = actual_category
        self._update_last_log_in_file()
        
        # Learn from this correction
        pattern = self._learn_from_correction(
            self._last_log.input_text,
            actual_category,
        )
        
        return pattern
    
    # -------------------------------------------------------------------------
    # Learning
    # -------------------------------------------------------------------------
    
    def _learn_from_correction(self, text: str, category: str) -> Optional[LearnedPattern]:
        """Create a new pattern from a correction."""
        # Extract key words/phrases for the pattern
        # Simple approach: use significant words as a pattern
        words = text.lower().split()
        
        # Filter out common stop words
        stop_words = {"a", "an", "the", "is", "are", "was", "were", "be", "been",
                      "to", "of", "in", "for", "on", "with", "at", "by", "from",
                      "i", "me", "my", "we", "our", "you", "your", "it", "this",
                      "that", "can", "could", "would", "should", "will", "do",
                      "does", "did", "have", "has", "had"}
        
        significant = [w for w in words if w not in stop_words and len(w) > 2]
        
        if not significant:
            return None
        
        # Create a pattern that matches these words in sequence
        # Use \b word boundaries for better matching
        pattern_parts = [rf"\b{re.escape(w)}\b" for w in significant[:4]]  # Max 4 words
        pattern = r".*".join(pattern_parts)
        
        learned = LearnedPattern(
            pattern=pattern,
            category=category,
            confidence=0.75,  # Learned patterns start at 0.75 confidence
            source="correction",
            created_at=datetime.now().isoformat(),
        )
        
        self._learned_patterns.append(learned)
        self._save_patterns()
        
        return learned
    
    def add_pattern(self, pattern: str, category: str, confidence: float = 0.8) -> LearnedPattern:
        """Manually add a new pattern."""
        learned = LearnedPattern(
            pattern=pattern,
            category=category,
            confidence=confidence,
            source="manual",
            created_at=datetime.now().isoformat(),
        )
        
        self._learned_patterns.append(learned)
        self._save_patterns()
        
        return learned
    
    def get_learned_patterns(self) -> list[LearnedPattern]:
        """Get all learned patterns."""
        return self._learned_patterns.copy()
    
    def check_learned_patterns(self, text: str) -> Optional[tuple[str, float]]:
        """
        Check if text matches any learned patterns.
        
        Returns (category, confidence) if matched, None otherwise.
        """
        text_lower = text.lower()
        
        for pattern in self._learned_patterns:
            try:
                if re.search(pattern.pattern, text_lower):
                    pattern.times_matched += 1
                    self._save_patterns()
                    return (pattern.category, pattern.confidence)
            except re.error:
                continue  # Skip invalid patterns
        
        return None
    
    def _load_patterns(self) -> list[LearnedPattern]:
        """Load learned patterns from file."""
        if not self.PATTERNS_FILE.exists():
            return []
        
        try:
            with open(self.PATTERNS_FILE, "r") as f:
                data = json.load(f)
            return [LearnedPattern.from_dict(p) for p in data]
        except (json.JSONDecodeError, KeyError):
            return []
    
    def _save_patterns(self) -> None:
        """Save learned patterns to file."""
        with open(self.PATTERNS_FILE, "w") as f:
            json.dump([p.to_dict() for p in self._learned_patterns], f, indent=2)
    
    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------
    
    def _update_stats(self, log: RouteLog) -> None:
        """Update running statistics."""
        stats = self._load_stats()
        
        stats["total_routes"] = stats.get("total_routes", 0) + 1
        stats["total_tokens_saved"] = stats.get("total_tokens_saved", 0) + log.tokens_saved
        
        # Track by category
        by_category = stats.get("by_category", {})
        cat = log.predicted_category
        by_category[cat] = by_category.get(cat, 0) + 1
        stats["by_category"] = by_category
        
        stats["last_updated"] = datetime.now().isoformat()
        
        self._save_stats(stats)
    
    def _load_stats(self) -> dict:
        """Load statistics from file."""
        if not self.STATS_FILE.exists():
            return {}
        
        try:
            with open(self.STATS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    
    def _save_stats(self, stats: dict) -> None:
        """Save statistics to file."""
        with open(self.STATS_FILE, "w") as f:
            json.dump(stats, f, indent=2)
    
    def get_stats(self) -> dict:
        """Get current statistics."""
        stats = self._load_stats()
        
        # Add computed fields
        total = stats.get("total_routes", 0)
        tokens = stats.get("total_tokens_saved", 0)
        
        # Estimate cost savings (assuming $0.01 per 1K tokens)
        cost_saved = (tokens / 1000) * 0.01
        
        return {
            "total_routes": total,
            "total_tokens_saved": tokens,
            "estimated_cost_saved": f"${cost_saved:.4f}",
            "routes_by_category": stats.get("by_category", {}),
            "learned_patterns": len(self._learned_patterns),
            "last_updated": stats.get("last_updated"),
        }
    
    def get_accuracy(self) -> dict:
        """Calculate accuracy from logged corrections."""
        if not self.ROUTES_FILE.exists():
            return {"total": 0, "correct": 0, "incorrect": 0, "unknown": 0, "accuracy": None}
        
        total = 0
        correct = 0
        incorrect = 0
        unknown = 0
        
        with open(self.ROUTES_FILE, "r") as f:
            for line in f:
                if line.strip():
                    try:
                        log = json.loads(line)
                        total += 1
                        was_correct = log.get("was_correct")
                        if was_correct is True:
                            correct += 1
                        elif was_correct is False:
                            incorrect += 1
                        else:
                            unknown += 1
                    except json.JSONDecodeError:
                        continue
        
        accuracy = correct / (correct + incorrect) if (correct + incorrect) > 0 else None
        
        return {
            "total": total,
            "correct": correct,
            "incorrect": incorrect,
            "unknown": unknown,
            "accuracy": f"{accuracy:.1%}" if accuracy else "N/A (need corrections)",
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_learner: Optional[LearningSystem] = None


def get_learner() -> LearningSystem:
    """Get or create the global learning system instance."""
    global _learner
    if _learner is None:
        _learner = LearningSystem()
    return _learner


def log_route(text: str, category: str, confidence: float, tool: Optional[str] = None) -> None:
    """Quick access to log a route."""
    get_learner().log_route(text, category, confidence, tool)


def correct(actual_category: str) -> None:
    """Quick access to correct the last route."""
    get_learner().correct_last(actual_category)


def stats() -> dict:
    """Quick access to get stats."""
    return get_learner().get_stats()


# =============================================================================
# CLI / TESTS
# =============================================================================

def run_tests():
    """Test the learning system."""
    import tempfile
    import shutil
    
    print("=" * 70)
    print("NINJA ASSIST - LEARNING SYSTEM TESTS")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    # Use temp directory for tests
    original_dir = LearningSystem.DATA_DIR
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            LearningSystem.DATA_DIR = Path(tmpdir)
            LearningSystem.ROUTES_FILE = Path(tmpdir) / "route_logs.jsonl"
            LearningSystem.PATTERNS_FILE = Path(tmpdir) / "learned_patterns.json"
            LearningSystem.STATS_FILE = Path(tmpdir) / "stats.json"
            
            # Test 1: Create learner
            print("\n✅ Test 1: Create LearningSystem")
            try:
                learner = LearningSystem()
                assert learner is not None
                passed += 1
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed += 1
            
            # Test 2: Log a route
            print("\n✅ Test 2: Log a route")
            try:
                log = learner.log_route("help me code", "code", 0.85)
                assert log.predicted_category == "code"
                assert log.tokens_saved == 50
                passed += 1
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed += 1
            
            # Test 3: Stats update
            print("\n✅ Test 3: Stats tracking")
            try:
                stats = learner.get_stats()
                assert stats["total_routes"] == 1
                assert stats["total_tokens_saved"] == 50
                passed += 1
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed += 1
            
            # Test 4: Correction
            print("\n✅ Test 4: Correct a route")
            try:
                learner.log_route("look up weather", "code", 0.6)
                pattern = learner.correct_last("research")
                assert pattern is not None
                assert pattern.category == "research"
                passed += 1
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed += 1
            
            # Test 5: Learned patterns persist
            print("\n✅ Test 5: Patterns persist")
            try:
                patterns = learner.get_learned_patterns()
                assert len(patterns) == 1
                
                # Create new learner, patterns should load
                learner2 = LearningSystem()
                patterns2 = learner2.get_learned_patterns()
                assert len(patterns2) == 1
                passed += 1
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed += 1
            
            # Test 6: Check learned patterns
            print("\n✅ Test 6: Match learned patterns")
            try:
                result = learner.check_learned_patterns("look up the weather forecast")
                assert result is not None
                assert result[0] == "research"
                passed += 1
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed += 1
            
            # Test 7: Manual pattern
            print("\n✅ Test 7: Add manual pattern")
            try:
                learner.add_pattern(r"\bweather\b", "research", 0.9)
                patterns = learner.get_learned_patterns()
                assert len(patterns) == 2
                passed += 1
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed += 1
            
            # Test 8: Accuracy tracking
            print("\n✅ Test 8: Accuracy calculation")
            try:
                learner.log_route("test 1", "code", 0.8)
                learner.mark_correct()
                learner.log_route("test 2", "code", 0.8)
                learner.mark_correct()
                
                accuracy = learner.get_accuracy()
                assert accuracy["correct"] == 2
                assert accuracy["incorrect"] == 1  # From earlier correction
                passed += 1
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                failed += 1
    
    finally:
        # Restore original paths
        LearningSystem.DATA_DIR = original_dir
        LearningSystem.ROUTES_FILE = original_dir / "route_logs.jsonl"
        LearningSystem.PATTERNS_FILE = original_dir / "learned_patterns.json"
        LearningSystem.STATS_FILE = original_dir / "stats.json"
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{passed + failed} passed")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = run_tests()
        sys.exit(0 if success else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "--stats":
        learner = LearningSystem()
        print(json.dumps(learner.get_stats(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "--accuracy":
        learner = LearningSystem()
        print(json.dumps(learner.get_accuracy(), indent=2))
    else:
        print("Usage:")
        print("  --test     Run tests")
        print("  --stats    Show statistics")
        print("  --accuracy Show accuracy metrics")
