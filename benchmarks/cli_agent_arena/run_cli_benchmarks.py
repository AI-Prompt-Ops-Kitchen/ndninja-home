#!/usr/bin/env python3
"""CLI Agent Benchmark Runner

Runs benchmark tasks against CLI coding agents (Kimi, Claude, Gemini)
and records metrics (speed, correctness, cost, autonomy, quality).
"""

import argparse
import sys
import uuid
from pathlib import Path
from typing import List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmarks.cli_agent_arena.task_loader import load_task, list_all_tasks
from benchmarks.cli_agent_arena.adapter_factory import get_adapter, check_adapter_availability
from benchmarks.cli_agent_arena.test_harness import TestHarness
from benchmarks.cli_agent_arena.scoring import ScoringEngine
from benchmarks.cli_agent_arena.database import DatabaseClient


def get_shared_tasks_base() -> Path:
    """Get the base path for shared-tasks directory"""
    for base_path in [Path("benchmarks/shared-tasks"), Path("shared-tasks")]:
        if base_path.exists():
            return base_path
    return Path("benchmarks/shared-tasks")  # Default


def list_tasks() -> List[str]:
    """List all available benchmark tasks"""
    tasks_dir = get_shared_tasks_base() / "algorithms"
    task_paths = []

    if not tasks_dir.exists():
        return task_paths

    for task_dir in tasks_dir.iterdir():
        if task_dir.is_dir() and (task_dir / "task.yaml").exists():
            task_paths.append(f"algorithms/{task_dir.name}")

    return sorted(task_paths)


def main():
    parser = argparse.ArgumentParser(
        description="CLI Agent Benchmark Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run quicksort with Kimi CLI
  %(prog)s --agent kimi --tasks algorithms/quicksort

  # Run all algorithm tasks with Claude
  %(prog)s --agent claude --category algorithms

  # List available tasks
  %(prog)s --list-tasks
        """
    )

    parser.add_argument(
        "--agent",
        choices=["mock", "kimi", "claude", "gemini"],
        help="CLI agent to benchmark"
    )

    parser.add_argument(
        "--tasks",
        nargs="+",
        help="Specific tasks to run (e.g., algorithms/quicksort)"
    )

    parser.add_argument(
        "--category",
        help="Run all tasks in a category (e.g., algorithms)"
    )

    parser.add_argument(
        "--list-tasks",
        action="store_true",
        help="List all available benchmark tasks"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tasks for all agents"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run benchmarks without saving to database"
    )

    args = parser.parse_args()

    # Handle --list-tasks
    if args.list_tasks:
        print("Available benchmark tasks:\n")
        for task_path in list_tasks():
            task = load_task(get_shared_tasks_base() / task_path)
            print(f"  {task_path:30s} ({task.difficulty:6s}, ~{task.estimated_time_seconds}s)")
        return 0

    # Handle execution
    if args.all or args.tasks or args.category:
        return run_benchmarks(args)

    print("No action specified. Use --help for usage information.")
    return 1


def run_benchmarks(args):
    """Run benchmarks based on arguments

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success)
    """
    # Determine which tasks to run
    if args.all or args.category:
        all_tasks = list_tasks()
        if args.category:
            task_list = [t for t in all_tasks if t.startswith(f"{args.category}/")]
        else:
            task_list = all_tasks
    else:
        task_list = args.tasks or []

    if not task_list:
        print("No tasks to run")
        return 1

    # Determine which agents to test
    if args.all:
        agents = ["mock", "kimi", "claude", "gemini"]
    elif args.agent:
        agents = [args.agent]
    else:
        print("Error: Must specify --agent or --all")
        return 1

    # Check adapter availability
    availability = check_adapter_availability()

    # Initialize services
    test_harness = TestHarness()
    scoring_engine = ScoringEngine()
    db_client = DatabaseClient() if not args.dry_run else None

    run_id = str(uuid.uuid4())
    print(f"Benchmark Run ID: {run_id}\n")

    results = []
    for agent in agents:
        if not availability.get(agent, False):
            print(f"⚠️  Skipping {agent}: CLI not available")
            continue

        print(f"Running benchmarks with {agent}:")

        for task_path in task_list:
            task = load_task(get_shared_tasks_base() / task_path)
            print(f"  - {task.name} ({task.difficulty}, ~{task.estimated_time_seconds}s)...", end=" ", flush=True)

            adapter = None
            try:
                # Get adapter
                adapter = get_adapter(agent)

                # Setup
                adapter.setup(str(task.task_dir))

                # Execute
                benchmark_result = adapter.execute_task(task.prompt, timeout=task.estimated_time_seconds * 2)

                # Run tests for correctness
                test_result = test_harness.run_tests(
                    task_dir=str(task.task_dir),
                    test_command=task.test_command
                )

                # Calculate score
                score = scoring_engine.calculate_total_score(
                    benchmark_result=benchmark_result,
                    test_result=test_result,
                    estimated_time=task.estimated_time_seconds,
                    budgeted_cost=task.budgeted_cost_usd,
                    linting_issues=0  # TODO: Add linting in Phase 4
                )

                # Display result
                if benchmark_result.success and test_result.pass_rate == 100.0:
                    print(f"✅ Score: {score.total_score:.1f}/100 ({benchmark_result.wall_time:.1f}s)")
                elif test_result.pass_rate > 0:
                    print(f"⚠️  Partial: {score.total_score:.1f}/100 ({test_result.pass_rate:.0f}% tests passed)")
                else:
                    print(f"❌ Failed: {score.total_score:.1f}/100")

                # Save to database
                if db_client:
                    result_id = db_client.save_result(
                        agent_name=agent,
                        task_name=task.name,
                        task_category=task.category,
                        benchmark_result=benchmark_result,
                        test_result=test_result,
                        score=score
                    )
                    print(f"     Saved to database (ID: {result_id})")

                results.append((agent, task, benchmark_result, test_result, score))

            except NotImplementedError as e:
                print(f"⚠️  Not implemented")
            except Exception as e:
                print(f"❌ Error: {e}")
            finally:
                if adapter:
                    adapter.cleanup()

    # Summary
    print(f"\n{'='*60}")
    print(f"Completed {len(results)} benchmarks")

    if args.dry_run:
        print("(Dry run - results not saved to database)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
