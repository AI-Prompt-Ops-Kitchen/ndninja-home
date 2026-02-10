from datetime import datetime
from typing import List, Optional, Dict
from sage_mode.models.team_simulator import DecisionJournal

class DecisionJournalDB:
    """In-memory Decision Journal storage (MVP - Phase 1)"""

    def __init__(self):
        self._decisions: Dict[int, DecisionJournal] = {}
        self._next_id = 1

    def save_decision(self, decision: DecisionJournal) -> int:
        """Save decision and return ID"""
        decision_id = self._next_id
        self._next_id += 1
        self._decisions[decision_id] = decision
        return decision_id

    def get_decision(self, decision_id: int) -> Optional[DecisionJournal]:
        """Retrieve decision by ID"""
        return self._decisions.get(decision_id)

    def get_user_decisions(self, user_id: str, limit: int = 100) -> List[DecisionJournal]:
        """Get all decisions for a user"""
        return [d for d in self._decisions.values() if d.user_id == user_id][:limit]

    def search_decisions(self, keyword: str, user_id: Optional[str] = None) -> List[DecisionJournal]:
        """Search decisions by keyword"""
        keyword_lower = keyword.lower()
        results = []
        for decision in self._decisions.values():
            if user_id and decision.user_id != user_id:
                continue
            if keyword_lower in decision.title.lower() or keyword_lower in decision.description.lower():
                results.append(decision)
        return results

    def get_decisions_by_category(self, user_id: str, category: str) -> List[DecisionJournal]:
        """Get decisions by category for user"""
        return [d for d in self._decisions.values() if d.user_id == user_id and d.category == category]

    def cleanup(self):
        """Clear all decisions (for testing)"""
        self._decisions.clear()
        self._next_id = 1
