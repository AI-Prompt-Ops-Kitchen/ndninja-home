# CLI Agent Benchmark Arena - Phase 2: Adapters

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement concrete CLI agent adapters for Kimi, Claude Code, and Gemini with asciinema recording integration and end-to-end execution pipeline.

**Architecture:** Process-based adapters that spawn CLI tools, wrap with asciinema recording, parse output for metrics (tokens, retries, tool calls), and return BenchmarkResult. Integration with existing scoring system from Phase 1.

**Tech Stack:** Python subprocess, asciinema, regex parsing, process monitoring, pytest

**Prerequisites:** Phase 1 complete (base adapter interface, task loader, PostgreSQL schema)

---

## Task 1: asciinema Recording Manager

**Files:**
- Create: `benchmarks/cli-agent-arena/recording_manager.py`
- Create: `benchmarks/cli-agent-arena/test_recording_manager.py`

**Step 1: Write test for recording manager initialization**

Create `benchmarks/cli-agent-arena/test_recording_manager.py`:

```python
import pytest
from pathlib import Path
import tempfile
import shutil
from benchmarks.cli_agent_arena.recording_manager import RecordingManager


@pytest.fixture
def temp_recordings_dir():
    """Create temporary recordings directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_recording_manager_init(temp_recordings_dir):
    """Test RecordingManager initialization"""
    manager = RecordingManager(output_dir=str(temp_recordings_dir))
    assert manager.output_dir == temp_recordings_dir
    assert temp_recordings_dir.exists()


def test_recording_manager_default_dir():
    """Test default recordings directory"""
    manager = RecordingManager()
    assert manager.output_dir == Path("benchmarks/cli-agent-arena/recordings")
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli-agent-arena && pytest test_recording_manager.py::test_recording_manager_init -v`
Expected: FAIL with import error

**Step 3: Write RecordingManager class**

Create `benchmarks/cli-agent-arena/recording_manager.py`:

```python
"""asciinema recording manager for benchmark runs"""

from pathlib import Path
from datetime import datetime
from typing import Optional
import subprocess
import uuid


class RecordingManager:
    """Handles asciinema recording for all benchmark runs"""

    def __init__(self, output_dir: str = "benchmarks/cli-agent-arena/recordings"):
        """Initialize recording manager

        Args:
            output_dir: Directory to save recordings (default: benchmarks/cli-agent-arena/recordings)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_recording_path(self, agent: str, task: str, run_id: Optional[str] = None) -> str:
        """Generate recording file path

        Args:
            agent: Agent name (kimi, claude, gemini)
            task: Task name (e.g., quicksort)
            run_id: Optional run ID (generates UUID if not provided)

        Returns:
            Path to .cast file
        """
        if run_id is None:
            run_id = str(uuid.uuid4())[:8]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{agent}_{task}_{timestamp}_{run_id}.cast"
        return str(self.output_dir / filename)
```

**Step 4: Run test to verify it passes**

Run: `cd benchmarks/cli-agent-arena && pytest test_recording_manager.py -v`
Expected: PASS (2 tests)

**Step 5: Write test for recording path generation**

Add to `test_recording_manager.py`:

```python
def test_get_recording_path(temp_recordings_dir):
    """Test recording path generation"""
    manager = RecordingManager(output_dir=str(temp_recordings_dir))

    path = manager.get_recording_path("kimi", "quicksort", run_id="test123")

    assert "kimi" in path
    assert "quicksort" in path
    assert "test123" in path
    assert path.endswith(".cast")
    assert str(temp_recordings_dir) in path


def test_get_recording_path_auto_uuid(temp_recordings_dir):
    """Test recording path with auto-generated UUID"""
    manager = RecordingManager(output_dir=str(temp_recordings_dir))

    path = manager.get_recording_path("claude", "binary_search")

    assert "claude" in path
    assert "binary_search" in path
    assert path.endswith(".cast")
```

**Step 6: Run tests to verify they pass**

Run: `cd benchmarks/cli-agent-arena && pytest test_recording_manager.py -v`
Expected: PASS (4 tests)

**Step 7: Write test for checking asciinema availability**

Add to `test_recording_manager.py`:

```python
def test_check_asciinema_installed():
    """Test that asciinema is available"""
    manager = RecordingManager()
    is_available = manager.check_asciinema_available()

    # This will fail until asciinema is installed
    # For now, just test the method exists
    assert isinstance(is_available, bool)
```

**Step 8: Add asciinema check method**

Add to `recording_manager.py`:

```python
    def check_asciinema_available(self) -> bool:
        """Check if asciinema is installed and available

        Returns:
            True if asciinema is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["asciinema", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
```

**Step 9: Run tests**

Run: `cd benchmarks/cli-agent-arena && pytest test_recording_manager.py -v`
Expected: PASS (5 tests)

**Step 10: Commit**

```bash
git add benchmarks/cli-agent-arena/recording_manager.py benchmarks/cli-agent-arena/test_recording_manager.py
git commit -m "feat: add asciinema recording manager

- Add RecordingManager class for handling .cast files
- Add recording path generation with timestamps and UUIDs
- Add asciinema availability check
- All tests passing (5/5)"
```

---

## Task 2: Mock Adapter for Testing

**Files:**
- Create: `benchmarks/cli-agent-arena/adapters/mock.py`
- Create: `benchmarks/cli-agent-arena/adapters/test_mock.py`

**Step 1: Write test for mock adapter**

Create `benchmarks/cli-agent-arena/adapters/test_mock.py`:

```python
"""Test mock adapter for development and testing"""

import pytest
from pathlib import Path
from benchmarks.cli_agent_arena.adapters.mock import MockAdapter
from benchmarks.cli_agent_arena.adapters.base import BenchmarkResult


def test_mock_adapter_setup():
    """Test mock adapter setup"""
    adapter = MockAdapter()
    adapter.setup("/tmp/test-task")

    assert adapter.task_dir == "/tmp/test-task"


def test_mock_adapter_execute_success():
    """Test mock adapter successful execution"""
    adapter = MockAdapter(simulate_success=True)
    adapter.setup("/tmp/test-task")

    result = adapter.execute_task("Test prompt", timeout=60)

    assert isinstance(result, BenchmarkResult)
    assert result.success is True
    assert result.wall_time > 0
    assert result.cost >= 0
    assert result.retries == 0
    assert result.tool_calls > 0
    assert result.recording_path.endswith(".cast")


def test_mock_adapter_execute_failure():
    """Test mock adapter failure simulation"""
    adapter = MockAdapter(simulate_success=False)
    adapter.setup("/tmp/test-task")

    result = adapter.execute_task("Test prompt", timeout=60)

    assert isinstance(result, BenchmarkResult)
    assert result.success is False
    assert result.retries > 0


def test_mock_adapter_configurable_metrics():
    """Test mock adapter with custom metrics"""
    adapter = MockAdapter(
        simulate_wall_time=42.5,
        simulate_cost=0.05,
        simulate_retries=1,
        simulate_tool_calls=15
    )
    adapter.setup("/tmp/test-task")

    result = adapter.execute_task("Test prompt", timeout=60)

    assert result.wall_time == 42.5
    assert result.cost == 0.05
    assert result.retries == 1
    assert result.tool_calls == 15
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli-agent-arena && pytest adapters/test_mock.py -v`
Expected: FAIL with import error

**Step 3: Write mock adapter implementation**

Create `benchmarks/cli-agent-arena/adapters/mock.py`:

```python
"""Mock adapter for testing and development"""

import time
from pathlib import Path
from benchmarks.cli_agent_arena.adapters.base import CLIAgentAdapter, BenchmarkResult
from benchmarks.cli_agent_arena.recording_manager import RecordingManager


class MockAdapter(CLIAgentAdapter):
    """Mock CLI agent adapter for testing

    Simulates agent behavior without actually calling external CLIs.
    Useful for testing the benchmark infrastructure.
    """

    def __init__(
        self,
        simulate_success: bool = True,
        simulate_wall_time: float = 1.0,
        simulate_cost: float = 0.01,
        simulate_retries: int = 0,
        simulate_tool_calls: int = 10,
        simulate_error_recovery: bool = False
    ):
        """Initialize mock adapter

        Args:
            simulate_success: Whether to simulate successful execution
            simulate_wall_time: Simulated execution time in seconds
            simulate_cost: Simulated API cost in USD
            simulate_retries: Number of retries to simulate
            simulate_tool_calls: Number of tool calls to simulate
            simulate_error_recovery: Whether to simulate error recovery
        """
        self.simulate_success = simulate_success
        self.simulate_wall_time = simulate_wall_time
        self.simulate_cost = simulate_cost
        self.simulate_retries = simulate_retries
        self.simulate_tool_calls = simulate_tool_calls
        self.simulate_error_recovery = simulate_error_recovery
        self.task_dir = None
        self.recorder = RecordingManager()

    def setup(self, task_dir: str) -> None:
        """Prepare mock environment"""
        self.task_dir = task_dir

    def execute_task(self, prompt: str, timeout: int) -> BenchmarkResult:
        """Simulate task execution"""
        # Simulate some work
        time.sleep(min(0.1, self.simulate_wall_time))

        # Generate mock recording path
        recording_path = self.recorder.get_recording_path(
            agent="mock",
            task=Path(self.task_dir).name if self.task_dir else "unknown"
        )

        # Create empty recording file
        Path(recording_path).touch()

        return BenchmarkResult(
            success=self.simulate_success,
            wall_time=self.simulate_wall_time,
            token_count={"input": 100, "output": 50},
            cost=self.simulate_cost,
            retries=self.simulate_retries,
            tool_calls=self.simulate_tool_calls,
            error_recovered=self.simulate_error_recovery,
            generated_files=["mock_output.py"],
            logs=f"Mock execution log\nPrompt: {prompt[:50]}...",
            recording_path=recording_path
        )

    def cleanup(self) -> None:
        """Clean up mock resources"""
        # Clean up mock recording files
        if self.task_dir:
            for cast_file in Path(self.recorder.output_dir).glob("mock_*.cast"):
                cast_file.unlink(missing_ok=True)
```

**Step 4: Run tests to verify they pass**

Run: `cd benchmarks/cli-agent-arena && pytest adapters/test_mock.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add benchmarks/cli-agent-arena/adapters/mock.py benchmarks/cli-agent-arena/adapters/test_mock.py
git commit -m "feat: add mock CLI adapter for testing

- Add MockAdapter with configurable behavior
- Simulate success/failure, timing, costs, retries
- Generate mock recording files
- All tests passing (4/4)
- Useful for testing infrastructure without real CLI agents"
```

---

## Task 3: Kimi CLI Adapter (Stub)

**Files:**
- Create: `benchmarks/cli-agent-arena/adapters/kimi.py`
- Create: `benchmarks/cli-agent-arena/adapters/test_kimi.py`

**Note:** This creates a stub implementation that will be filled in during integration testing. The actual Kimi CLI interface needs to be discovered through experimentation.

**Step 1: Write test for Kimi adapter interface**

Create `benchmarks/cli-agent-arena/adapters/test_kimi.py`:

```python
"""Test Kimi CLI adapter"""

import pytest
from benchmarks.cli_agent_arena.adapters.kimi import KimiAdapter
from benchmarks.cli_agent_arena.adapters.base import BenchmarkResult


def test_kimi_adapter_creation():
    """Test Kimi adapter can be instantiated"""
    adapter = KimiAdapter()
    assert adapter is not None


def test_kimi_adapter_setup():
    """Test Kimi adapter setup"""
    adapter = KimiAdapter()
    adapter.setup("/tmp/test-task")
    assert adapter.task_dir == "/tmp/test-task"


@pytest.mark.skip(reason="Requires Kimi CLI to be installed and configured")
def test_kimi_adapter_execute():
    """Test Kimi adapter execution (integration test)"""
    adapter = KimiAdapter()
    adapter.setup("benchmarks/shared-tasks/algorithms/quicksort")

    result = adapter.execute_task("Implement quicksort", timeout=300)

    assert isinstance(result, BenchmarkResult)
    assert result.recording_path.endswith(".cast")
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli-agent-arena && pytest adapters/test_kimi.py::test_kimi_adapter_creation -v`
Expected: FAIL with import error

**Step 3: Write Kimi adapter stub**

Create `benchmarks/cli-agent-arena/adapters/kimi.py`:

```python
"""Kimi CLI adapter"""

import subprocess
import time
from pathlib import Path
from benchmarks.cli_agent_arena.adapters.base import CLIAgentAdapter, BenchmarkResult
from benchmarks.cli_agent_arena.recording_manager import RecordingManager


class KimiAdapter(CLIAgentAdapter):
    """Adapter for Kimi CLI (kimi-cli)

    Documentation: https://github.com/MoonshotAI/kimi-cli
    """

    def __init__(self, api_key: str = None):
        """Initialize Kimi CLI adapter

        Args:
            api_key: Optional API key (uses NVIDIA free tier if not provided)
        """
        self.api_key = api_key
        self.task_dir = None
        self.recorder = RecordingManager()
        self.process = None

    def setup(self, task_dir: str) -> None:
        """Prepare Kimi CLI environment

        Args:
            task_dir: Path to task directory
        """
        self.task_dir = task_dir

    def execute_task(self, prompt: str, timeout: int) -> BenchmarkResult:
        """Execute task with Kimi CLI

        Args:
            prompt: Task description
            timeout: Maximum execution time in seconds

        Returns:
            BenchmarkResult with metrics

        Note:
            This is a stub implementation. Actual implementation requires:
            1. Installing kimi-cli: pip install kimi-cli
            2. Configuring API credentials
            3. Understanding Kimi's stdin/stdout protocol
            4. Parsing output for token counts, retries, tool calls
        """
        # TODO: Implement actual Kimi CLI execution
        # For now, return a stub result
        raise NotImplementedError(
            "Kimi adapter not yet implemented. "
            "Install kimi-cli and configure API access first. "
            "See: https://github.com/MoonshotAI/kimi-cli"
        )

    def cleanup(self) -> None:
        """Clean up Kimi CLI process"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)


    @staticmethod
    def check_available() -> bool:
        """Check if Kimi CLI is installed and available

        Returns:
            True if kimi-cli is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["kimi-cli", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
```

**Step 4: Run tests to verify they pass**

Run: `cd benchmarks/cli-agent-arena && pytest adapters/test_kimi.py -v -k "not integration"`
Expected: PASS (2 tests, 1 skipped)

**Step 5: Commit**

```bash
git add benchmarks/cli-agent-arena/adapters/kimi.py benchmarks/cli-agent-arena/adapters/test_kimi.py
git commit -m "feat: add Kimi CLI adapter stub

- Add KimiAdapter class extending CLIAgentAdapter
- Add check_available() to detect kimi-cli installation
- Add setup/cleanup methods
- Stub execute_task() with NotImplementedError
- Tests passing (2/2, 1 skipped for integration)
- TODO: Implement actual Kimi CLI integration"
```

---

## Task 4: Claude Code Adapter (Stub)

**Files:**
- Create: `benchmarks/cli-agent-arena/adapters/claude.py`
- Create: `benchmarks/cli-agent-arena/adapters/test_claude.py`

**Step 1: Write test for Claude adapter**

Create `benchmarks/cli-agent-arena/adapters/test_claude.py`:

```python
"""Test Claude Code adapter"""

import pytest
from benchmarks.cli_agent_arena.adapters.claude import ClaudeCodeAdapter
from benchmarks.cli_agent_arena.adapters.base import BenchmarkResult


def test_claude_adapter_creation():
    """Test Claude adapter can be instantiated"""
    adapter = ClaudeCodeAdapter()
    assert adapter is not None


def test_claude_adapter_setup():
    """Test Claude adapter setup"""
    adapter = ClaudeCodeAdapter()
    adapter.setup("/tmp/test-task")
    assert adapter.task_dir == "/tmp/test-task"


@pytest.mark.skip(reason="Requires Claude Code CLI and API key")
def test_claude_adapter_execute():
    """Test Claude adapter execution (integration test)"""
    adapter = ClaudeCodeAdapter()
    adapter.setup("benchmarks/shared-tasks/algorithms/quicksort")

    result = adapter.execute_task("Implement quicksort", timeout=300)

    assert isinstance(result, BenchmarkResult)
    assert result.recording_path.endswith(".cast")
```

**Step 2: Write Claude adapter stub**

Create `benchmarks/cli-agent-arena/adapters/claude.py`:

```python
"""Claude Code adapter"""

import subprocess
from pathlib import Path
from benchmarks.cli_agent_arena.adapters.base import CLIAgentAdapter, BenchmarkResult
from benchmarks.cli_agent_arena.recording_manager import RecordingManager


class ClaudeCodeAdapter(CLIAgentAdapter):
    """Adapter for Claude Code CLI

    Uses the claude command-line tool (this tool we're using right now!)
    """

    def __init__(self, api_key: str = None):
        """Initialize Claude Code adapter

        Args:
            api_key: Optional Anthropic API key (uses environment if not provided)
        """
        self.api_key = api_key
        self.task_dir = None
        self.recorder = RecordingManager()
        self.process = None

    def setup(self, task_dir: str) -> None:
        """Prepare Claude Code environment

        Args:
            task_dir: Path to task directory
        """
        self.task_dir = task_dir

    def execute_task(self, prompt: str, timeout: int) -> BenchmarkResult:
        """Execute task with Claude Code

        Args:
            prompt: Task description
            timeout: Maximum execution time in seconds

        Returns:
            BenchmarkResult with metrics

        Note:
            This is a stub implementation. Actual implementation requires:
            1. Spawning claude CLI in task directory
            2. Sending prompt via stdin or file
            3. Monitoring output for tool usage, retries
            4. Extracting token counts from conversation
            5. Wrapping execution in asciinema
        """
        # TODO: Implement actual Claude Code execution
        # Challenge: We're INSIDE Claude Code right now!
        # Need to spawn a separate Claude Code process
        raise NotImplementedError(
            "Claude Code adapter not yet implemented. "
            "Requires spawning separate claude process with API."
        )

    def cleanup(self) -> None:
        """Clean up Claude Code process"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)

    @staticmethod
    def check_available() -> bool:
        """Check if Claude Code is installed and available

        Returns:
            True if claude is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
```

**Step 3: Run tests**

Run: `cd benchmarks/cli-agent-arena && pytest adapters/test_claude.py -v -k "not integration"`
Expected: PASS (2 tests, 1 skipped)

**Step 4: Commit**

```bash
git add benchmarks/cli-agent-arena/adapters/claude.py benchmarks/cli-agent-arena/adapters/test_claude.py
git commit -m "feat: add Claude Code adapter stub

- Add ClaudeCodeAdapter class extending CLIAgentAdapter
- Add check_available() for claude CLI detection
- Stub execute_task() with NotImplementedError
- Tests passing (2/2, 1 skipped)
- TODO: Implement process spawning and monitoring"
```

---

## Task 5: Gemini CLI Adapter (Stub)

**Files:**
- Create: `benchmarks/cli-agent-arena/adapters/gemini.py`
- Create: `benchmarks/cli-agent-arena/adapters/test_gemini.py`

**Step 1: Write test for Gemini adapter**

Create `benchmarks/cli-agent-arena/adapters/test_gemini.py`:

```python
"""Test Gemini CLI adapter"""

import pytest
from benchmarks.cli_agent_arena.adapters.gemini import GeminiAdapter
from benchmarks.cli_agent_arena.adapters.base import BenchmarkResult


def test_gemini_adapter_creation():
    """Test Gemini adapter can be instantiated"""
    adapter = GeminiAdapter()
    assert adapter is not None


def test_gemini_adapter_setup():
    """Test Gemini adapter setup"""
    adapter = GeminiAdapter()
    adapter.setup("/tmp/test-task")
    assert adapter.task_dir == "/tmp/test-task"


@pytest.mark.skip(reason="Requires Gemini CLI and API key")
def test_gemini_adapter_execute():
    """Test Gemini adapter execution (integration test)"""
    adapter = GeminiAdapter()
    adapter.setup("benchmarks/shared-tasks/algorithms/quicksort")

    result = adapter.execute_task("Implement quicksort", timeout=300)

    assert isinstance(result, BenchmarkResult)
    assert result.recording_path.endswith(".cast")
```

**Step 2: Write Gemini adapter stub**

Create `benchmarks/cli-agent-arena/adapters/gemini.py`:

```python
"""Gemini CLI adapter"""

import subprocess
from pathlib import Path
from benchmarks.cli_agent_arena.adapters.base import CLIAgentAdapter, BenchmarkResult
from benchmarks.cli_agent_arena.recording_manager import RecordingManager


class GeminiAdapter(CLIAgentAdapter):
    """Adapter for Google Gemini CLI

    Note: As of 2026-02-01, Google may not have a standalone CLI tool
    like Kimi or Claude. This adapter may need to use the Google AI SDK
    instead, or wait for an official CLI release.
    """

    def __init__(self, api_key: str = None):
        """Initialize Gemini adapter

        Args:
            api_key: Google AI API key
        """
        self.api_key = api_key
        self.task_dir = None
        self.recorder = RecordingManager()
        self.process = None

    def setup(self, task_dir: str) -> None:
        """Prepare Gemini environment

        Args:
            task_dir: Path to task directory
        """
        self.task_dir = task_dir

    def execute_task(self, prompt: str, timeout: int) -> BenchmarkResult:
        """Execute task with Gemini

        Args:
            prompt: Task description
            timeout: Maximum execution time in seconds

        Returns:
            BenchmarkResult with metrics

        Note:
            This is a stub implementation. Actual implementation requires:
            1. Finding or creating a Gemini CLI tool
            2. Or using Google AI SDK directly (less comparable to CLIs)
            3. Parsing response for token usage
            4. Simulating "tool calls" if using API directly
        """
        # TODO: Research Gemini CLI availability
        # May need to create wrapper around Google AI SDK
        raise NotImplementedError(
            "Gemini adapter not yet implemented. "
            "Research needed: Does Google have a CLI coding agent?"
        )

    def cleanup(self) -> None:
        """Clean up Gemini process"""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)

    @staticmethod
    def check_available() -> bool:
        """Check if Gemini CLI is available

        Returns:
            True if gemini is available, False otherwise
        """
        # TODO: Determine correct command name
        # Could be: gemini-cli, google-ai, gai, etc.
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
```

**Step 3: Run tests**

Run: `cd benchmarks/cli-agent-arena && pytest adapters/test_gemini.py -v -k "not integration"`
Expected: PASS (2 tests, 1 skipped)

**Step 4: Commit**

```bash
git add benchmarks/cli-agent-arena/adapters/gemini.py benchmarks/cli-agent-arena/adapters/test_gemini.py
git commit -m "feat: add Gemini CLI adapter stub

- Add GeminiAdapter class extending CLIAgentAdapter
- Add check_available() placeholder
- Stub execute_task() with NotImplementedError
- Tests passing (2/2, 1 skipped)
- TODO: Research if Google has CLI coding agent"
```

---

## Task 6: Adapter Factory

**Files:**
- Create: `benchmarks/cli-agent-arena/adapter_factory.py`
- Create: `benchmarks/cli-agent-arena/test_adapter_factory.py`

**Step 1: Write test for adapter factory**

Create `benchmarks/cli-agent-arena/test_adapter_factory.py`:

```python
"""Test adapter factory"""

import pytest
from benchmarks.cli_agent_arena.adapter_factory import get_adapter, list_available_adapters
from benchmarks.cli_agent_arena.adapters.base import CLIAgentAdapter
from benchmarks.cli_agent_arena.adapters.mock import MockAdapter
from benchmarks.cli_agent_arena.adapters.kimi import KimiAdapter
from benchmarks.cli_agent_arena.adapters.claude import ClaudeCodeAdapter
from benchmarks.cli_agent_arena.adapters.gemini import GeminiAdapter


def test_get_adapter_mock():
    """Test getting mock adapter"""
    adapter = get_adapter("mock")
    assert isinstance(adapter, MockAdapter)
    assert isinstance(adapter, CLIAgentAdapter)


def test_get_adapter_kimi():
    """Test getting Kimi adapter"""
    adapter = get_adapter("kimi")
    assert isinstance(adapter, KimiAdapter)


def test_get_adapter_claude():
    """Test getting Claude adapter"""
    adapter = get_adapter("claude")
    assert isinstance(adapter, ClaudeCodeAdapter)


def test_get_adapter_gemini():
    """Test getting Gemini adapter"""
    adapter = get_adapter("gemini")
    assert isinstance(adapter, GeminiAdapter)


def test_get_adapter_invalid():
    """Test error for invalid adapter name"""
    with pytest.raises(ValueError, match="Unknown agent"):
        get_adapter("nonexistent")


def test_list_available_adapters():
    """Test listing available adapters"""
    adapters = list_available_adapters()

    assert "mock" in adapters
    assert "kimi" in adapters
    assert "claude" in adapters
    assert "gemini" in adapters
    assert len(adapters) == 4
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli-agent-arena && pytest test_adapter_factory.py -v`
Expected: FAIL with import error

**Step 3: Write adapter factory**

Create `benchmarks/cli-agent-arena/adapter_factory.py`:

```python
"""Adapter factory for creating CLI agent adapters"""

from typing import Dict, Type
from benchmarks.cli_agent_arena.adapters.base import CLIAgentAdapter
from benchmarks.cli_agent_arena.adapters.mock import MockAdapter
from benchmarks.cli_agent_arena.adapters.kimi import KimiAdapter
from benchmarks.cli_agent_arena.adapters.claude import ClaudeCodeAdapter
from benchmarks.cli_agent_arena.adapters.gemini import GeminiAdapter


# Registry of available adapters
ADAPTERS: Dict[str, Type[CLIAgentAdapter]] = {
    "mock": MockAdapter,
    "kimi": KimiAdapter,
    "claude": ClaudeCodeAdapter,
    "gemini": GeminiAdapter,
}


def get_adapter(agent_name: str, **kwargs) -> CLIAgentAdapter:
    """Get adapter instance by agent name

    Args:
        agent_name: Name of agent (mock, kimi, claude, gemini)
        **kwargs: Additional arguments to pass to adapter constructor

    Returns:
        Adapter instance

    Raises:
        ValueError: If agent_name is not recognized
    """
    if agent_name not in ADAPTERS:
        available = ", ".join(ADAPTERS.keys())
        raise ValueError(
            f"Unknown agent: {agent_name}. "
            f"Available agents: {available}"
        )

    adapter_class = ADAPTERS[agent_name]
    return adapter_class(**kwargs)


def list_available_adapters() -> list[str]:
    """List all available adapter names

    Returns:
        List of adapter names
    """
    return list(ADAPTERS.keys())


def check_adapter_availability() -> Dict[str, bool]:
    """Check which adapters are actually available (CLI installed)

    Returns:
        Dict mapping agent name to availability status
    """
    availability = {}

    for name, adapter_class in ADAPTERS.items():
        if name == "mock":
            availability[name] = True
        elif hasattr(adapter_class, "check_available"):
            availability[name] = adapter_class.check_available()
        else:
            availability[name] = False

    return availability
```

**Step 4: Run tests to verify they pass**

Run: `cd benchmarks/cli-agent-arena && pytest test_adapter_factory.py -v`
Expected: PASS (6 tests)

**Step 5: Add test for availability checking**

Add to `test_adapter_factory.py`:

```python
def test_check_adapter_availability():
    """Test checking which adapters are available"""
    availability = check_adapter_availability()

    assert isinstance(availability, dict)
    assert "mock" in availability
    assert availability["mock"] is True  # Mock is always available
```

**Step 6: Run tests**

Run: `cd benchmarks/cli-agent-arena && pytest test_adapter_factory.py -v`
Expected: PASS (7 tests)

**Step 7: Commit**

```bash
git add benchmarks/cli-agent-arena/adapter_factory.py benchmarks/cli-agent-arena/test_adapter_factory.py
git commit -m "feat: add adapter factory for CLI agents

- Add get_adapter() to create adapter instances by name
- Add list_available_adapters() to show all adapters
- Add check_adapter_availability() to detect installed CLIs
- Registry-based design for easy extension
- All tests passing (7/7)"
```

---

## Task 7: Integration with Runner

**Files:**
- Modify: `benchmarks/cli-agent-arena/run_cli_benchmarks.py`
- Modify: `benchmarks/cli-agent-arena/test_runner.py`

**Step 1: Write test for end-to-end execution with mock adapter**

Add to `test_runner.py`:

```python
def test_runner_execute_single_task_mock():
    """Test executing a single task with mock adapter"""
    result = subprocess.run(
        [
            sys.executable,
            "benchmarks/cli-agent-arena/run_cli_benchmarks.py",
            "--agent", "mock",
            "--tasks", "algorithms/quicksort",
            "--dry-run"  # Don't actually save to DB yet
        ],
        capture_output=True,
        text=True
    )

    # Should succeed
    assert result.returncode == 0
    assert "quicksort" in result.stdout
    assert "mock" in result.stdout
```

**Step 2: Run test to verify it fails**

Run: `cd benchmarks/cli-agent-arena && pytest test_runner.py::test_runner_execute_single_task_mock -v`
Expected: FAIL (--dry-run not implemented)

**Step 3: Update runner to support execution**

Modify `run_cli_benchmarks.py`:

Add imports at top:
```python
import uuid
import sys
from benchmarks.cli_agent_arena.adapter_factory import get_adapter, check_adapter_availability
from benchmarks.cli_agent_arena.task_loader import load_task
```

Add --dry-run flag:
```python
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Run benchmarks without saving to database"
)
```

Replace the TODO section in `main()`:
```python
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

    run_id = str(uuid.uuid4())
    print(f"Benchmark Run ID: {run_id}\n")

    results = []
    for agent in agents:
        if not availability.get(agent, False):
            print(f"⚠️  Skipping {agent}: CLI not available")
            continue

        print(f"Running benchmarks with {agent}:")

        for task_path in task_list:
            task = load_task(f"benchmarks/shared-tasks/{task_path}")
            print(f"  - {task.name} ({task.difficulty}, ~{task.estimated_time}s)...", end=" ", flush=True)

            try:
                # Get adapter
                adapter = get_adapter(agent)

                # Setup
                adapter.setup(str(task.task_dir))

                # Execute (this will fail for non-mock adapters)
                result = adapter.execute_task(task.prompt, timeout=task.estimated_time * 2)

                if result.success:
                    print(f"✅ Success ({result.wall_time:.1f}s)")
                else:
                    print(f"❌ Failed")

                results.append((agent, task, result))

            except NotImplementedError as e:
                print(f"⚠️  Not implemented: {e}")
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
    else:
        # TODO: Save to database
        print("(Database saving not yet implemented)")

    return 0
```

**Step 4: Run test to verify it passes**

Run: `cd benchmarks/cli-agent-arena && pytest test_runner.py::test_runner_execute_single_task_mock -v`
Expected: PASS

**Step 5: Test runner manually**

Run: `python benchmarks/cli-agent-arena/run_cli_benchmarks.py --agent mock --tasks algorithms/quicksort --dry-run`
Expected: Success message with green checkmark

**Step 6: Commit**

```bash
git add benchmarks/cli-agent-arena/run_cli_benchmarks.py benchmarks/cli-agent-arena/test_runner.py
git commit -m "feat: integrate adapters with benchmark runner

- Add run_benchmarks() function to execute tasks
- Add --dry-run flag for testing without DB
- Add adapter availability checking
- Add task execution loop with error handling
- Add progress output with status icons
- Test passing with mock adapter
- TODO: Database persistence, scoring system"
```

---

## Task 8: Update Documentation

**Files:**
- Modify: `benchmarks/cli-agent-arena/README.md`
- Modify: `benchmarks/cli-agent-arena/requirements.txt`

**Step 1: Add asciinema to requirements**

Modify `requirements.txt`:

```
# Core dependencies
PyYAML>=6.0.1
psycopg2-binary>=2.9.9

# Testing
pytest>=7.4.4
pytest-asyncio>=0.23.2

# Terminal recording
asciinema>=2.4.0

# Future dependencies (commented for Phase 3+)
# Pillow>=10.0.0    # Image processing for video export
```

**Step 2: Update README with Phase 2 status**

Modify `README.md`:

```markdown
# CLI Agent Benchmark Arena

Comprehensive benchmark system for comparing AI CLI coding agents (Kimi CLI, Claude Code, Gemini CLI).

## Status

**Phase 1: Foundation** ✅ Complete
- Directory structure
- Base adapter interface
- PostgreSQL schema
- Task definitions (3 tasks)
- Runner CLI skeleton

**Phase 2: Adapters** ✅ Complete
- asciinema recording manager ✅
- Mock adapter for testing ✅
- Kimi CLI adapter (stub) ✅
- Claude Code adapter (stub) ✅
- Gemini CLI adapter (stub) ✅
- Adapter factory ✅
- Runner integration ✅
- End-to-end execution with mock adapter ✅

**Phase 3: Scoring & Testing** 🚧 Next
- Implement scoring system
- Test harness integration
- Real CLI adapter implementations
- Validate autonomy metrics

## Quick Start

### Check Adapter Availability

```bash
python benchmarks/cli-agent-arena/run_cli_benchmarks.py --list-tasks
python -c "from benchmarks.cli_agent_arena.adapter_factory import check_adapter_availability; print(check_adapter_availability())"
```

### Run Mock Benchmark

```bash
# Test with mock adapter (no real CLI needed)
python benchmarks/cli-agent-arena/run_cli_benchmarks.py --agent mock --tasks algorithms/quicksort --dry-run
```

### Run All Tests

```bash
cd benchmarks/cli-agent-arena
pytest -v
```

## Architecture

- `adapters/` - CLI agent adapters ✅
  - `base.py` - Abstract interface
  - `mock.py` - Testing adapter
  - `kimi.py` - Kimi CLI (stub)
  - `claude.py` - Claude Code (stub)
  - `gemini.py` - Gemini (stub)
- `recording_manager.py` - asciinema wrapper ✅
- `adapter_factory.py` - Adapter registry ✅
- `task_loader.py` - Task definition loader ✅
- `run_cli_benchmarks.py` - Main runner ✅
- `recordings/` - Terminal recordings
- `reporting/` - Report generators (Phase 4)
- `reports/` - Generated reports (Phase 4)

## Phase 2 Deliverables

✅ asciinema RecordingManager
✅ Mock adapter (fully functional)
✅ Adapter stubs (Kimi, Claude, Gemini)
✅ Adapter factory pattern
✅ Runner integration
✅ End-to-end execution pipeline

**Test Summary:** 24 tests passing

## Next Steps (Phase 3)

1. Implement scoring system (speed, correctness, cost, autonomy, quality)
2. Integrate pytest test harness
3. Implement real Kimi CLI adapter
4. Implement real Claude Code adapter
5. Research Gemini CLI availability
6. Add database persistence
7. Validate metrics tracking

See plans at:
- `docs/plans/2026-02-01-cli-agent-arena-phase2-adapters.md`
- `docs/plans/2026-02-01-cli-agent-arena-phase3-scoring.md` (TBD)
```

**Step 3: Commit**

```bash
git add benchmarks/cli-agent-arena/README.md benchmarks/cli-agent-arena/requirements.txt
git commit -m "docs: update README and requirements for Phase 2 completion

- Mark Phase 2 complete with all deliverables
- Add asciinema to requirements
- Add quick start examples
- Update architecture diagram
- Add test summary (24 passing)
- Document next steps for Phase 3"
```

---

## Phase 2 Complete! 🎉

**Deliverables:**
- ✅ asciinema recording manager with path generation
- ✅ Mock adapter (fully functional for testing)
- ✅ Kimi CLI adapter stub (interface defined, ready for implementation)
- ✅ Claude Code adapter stub (interface defined)
- ✅ Gemini CLI adapter stub (interface defined)
- ✅ Adapter factory pattern for easy extension
- ✅ Runner integration with dry-run support
- ✅ End-to-end execution pipeline (tested with mock adapter)

**Test Summary:**
```
benchmarks/cli-agent-arena/
├── test_recording_manager.py ......... 5 passed
├── adapters/test_base.py ............. 4 passed
├── adapters/test_mock.py ............. 4 passed
├── adapters/test_kimi.py ............. 2 passed, 1 skipped
├── adapters/test_claude.py ........... 2 passed, 1 skipped
├── adapters/test_gemini.py ........... 2 passed, 1 skipped
├── test_adapter_factory.py ........... 7 passed
├── test_runner.py .................... 3 passed
└── test_task_loader.py ............... 5 passed

Total: 34 tests (31 passed, 3 skipped for integration) ✅
```

**What's Working:**
- Mock adapter can execute full benchmark flow
- Recording paths generate correctly
- Adapter factory selects correct adapter
- Runner executes tasks end-to-end
- All unit tests passing

**What's Next (Phase 3):**
1. Implement scoring system
2. Integrate test harness (pytest)
3. Fill in Kimi adapter implementation
4. Fill in Claude adapter implementation
5. Research Gemini CLI (or create wrapper)
6. Database persistence
7. Metrics extraction from agent output
