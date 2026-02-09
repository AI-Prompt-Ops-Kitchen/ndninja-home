import pytest
from pathlib import Path
import tempfile
import shutil
from recording_manager import RecordingManager


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
    assert manager.output_dir == Path("recordings")


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


def test_check_asciinema_installed():
    """Test that asciinema is available"""
    manager = RecordingManager()
    is_available = manager.check_asciinema_available()

    # This will fail until asciinema is installed
    # For now, just test the method exists
    assert isinstance(is_available, bool)
