"""asciinema recording manager for benchmark runs"""

from pathlib import Path
from datetime import datetime
from typing import Optional
import subprocess
import uuid


class RecordingManager:
    """Handles asciinema recording for all benchmark runs"""

    def __init__(self, output_dir: str = "recordings"):
        """Initialize recording manager

        Args:
            output_dir: Directory to save recordings (default: recordings)
        """
        path = Path(output_dir)
        if not path.is_absolute():
            path = Path(__file__).parent / path
        self.output_dir = path
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
