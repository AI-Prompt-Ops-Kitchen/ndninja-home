#!/usr/bin/env python3
"""
Tool Registry Seed Script

Populates the tool registry in claude-memory database with initial high-value tools.
"""

import sys
import json
import psycopg2

TOOLS = [
    {
        'title': 'llm-council',
        'name': 'LLM Council',
        'location': '/home/ndninja/projects/llm-council/',
        'command': 'python3 /home/ndninja/projects/llm-council/council.py "your question"',
        'description': 'Multi-model analysis tool - queries 4 LLMs in parallel (GPT-5.2, Claude Sonnet 4.5, Gemini 3 Pro, Perplexity) and synthesizes results',
        'keywords': ['multi-model', 'research', 'analysis', 'consensus', 'complex-question', 'vpn', 'comparison', 'diverse-perspectives'],
        'usage_examples': [
            'Research: Compare VPN providers with multi-model analysis',
            'Analysis: Evaluate architectural trade-offs from different perspectives',
            'Validation: Cross-check complex technical decisions'
        ],
        'performance': '~3-5 min, $0.15-0.30 per query',
        'last_used': '2026-01-16',
        'use_count': 15
    },
    {
        'title': 'kage-bunshin',
        'name': 'Kage Bunshin',
        'location': '/home/ndninja/projects/kage-bunshin/',
        'command': 'cd /home/ndninja/projects/kage-bunshin && python3 api/main.py',
        'description': 'Distributed AI orchestration system - executes tasks across 4-node cluster (ndnlinuxserv, ndnlinuxsrv2, vengeance, rog-flow-z13) with 72B model capability',
        'keywords': ['distributed', 'kage-bunshin', '72b', 'cluster', 'parallel', 'orchestration', 'multi-node', 'large-model'],
        'usage_examples': [
            'Dispatch: Run complex task across distributed cluster',
            'Parallel: Execute multiple independent tasks simultaneously',
            '72B: Access flagship model for advanced reasoning'
        ],
        'performance': 'Variable - 2-10 min depending on task complexity',
        'last_used': '2026-01-16',
        'use_count': 23
    },
    {
        'title': 'doc-generator',
        'name': 'Documentation Generator',
        'location': '/home/ndninja/scripts/doc_generator/',
        'command': 'python3 /home/ndninja/scripts/doc_generator/main.py --doc-type README --project "Project Name"',
        'description': 'Automated documentation system - generates README, USER_GUIDE, API, MEETING_NOTES, STATUS_REPORT, ONBOARDING docs using Claude API with workspace DB analysis',
        'keywords': ['documentation', 'readme', 'api-docs', 'user-guide', 'status-report', 'onboarding', 'automated-docs'],
        'usage_examples': [
            'README: Generate project README from workspace DB',
            'API: Create API documentation with examples',
            'Status: Weekly status reports via n8n automation'
        ],
        'performance': '~30-60 sec, $0.02-0.09 per doc',
        'last_used': '2026-01-16',
        'use_count': 12
    },
    {
        'title': 'vengeance-validate',
        'name': 'Vengeance Code Validator',
        'location': '/home/ndninja/scripts/',
        'command': 'vengeance-validate <file.py>',
        'description': 'Automated validation pipeline for LLM-generated code - syntax check, linting, formatting, security scan. Supports Python, JavaScript, TypeScript',
        'keywords': ['validation', 'code-quality', 'linting', 'security', 'llm-code', 'vengeance', 'qwen2.5'],
        'usage_examples': [
            'Validate: Check Python script from Vengeance LLM',
            'Security: Scan for vulnerabilities in generated code',
            'Quality: Ensure code meets standards'
        ],
        'performance': '<5 sec per file',
        'last_used': '2026-01-15',
        'use_count': 8
    },
    {
        'title': 'permission-helper',
        'name': 'Permission Helper Plugin',
        'location': '/home/ndninja/.claude/plugins/local/permission-helper/',
        'command': '/plan-permissions "plan text or file path"',
        'description': 'Pre-approves permissions for implementation plans - detects file writes, bash commands, skills, web operations. Updates settings.json automatically',
        'keywords': ['permissions', 'pre-approve', 'plan-analysis', 'settings', 'file-detection', 'bash-detection'],
        'usage_examples': [
            'Pre-approve: Analyze plan and approve all permissions upfront',
            'Rollback: Restore previous permission settings',
            'History: View permission change history'
        ],
        'performance': '<1 sec analysis',
        'last_used': '2026-01-17',
        'use_count': 18
    },
    {
        'title': 'server-health',
        'name': 'Server Health Monitor',
        'location': '/home/ndninja/.claude/plugins/local/server-health/',
        'command': '/health --quick',
        'description': 'Quick server health checks - PostgreSQL, Docker, disk usage, critical services. Full scan with --deep flag',
        'keywords': ['health', 'monitoring', 'postgresql', 'docker', 'disk', 'services', 'diagnostics'],
        'usage_examples': [
            'Quick: Run fast health check (~100ms)',
            'Deep: Full system diagnostics (~2 sec)',
            'Audit: Log results to PostgreSQL'
        ],
        'performance': '100ms quick, 2s deep',
        'last_used': '2026-01-19',
        'use_count': 31
    },
    {
        'title': 'llm-code-validator',
        'name': 'LLM Code Validator',
        'location': '/home/ndninja/scripts/llm-code-validator.py',
        'command': 'python3 /home/ndninja/scripts/llm-code-validator.py <file>',
        'description': 'Generic code validation for any LLM output - syntax, structure, common patterns. Language-agnostic checks',
        'keywords': ['validation', 'llm', 'code-quality', 'syntax', 'generic'],
        'usage_examples': [
            'Validate: Check any code file for basic quality',
            'Syntax: Verify code parses correctly',
            'Patterns: Detect common anti-patterns'
        ],
        'performance': '<3 sec',
        'last_used': '2026-01-14',
        'use_count': 6
    },
    {
        'title': 'reflection-engine',
        'name': 'Skill Reflection Engine',
        'location': '/home/ndninja/scripts/reflection_engine/',
        'command': 'python3 /home/ndninja/scripts/reflection_engine/main.py',
        'description': 'Automated skill improvement system - detects correction signals from conversations, analyzes with LLM Council, updates skill files',
        'keywords': ['reflection', 'skill-improvement', 'automated-learning', 'correction-signals', 'stop-hook'],
        'usage_examples': [
            'Auto-improve: Detect and fix skill issues from conversations',
            'Signals: Analyze correction patterns',
            'Dedup: Prevent duplicate improvements'
        ],
        'performance': '~2-5 min per reflection',
        'last_used': '2026-01-16',
        'use_count': 14
    },
    {
        'title': 'draft-generator',
        'name': 'Content Draft Generator',
        'location': '/home/ndninja/projects/content-automation/',
        'command': 'curl -X POST http://localhost:5002/generate-draft -d \'{"count": 1}\'',
        'description': 'Weekly automated content draft generation - uses LLM Council for research, generates gaming/tech content drafts',
        'keywords': ['content', 'draft', 'automation', 'gaming', 'tech', 'weekly', 'n8n'],
        'usage_examples': [
            'Generate: Create content draft via API',
            'Weekly: Automated Sunday 2:30 AM generation',
            'Research: LLM Council-powered topic research'
        ],
        'performance': '~3 min per draft',
        'last_used': '2026-01-17',
        'use_count': 9
    },
    {
        'title': 'video-production',
        'name': 'Video Production Pipeline',
        'location': '/home/ndninja/projects/content-automation/',
        'command': 'python3 production_orchestrator.py create <draft_id>',
        'description': 'Complete video production workflow - voiceover generation, screen recording, thumbnail creation, assembly, quality validation',
        'keywords': ['video', 'production', 'voiceover', 'thumbnail', 'assembly', 'ffmpeg', 'elevenlabs'],
        'usage_examples': [
            'Create: Start new video production from draft',
            'Status: Check production workflow state',
            'Validate: Quality checks before publishing'
        ],
        'performance': 'Variable - 5-15 min per video',
        'last_used': '2026-01-16',
        'use_count': 7
    }
]

def seed_registry():
    """Seed the tool registry in claude-memory database"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            user='claude_mcp',
            database='claude_memory'
        )
        cursor = conn.cursor()

        print("Seeding tool registry...")
        added = 0
        updated = 0

        for tool in TOOLS:
            title = tool['title']
            # Remove title from content to avoid duplication
            content_data = {k: v for k, v in tool.items() if k != 'title'}
            content_json = json.dumps(content_data)

            # Check if exists
            cursor.execute("""
                SELECT title FROM reference_info
                WHERE category = 'tool' AND title = %s
            """, (title,))

            exists = cursor.fetchone() is not None

            if exists:
                # Update existing
                cursor.execute("""
                    UPDATE reference_info
                    SET content = %s, updated_at = NOW()
                    WHERE category = 'tool' AND title = %s
                """, (content_json, title))
                updated += 1
                print(f"  Updated: {tool['name']}")
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO reference_info (category, title, content, context_tag, device, notes, created_at, updated_at)
                    VALUES ('tool', %s, %s, 'always', 'all', 'Memory-Assisted Tool Discovery registry', NOW(), NOW())
                """, (title, content_json))
                added += 1
                print(f"  Added: {tool['name']}")

        conn.commit()
        cursor.close()
        conn.close()

        print(f"\n✅ Registry seeded successfully!")
        print(f"   Added: {added} tools")
        print(f"   Updated: {updated} tools")
        print(f"   Total: {len(TOOLS)} tools in registry")

        return 0

    except Exception as e:
        print(f"❌ Error seeding registry: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(seed_registry())
