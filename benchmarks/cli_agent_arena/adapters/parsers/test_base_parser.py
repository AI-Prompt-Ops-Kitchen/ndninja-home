"""Tests for base output parser interface."""

import pytest
from abc import ABC
from typing import Dict, Any
from .base_parser import BaseOutputParser


class ConcreteParser(BaseOutputParser):
    """Concrete implementation for testing base parser."""

    def extract_metrics(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Extract metrics from CLI output."""
        return {
            "tokens": {"input": 100, "output": 200},
            "cost": 0.001,
            "retries": 0,
            "tool_calls": 5,
            "error_recovered": False
        }


class TestBaseOutputParser:
    """Test suite for BaseOutputParser interface."""

    def test_base_parser_is_abstract(self):
        """Test that BaseOutputParser cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseOutputParser()

    def test_concrete_parser_can_be_instantiated(self):
        """Test that a concrete parser subclass can be instantiated."""
        parser = ConcreteParser()
        assert parser is not None
        assert isinstance(parser, BaseOutputParser)

    def test_extract_metrics_returns_dict(self):
        """Test that extract_metrics returns a dictionary."""
        parser = ConcreteParser()
        result = parser.extract_metrics("sample stdout", "sample stderr")
        assert isinstance(result, dict)

    def test_extract_metrics_has_required_fields(self):
        """Test that extract_metrics returns all required fields."""
        parser = ConcreteParser()
        result = parser.extract_metrics("sample stdout", "sample stderr")

        required_fields = ["tokens", "cost", "retries", "tool_calls", "error_recovered"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_extract_metrics_field_types(self):
        """Test that extract_metrics returns correct field types."""
        parser = ConcreteParser()
        result = parser.extract_metrics("sample stdout", "sample stderr")

        assert isinstance(result["tokens"], dict), "tokens should be dict"
        assert "input" in result["tokens"], "tokens should have 'input' key"
        assert "output" in result["tokens"], "tokens should have 'output' key"
        assert isinstance(result["tokens"]["input"], int), "tokens.input should be int"
        assert isinstance(result["tokens"]["output"], int), "tokens.output should be int"
        assert isinstance(result["cost"], (int, float)), "cost should be numeric"
        assert isinstance(result["retries"], int), "retries should be int"
        assert isinstance(result["tool_calls"], int), "tool_calls should be int"
        assert isinstance(result["error_recovered"], bool), "error_recovered should be bool"

    def test_subclass_without_extract_metrics_cannot_be_instantiated(self):
        """Test that a subclass without extract_metrics cannot be instantiated."""
        class IncompleteParser(BaseOutputParser):
            pass

        with pytest.raises(TypeError):
            IncompleteParser()
