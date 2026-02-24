from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/preflight")
async def preflight(db: AsyncSession = Depends(get_db)):
    """Check DB connectivity and return table counts."""
    result = await db.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
    )
    tables = [row[0] for row in result.fetchall()]

    counts = {}
    for table in tables:
        r = await db.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
        counts[table] = r.scalar()

    return {"status": "ok", "tables": counts}
