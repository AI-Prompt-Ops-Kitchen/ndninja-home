"""
Unit tests for Perplexity adapter
"""

import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data_sources.perplexity_adapter import PerplexityAdapter


class TestPerplexityAdapter:
    """Test suite for PerplexityAdapter"""

    @pytest.fixture
    def adapter(self):
        """Create adapter instance"""
        return PerplexityAdapter()

    @pytest.fixture
    def sample_project(self):
        """Sample project data"""
        return {
            'title': 'Test Project',
            'category': 'web application',
            'metadata': {}
        }

    @pytest.fixture
    def mock_args_with_git(self):
        """Mock args with git data"""
        class MockArgs:
            data = {
                'git': {
                    'available': True,
                    'languages': {
                        'Python': 15000,
                        'JavaScript': 8000
                    },
                    'dependencies': {
                        'fastapi': 1,
                        'pytest': 1
                    }
                }
            }
        return MockArgs()

    @pytest.fixture
    def mock_args_without_git(self):
        """Mock args without git data"""
        class MockArgs:
            data = {}
        return MockArgs()

    def test_is_available_with_api_key(self, adapter, sample_project, mock_args_with_git):
        """Test that adapter is available when API key is set"""
        with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test-key'}):
            # Also need to mock PerplexityClient being available
            with patch('data_sources.perplexity_adapter.PerplexityClient', MagicMock()):
                assert adapter.is_available(sample_project, mock_args_with_git)

    def test_is_available_without_api_key(self, adapter, sample_project, mock_args_with_git):
        """Test that adapter is not available when API key is missing"""
        with patch.dict(os.environ, {}, clear=True):
            assert not adapter.is_available(sample_project, mock_args_with_git)

    def test_generate_queries_with_git_data(self, adapter, sample_project, mock_args_with_git):
        """Test query generation with git data available"""
        queries = adapter._generate_queries(sample_project, mock_args_with_git)

        # Should generate at least 2 queries (language + dependency)
        assert len(queries) >= 2

        # Check that queries contain expected categories
        categories = [cat for cat, _ in queries]
        assert 'technology_context' in categories or 'best_practices' in categories

        # Check that queries mention the technologies
        query_text = ' '.join([q for _, q in queries])
        assert 'Python' in query_text or 'fastapi' in query_text

    def test_generate_queries_without_git_data(self, adapter, sample_project, mock_args_without_git):
        """Test query generation without git data (fallback)"""
        queries = adapter._generate_queries(sample_project, mock_args_without_git)

        # Should still generate at least 1 fallback query
        assert len(queries) >= 1

        # Fallback query should mention project title
        query_text = ' '.join([q for _, q in queries])
        assert 'Test Project' in query_text

    def test_generate_queries_with_category(self, adapter, mock_args_without_git):
        """Test that category influences query generation"""
        project_with_category = {
            'title': 'Test API',
            'category': 'api development',
            'metadata': {}
        }

        queries = adapter._generate_queries(project_with_category, mock_args_without_git)

        # Should generate category-based query
        query_text = ' '.join([q for _, q in queries])
        assert 'api development' in query_text

    @pytest.mark.asyncio
    async def test_perform_research_success(self, adapter):
        """Test successful research execution"""
        queries = [
            ('technology_context', 'Python best practices'),
            ('best_practices', 'FastAPI latest features')
        ]

        mock_result = MagicMock()
        mock_result.content = "Test research content"
        mock_result.citations = ["https://example.com"]
        mock_result.cost = 0.02
        mock_result.tokens_used = 100

        with patch('data_sources.perplexity_adapter.PerplexityClient') as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            mock_client_instance.research = AsyncMock(return_value=mock_result)

            result = await adapter._perform_research(queries)

            assert 'results' in result
            assert 'sources' in result
            assert 'cost' in result
            assert 'tokens' in result

            assert len(result['results']) == 2
            assert 'technology_context' in result['results']
            assert 'best_practices' in result['results']
            assert result['cost'] == 0.04  # 2 queries * 0.02
            assert result['tokens'] == 200  # 2 queries * 100

    @pytest.mark.asyncio
    async def test_perform_research_with_failure(self, adapter):
        """Test research with one query failing"""
        queries = [
            ('technology_context', 'Python best practices'),
            ('best_practices', 'FastAPI latest features')
        ]

        mock_success = MagicMock()
        mock_success.content = "Success content"
        mock_success.citations = ["https://example.com"]
        mock_success.cost = 0.02
        mock_success.tokens_used = 100

        with patch('data_sources.perplexity_adapter.PerplexityClient') as MockClient:
            mock_client_instance = MockClient.return_value.__aenter__.return_value
            # First succeeds, second fails
            mock_client_instance.research = AsyncMock(
                side_effect=[mock_success, Exception("API Error")]
            )

            result = await adapter._perform_research(queries)

            # Should have results for both (one success, one error message)
            assert len(result['results']) == 2
            assert result['results']['technology_context'] == "Success content"
            assert "Research unavailable" in result['results']['best_practices']

    def test_gather_with_api_unavailable(self, adapter, sample_project, mock_args_with_git):
        """Test gather when API is not available"""
        with patch.dict(os.environ, {}, clear=True):
            result = adapter.gather(sample_project, mock_args_with_git)

            assert 'perplexity' in result
            assert result['perplexity']['available'] is False
            assert 'message' in result['perplexity']

    def test_gather_success(self, adapter, sample_project, mock_args_with_git):
        """Test successful gather operation"""
        mock_research_data = {
            'results': {
                'technology_context': 'Python is great',
                'best_practices': 'Use type hints'
            },
            'sources': ['https://example.com'],
            'cost': 0.02,
            'tokens': 100
        }

        with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test-key'}):
            with patch('data_sources.perplexity_adapter.PerplexityClient', MagicMock()):
                with patch.object(adapter, '_perform_research', return_value=mock_research_data):
                    with patch('asyncio.run', return_value=mock_research_data):
                        result = adapter.gather(sample_project, mock_args_with_git)

                        assert 'perplexity' in result
                        assert result['perplexity']['available'] is True
                        assert 'research_results' in result['perplexity']
                        assert 'sources' in result['perplexity']
                        assert 'cost' in result['perplexity']
                        assert 'timestamp' in result['perplexity']

    def test_gather_with_exception(self, adapter, sample_project, mock_args_with_git):
        """Test gather when research raises exception"""
        with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test-key'}):
            with patch('data_sources.perplexity_adapter.PerplexityClient', MagicMock()):
                with patch('asyncio.run', side_effect=Exception("Network error")):
                    result = adapter.gather(sample_project, mock_args_with_git)

                    assert 'perplexity' in result
                    assert result['perplexity']['available'] is False
                    assert 'error' in result['perplexity']
                    assert 'Network error' in result['perplexity']['error']

    def test_gather_with_no_queries(self, adapter, mock_args_without_git):
        """Test gather when no queries can be generated"""
        # Project with minimal info
        minimal_project = {
            'title': '',
            'category': '',
            'metadata': {}
        }

        with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test-key'}):
            with patch('data_sources.perplexity_adapter.PerplexityClient', MagicMock()):
                with patch.object(adapter, '_generate_queries', return_value=[]):
                    result = adapter.gather(minimal_project, mock_args_without_git)

                    assert 'perplexity' in result
                    assert result['perplexity']['available'] is False
                    assert 'No research queries' in result['perplexity']['message']


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
