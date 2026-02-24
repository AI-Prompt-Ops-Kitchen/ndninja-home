"""Seed the database with initial data. Idempotent — skips existing records."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database import async_session
from models.content import Standard, TemplateStructure, StandardCombination
from seeds.standards import STANDARDS
from seeds.templates import TEMPLATES
from seeds.combinations import COMBINATIONS


async def seed_standards(session):
    count = 0
    for data in STANDARDS:
        result = await session.execute(select(Standard).where(Standard.code == data["code"]))
        if result.scalar_one_or_none() is None:
            session.add(Standard(**data))
            count += 1
    await session.commit()
    print(f"  Standards: {count} added, {len(STANDARDS) - count} already existed")


async def seed_templates(session):
    count = 0
    for data in TEMPLATES:
        result = await session.execute(select(TemplateStructure).where(TemplateStructure.name == data["name"]))
        if result.scalar_one_or_none() is None:
            session.add(TemplateStructure(**data))
            count += 1
    await session.commit()
    print(f"  Templates: {count} added, {len(TEMPLATES) - count} already existed")


async def seed_combinations(session):
    count = 0
    for data in COMBINATIONS:
        result = await session.execute(select(StandardCombination).where(StandardCombination.combo_key == data["combo_key"]))
        if result.scalar_one_or_none() is None:
            session.add(StandardCombination(**data))
            count += 1
    await session.commit()
    print(f"  Combinations: {count} added, {len(COMBINATIONS) - count} already existed")


async def main():
    print("Seeding ROYS database...")
    async with async_session() as session:
        await seed_standards(session)
        await seed_templates(session)
        await seed_combinations(session)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
