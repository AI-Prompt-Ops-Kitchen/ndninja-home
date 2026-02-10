import pytest
from tools.prompt_versioning import PromptVersionManager
import tempfile
import json


def test_prompt_versioning_stores_versions():
    """Should store and retrieve prompt versions"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = PromptVersionManager(storage_dir=tmpdir)

        version_id = manager.save_version(
            prompt_id="keyword_extractor",
            prompt_text="Extract keywords from the following text...",
            purpose="keyword_extraction",
            created_by="test_user"
        )

        assert version_id is not None

        version = manager.get_version(prompt_id="keyword_extractor", version=1)
        assert version is not None
        assert version["prompt_text"] == "Extract keywords from the following text..."


def test_prompt_versioning_runs_tests():
    """Should run prompt against test cases"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = PromptVersionManager(storage_dir=tmpdir)

        test_cases = [
            {
                "input": "The sunset was beautiful",
                "expected_output": "sunset, beautiful"
            }
        ]

        results = manager.test_prompt_version(
            prompt_id="keyword_extractor",
            version=1,
            test_cases=test_cases
        )

        assert "total" in results
        assert "passed" in results
