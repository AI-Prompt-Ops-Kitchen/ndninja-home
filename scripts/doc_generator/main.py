#!/usr/bin/env python3
"""
Documentation Generator - Main Orchestrator

Generates comprehensive documentation using Claude API,
workspace database, and git repository analysis.
"""

import argparse
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from utils.logger import setup_logger
from utils.validators import validate_project, validate_api_key
from templates import get_template
from data_sources import get_adapters
from generators.claude_client import ClaudeClient
from outputs.file_output import FileOutputHandler
from outputs.craft_output import CraftOutputHandler

logger = setup_logger('doc_generator')


def track_in_workspace(project, doc_type, content, craft_block_id=None):
    """
    Track generated document in workspace.items

    Args:
        project: Project dict
        doc_type: Documentation type
        content: Generated markdown
        craft_block_id: Craft block ID (if published to Craft)

    Returns:
        str: UUID of created workspace item
    """
    import psycopg2
    import json

    conn = psycopg2.connect(**Config.WORKSPACE_DB)
    cur = conn.cursor()

    title = f"{doc_type}: {project['title']}"
    metadata = {
        'doc_type': doc_type,
        'project_id': str(project['id']),
        'craft_block_id': craft_block_id,
        'generated_at': datetime.now().isoformat(),
        'template_version': '1.0',
        'word_count': len(content.split())
    }

    cur.execute("""
        INSERT INTO items (type, title, body, status, category, metadata, parent_id)
        VALUES ('doc', %s, %s, 'published', %s, %s::jsonb, %s)
        RETURNING id
    """, (title, content, doc_type, json.dumps(metadata), str(project['id'])))

    doc_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    logger.info(f"Tracked in workspace.items: {doc_id}")
    return doc_id


def main():
    """Main execution flow"""
    parser = argparse.ArgumentParser(
        description='Generate comprehensive documentation for projects',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --doc-type README --project "Daily Review System"
  %(prog)s --doc-type README --project "LLM Council" --output both
  %(prog)s --doc-type README --project "Workspace" --dry-run
        """
    )

    parser.add_argument(
        '--doc-type',
        required=True,
        choices=['README', 'API', 'ARCHITECTURE', 'REPORT'],
        help='Type of documentation to generate'
    )
    parser.add_argument(
        '--project',
        required=True,
        help='Project name or partial match'
    )
    parser.add_argument(
        '--output',
        default='file',
        choices=['file', 'craft', 'both'],
        help='Output destination (default: file)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview generated content without saving'
    )
    parser.add_argument(
        '--days',
        type=int,
        help='Days for REPORT type (default: 30)'
    )
    parser.add_argument(
        '--include-tests',
        action='store_true',
        help='Include test files in API documentation'
    )

    args = parser.parse_args()

    try:
        # Step 1: Validate
        logger.info("="*60)
        logger.info(f"Generating {args.doc_type} for: {args.project}")
        logger.info("="*60)

        validate_api_key()
        project = validate_project(args.project)
        logger.info(f"✓ Project found: {project['title']}")

        # Step 2: Get template
        template = get_template(args.doc_type)
        logger.info(f"✓ Template loaded: {args.doc_type}")

        # Step 3: Gather data
        logger.info("Gathering data from sources...")
        adapters = get_adapters(template.required_sources)
        data = {}

        for adapter in adapters:
            adapter_name = adapter.__class__.__name__
            try:
                logger.info(f"  - {adapter_name}...")
                adapter_data = adapter.gather(project, args)
                data.update(adapter_data)

                # Log what was found
                source_key = list(adapter_data.keys())[0]
                source_data = adapter_data[source_key]
                if isinstance(source_data, dict):
                    if 'available' in source_data and not source_data['available']:
                        logger.warning(f"    {source_data.get('message', 'Not available')}")
                    else:
                        logger.info(f"    ✓ Data gathered successfully")

            except Exception as e:
                logger.warning(f"  ✗ {adapter_name} failed: {e}")
                # Continue with other adapters

        # Step 4: Build prompt
        logger.info("Building prompt...")
        prompt = template.build_prompt(project, data)
        logger.info(f"  Prompt length: {len(prompt)} characters")

        # Step 5: Generate with Claude
        logger.info("Generating content with Claude API...")
        logger.info(f"  Model: {Config.CLAUDE_MODEL}")
        claude = ClaudeClient(Config.ANTHROPIC_API_KEY)

        try:
            content = claude.generate(prompt, template.system_prompt)
            logger.info(f"  ✓ Generated {len(content)} characters")
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return 1

        # Step 6: Post-process
        enhanced = template.post_process(content, data)
        word_count = len(enhanced.split())
        logger.info(f"  Word count: {word_count}")

        # Step 7: Dry run check
        if args.dry_run:
            logger.info("\n" + "="*60)
            logger.info("DRY RUN - Content Preview (first 1000 chars):")
            logger.info("="*60)
            print("\n" + enhanced[:1000] + "\n...")
            logger.info("="*60)
            logger.info("Dry run complete. No files saved.")
            return 0

        # Step 8: Output
        craft_block_id = None

        if args.output in ['file', 'both']:
            logger.info("Saving to file...")
            file_handler = FileOutputHandler()
            filepath = file_handler.save(enhanced, project, args.doc_type)
            logger.info(f"  ✓ Saved to: {filepath}")

        if args.output in ['craft', 'both']:
            logger.info("Preparing content for Craft...")
            craft_handler = CraftOutputHandler()
            staging_file = craft_handler.publish(enhanced, project, args.doc_type)
            if staging_file:
                logger.info(f"  ✓ Content staged for Craft publishing")
                logger.info(f"  Use skill to complete: /publish-to-craft {staging_file}")
                craft_block_id = staging_file  # Store staging path for workspace tracking
            else:
                logger.warning("  ✗ Craft preparation failed (see errors above)")
                craft_block_id = None

        # Step 9: Track in workspace
        if not args.dry_run and args.output in ['craft', 'both']:
            try:
                logger.info("Tracking in workspace database...")
                doc_id = track_in_workspace(project, args.doc_type, enhanced, craft_block_id)
            except Exception as e:
                logger.warning(f"Could not track in workspace: {e}")
                logger.warning("Document generated successfully but not tracked in database.")

        # Success summary
        logger.info("\n" + "="*60)
        logger.info("✓ Documentation generated successfully!")
        logger.info("="*60)
        logger.info(f"Project: {project['title']}")
        logger.info(f"Type: {args.doc_type}")
        logger.info(f"Words: {word_count}")
        if args.output in ['file', 'both']:
            logger.info(f"File: {filepath}")
        logger.info("="*60)

        return 0

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
