# .claude/hooks/lib/test_manifest_parsers.py
import pytest
import json
from manifest_parsers import (
    parse_package_json, parse_gemfile, parse_requirements_txt,
    parse_all_manifests, extract_major_version
)

def test_extract_major_version():
    """Test version string parsing."""
    assert extract_major_version("^18.2.0") == "18"
    assert extract_major_version("~7.0.4") == "7"
    assert extract_major_version("14.0.3") == "14"
    assert extract_major_version(">=5.0.0") == "5"
    assert extract_major_version("latest") == "latest"

def test_parse_package_json(tmp_path):
    """Test parsing package.json for dependencies."""
    package_json = {
        "dependencies": {
            "react": "^18.2.0",
            "next": "14.0.3"
        },
        "devDependencies": {
            "typescript": "^5.0.0"
        }
    }

    pkg_file = tmp_path / "package.json"
    pkg_file.write_text(json.dumps(package_json))

    libraries = parse_package_json(str(tmp_path))

    assert len(libraries) == 3
    lib_pairs = [(lib['library'], lib['major_version']) for lib in libraries]
    assert ("react", "18") in lib_pairs
    assert ("next", "14") in lib_pairs
    assert ("typescript", "5") in lib_pairs

def test_parse_package_json_missing(tmp_path):
    """Test handling missing package.json."""
    libraries = parse_package_json(str(tmp_path))
    assert libraries == []

def test_parse_gemfile(tmp_path):
    """Test parsing Gemfile for Ruby gems."""
    gemfile_content = """
source 'https://rubygems.org'

gem 'rails', '~> 7.0'
gem 'pg', '~> 1.5'
gem 'puma'
gem "devise", "~> 4.9"
"""
    gemfile = tmp_path / "Gemfile"
    gemfile.write_text(gemfile_content)

    libraries = parse_gemfile(str(tmp_path))

    assert len(libraries) == 4
    lib_pairs = [(lib['library'], lib['major_version']) for lib in libraries]
    assert ("rails", "7") in lib_pairs
    assert ("pg", "1") in lib_pairs
    assert ("puma", "latest") in lib_pairs
    assert ("devise", "4") in lib_pairs

def test_parse_gemfile_missing(tmp_path):
    """Test handling missing Gemfile."""
    libraries = parse_gemfile(str(tmp_path))
    assert libraries == []

def test_parse_requirements_txt(tmp_path):
    """Test parsing requirements.txt for Python packages."""
    requirements = """
# Core deps
flask==3.0.2
psycopg2>=2.9
requests~=2.31.0
# Dev deps
pytest
"""
    req_file = tmp_path / "requirements.txt"
    req_file.write_text(requirements)

    libraries = parse_requirements_txt(str(tmp_path))

    assert len(libraries) == 4
    lib_pairs = [(lib['library'], lib['major_version']) for lib in libraries]
    assert ("flask", "3") in lib_pairs
    assert ("psycopg2", "2") in lib_pairs
    assert ("requests", "2") in lib_pairs
    assert ("pytest", "latest") in lib_pairs

def test_parse_requirements_txt_missing(tmp_path):
    """Test handling missing requirements.txt."""
    libraries = parse_requirements_txt(str(tmp_path))
    assert libraries == []

def test_parse_all_manifests(tmp_path):
    """Test parsing multiple manifests in one project."""
    # Create package.json
    pkg = tmp_path / "package.json"
    pkg.write_text(json.dumps({"dependencies": {"react": "^18.0"}}))

    # Create requirements.txt
    req = tmp_path / "requirements.txt"
    req.write_text("flask==3.0.2\n")

    libraries = parse_all_manifests(str(tmp_path))
    assert len(libraries) == 2
    lib_names = [lib['library'] for lib in libraries]
    assert "react" in lib_names
    assert "flask" in lib_names
