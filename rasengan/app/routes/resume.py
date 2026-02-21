"""Context resume route — GET /resume."""

import asyncio

from fastapi import APIRouter

from app.services.context import build_resume

router = APIRouter()


@router.get("/resume")
async def resume():
    return await asyncio.to_thread(build_resume)
