#!/usr/bin/env python3
"""CLI tool to generate an assembled SOP document."""
import argparse
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from uuid import UUID
from database import async_session
from services.assembly import assemble_sop
from services.docgen import generate_docx


async def main():
    parser = argparse.ArgumentParser(description="Generate an assembled SOP")
    parser.add_argument("--sop-id", required=True, help="UUID of the SOP")
    parser.add_argument("--standards", required=True, nargs="+", help="UUID(s) of standards")
    parser.add_argument("--tier", default="standard", choices=["standard", "enhanced"])
    parser.add_argument("--template-id", default=None, help="UUID of template structure")
    parser.add_argument("--format", default="json", choices=["json", "docx"])
    parser.add_argument("--output", "-o", default=None, help="Output file path")
    args = parser.parse_args()

    async with async_session() as db:
        result = await assemble_sop(
            db,
            sop_id=UUID(args.sop_id),
            standard_ids=[UUID(s) for s in args.standards],
            content_tier=args.tier,
            template_structure_id=UUID(args.template_id) if args.template_id else None,
        )

    if result is None:
        print("Error: No content found for this SOP/standard combination", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        output = result.model_dump_json(indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Written to {args.output}")
        else:
            print(output)
    else:
        buffer = generate_docx(result)
        out_path = args.output or f"{result.sop_code}_{result.combo_key}.docx"
        with open(out_path, "wb") as f:
            f.write(buffer.read())
        print(f"Written to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
