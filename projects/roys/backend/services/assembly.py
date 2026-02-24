from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.content import (
    SOP,
    Standard,
    ContentBlock,
    RequirementSOPMapping,
    SOPCrossReference,
    TemplateStructure,
    StandardCombination,
)
from schemas.assembly import AssembledSOP, AssembledSection, TraceabilityEntry


def make_combo_key(standard_codes: list[str]) -> str:
    """Sort standard codes alphabetically and join with +."""
    return "+".join(sorted(standard_codes))


async def assemble_sop(
    db: AsyncSession,
    sop_id: UUID,
    standard_ids: list[UUID],
    content_tier: str = "standard",
    template_structure_id: UUID | None = None,
) -> AssembledSOP | None:
    """
    Assemble an SOP from content blocks matching the given standards.

    Fallback strategy:
    1. Try exact combo key match
    2. Merge individual standard blocks
    3. Return None if no content found
    """
    # Fetch SOP
    sop = await db.get(SOP, sop_id)
    if not sop:
        return None

    # Resolve standard codes from IDs
    result = await db.execute(select(Standard).where(Standard.id.in_(standard_ids)))
    standards = result.scalars().all()
    if len(standards) != len(standard_ids):
        return None

    standard_codes = [s.code for s in standards]
    combo_key = make_combo_key(standard_codes)

    # Strategy 1: Exact combo key match
    blocks = await _fetch_blocks(db, sop_id, content_tier, combo_key)

    # Strategy 2: Merge individual standard blocks
    if not blocks and len(standard_codes) > 1:
        all_blocks = []
        seen_sections = set()
        for code in sorted(standard_codes):
            individual_blocks = await _fetch_blocks(db, sop_id, content_tier, code)
            for block in individual_blocks:
                if block.section_number not in seen_sections:
                    all_blocks.append(block)
                    seen_sections.add(block.section_number)
        blocks = all_blocks

    if not blocks:
        return None

    # Resolve template
    template_name = None
    if template_structure_id:
        template = await db.get(TemplateStructure, template_structure_id)
        if template:
            template_name = template.name

    # Build sections
    sections = [
        AssembledSection(
            section_number=b.section_number,
            section_title=b.section_title,
            body=b.body,
            block_metadata=b.block_metadata,
        )
        for b in sorted(blocks, key=lambda b: b.sort_order)
    ]

    # Enhanced tier: add traceability + cross-references
    traceability = None
    cross_references = None
    if content_tier == "enhanced":
        traceability = await _build_traceability(db, sop_id, standard_ids)
        cross_references = await _build_cross_references(db, sop_id)

    return AssembledSOP(
        sop_id=sop.id,
        sop_code=sop.code,
        sop_title=sop.title,
        combo_key=combo_key,
        content_tier=content_tier,
        template_name=template_name,
        sections=sections,
        traceability=traceability,
        cross_references=cross_references,
    )


async def _fetch_blocks(
    db: AsyncSession, sop_id: UUID, content_tier: str, combo_key: str
) -> list[ContentBlock]:
    result = await db.execute(
        select(ContentBlock)
        .where(
            ContentBlock.sop_id == sop_id,
            ContentBlock.content_tier == content_tier,
            ContentBlock.combo_key == combo_key,
            ContentBlock.is_active == True,
        )
        .order_by(ContentBlock.sort_order)
    )
    return list(result.scalars().all())


async def _build_traceability(
    db: AsyncSession, sop_id: UUID, standard_ids: list[UUID]
) -> list[TraceabilityEntry]:
    result = await db.execute(
        select(RequirementSOPMapping)
        .join(RequirementSOPMapping.requirement)
        .join(RequirementSOPMapping.requirement.property.mapper.class_.standard)
        .where(
            RequirementSOPMapping.sop_id == sop_id,
            RequirementSOPMapping.requirement.has(
                RequirementSOPMapping.requirement.property.mapper.class_.standard_id.in_(standard_ids)
            ),
        )
    )
    mappings = result.scalars().all()

    entries = []
    for m in mappings:
        req = await db.get(m.requirement.__class__, m.requirement_id, options=[selectinload(m.requirement.__class__.standard)])
        if req:
            entries.append(
                TraceabilityEntry(
                    requirement_clause=req.clause_number,
                    requirement_title=req.title,
                    standard_code=req.standard.code if req.standard else "",
                    section_number=m.section_number or "",
                    coverage_notes=m.coverage_notes,
                )
            )
    return entries


async def _build_cross_references(db: AsyncSession, sop_id: UUID) -> list[dict]:
    result = await db.execute(
        select(SOPCrossReference)
        .options(selectinload(SOPCrossReference.target_sop))
        .where(SOPCrossReference.source_sop_id == sop_id)
    )
    refs = result.scalars().all()
    return [
        {
            "target_sop_code": ref.target_sop.code,
            "target_sop_title": ref.target_sop.title,
            "relationship_type": ref.relationship_type,
            "description": ref.description,
        }
        for ref in refs
    ]
