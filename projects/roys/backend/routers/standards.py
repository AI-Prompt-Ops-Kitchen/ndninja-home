from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.content import Standard, StandardCombination
from schemas.standards import StandardOut, StandardDetailOut, StandardCombinationOut

router = APIRouter(prefix="/api/standards", tags=["standards"])


@router.get("", response_model=list[StandardOut])
async def list_standards(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Standard).where(Standard.is_active == True).order_by(Standard.code))
    return result.scalars().all()


@router.get("/combinations", response_model=list[StandardCombinationOut])
async def list_combinations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(StandardCombination).where(StandardCombination.is_active == True).order_by(StandardCombination.combo_key)
    )
    return result.scalars().all()


@router.get("/{standard_id}", response_model=StandardDetailOut)
async def get_standard(standard_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Standard).options(selectinload(Standard.requirements)).where(Standard.id == standard_id)
    )
    standard = result.scalar_one_or_none()
    if not standard:
        raise HTTPException(status_code=404, detail="Standard not found")
    return standard
