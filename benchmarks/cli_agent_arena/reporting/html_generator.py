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

    def determine_winner(self, values: Dict[str, float], lower_is_better: bool = False) -> str:
        """Determine winner for a metric

        Args:
            values: Dict of agent_name -> metric value
            lower_is_better: True if lower values are better (time, cost)

        Returns:
            Agent name that won, or "tie"
        """
        if not values:
            return "tie"

        if lower_is_better:
            min_val = min(values.values())
            winners = [k for k, v in values.items() if v == min_val]
        else:
            max_val = max(values.values())
            winners = [k for k, v in values.items() if v == max_val]

        return winners[0] if len(winners) == 1 else "tie"

    def generate_comparison(self, results: Dict[str, BenchmarkResult], task_name: str) -> str:
        """Generate comparison report for multiple agents

        Args:
            results: Dict of agent_name -> BenchmarkResult
            task_name: Name of task being compared

        Returns:
            HTML string with comparison dashboard
        """
        if not results:
            return "<html><body><h1>No results to compare</h1></body></html>"

        agents = list(results.keys())

        # Build comparison table
        comparison_rows = []

        # Speed comparison
        speeds = {agent: results[agent].wall_time for agent in agents}
        speed_winner = self.determine_winner(speeds, lower_is_better=True)
        comparison_rows.append({
            "metric": "Speed (seconds)",
            "values": speeds,
            "winner": speed_winner,
        })

        # Cost comparison
        costs = {agent: results[agent].cost for agent in agents}
        cost_winner = self.determine_winner(costs, lower_is_better=True)
        comparison_rows.append({
            "metric": "Cost (USD)",
            "values": costs,
            "winner": cost_winner,
        })

        # Tool calls comparison
        tool_calls = {agent: results[agent].tool_calls for agent in agents}
        tools_winner = self.determine_winner(tool_calls, lower_is_better=True)
        comparison_rows.append({
            "metric": "Tool Calls",
            "values": tool_calls,
            "winner": tools_winner,
        })

        # Quality comparison
        qualities = {agent: getattr(results[agent], 'quality_score', 0.0) for agent in agents}
        quality_winner = self.determine_winner(qualities, lower_is_better=False)
        comparison_rows.append({
            "metric": "Code Quality",
            "values": qualities,
            "winner": quality_winner,
        })

        # Build HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Comparison: {task_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .winner {{ background-color: #d4edda; font-weight: bold; }}
        .tie {{ background-color: #f8f9fa; }}
    </style>
</head>
<body>
    <h1>Benchmark Comparison: {task_name}</h1>
    <h2>Head-to-Head Comparison</h2>
    <table>
        <tr>
            <th>Metric</th>
"""

        for agent in agents:
            html += f"            <th>{agent.capitalize()}</th>\n"
        html += "            <th>Winner</th>\n        </tr>\n"

        for row in comparison_rows:
            html += "        <tr>\n"
            html += f"            <td>{row['metric']}</td>\n"

            for agent in agents:
                value = row['values'][agent]
                is_winner = row['winner'] == agent
                is_tie = row['winner'] == "tie"
                cell_class = "winner" if is_winner else ("tie" if is_tie else "")

                # Format value
                if isinstance(value, float):
                    if "Cost" in row['metric']:
                        formatted = f"${value:.4f}"
                    elif "Quality" in row['metric']:
                        formatted = f"{value:.1f}"
                    else:
                        formatted = f"{value:.1f}"
                else:
                    formatted = str(value)

                checkmark = " ✓" if is_winner else ""
                html += f"            <td class='{cell_class}'>{formatted}{checkmark}</td>\n"

            winner_text = row['winner'].capitalize() if row['winner'] != "tie" else "Tie"
            html += f"            <td>{winner_text}</td>\n"
            html += "        </tr>\n"

        html += """
    </table>
</body>
</html>
"""
        return html
