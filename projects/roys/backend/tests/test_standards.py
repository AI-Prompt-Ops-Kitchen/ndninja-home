import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.content import Standard, StandardCombination


@pytest.mark.asyncio
async def test_list_standards_empty(client: AsyncClient):
    resp = await client.get("/api/standards")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_standards_with_data(client: AsyncClient, db_session: AsyncSession):
    std = Standard(code="TEST_STD", name="Test Standard", category="Testing")
    db_session.add(std)
    await db_session.commit()

    resp = await client.get("/api/standards")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["code"] == "TEST_STD"


@pytest.mark.asyncio
async def test_get_standard_not_found(client: AsyncClient):
    resp = await client.get("/api/standards/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_combinations(client: AsyncClient, db_session: AsyncSession):
    combo = StandardCombination(
        combo_key="A+B",
        name="A plus B",
        standard_codes=["A", "B"],
    )
    db_session.add(combo)
    await db_session.commit()

    resp = await client.get("/api/standards/combinations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["combo_key"] == "A+B"
