"""Task definition and loading utilities for CLI agent benchmarks"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import yaml


@dataclass
class Task:
    """Represents a benchmark task"""
    name: str
    category: str
    difficulty: str
    description: str
    budgeted_cost_usd: float
    estimated_time_seconds: int
    test_command: str
    success_criteria: List[str]
    validation: dict
    tags: List[str]
    prompt: str
    task_dir: Path


def load_task(task_path: Path) -> Task:
    """
    Load a task definition from a directory containing task.yaml and prompt.md

    Args:
        task_path: Path to the task directory

    Returns:
        Task object with all metadata and prompt content

    Raises:
        FileNotFoundError: If task.yaml or prompt.md is missing
        ValueError: If task.yaml is malformed or missing required fields
    """
    task_path = Path(task_path)

    if not task_path.exists():
        raise FileNotFoundError(f"Task directory not found: {task_path}")

    yaml_path = task_path / "task.yaml"
    prompt_path = task_path / "prompt.md"

    if not yaml_path.exists():
        raise FileNotFoundError(f"task.yaml not found in {task_path}")

    if not prompt_path.exists():
        raise FileNotFoundError(f"prompt.md not found in {task_path}")

    # Load YAML metadata
    with open(yaml_path, 'r') as f:
        metadata = yaml.safe_load(f)

    # Validate required fields
    required_fields = [
        'name', 'category', 'difficulty', 'description',
        'budgeted_cost_usd', 'estimated_time_seconds', 'test_command',
        'success_criteria', 'validation', 'tags'
    ]

    missing_fields = [field for field in required_fields if field not in metadata]
    if missing_fields:
        raise ValueError(f"Missing required fields in task.yaml: {missing_fields}")

    # Load prompt content
    with open(prompt_path, 'r') as f:
        prompt = f.read()

    return Task(
        name=metadata['name'],
        category=metadata['category'],
        difficulty=metadata['difficulty'],
        description=metadata['description'],
        budgeted_cost_usd=float(metadata['budgeted_cost_usd']),
        estimated_time_seconds=int(metadata['estimated_time_seconds']),
        test_command=metadata['test_command'],
        success_criteria=metadata['success_criteria'],
        validation=metadata['validation'],
        tags=metadata['tags'],
        prompt=prompt,
        task_dir=task_path
    )


def list_all_tasks(tasks_dir: Path) -> List[Task]:
    """
    List all available tasks in the tasks directory

    Args:
        tasks_dir: Path to the directory containing task subdirectories

    Returns:
        List of Task objects
    """
    tasks = []
    tasks_dir = Path(tasks_dir)

    if not tasks_dir.exists():
        return tasks

    for item in tasks_dir.iterdir():
        if item.is_dir() and (item / "task.yaml").exists():
            try:
                task = load_task(item)
                tasks.append(task)
            except (FileNotFoundError, ValueError) as e:
                # Skip invalid tasks but log the error
                print(f"Warning: Skipping invalid task {item.name}: {e}")

    return tasks
