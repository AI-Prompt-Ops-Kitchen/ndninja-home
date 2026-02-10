"""
Perplexity API Client Library
Provides async interface to Perplexity's research API with retry logic and cost tracking.
"""

import os
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

try:
    import httpx
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type
    )
except ImportError:
    raise ImportError(
        "Required packages not installed. Run: pip install httpx tenacity"
    )

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """Result from a Perplexity research query."""
    content: str
    citations: List[str]
    tokens_used: int
    cost: float
    timestamp: str
    model: str


class PerplexityError(Exception):
    """Base exception for Perplexity API errors."""
    pass


class PerplexityRateLimitError(PerplexityError):
    """Raised when API rate limit is exceeded."""
    pass


class PerplexityTimeoutError(PerplexityError):
    """Raised when API request times out."""
    pass


class PerplexityClient:
    """
    Async client for Perplexity AI research API.

    Features:
    - Async/await pattern for non-blocking research queries
    - Automatic retry with exponential backoff
    - Cost tracking based on token usage
    - Citation extraction from responses
    - Configurable timeouts and rate limits

    Usage:
        client = PerplexityClient(api_key="pplx-...")
        result = await client.research("What are the latest FastAPI features?")
        print(result.content)
        print(result.citations)
    """

    # Perplexity API pricing (estimated, adjust based on actual pricing)
    PRICING = {
        'sonar': 0.00001,      # $0.01 per 1k tokens
        'sonar-pro': 0.00002,   # $0.02 per 1k tokens
    }

    API_BASE_URL = "https://api.perplexity.ai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "sonar-pro",
        timeout: float = 60.0,
        max_retries: int = 3
    ):
        """
        Initialize Perplexity client.

        Args:
            api_key: Perplexity API key (defaults to PERPLEXITY_API_KEY env var)
            model: Model to use ('sonar' or 'sonar-pro')
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Perplexity API key required. Set PERPLEXITY_API_KEY environment "
                "variable or pass api_key parameter."
            )

        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        # HTTP client with retry configuration
        self.client = httpx.AsyncClient(
            base_url=self.API_BASE_URL,
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

        logger.info(f"Initialized PerplexityClient with model={model}, timeout={timeout}s")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, PerplexityRateLimitError)),
        reraise=True
    )
    async def _make_request(self, payload: Dict) -> Dict:
        """
        Make HTTP request to Perplexity API with retry logic.

        Args:
            payload: JSON payload for the request

        Returns:
            API response as dictionary

        Raises:
            PerplexityRateLimitError: When rate limit is exceeded
            PerplexityTimeoutError: When request times out
            PerplexityError: For other API errors
        """
        try:
            response = await self.client.post("/chat/completions", json=payload)

            # Handle rate limiting
            if response.status_code == 429:
                logger.warning("Rate limit exceeded, will retry")
                raise PerplexityRateLimitError("API rate limit exceeded")

            # Handle other errors
            if response.status_code != 200:
                error_msg = f"API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise PerplexityError(error_msg)

            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout after {self.timeout}s")
            raise PerplexityTimeoutError(f"Request timed out after {self.timeout}s") from e

        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise PerplexityError(f"HTTP error: {e}") from e

    def _extract_citations(self, response: Dict) -> List[str]:
        """
        Extract citation URLs from API response.

        Args:
            response: API response dictionary

        Returns:
            List of citation URLs
        """
        citations = []

        # Try to extract from citations field
        if 'citations' in response:
            citations.extend(response['citations'])

        # Try to extract from choices[0].message.citations
        try:
            message = response['choices'][0]['message']
            if 'citations' in message:
                citations.extend(message['citations'])
        except (KeyError, IndexError):
            pass

        return list(set(citations))  # Remove duplicates

    def _calculate_cost(self, tokens_used: int) -> float:
        """
        Calculate cost based on token usage.

        Args:
            tokens_used: Number of tokens used

        Returns:
            Cost in USD
        """
        price_per_token = self.PRICING.get(self.model, 0.00002)
        return tokens_used * price_per_token

    async def research(
        self,
        query: str,
        model: Optional[str] = None,
        return_citations: bool = True,
        max_tokens: int = 2000,
        temperature: float = 0.2,
        search_domain_filter: Optional[List[str]] = None
    ) -> ResearchResult:
        """
        Perform a research query using Perplexity API.

        Args:
            query: Research question or query
            model: Override default model (optional)
            return_citations: Whether to return citations
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-2)
            search_domain_filter: List of domains to search (e.g., ["github.com"])

        Returns:
            ResearchResult with content, citations, tokens, and cost

        Example:
            result = await client.research(
                "What are the latest Python async best practices?",
                return_citations=True
            )
            print(result.content)
            for citation in result.citations:
                print(f"  - {citation}")
        """
        model = model or self.model

        logger.info(f"Starting research query with model={model}")
        logger.debug(f"Query: {query[:100]}...")

        # Build request payload
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful research assistant. Provide comprehensive, "
                        "accurate information with citations from reliable sources."
                    )
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "return_citations": return_citations,
            "return_images": False,
            "search_recency_filter": "month"  # Prefer recent sources
        }

        # Add domain filter if specified
        if search_domain_filter:
            payload["search_domain_filter"] = search_domain_filter

        # Make API request
        start_time = datetime.now()
        response = await self._make_request(payload)
        duration = (datetime.now() - start_time).total_seconds()

        # Extract response data
        try:
            content = response['choices'][0]['message']['content']
            tokens_used = response.get('usage', {}).get('total_tokens', 0)
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse API response: {e}")
            raise PerplexityError(f"Invalid API response format: {e}") from e

        # Extract citations
        citations = self._extract_citations(response) if return_citations else []

        # Calculate cost
        cost = self._calculate_cost(tokens_used)

        logger.info(
            f"Research completed in {duration:.2f}s: "
            f"{tokens_used} tokens, {len(citations)} citations, ${cost:.4f}"
        )

        return ResearchResult(
            content=content,
            citations=citations,
            tokens_used=tokens_used,
            cost=cost,
            timestamp=datetime.now().isoformat(),
            model=model
        )

    async def multi_query_research(
        self,
        queries: List[str],
        **kwargs
    ) -> List[ResearchResult]:
        """
        Perform multiple research queries in parallel.

        Args:
            queries: List of research questions
            **kwargs: Additional arguments passed to research()

        Returns:
            List of ResearchResults corresponding to each query
        """
        logger.info(f"Starting multi-query research with {len(queries)} queries")

        tasks = [self.research(query, **kwargs) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Query {i} failed: {result}")
                # Return empty result for failed queries
                processed_results.append(
                    ResearchResult(
                        content=f"Research failed: {result}",
                        citations=[],
                        tokens_used=0,
                        cost=0.0,
                        timestamp=datetime.now().isoformat(),
                        model=self.model
                    )
                )
            else:
                processed_results.append(result)

        total_cost = sum(r.cost for r in processed_results)
        total_tokens = sum(r.tokens_used for r in processed_results)
        logger.info(
            f"Multi-query research completed: "
            f"{total_tokens} tokens, ${total_cost:.4f}"
        )

        return processed_results


# Convenience function for one-off queries
async def quick_research(query: str, **kwargs) -> ResearchResult:
    """
    Convenience function for one-off research queries.

    Args:
        query: Research question
        **kwargs: Additional arguments passed to PerplexityClient

    Returns:
        ResearchResult

    Example:
        result = await quick_research("What's new in Python 3.13?")
        print(result.content)
    """
    async with PerplexityClient(**kwargs) as client:
        return await client.research(query)


# Example usage
if __name__ == "__main__":
    async def main():
        # Example 1: Basic research query
        client = PerplexityClient()
        result = await client.research(
            "What are the latest features in FastAPI 2026?",
            return_citations=True
        )

        print("=" * 80)
        print("RESEARCH RESULT")
        print("=" * 80)
        print(result.content)
        print("\n" + "=" * 80)
        print("CITATIONS")
        print("=" * 80)
        for i, citation in enumerate(result.citations, 1):
            print(f"{i}. {citation}")
        print("\n" + "=" * 80)
        print(f"Tokens: {result.tokens_used}, Cost: ${result.cost:.4f}")
        print("=" * 80)

        await client.close()

        # Example 2: Multi-query research
        queries = [
            "FastAPI best practices 2026",
            "Python async/await patterns",
            "PostgreSQL performance optimization"
        ]

        async with PerplexityClient() as client:
            results = await client.multi_query_research(queries)
            for query, result in zip(queries, results):
                print(f"\nQuery: {query}")
                print(f"Citations: {len(result.citations)}")
                print(f"Cost: ${result.cost:.4f}")

    # Run example
    asyncio.run(main())
