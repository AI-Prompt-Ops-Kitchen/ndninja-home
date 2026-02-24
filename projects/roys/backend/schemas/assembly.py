from pydantic import BaseModel, Field
from uuid import UUID


class AssemblyRequest(BaseModel):
    sop_id: UUID
    standard_ids: list[UUID] = Field(min_length=1)
    content_tier: str = Field(default="standard", pattern="^(standard|enhanced)$")
    template_structure_id: UUID | None = None


class TraceabilityEntry(BaseModel):
    requirement_clause: str
    requirement_title: str
    standard_code: str
    section_number: str
    coverage_notes: str | None = None


class AssembledSection(BaseModel):
    section_number: str
    section_title: str
    body: str
    block_metadata: dict | None = None


class AssembledSOP(BaseModel):
    sop_id: UUID
    sop_code: str
    sop_title: str
    combo_key: str
    content_tier: str
    template_name: str | None = None
    sections: list[AssembledSection]
    traceability: list[TraceabilityEntry] | None = None
    cross_references: list[dict] | None = None
