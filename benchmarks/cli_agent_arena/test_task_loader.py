"""Tests for task loading functionality"""

import pytest
from pathlib import Path
import tempfile
import os
from task_loader import Task, load_task, list_all_tasks


@pytest.fixture
def sample_task_dir(tmp_path):
    """Create a sample task directory for testing"""
    task_dir = tmp_path / "sample_task"
    task_dir.mkdir()

    # Create task.yaml
    task_yaml = task_dir / "task.yaml"
    task_yaml.write_text("""
name: sample_task
category: test
difficulty: easy
description: A sample task for testing
budgeted_cost_usd: 0.01
estimated_time_seconds: 60
test_command: pytest test_sample.py
success_criteria:
  - Tests must pass
  - Code must be clean
validation:
  required_files:
    - sample.py
  test_file: test_sample.py
  min_correctness_score: 70.0
tags:
  - test
  - sample
""")

    # Create prompt.md
    prompt_md = task_dir / "prompt.md"
    prompt_md.write_text("# Sample Task\n\nThis is a sample task prompt.")

    return task_dir


def test_load_task_success(sample_task_dir):
    """Test loading a valid task"""
    task = load_task(sample_task_dir)

    assert isinstance(task, Task)
    assert task.name == "sample_task"
    assert task.category == "test"
    assert task.difficulty == "easy"
    assert task.budgeted_cost_usd == 0.01
    assert task.estimated_time_seconds == 60
    assert task.test_command == "pytest test_sample.py"
    assert len(task.success_criteria) == 2
    assert len(task.tags) == 2
    assert "Sample Task" in task.prompt
    assert task.task_dir == sample_task_dir


def test_load_task_nonexistent_dir():
    """Test loading from non-existent directory"""
    with pytest.raises(FileNotFoundError):
        load_task(Path("/nonexistent/task"))


def test_load_task_missing_yaml(tmp_path):
    """Test loading task with missing task.yaml"""
    task_dir = tmp_path / "no_yaml"
    task_dir.mkdir()
    (task_dir / "prompt.md").write_text("# Test")

    with pytest.raises(FileNotFoundError):
        load_task(task_dir)


def test_load_task_missing_prompt(tmp_path):
    """Test loading task with missing prompt.md"""
    task_dir = tmp_path / "no_prompt"
    task_dir.mkdir()
    (task_dir / "task.yaml").write_text("name: test\ncategory: test")

    with pytest.raises(FileNotFoundError):
        load_task(task_dir)


def test_load_task_malformed_yaml(tmp_path):
    """Test loading task with malformed YAML"""
    task_dir = tmp_path / "bad_yaml"
    task_dir.mkdir()
    (task_dir / "task.yaml").write_text("name: test")  # Missing required fields
    (task_dir / "prompt.md").write_text("# Test")

    with pytest.raises(ValueError):
        load_task(task_dir)


def test_load_real_quicksort_task():
    """Test loading the actual quicksort task"""
    # Find the shared-tasks directory
    current_file = Path(__file__).resolve()
    benchmarks_dir = current_file.parent.parent
    tasks_dir = benchmarks_dir / "shared-tasks"
    quicksort_dir = tasks_dir / "quicksort"

    if not quicksort_dir.exists():
        pytest.skip("Quicksort task not found")

    task = load_task(quicksort_dir)

    assert task.name == "quicksort"
    assert task.category == "algorithms"
    assert task.difficulty == "medium"
    assert "quicksort" in task.description.lower()
    assert task.budgeted_cost_usd > 0
    assert len(task.success_criteria) > 0
    assert len(task.prompt) > 0


def test_list_all_tasks(tmp_path):
    """Test listing all tasks in a directory"""
    # Create multiple task directories
    for i in range(3):
        task_dir = tmp_path / f"task_{i}"
        task_dir.mkdir()

        (task_dir / "task.yaml").write_text(f"""
name: task_{i}
category: test
difficulty: easy
description: Task {i}
budgeted_cost_usd: 0.01
estimated_time_seconds: 60
test_command: pytest test.py
success_criteria: ["pass"]
validation:
  required_files: ["file.py"]
  test_file: test.py
  min_correctness_score: 70.0
tags: ["test"]
""")
        (task_dir / "prompt.md").write_text(f"# Task {i}")

    tasks = list_all_tasks(tmp_path)

    assert len(tasks) == 3
    assert all(isinstance(t, Task) for t in tasks)
    assert {t.name for t in tasks} == {"task_0", "task_1", "task_2"}


def test_list_all_tasks_empty_dir(tmp_path):
    """Test listing tasks from empty directory"""
    tasks = list_all_tasks(tmp_path)
    assert tasks == []


def test_list_all_tasks_nonexistent_dir():
    """Test listing tasks from non-existent directory"""
    tasks = list_all_tasks(Path("/nonexistent"))
    assert tasks == []
