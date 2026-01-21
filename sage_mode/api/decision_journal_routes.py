from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from sage_mode.models.team_simulator import DecisionJournal
from sage_mode.database.decision_journal import DecisionJournalDB
from pydantic import BaseModel

router = APIRouter()

class DecisionRequest(BaseModel):
    user_id: str
    title: str
    description: str
    category: str
    decision_type: str
    context_snippet: Optional[str] = None
    related_task: Optional[str] = None
    confidence_level: int = 80

class DecisionResponse(BaseModel):
    id: int
    user_id: str
    title: str
    description: str
    category: str
    decision_type: str
    timestamp: datetime
    confidence_level: int

db = DecisionJournalDB()

@router.post("/decisions", status_code=201, response_model=DecisionResponse)
def create_decision(request: DecisionRequest):
    decision = DecisionJournal(
        user_id=request.user_id,
        title=request.title,
        description=request.description,
        category=request.category,
        decision_type=request.decision_type,
        context_snippet=request.context_snippet,
        related_task=request.related_task,
        confidence_level=request.confidence_level
    )
    decision_id = db.save_decision(decision)
    retrieved = db.get_decision(decision_id)
    return DecisionResponse(
        id=decision_id, user_id=retrieved.user_id, title=retrieved.title,
        description=retrieved.description, category=retrieved.category,
        decision_type=retrieved.decision_type, timestamp=retrieved.timestamp,
        confidence_level=retrieved.confidence_level
    )

@router.get("/decisions/search", response_model=List[DecisionResponse])
def search_decisions(q: str):
    decisions = db.search_decisions(q)
    return [DecisionResponse(
        id=i, user_id=d.user_id, title=d.title,
        description=d.description, category=d.category,
        decision_type=d.decision_type, timestamp=d.timestamp,
        confidence_level=d.confidence_level
    ) for i, d in enumerate(decisions)]

@router.get("/decisions/{decision_id}", response_model=DecisionResponse)
def get_decision(decision_id: int):
    decision = db.get_decision(decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return DecisionResponse(
        id=decision_id, user_id=decision.user_id, title=decision.title,
        description=decision.description, category=decision.category,
        decision_type=decision.decision_type, timestamp=decision.timestamp,
        confidence_level=decision.confidence_level
    )
