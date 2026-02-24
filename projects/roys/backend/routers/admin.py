from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.content import Standard, SOP, ContentBlock, TemplateStructure, StandardCombination
from models.users import User, Subscription
from services.auth import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    standards = (await db.execute(select(func.count(Standard.id)))).scalar()
    sops = (await db.execute(select(func.count(SOP.id)))).scalar()
    content_blocks = (await db.execute(select(func.count(ContentBlock.id)))).scalar()
    users = (await db.execute(select(func.count(User.id)))).scalar()
    combinations = (await db.execute(select(func.count(StandardCombination.id)))).scalar()

    return {
        "standards": standards,
        "sops": sops,
        "content_blocks": content_blocks,
        "users": users,
        "combinations": combinations,
    }
