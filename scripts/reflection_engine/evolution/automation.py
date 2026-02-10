#!/usr/bin/env python3
"""
Evolution Automation Module

Provides entry points for automated evolution tasks:
- Weekly digest generation
- Attention alerts
- Integration with daily review

Can be called from n8n, cron, or command line.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import HOME_DIR
from evolution.digest import DigestGenerator, generate_and_save_digest
from evolution.health import HealthCalculator


def generate_weekly_digest(days: int = 7, save_file: bool = True) -> Dict[str, Any]:
    """
    Generate weekly evolution digest.

    Args:
        days: Number of days to include
        save_file: Whether to save to file

    Returns:
        Dict with digest content and metadata
    """
    generator = DigestGenerator()
    try:
        digest = generator.generate_weekly_digest(days)

        result = {
            'success': True,
            'generated_at': datetime.now().isoformat(),
            'days_covered': days,
            'digest': digest
        }

        if save_file:
            path = generator.save_digest(days)
            result['file_path'] = str(path)

        return result

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'generated_at': datetime.now().isoformat()
        }
    finally:
        generator.close()


def check_attention_needed(save_file: bool = True) -> Dict[str, Any]:
    """
    Check for skills needing attention.

    Args:
        save_file: Whether to save alert to file

    Returns:
        Dict with attention status and alert content
    """
    generator = DigestGenerator()
    try:
        alert = generator.generate_attention_alert()

        result = {
            'success': True,
            'checked_at': datetime.now().isoformat(),
            'attention_needed': alert is not None,
            'alert': alert
        }

        if save_file and alert:
            path = generator.save_attention_alert()
            result['file_path'] = str(path) if path else None

        return result

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'checked_at': datetime.now().isoformat()
        }
    finally:
        generator.close()


def get_evolution_summary() -> Dict[str, Any]:
    """
    Get a quick summary of evolution status for n8n integration.

    Returns:
        Dict with stats for dashboard/notifications
    """
    generator = DigestGenerator()
    try:
        stats = generator.get_period_stats(days=7)
        attention_skills = generator.health_calc.get_attention_needed()

        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'reflections_applied_7d': stats.reflections_applied,
                'skills_updated_7d': stats.skills_updated,
                'feedback_given_7d': stats.feedback_given,
                'skill_usages_7d': stats.skills_used,
                'health_improved_7d': stats.health_improved,
                'health_declined_7d': stats.health_declined,
                'attention_needed': stats.attention_needed
            },
            'attention_skills': [
                {
                    'skill': s.skill_name,
                    'score': s.health_score,
                    'reason': s.attention_reason
                }
                for s in attention_skills[:5]
            ]
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
    finally:
        generator.close()


def run_weekly_automation() -> Dict[str, Any]:
    """
    Run full weekly automation tasks.

    This is the main entry point for weekly n8n automation:
    1. Generate weekly digest
    2. Check attention alerts
    3. Return summary for notifications

    Returns:
        Dict with all results
    """
    results = {
        'run_at': datetime.now().isoformat(),
        'success': True,
        'errors': []
    }

    # Generate digest
    digest_result = generate_weekly_digest(days=7, save_file=True)
    results['digest'] = {
        'generated': digest_result.get('success', False),
        'file_path': digest_result.get('file_path')
    }
    if not digest_result.get('success'):
        results['errors'].append(f"Digest: {digest_result.get('error')}")

    # Check attention
    attention_result = check_attention_needed(save_file=True)
    results['attention'] = {
        'checked': attention_result.get('success', False),
        'needs_attention': attention_result.get('attention_needed', False),
        'file_path': attention_result.get('file_path')
    }
    if not attention_result.get('success'):
        results['errors'].append(f"Attention: {attention_result.get('error')}")

    # Get summary stats
    summary_result = get_evolution_summary()
    results['summary'] = summary_result.get('stats', {})
    results['attention_skills'] = summary_result.get('attention_skills', [])
    if not summary_result.get('success'):
        results['errors'].append(f"Summary: {summary_result.get('error')}")

    results['success'] = len(results['errors']) == 0

    return results


def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(
        description='Evolution Automation - Weekly digest and attention alerts'
    )
    parser.add_argument(
        '--action',
        choices=['digest', 'attention', 'summary', 'weekly'],
        default='weekly',
        help='Action to run (default: weekly)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Days to cover for digest (default: 7)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON (for n8n integration)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save files'
    )

    args = parser.parse_args()

    # Run requested action
    if args.action == 'digest':
        result = generate_weekly_digest(args.days, not args.no_save)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(result.get('digest', result.get('error', 'Unknown error')))

    elif args.action == 'attention':
        result = check_attention_needed(not args.no_save)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result.get('alert'):
                print(result['alert'])
            else:
                print("No skills need attention!")

    elif args.action == 'summary':
        result = get_evolution_summary()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result.get('success'):
                stats = result['stats']
                print("=== Evolution Summary (7 days) ===")
                print(f"Reflections Applied: {stats['reflections_applied_7d']}")
                print(f"Skills Updated: {stats['skills_updated_7d']}")
                print(f"Feedback Given: {stats['feedback_given_7d']}")
                print(f"Skill Usages: {stats['skill_usages_7d']}")
                print(f"Attention Needed: {stats['attention_needed']}")
            else:
                print(f"Error: {result.get('error')}")

    elif args.action == 'weekly':
        result = run_weekly_automation()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("=== Weekly Evolution Automation ===")
            print(f"Run at: {result['run_at']}")
            print(f"Success: {result['success']}")

            if result['digest'].get('generated'):
                print(f"Digest saved to: {result['digest']['file_path']}")

            if result['attention'].get('needs_attention'):
                print(f"Attention alert saved to: {result['attention']['file_path']}")
            else:
                print("No skills need attention")

            if result.get('summary'):
                print(f"\nWeekly stats:")
                for key, value in result['summary'].items():
                    print(f"  {key}: {value}")

            if result['errors']:
                print(f"\nErrors: {', '.join(result['errors'])}")


if __name__ == '__main__':
    main()
