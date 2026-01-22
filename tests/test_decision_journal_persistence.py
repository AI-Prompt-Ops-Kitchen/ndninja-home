import pytest
from datetime import datetime
from sage_mode.database.decision_journal import DecisionJournalDB
from sage_mode.models.team_simulator import DecisionJournal

@pytest.fixture
def journal_db():
    """Initialize test database connection - uses in-memory mock"""
    db = DecisionJournalDB()
    yield db
    db.cleanup()

def test_decision_journal_save_and_retrieve(journal_db):
    """Save decision to database and retrieve it"""
    decision = DecisionJournal(
        user_id="user-123",
        title="Use async/await for database calls",
        description="Convert all blocking DB queries to async",
        category="architecture",
        decision_type="technical",
        context_snippet="Working on latency optimization",
        confidence_level=95
    )

    journal_id = journal_db.save_decision(decision)
    assert journal_id is not None

    retrieved = journal_db.get_decision(journal_id)
    assert retrieved.title == decision.title
    assert retrieved.confidence_level == 95

def test_decision_journal_list_by_user(journal_db):
    """List all decisions for a user"""
    for i in range(3):
        decision = DecisionJournal(
            user_id="user-123",
            title=f"Decision {i}",
            description=f"Description {i}",
            category="architecture",
            decision_type="technical"
        )
        journal_db.save_decision(decision)

    decisions = journal_db.get_user_decisions("user-123")
    assert len(decisions) == 3

def test_decision_journal_search(journal_db):
    """Search decisions by keyword"""
    decision = DecisionJournal(
        user_id="user-123",
        title="Implement caching layer",
        description="Redis for session storage",
        category="performance",
        decision_type="technical"
    )
    journal_db.save_decision(decision)

    results = journal_db.search_decisions("caching")
    assert len(results) >= 1
    assert any(r.title == decision.title for r in results)

def test_decision_journal_by_category(journal_db):
    """Filter decisions by category"""
    arch_decision = DecisionJournal(
        user_id="user-123",
        title="Microservices",
        description="Split monolith",
        category="architecture",
        decision_type="technical"
    )
    process_decision = DecisionJournal(
        user_id="user-123",
        title="Daily standups",
        description="10am every day",
        category="process",
        decision_type="operational"
    )

    journal_db.save_decision(arch_decision)
    journal_db.save_decision(process_decision)

    arch_decisions = journal_db.get_decisions_by_category("user-123", "architecture")
    assert len(arch_decisions) == 1
    assert arch_decisions[0].title == "Microservices"
