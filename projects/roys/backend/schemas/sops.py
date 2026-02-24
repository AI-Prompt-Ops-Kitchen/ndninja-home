from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class ContentBlockOut(BaseModel):
    id: UUID
    section_number: str
    section_title: str
    content_tier: str
    combo_key: str
    body: str
    sort_order: int
    block_metadata: dict | None = None

    model_config = {"from_attributes": True}


class SOPOut(BaseModel):
    id: UUID
    code: str
    title: str
    description: str | None = None
    category: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class SOPDetailOut(SOPOut):
    content_blocks: list[ContentBlockOut] = []
