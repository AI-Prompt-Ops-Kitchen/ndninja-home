from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.content import SOP
from schemas.sops import SOPOut, SOPDetailOut

router = APIRouter(prefix="/api/sops", tags=["sops"])


@router.get("", response_model=list[SOPOut])
async def list_sops(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SOP).where(SOP.is_active == True).order_by(SOP.code))
    return result.scalars().all()


@router.get("/{sop_id}", response_model=SOPDetailOut)
async def get_sop(sop_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SOP).options(selectinload(SOP.content_blocks)).where(SOP.id == sop_id)
    )
    sop = result.scalar_one_or_none()
    if not sop:
        raise HTTPException(status_code=404, detail="SOP not found")
    return sop
