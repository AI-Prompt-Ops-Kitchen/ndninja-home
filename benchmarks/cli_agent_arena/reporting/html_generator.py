"""HTML report generator for benchmark results."""

from typing import Dict, List, Tuple
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

    def _rank_agents(self, results: Dict[str, BenchmarkResult]) -> Dict[str, int]:
        """Rank agents by overall score (1=best).

        Args:
            results: Dict of agent_name -> BenchmarkResult

        Returns:
            Dict of agent_name -> rank (1=best, 2=second, etc.)
        """
        if not results:
            return {}

        # Use _determine_winner's scoring logic
        scores = {}
        times = [r.wall_time for r in results.values() if r.success]
        costs = [r.cost for r in results.values() if r.success]
        qualities = [r.quality_score for r in results.values() if r.success]

        if not times:
            return {name: 1 for name in results}

        max_time = max(times) if times else 1
        max_cost = max(costs) if costs and max(costs) > 0 else 1
        max_quality = max(qualities) if qualities and max(qualities) > 0 else 100

        for agent_name, result in results.items():
            if not result.success:
                scores[agent_name] = 0
                continue
            time_score = (1 - (result.wall_time / max_time)) * 30 if max_time > 0 else 30
            cost_score = (1 - (result.cost / max_cost)) * 30 if max_cost > 0 else 30
            quality_score = (result.quality_score / max_quality) * 40
            scores[agent_name] = time_score + cost_score + quality_score

        # Sort by score descending, assign ranks
        sorted_agents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        ranks = {}
        for i, (name, _) in enumerate(sorted_agents):
            ranks[name] = i + 1

        return ranks

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
        rankings = self._rank_agents(results)

        # Build comparison table rows
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

        # Autonomy comparison (retries + error recovery)
        autonomy = {}
        for agent in agents:
            r = results[agent]
            # Higher autonomy = fewer retries and error recovery capability
            score = 100 - (r.retries * 10) + (20 if r.error_recovered else 0)
            autonomy[agent] = max(0, min(100, score))
        autonomy_winner = self.determine_winner(autonomy, lower_is_better=False)
        comparison_rows.append({
            "metric": "Autonomy",
            "values": autonomy,
            "winner": autonomy_winner,
        })

        # Quality comparison
        qualities = {agent: getattr(results[agent], 'quality_score', 0.0) for agent in agents}
        quality_winner = self.determine_winner(qualities, lower_is_better=False)
        comparison_rows.append({
            "metric": "Code Quality",
            "values": qualities,
            "winner": quality_winner,
        })

        # Determine overall winner
        overall_winner = min(rankings, key=rankings.get) if rankings else "tie"
        medal_icons = {1: "&#x1F947;", 2: "&#x1F948;", 3: "&#x1F949;"}

        # Rank color classes
        rank_colors = {1: "#d4edda", 2: "#fff3cd", 3: "#f8d7da"}

        # Build radar chart data
        radar_labels = ["Speed", "Cost", "Quality", "Autonomy", "Efficiency"]
        radar_datasets = []
        colors = ["rgba(102, 126, 234, 0.6)", "rgba(118, 75, 162, 0.6)", "rgba(40, 167, 69, 0.6)"]
        border_colors = ["rgba(102, 126, 234, 1)", "rgba(118, 75, 162, 1)", "rgba(40, 167, 69, 1)"]
        for i, agent in enumerate(agents):
            r = results[agent]
            max_time = max(speeds.values()) if max(speeds.values()) > 0 else 1
            max_cost_val = max(costs.values()) if max(costs.values()) > 0 else 1
            speed_score = (1 - r.wall_time / max_time) * 100 if max_time > 0 else 100
            cost_score = (1 - r.cost / max_cost_val) * 100 if max_cost_val > 0 else 100
            max_tc = max(tool_calls.values()) if max(tool_calls.values()) > 0 else 1
            efficiency_score = (1 - r.tool_calls / max_tc) * 100 if max_tc > 0 else 100
            radar_datasets.append({
                "label": agent.capitalize(),
                "data": [
                    max(0, speed_score),
                    max(0, cost_score),
                    r.quality_score,
                    autonomy[agent],
                    max(0, efficiency_score),
                ],
                "color": colors[i % len(colors)],
                "border": border_colors[i % len(border_colors)],
            })

        # Build HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Comparison: {task_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th, td {{ border: 1px solid #e9ecef; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .rank-1 {{ background-color: #d4edda; font-weight: bold; }}
        .rank-2 {{ background-color: #fff3cd; }}
        .rank-3 {{ background-color: #f8d7da; }}
        .winner {{ background-color: #d4edda; font-weight: bold; }}
        .tie {{ background-color: #f8f9fa; }}
        .winner-summary {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
        .winner-summary .medal {{ font-size: 2em; }}
        .winner-summary .name {{ font-size: 1.5em; font-weight: bold; color: #333; }}
        .rankings {{ display: flex; gap: 15px; justify-content: center; margin-top: 15px; }}
        .rank-card {{ padding: 10px 20px; border-radius: 8px; text-align: center; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 500px; margin-left: auto; margin-right: auto; }}
    </style>
</head>
<body>
<div class="container">
    <h1>Benchmark Comparison: {task_name}</h1>

    <div class="winner-summary">
        <div class="medal">{medal_icons.get(1, '')}</div>
        <div class="name">Overall Winner: {overall_winner.capitalize()}</div>
        <div class="rankings">
"""

        for agent in agents:
            rank = rankings.get(agent, len(agents))
            medal = medal_icons.get(rank, f"#{rank}")
            bg = rank_colors.get(rank, "#f8f9fa")
            html += f'            <div class="rank-card" style="background: {bg};">{medal} {agent.capitalize()} (#{rank})</div>\n'

        html += """        </div>
    </div>

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

                # Rank-based color coding
                rank = rankings.get(agent, len(agents))
                if is_winner:
                    cell_class = "rank-1"
                elif is_tie:
                    cell_class = "tie"
                else:
                    cell_class = f"rank-{rank}" if rank <= 3 else ""

                # Format value
                if isinstance(value, float):
                    if "Cost" in row['metric']:
                        formatted = f"${value:.4f}"
                    elif "Quality" in row['metric'] or "Autonomy" in row['metric']:
                        formatted = f"{value:.1f}"
                    else:
                        formatted = f"{value:.1f}"
                else:
                    formatted = str(value)

                checkmark = " &#10003;" if is_winner else ""
                html += f"            <td class='{cell_class}'>{formatted}{checkmark}</td>\n"

            winner_text = row['winner'].capitalize() if row['winner'] != "tie" else "Tie"
            html += f"            <td>{winner_text}</td>\n"
            html += "        </tr>\n"

        html += """
    </table>

    <h2>Performance Radar</h2>
    <div class="chart-container">
        <canvas id="radarChart"></canvas>
    </div>

    <script>
    const ctx = document.getElementById('radarChart').getContext('2d');
    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: """ + str(radar_labels) + """,
            datasets: [
"""

        for ds in radar_datasets:
            html += f"""                {{
                    label: '{ds["label"]}',
                    data: {ds["data"]},
                    backgroundColor: '{ds["color"]}',
                    borderColor: '{ds["border"]}',
                    pointBackgroundColor: '{ds["border"]}',
                }},
"""

        html += """            ]
        },
        options: {
            responsive: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                }
            }
        }
    });
    </script>
</div>
</body>
</html>
"""
        return html
