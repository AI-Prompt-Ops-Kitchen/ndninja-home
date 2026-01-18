"""
Perplexity adapter - gathers current web research for documentation generation
"""

import os
import sys
import asyncio
from datetime import datetime
from data_sources.base_adapter import BaseAdapter

# Import Perplexity client from lib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
try:
    from perplexity_client import PerplexityClient, ResearchResult
except ImportError:
    PerplexityClient = None
    ResearchResult = None


class PerplexityAdapter(BaseAdapter):
    """
    Adapter for gathering web research using Perplexity API.

    Provides current information about:
    - Technology stack best practices
    - Framework/library documentation
    - Industry trends and standards
    - Similar projects and tools
    """

    def gather(self, project, args):
        """
        Gather web research data for documentation generation.

        Analyzes project metadata and git data to generate targeted research queries
        about the technology stack, best practices, and current trends.

        Args:
            project: Project dict with title, category, metadata
            args: Command-line arguments

        Returns:
            dict: {
                'perplexity': {
                    'available': bool,
                    'research_results': {
                        'technology_context': str,
                        'best_practices': str,
                        'current_trends': str
                    },
                    'sources': [str],
                    'timestamp': str,
                    'cost': float
                }
            }
        """
        # Check if Perplexity is available
        if not self.is_available(project, args):
            return {
                'perplexity': {
                    'available': False,
                    'message': 'Perplexity API not configured (set PERPLEXITY_API_KEY)'
                }
            }

        # Generate research queries based on project data
        queries = self._generate_queries(project, args)

        if not queries:
            return {
                'perplexity': {
                    'available': False,
                    'message': 'No research queries generated for this project'
                }
            }

        # Perform research
        try:
            research_data = asyncio.run(self._perform_research(queries))

            return {
                'perplexity': {
                    'available': True,
                    'research_results': research_data['results'],
                    'sources': research_data['sources'],
                    'timestamp': datetime.now().isoformat(),
                    'cost': research_data['cost'],
                    'tokens_used': research_data['tokens']
                }
            }

        except Exception as e:
            return {
                'perplexity': {
                    'available': False,
                    'error': str(e),
                    'message': f'Research failed: {e}'
                }
            }

    def is_available(self, project, args):
        """Check if Perplexity API is configured."""
        api_key = os.getenv('PERPLEXITY_API_KEY')
        return bool(api_key and PerplexityClient)

    def _generate_queries(self, project, args):
        """
        Generate intelligent research queries based on project data.

        Args:
            project: Project dict
            args: Command-line arguments with potential 'data' from other adapters

        Returns:
            list: List of (category, query) tuples
        """
        queries = []

        # Get project metadata
        title = project.get('title', 'Unknown Project')
        category = project.get('category', '')

        # Try to get git data if available (from previous adapters)
        git_data = getattr(args, 'data', {}).get('git', {})
        languages = git_data.get('languages', {})
        dependencies = git_data.get('dependencies', {})

        # Query 1: Technology stack context
        if languages:
            primary_lang = max(languages, key=languages.get) if languages else None
            if primary_lang:
                query = f"{primary_lang} best practices and documentation standards 2026"
                queries.append(('technology_context', query))

        # Query 2: Framework/library best practices
        if dependencies:
            # Get top 3 dependencies
            top_deps = sorted(dependencies.items(), key=lambda x: x[1], reverse=True)[:3]
            for dep_name, _ in top_deps:
                # Clean up dependency name (remove version specifiers)
                clean_name = dep_name.split('==')[0].split('>=')[0].split('~=')[0]
                query = f"{clean_name} latest features best practices 2026"
                queries.append(('best_practices', query))
                break  # Just use the top dependency to avoid too many queries

        # Query 3: Project category trends (if category is specified)
        if category and category != 'general':
            query = f"{category} software development trends and standards 2026"
            queries.append(('current_trends', query))

        # Fallback: General query based on project title
        if not queries:
            query = f"{title} technology stack documentation best practices"
            queries.append(('technology_context', query))

        return queries

    async def _perform_research(self, queries):
        """
        Perform research queries using Perplexity API.

        Args:
            queries: List of (category, query) tuples

        Returns:
            dict: {
                'results': {category: research_content},
                'sources': [urls],
                'cost': float,
                'tokens': int
            }
        """
        async with PerplexityClient() as client:
            results = {}
            all_sources = []
            total_cost = 0.0
            total_tokens = 0

            for category, query in queries:
                try:
                    result = await client.research(
                        query=query,
                        return_citations=True,
                        max_tokens=1500  # Limit tokens per query
                    )

                    results[category] = result.content
                    all_sources.extend(result.citations)
                    total_cost += result.cost
                    total_tokens += result.tokens_used

                except Exception as e:
                    print(f"Warning: Research query failed for {category}: {e}")
                    results[category] = f"Research unavailable: {e}"

            # Remove duplicate sources
            unique_sources = list(set(all_sources))

            return {
                'results': results,
                'sources': unique_sources,
                'cost': total_cost,
                'tokens': total_tokens
            }


# Example usage for testing
if __name__ == "__main__":
    # Test with a sample project
    test_project = {
        'title': 'LLM Council Web',
        'category': 'web application',
        'metadata': {}
    }

    # Mock args with git data
    class MockArgs:
        data = {
            'git': {
                'available': True,
                'languages': {
                    'Python': 15000,
                    'JavaScript': 8000,
                    'HTML': 2000
                },
                'dependencies': {
                    'fastapi': 1,
                    'anthropic': 1,
                    'openai': 1
                }
            }
        }

    adapter = PerplexityAdapter()

    if adapter.is_available(test_project, MockArgs()):
        print("Perplexity adapter is available")
        queries = adapter._generate_queries(test_project, MockArgs())
        print(f"Generated {len(queries)} research queries:")
        for category, query in queries:
            print(f"  [{category}] {query}")

        print("\nPerforming research...")
        result = adapter.gather(test_project, MockArgs())

        if result['perplexity']['available']:
            print(f"\nResearch completed!")
            print(f"Cost: ${result['perplexity']['cost']:.4f}")
            print(f"Tokens: {result['perplexity']['tokens_used']}")
            print(f"Sources: {len(result['perplexity']['sources'])}")
            print("\nResults:")
            for category, content in result['perplexity']['research_results'].items():
                print(f"\n[{category}]")
                print(content[:200] + "..." if len(content) > 200 else content)
        else:
            print(f"Research failed: {result['perplexity'].get('message')}")
    else:
        print("Perplexity adapter not available (check PERPLEXITY_API_KEY)")
