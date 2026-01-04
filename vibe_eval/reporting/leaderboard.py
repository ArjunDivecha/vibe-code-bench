"""Leaderboard generation and results display."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..judge.absolute import AbsoluteScore
from ..judge.comparative import ComparisonResult


@dataclass
class ModelMetrics:
    """Metrics for a single model run on a case."""
    time_seconds: float
    turns: int
    files_created: int
    input_tokens: int
    output_tokens: int
    # V2: Separate judge cost tracking
    judge_tokens: int = 0
    judge_cost: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def estimated_llm_cost(self, model_name: str) -> float:
        """Estimate LLM cost in USD based on model pricing (OpenRouter rates)."""
        # OpenRouter pricing per 1M tokens (input, output) - updated Jan 2026
        pricing = {
            "anthropic/claude-opus-4.5": (5.0, 25.0),
            "anthropic/claude-sonnet-4": (3.0, 15.0),
            "openai/gpt-4o": (3.0, 10.0),
            "google/gemini-3-flash": (0.075, 0.3),
            "meta-llama/llama-3.1-8b-instruct": (0.055, 0.055),
            "meta-llama/llama-3.1-70b-instruct": (0.35, 0.4),
            # Fallback rates
            "default": (1.0, 3.0),
        }
        # Normalize model name for lookup
        model_key = model_name.lower()
        input_rate, output_rate = pricing.get(model_key, pricing["default"])
        cost = (self.input_tokens / 1_000_000) * input_rate
        cost += (self.output_tokens / 1_000_000) * output_rate
        return round(cost, 4)

    def estimated_cost(self, model_name: str) -> float:
        """Estimate total cost (LLM + Judge) in USD - legacy compatibility."""
        return self.estimated_llm_cost(model_name) + self.judge_cost


@dataclass
class CaseResult:
    """Result for a single case across models."""
    case_name: str
    absolute_scores: dict[str, AbsoluteScore]  # model -> score
    comparisons: list[ComparisonResult]
    model_metrics: dict[str, ModelMetrics] = field(default_factory=dict)  # model -> metrics
    winner: Optional[str] = None  # Overall case winner
    
    def compute_winner(self) -> str:
        """Determine the case winner based on comparisons."""
        wins = defaultdict(int)
        for comp in self.comparisons:
            if comp.winner == "A":
                wins[comp.model_a] += 1
            elif comp.winner == "B":
                wins[comp.model_b] += 1
        
        if not wins:
            return "TIE"
        
        max_wins = max(wins.values())
        winners = [m for m, w in wins.items() if w == max_wins]
        
        if len(winners) == 1:
            return winners[0]
        else:
            return " = ".join(sorted(winners))


@dataclass
class Leaderboard:
    """Complete leaderboard with rankings."""
    models: list[str]
    wins: dict[str, float]
    losses: dict[str, float]
    rankings: list[str]
    
    @property
    def total_matchups(self) -> int:
        return int(sum(self.wins.values()))


@dataclass
class EvalRun:
    """Complete evaluation run across models and cases."""
    timestamp: datetime
    models: list[str]
    cases: list[str]
    case_results: dict[str, CaseResult]  # case_name -> result
    timeout_minutes: int
    
    def compute_leaderboard(self) -> Leaderboard:
        """Compute win counts and rankings."""
        wins = defaultdict(float)
        losses = defaultdict(float)
        
        for case_result in self.case_results.values():
            for comparison in case_result.comparisons:
                if comparison.winner == "A":
                    wins[comparison.model_a] += 1
                    losses[comparison.model_b] += 1
                elif comparison.winner == "B":
                    wins[comparison.model_b] += 1
                    losses[comparison.model_a] += 1
                else:  # TIE
                    wins[comparison.model_a] += 0.5
                    wins[comparison.model_b] += 0.5
        
        # Sort by wins descending, then by losses ascending
        rankings = sorted(
            self.models,
            key=lambda m: (wins[m], -losses[m]),
            reverse=True
        )
        
        return Leaderboard(
            models=self.models,
            wins=dict(wins),
            losses=dict(losses),
            rankings=rankings
        )
    
    def get_absolute_averages(self) -> dict[str, float]:
        """Get average absolute score per model."""
        totals = defaultdict(list)
        
        for case_result in self.case_results.values():
            for model, score in case_result.absolute_scores.items():
                totals[model].append(score.total_score)
        
        return {
            model: round(sum(scores) / len(scores), 1)
            for model, scores in totals.items()
        }
    
    def get_head_to_head_matrix(self) -> dict[str, dict[str, str]]:
        """Get head-to-head win-loss matrix."""
        matrix = {m: {n: "0-0" for n in self.models if n != m} for m in self.models}
        h2h = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # [wins, losses]
        
        for case_result in self.case_results.values():
            for comp in case_result.comparisons:
                if comp.winner == "A":
                    h2h[comp.model_a][comp.model_b][0] += 1
                    h2h[comp.model_b][comp.model_a][1] += 1
                elif comp.winner == "B":
                    h2h[comp.model_b][comp.model_a][0] += 1
                    h2h[comp.model_a][comp.model_b][1] += 1
        
        for m1 in self.models:
            for m2 in self.models:
                if m1 != m2:
                    w, l = h2h[m1][m2]
                    matrix[m1][m2] = f"{w}-{l}"
        
        return matrix


def print_leaderboard(run: EvalRun, console: Optional[Console] = None):
    """
    Print a formatted leaderboard to console.
    
    Args:
        run: Completed evaluation run
        console: Rich console (creates new one if not provided)
    """
    if console is None:
        console = Console()
    
    leaderboard = run.compute_leaderboard()
    averages = run.get_absolute_averages()
    matrix = run.get_head_to_head_matrix()
    
    # Header
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]VIBE EVAL RESULTS[/bold cyan]\n"
        f"[dim]{run.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n"
        f"[dim]{len(run.cases)} cases • {len(run.models)} models • {run.timeout_minutes}min timeout[/dim]",
        border_style="cyan"
    ))
    console.print()
    
    # Overall rankings table
    table = Table(title="Overall Head-to-Head Record", show_header=True, header_style="bold")
    table.add_column("Rank", style="dim", width=4)
    table.add_column("Model", style="cyan")
    table.add_column("Wins", justify="right")
    table.add_column("Losses", justify="right")
    table.add_column("Win Rate", justify="right")
    table.add_column("", width=12)  # Progress bar
    
    total_possible = leaderboard.total_matchups / len(run.models) if run.models else 0
    
    for i, model in enumerate(leaderboard.rankings, 1):
        wins = leaderboard.wins.get(model, 0)
        losses = leaderboard.losses.get(model, 0)
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0
        
        # Create progress bar
        bar_width = 10
        filled = int(win_rate / 100 * bar_width)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        table.add_row(
            str(i),
            model,
            f"{wins:.1f}" if wins % 1 else str(int(wins)),
            f"{losses:.1f}" if losses % 1 else str(int(losses)),
            f"{win_rate:.1f}%",
            f"[green]{bar}[/green]"
        )
    
    console.print(table)
    console.print()
    
    # Head-to-head matrix
    if len(run.models) > 1:
        matrix_table = Table(title="Head-to-Head Matrix", show_header=True, header_style="bold")
        matrix_table.add_column("", style="cyan")
        for model in run.models:
            # Truncate long model names
            short_name = model[:12] + "…" if len(model) > 12 else model
            matrix_table.add_column(short_name, justify="center")
        
        for model in run.models:
            row = [model[:12] + "…" if len(model) > 12 else model]
            for other in run.models:
                if model == other:
                    row.append("-")
                else:
                    record = matrix[model][other]
                    w, l = record.split("-")
                    if int(w) > int(l):
                        row.append(f"[green]{record}[/green]")
                    elif int(w) < int(l):
                        row.append(f"[red]{record}[/red]")
                    else:
                        row.append(record)
            matrix_table.add_row(*row)
        
        console.print(matrix_table)
        console.print()
    
    # Case-by-case winners
    case_table = Table(title="Case-by-Case Winners", show_header=True, header_style="bold")
    case_table.add_column("Case", style="cyan")
    case_table.add_column("Winner")
    case_table.add_column("Scores", style="dim")
    
    for case_name in run.cases:
        result = run.case_results.get(case_name)
        if result:
            winner = result.compute_winner()
            scores = " | ".join(
                f"{m}: {s.total_score}" 
                for m, s in result.absolute_scores.items()
            )
            case_table.add_row(case_name, winner, scores)
    
    console.print(case_table)
    console.print()
    
    # Average metrics table - V2: Separate LLM and Judge costs
    metrics_table = Table(title="Model Performance & Cost", show_header=True, header_style="bold")
    metrics_table.add_column("Model", style="cyan")
    metrics_table.add_column("Avg Score", justify="right")
    metrics_table.add_column("Avg Time", justify="right")
    metrics_table.add_column("LLM Cost", justify="right")
    metrics_table.add_column("Judge Cost", justify="right")
    metrics_table.add_column("Total Files", justify="right")

    for model in leaderboard.rankings:
        # Calculate averages/totals
        score = averages.get(model, 0)
        total_time = 0
        total_llm_cost = 0
        total_judge_cost = 0
        total_files = 0
        case_count = 0

        for result in run.case_results.values():
            if model in result.model_metrics:
                m = result.model_metrics[model]
                total_time += m.time_seconds
                total_llm_cost += m.estimated_llm_cost(model)
                total_judge_cost += m.judge_cost
                total_files += m.files_created
                case_count += 1

        avg_time = total_time / case_count if case_count else 0

        metrics_table.add_row(
            model,
            f"{score:.1f}",
            f"{avg_time:.0f}s",
            f"${total_llm_cost:.4f}",
            f"${total_judge_cost:.4f}",
            str(total_files)
        )
    
    console.print(metrics_table)
    console.print()
