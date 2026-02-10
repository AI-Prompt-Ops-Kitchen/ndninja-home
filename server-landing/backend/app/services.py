import socket
import time
from typing import List
import os
import json
from .models import ServiceInfo
from .validators import validate_services, validate_service_config_env
from .config import get_service_url, get_status_check_host

def load_services_config() -> List[ServiceInfo]:
    """Load services configuration from environment variable."""
    services_json = os.getenv('SERVICES_CONFIG', '[]')

    # Validate that config doesn't contain localhost URLs
    validate_service_config_env(services_json)

    try:
        services_data = json.loads(services_json)
        services = [ServiceInfo(**service) for service in services_data]

        # Validate parsed services
        validate_services(services)

        return services
    except (json.JSONDecodeError, ValueError):
        # Return default services if config is invalid
        return get_default_services()

def get_default_services() -> List[ServiceInfo]:
    """Return default services configuration."""
    services = [
        ServiceInfo(
            name="Project Hummingbird",
            url=get_service_url(8888),
            port=8888,
            description="Vulnerability patch management",
            icon="shield"
        ),
        ServiceInfo(
            name="n8n Workflows",
            url=get_service_url(5678),
            port=5678,
            description="Workflow automation",
            icon="workflow"
        ),
        ServiceInfo(
            name="Kage Bunshin API",
            url=get_service_url(8000),
            port=8000,
            description="AI orchestration",
            icon="cpu"
        ),
        ServiceInfo(
            name="Draft API",
            url=get_service_url(5002),
            port=5002,
            description="Draft generation",
            icon="document"
        ),
        ServiceInfo(
            name="Video API",
            url=get_service_url(5679),
            port=5679,
            description="Video assembly",
            icon="video"
        ),
        ServiceInfo(
            name="Prompt Reverser",
            url=get_service_url(8010),
            port=8010,
            description="Image prompt analysis",
            icon="sparkles"
        ),
    ]

    # Validate default services (should never fail, but ensures consistency)
    validate_services(services)

    return services

def check_service_status(service: ServiceInfo, timeout: int = 5) -> ServiceInfo:
    """Check if a service is reachable via TCP socket."""
    start_time = time.time()

    try:
        # Connect to Docker host (services run on host, not in container)
        host = get_status_check_host()

        # Try to connect to the service
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, service.port))
        sock.close()

        response_time = (time.time() - start_time) * 1000  # Convert to ms

        if result == 0:
            service.status = 'online'
            service.response_time = round(response_time, 2)
        else:
            service.status = 'offline'
            service.response_time = None
    except Exception:
        service.status = 'offline'
        service.response_time = None

    return service

async def get_all_services_status() -> List[ServiceInfo]:
    """Get status of all configured services."""
    services = load_services_config()

    # Check each service status
    checked_services = []
    for service in services:
        checked_service = check_service_status(service)
        checked_services.append(checked_service)

    return checked_services
