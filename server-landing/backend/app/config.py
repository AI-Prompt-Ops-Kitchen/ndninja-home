"""
Centralized configuration for the server landing page backend.

This module provides a single source of truth for network configuration,
ensuring consistent use of the Tailscale IP across all service URLs.
"""

from typing import Final

# Tailscale IP for public-facing service URLs
# This IP is accessible from all devices on the Tailscale network
TAILSCALE_IP: Final[str] = "100.77.248.9"

# Docker host gateway IP for service status checks
# This is the gateway IP for the server-landing Docker network
# Used to check if services are running on the host machine
DOCKER_HOST_GATEWAY: Final[str] = "172.23.0.1"


def get_service_url(port: int) -> str:
    """
    Build a service URL using the Tailscale IP.

    Args:
        port: The port number where the service is running

    Returns:
        A complete URL string in the format http://100.77.248.9:PORT

    Example:
        >>> get_service_url(8888)
        'http://100.77.248.9:8888'
    """
    return f"http://{TAILSCALE_IP}:{port}"


def get_status_check_host() -> str:
    """
    Get the host IP to use for service status checks.

    When running inside Docker, services on the host machine are accessible
    via the Docker network gateway IP, not via localhost.

    Returns:
        The Docker host gateway IP for status checks
    """
    return DOCKER_HOST_GATEWAY
