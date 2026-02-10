"""
Validators to prevent localhost URLs in service configuration.

This module ensures that all service URLs use the Tailscale IP (100.77.248.9)
instead of localhost or 127.0.0.1, which are not accessible from remote devices.
"""

import re
from typing import List
from .models import ServiceInfo


class LocalhostDetectionError(Exception):
    """Raised when a localhost URL is detected in service configuration."""
    pass


def is_localhost_url(url: str) -> bool:
    """
    Check if a URL contains localhost or 127.0.0.1.

    Args:
        url: The URL to check

    Returns:
        True if the URL contains localhost or 127.0.0.1, False otherwise
    """
    # Pattern matches localhost or 127.0.0.1 in various formats
    localhost_pattern = r'(localhost|127\.0\.0\.1)'
    return bool(re.search(localhost_pattern, url, re.IGNORECASE))


def validate_services(services: List[ServiceInfo]) -> None:
    """
    Validate that no services use localhost URLs.

    Args:
        services: List of ServiceInfo objects to validate

    Raises:
        LocalhostDetectionError: If any service uses a localhost URL
    """
    for service in services:
        if is_localhost_url(service.url):
            raise LocalhostDetectionError(
                f"FATAL ERROR: Localhost URL detected in service '{service.name}': {service.url}\n"
                f"\n"
                f"Service URLs must use the Tailscale IP: 100.77.248.9\n"
                f"Correct URL format: http://100.77.248.9:{service.port}\n"
                f"\n"
                f"This error prevents the application from starting with invalid URLs.\n"
                f"Please update your configuration to use the Tailscale IP address."
            )


def validate_service_config_env(services_json: str) -> None:
    """
    Validate the SERVICES_CONFIG environment variable for localhost URLs.

    Args:
        services_json: The raw JSON string from SERVICES_CONFIG env var

    Raises:
        LocalhostDetectionError: If the config contains localhost URLs
    """
    if is_localhost_url(services_json):
        raise LocalhostDetectionError(
            f"FATAL ERROR: Localhost URL detected in SERVICES_CONFIG environment variable\n"
            f"\n"
            f"The SERVICES_CONFIG contains localhost or 127.0.0.1 URLs.\n"
            f"All service URLs must use the Tailscale IP: 100.77.248.9\n"
            f"\n"
            f"Example correct format:\n"
            f'SERVICES_CONFIG=[{{"name":"Service","url":"http://100.77.248.9:8888","port":8888,...}}]\n'
            f"\n"
            f"Please update your .env file to use the correct IP address."
        )
