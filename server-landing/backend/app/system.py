import psutil
import time
from .models import SystemMetrics

# Store the start time when the module is imported
_start_time = time.time()

def get_system_metrics() -> SystemMetrics:
    """Get current system metrics."""
    # CPU usage (average over 1 second)
    cpu_percent = psutil.cpu_percent(interval=1)

    # Memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent

    # Disk usage (root partition)
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent

    # Docker container count (try to get from docker, fallback to 0)
    container_count = 0
    try:
        import docker
        client = docker.from_env()
        containers = client.containers.list()
        container_count = len(containers)
    except Exception:
        # Docker not available or not running
        pass

    # Uptime in seconds
    uptime_seconds = time.time() - _start_time

    return SystemMetrics(
        cpu_percent=round(cpu_percent, 2),
        memory_percent=round(memory_percent, 2),
        disk_percent=round(disk_percent, 2),
        container_count=container_count,
        uptime_seconds=round(uptime_seconds, 2)
    )
