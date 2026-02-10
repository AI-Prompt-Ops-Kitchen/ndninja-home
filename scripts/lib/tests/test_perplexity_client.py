"""
Unit tests for Perplexity client library.
"""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import the client (adjust path as needed)
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from perplexity_client import (
    PerplexityClient,
    PerplexityError,
    PerplexityRateLimitError,
    PerplexityTimeoutError,
    ResearchResult,
    quick_research
)


@pytest.fixture
def mock_api_response():
    """Mock successful API response."""
    return {
        "id": "test-id",
        "model": "sonar-pro",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a research result about FastAPI.",
                    "citations": [
                        "https://fastapi.tiangolo.com/",
                        "https://github.com/tiangolo/fastapi"
                    ]
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 150,
            "total_tokens": 200
        },
        "citations": [
            "https://fastapi.tiangolo.com/",
            "https://github.com/tiangolo/fastapi"
        ]
    }


@pytest.fixture
def client():
    """Create a test client with mocked API key."""
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "test-key"}):
        client = PerplexityClient(api_key="test-key-123")
        yield client


class TestPerplexityClient:
    """Test suite for PerplexityClient."""

    def test_client_initialization(self):
        """Test client initializes with correct parameters."""
        client = PerplexityClient(
            api_key="test-key",
            model="sonar-pro",
            timeout=30.0,
            max_retries=5
        )

        assert client.api_key == "test-key"
        assert client.model == "sonar-pro"
        assert client.timeout == 30.0
        assert client.max_retries == 5

    def test_client_requires_api_key(self):
        """Test that client raises error without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                PerplexityClient()

    def test_client_uses_env_var_api_key(self):
        """Test that client uses PERPLEXITY_API_KEY from environment."""
        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "env-key"}):
            client = PerplexityClient()
            assert client.api_key == "env-key"

    @pytest.mark.asyncio
    async def test_research_success(self, client, mock_api_response):
        """Test successful research query."""
        # Mock the HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response

        client.client.post = AsyncMock(return_value=mock_response)

        # Perform research
        result = await client.research("What is FastAPI?")

        # Assertions
        assert isinstance(result, ResearchResult)
        assert "FastAPI" in result.content
        assert len(result.citations) == 2
        assert result.tokens_used == 200
        assert result.cost > 0
        assert result.model == "sonar-pro"

        # Verify API was called
        client.client.post.assert_called_once()
        call_args = client.client.post.call_args
        assert call_args[0][0] == "/chat/completions"

        payload = call_args[1]["json"]
        assert payload["model"] == "sonar-pro"
        assert payload["messages"][1]["content"] == "What is FastAPI?"

    @pytest.mark.asyncio
    async def test_research_with_custom_params(self, client, mock_api_response):
        """Test research with custom parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response

        client.client.post = AsyncMock(return_value=mock_response)

        result = await client.research(
            "Test query",
            model="sonar",
            max_tokens=1000,
            temperature=0.5,
            search_domain_filter=["github.com"]
        )

        # Verify custom parameters were used
        call_args = client.client.post.call_args
        payload = call_args[1]["json"]

        assert payload["model"] == "sonar"
        assert payload["max_tokens"] == 1000
        assert payload["temperature"] == 0.5
        assert payload["search_domain_filter"] == ["github.com"]

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, client):
        """Test handling of rate limit errors."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"

        client.client.post = AsyncMock(return_value=mock_response)

        # Should raise PerplexityRateLimitError after retries
        with pytest.raises(PerplexityRateLimitError):
            await client.research("Test query")

    @pytest.mark.asyncio
    async def test_api_error(self, client):
        """Test handling of API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        client.client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(PerplexityError, match="API error 500"):
            await client.research("Test query")

    @pytest.mark.asyncio
    async def test_timeout_error(self, client):
        """Test handling of timeout errors."""
        import httpx

        client.client.post = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )

        with pytest.raises(PerplexityTimeoutError):
            await client.research("Test query")

    @pytest.mark.asyncio
    async def test_multi_query_research(self, client, mock_api_response):
        """Test multi-query research."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response

        client.client.post = AsyncMock(return_value=mock_response)

        queries = [
            "What is FastAPI?",
            "What is Python?",
            "What is PostgreSQL?"
        ]

        results = await client.multi_query_research(queries)

        assert len(results) == 3
        assert all(isinstance(r, ResearchResult) for r in results)
        assert client.client.post.call_count == 3

    @pytest.mark.asyncio
    async def test_multi_query_with_failure(self, client, mock_api_response):
        """Test multi-query research with some failures."""
        # First two succeed, third fails
        success_response = MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = mock_api_response

        fail_response = MagicMock()
        fail_response.status_code = 500
        fail_response.text = "Error"

        client.client.post = AsyncMock(
            side_effect=[success_response, success_response, fail_response]
        )

        queries = ["Query 1", "Query 2", "Query 3"]
        results = await client.multi_query_research(queries)

        # Should have 3 results, last one with error content
        assert len(results) == 3
        assert "FastAPI" in results[0].content
        assert "FastAPI" in results[1].content
        assert "Research failed" in results[2].content
        assert results[2].tokens_used == 0
        assert results[2].cost == 0.0

    def test_calculate_cost(self, client):
        """Test cost calculation."""
        # Test with sonar-pro model
        cost = client._calculate_cost(1000)
        assert cost == 1000 * 0.00002  # $0.02

        # Test with sonar model
        client.model = "sonar"
        cost = client._calculate_cost(1000)
        assert cost == 1000 * 0.00001  # $0.01

    def test_extract_citations(self, client, mock_api_response):
        """Test citation extraction."""
        citations = client._extract_citations(mock_api_response)

        assert len(citations) == 2
        assert "https://fastapi.tiangolo.com/" in citations
        assert "https://github.com/tiangolo/fastapi" in citations

    def test_extract_citations_empty(self, client):
        """Test citation extraction with no citations."""
        response = {
            "choices": [
                {
                    "message": {
                        "content": "No citations here"
                    }
                }
            ]
        }

        citations = client._extract_citations(response)
        assert citations == []

    def test_extract_citations_deduplication(self, client):
        """Test that duplicate citations are removed."""
        response = {
            "citations": ["https://example.com", "https://example.com"],
            "choices": [
                {
                    "message": {
                        "citations": ["https://example.com", "https://test.com"]
                    }
                }
            ]
        }

        citations = client._extract_citations(response)
        assert len(citations) == 2
        assert "https://example.com" in citations
        assert "https://test.com" in citations

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_api_response):
        """Test client as async context manager."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response

        async with PerplexityClient(api_key="test-key") as client:
            client.client.post = AsyncMock(return_value=mock_response)
            result = await client.research("Test query")
            assert isinstance(result, ResearchResult)

        # Client should be closed after context exit
        # (We can't easily test this without more mocking)

    @pytest.mark.asyncio
    async def test_quick_research(self, mock_api_response):
        """Test quick_research convenience function."""
        with patch("perplexity_client.PerplexityClient") as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.research = AsyncMock(
                return_value=ResearchResult(
                    content="Test content",
                    citations=["https://example.com"],
                    tokens_used=100,
                    cost=0.002,
                    timestamp=datetime.now().isoformat(),
                    model="sonar-pro"
                )
            )

            result = await quick_research("Test query", api_key="test-key")

            assert isinstance(result, ResearchResult)
            assert result.content == "Test content"
            mock_client_instance.research.assert_called_once_with("Test query")


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
