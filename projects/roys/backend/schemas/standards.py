from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class StandardOut(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None
    version: str | None = None
    category: str
    is_active: bool

    model_config = {"from_attributes": True}


class RequirementOut(BaseModel):
    id: UUID
    standard_id: UUID
    clause_number: str
    title: str
    description: str | None = None
    is_critical: bool

    model_config = {"from_attributes": True}


class StandardDetailOut(StandardOut):
    requirements: list[RequirementOut] = []


class StandardCombinationOut(BaseModel):
    id: UUID
    combo_key: str
    name: str
    description: str | None = None
    standard_codes: list[str]
    is_active: bool

    model_config = {"from_attributes": True}
