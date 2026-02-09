# .claude/hooks/lib/manifest_parsers.py
import json
import os
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def extract_major_version(version_string: str) -> str:
    """Extract major version from version string.

    Handles: ^18.2.0, ~18.2.0, 18.2.0, >=18.0.0, etc.
    """
    match = re.search(r'(\d+)', version_string)
    return match.group(1) if match else "latest"


def parse_package_json(project_path: str) -> List[Dict[str, str]]:
    """Parse package.json for JavaScript/TypeScript dependencies.

    Returns: [{'library': str, 'major_version': str, 'source': 'manifest'}, ...]
    """
    pkg_file = os.path.join(project_path, "package.json")
    if not os.path.exists(pkg_file):
        return []

    try:
        with open(pkg_file, 'r') as f:
            pkg_data = json.load(f)

        libraries = []

        for dep, version in pkg_data.get('dependencies', {}).items():
            libraries.append({
                'library': dep,
                'major_version': extract_major_version(version),
                'source': 'manifest'
            })

        for dep, version in pkg_data.get('devDependencies', {}).items():
            libraries.append({
                'library': dep,
                'major_version': extract_major_version(version),
                'source': 'manifest'
            })

        logger.info(f"Parsed {len(libraries)} libraries from package.json")
        return libraries

    except Exception as e:
        logger.error(f"Failed to parse package.json: {e}")
        return []


def parse_gemfile(project_path: str) -> List[Dict[str, str]]:
    """Parse Gemfile for Ruby gems.

    Returns: [{'library': str, 'major_version': str, 'source': 'manifest'}, ...]
    """
    gemfile = os.path.join(project_path, "Gemfile")
    if not os.path.exists(gemfile):
        return []

    try:
        with open(gemfile, 'r') as f:
            content = f.read()

        libraries = []

        # Match: gem 'rails', '~> 7.0' or gem "rails" (no version)
        pattern = r"gem\s+['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?"

        for match in re.finditer(pattern, content):
            gem_name = match.group(1)
            version = match.group(2) if match.group(2) else "latest"

            libraries.append({
                'library': gem_name,
                'major_version': extract_major_version(version),
                'source': 'manifest'
            })

        logger.info(f"Parsed {len(libraries)} gems from Gemfile")
        return libraries

    except Exception as e:
        logger.error(f"Failed to parse Gemfile: {e}")
        return []


def parse_requirements_txt(project_path: str) -> List[Dict[str, str]]:
    """Parse requirements.txt for Python packages.

    Returns: [{'library': str, 'major_version': str, 'source': 'manifest'}, ...]
    """
    req_file = os.path.join(project_path, "requirements.txt")
    if not os.path.exists(req_file):
        return []

    try:
        with open(req_file, 'r') as f:
            lines = f.readlines()

        libraries = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Match: package==1.2.3, package>=1.2, package~=1.2, package (no version)
            match = re.match(r'^([a-zA-Z0-9_-]+)(?:[=~><]+)?([\d.]+)?', line)
            if match:
                package = match.group(1)
                version = match.group(2) if match.group(2) else "latest"

                libraries.append({
                    'library': package,
                    'major_version': extract_major_version(version),
                    'source': 'manifest'
                })

        logger.info(f"Parsed {len(libraries)} packages from requirements.txt")
        return libraries

    except Exception as e:
        logger.error(f"Failed to parse requirements.txt: {e}")
        return []


def parse_all_manifests(project_path: str) -> List[Dict[str, str]]:
    """Parse all supported manifest files in project."""
    all_libraries = []

    all_libraries.extend(parse_package_json(project_path))
    all_libraries.extend(parse_gemfile(project_path))
    all_libraries.extend(parse_requirements_txt(project_path))

    return all_libraries
