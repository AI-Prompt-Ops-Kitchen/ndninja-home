"""HTML report generator for benchmark results."""

from typing import Dict
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from adapters.base import BenchmarkResult


class HTMLGenerator:
    """Generate HTML dashboard reports from benchmark results."""

    def __init__(self, template_path: str = None):
        """Initialize HTML generator.

        Args:
            template_path: Optional path to custom Jinja2 template
        """
        if template_path is None:
            # Use default template
            template_path = Path(__file__).parent / "templates" / "dashboard.html"

        with open(template_path, "r") as f:
            self.template = Template(f.read())

    def generate(
        self,
        results: Dict[str, BenchmarkResult],
        task_name: str,
    ) -> str:
        """Generate HTML report from benchmark results.

        Args:
            results: Dictionary mapping agent names to BenchmarkResult objects
            task_name: Name of the task being benchmarked

        Returns:
            HTML string ready to be written to file
        """
        # Calculate summary statistics
        winner = self._determine_winner(results)
        fastest_time = min(r.wall_time for r in results.values()) if results else 0
        lowest_cost = min(r.cost for r in results.values()) if results else 0
        highest_quality = max(r.quality_score for r in results.values()) if results else 0

        # Render template
        html = self.template.render(
            task_name=task_name,
            results=results,
            winner=winner,
            fastest_time=fastest_time,
            lowest_cost=lowest_cost,
            highest_quality=highest_quality,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        return html

    def _determine_winner(self, results: Dict[str, BenchmarkResult]) -> dict:
        """Determine the winning agent based on a simple scoring system.

        Args:
            results: Dictionary of agent results

        Returns:
            Dictionary with 'name' and 'score' of the winning agent
        """
        if not results:
            return {"name": "None", "score": 0}

        # Simple scoring: quality (40%) + speed (30%) + cost (30%)
        scores = {}

        # Get ranges for normalization
        times = [r.wall_time for r in results.values() if r.success]
        costs = [r.cost for r in results.values() if r.success]
        qualities = [r.quality_score for r in results.values() if r.success]

        if not times:
            return {"name": "None", "score": 0}

        max_time = max(times)
        max_cost = max(costs) if max(costs) > 0 else 1
        max_quality = max(qualities) if max(qualities) > 0 else 100

        for agent_name, result in results.items():
            if not result.success:
                scores[agent_name] = 0
                continue

            # Normalize and invert (lower is better for time and cost)
            time_score = (1 - (result.wall_time / max_time)) * 30 if max_time > 0 else 30
            cost_score = (1 - (result.cost / max_cost)) * 30 if max_cost > 0 else 30
            quality_score = (result.quality_score / max_quality) * 40

            scores[agent_name] = time_score + cost_score + quality_score

        # Find winner
        winner_name = max(scores, key=scores.get)
        winner_score = scores[winner_name]

        return {"name": winner_name, "score": winner_score}

    def save(self, html: str, output_path: str) -> None:
        """Save HTML to file.

        Args:
            html: HTML content to save
            output_path: Path to output file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write(html)
