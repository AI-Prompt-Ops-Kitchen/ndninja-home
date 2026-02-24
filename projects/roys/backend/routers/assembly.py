from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.assembly import AssemblyRequest, AssembledSOP
from services.assembly import assemble_sop
from services.docgen import generate_docx

router = APIRouter(prefix="/api/generate", tags=["assembly"])


@router.post("", response_model=AssembledSOP)
async def generate_json(req: AssemblyRequest, db: AsyncSession = Depends(get_db)):
    result = await assemble_sop(
        db,
        sop_id=req.sop_id,
        standard_ids=req.standard_ids,
        content_tier=req.content_tier,
        template_structure_id=req.template_structure_id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="No content found for this SOP/standard combination")
    return result


@router.post("/docx")
async def generate_docx_file(req: AssemblyRequest, db: AsyncSession = Depends(get_db)):
    result = await assemble_sop(
        db,
        sop_id=req.sop_id,
        standard_ids=req.standard_ids,
        content_tier=req.content_tier,
        template_structure_id=req.template_structure_id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="No content found for this SOP/standard combination")

    buffer = generate_docx(result)
    filename = f"{result.sop_code}_{result.combo_key}.docx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
