import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.content import Standard, SOP, ContentBlock


async def _seed_sop_with_blocks(db: AsyncSession):
    """Helper: create a standard, SOP, and content blocks for testing."""
    std = Standard(code="ISO_TEST", name="ISO Test", category="Testing")
    db.add(std)
    await db.flush()

    sop = SOP(code="SOP-001", title="Test SOP")
    db.add(sop)
    await db.flush()

    blocks = [
        ContentBlock(
            sop_id=sop.id,
            section_number="1",
            section_title="Purpose",
            content_tier="standard",
            combo_key="ISO_TEST",
            body="This is the purpose section.",
            sort_order=1,
        ),
        ContentBlock(
            sop_id=sop.id,
            section_number="2",
            section_title="Scope",
            content_tier="standard",
            combo_key="ISO_TEST",
            body="This is the scope section.",
            sort_order=2,
        ),
    ]
    db.add_all(blocks)
    await db.commit()
    return std, sop


@pytest.mark.asyncio
async def test_generate_exact_combo(client: AsyncClient, db_session: AsyncSession):
    std, sop = await _seed_sop_with_blocks(db_session)
    resp = await client.post("/api/generate", json={
        "sop_id": str(sop.id),
        "standard_ids": [str(std.id)],
        "content_tier": "standard",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["sop_code"] == "SOP-001"
    assert len(data["sections"]) == 2


@pytest.mark.asyncio
async def test_generate_not_found(client: AsyncClient, db_session: AsyncSession):
    std = Standard(code="EMPTY_STD", name="Empty", category="Testing")
    sop = SOP(code="SOP-EMPTY", title="Empty SOP")
    db_session.add_all([std, sop])
    await db_session.commit()

    resp = await client.post("/api/generate", json={
        "sop_id": str(sop.id),
        "standard_ids": [str(std.id)],
        "content_tier": "standard",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_generate_deterministic(client: AsyncClient, db_session: AsyncSession):
    std, sop = await _seed_sop_with_blocks(db_session)
    payload = {
        "sop_id": str(sop.id),
        "standard_ids": [str(std.id)],
        "content_tier": "standard",
    }
    resp1 = await client.post("/api/generate", json=payload)
    resp2 = await client.post("/api/generate", json=payload)
    assert resp1.json() == resp2.json()


@pytest.mark.asyncio
async def test_generate_invalid_sop(client: AsyncClient):
    resp = await client.post("/api/generate", json={
        "sop_id": "00000000-0000-0000-0000-000000000000",
        "standard_ids": ["00000000-0000-0000-0000-000000000001"],
        "content_tier": "standard",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_generate_enhanced_tier(client: AsyncClient, db_session: AsyncSession):
    std, sop = await _seed_sop_with_blocks(db_session)
    # No enhanced blocks exist, so should 404
    resp = await client.post("/api/generate", json={
        "sop_id": str(sop.id),
        "standard_ids": [str(std.id)],
        "content_tier": "enhanced",
    })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_generate_bad_tier(client: AsyncClient):
    resp = await client.post("/api/generate", json={
        "sop_id": "00000000-0000-0000-0000-000000000000",
        "standard_ids": ["00000000-0000-0000-0000-000000000001"],
        "content_tier": "invalid",
    })
    assert resp.status_code == 422
