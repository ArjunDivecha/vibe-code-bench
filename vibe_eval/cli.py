"""
=============================================================================
SCRIPT NAME: cli.py
=============================================================================

INPUT FILES:
- .env file containing OPENROUTER_API_KEY environment variable
- Results JSON files for show/dashboard commands

OUTPUT FILES:
- New eval cases added to eval_cases/ with spec.md and optional criteria

VERSION: 3.0
LAST UPDATED: 2026-01-28

DESCRIPTION:
CLI entry point for Vibe Eval V3. Provides commands for:
- run: Execute evaluations across models and cases
- show: Display results from a previous run
- diagnose: Generate variance and runtime diagnostics reports
- add-case: Add a new eval case
- list-cases: List available eval cases
- dashboard: Show detailed metrics dashboard
- list-models: List supported models available via OpenRouter

V3 FEATURES:
- Fast suite mode for high-signal subset evaluation
- Multi-judge arbitration via OpenRouter (default)
- Execution validation and functional tests
- Tiered cases (Tier 1=simple, 2=complex, 3=agentic)

DEPENDENCIES:
- click
- rich
- python-dotenv

USAGE:
python -m vibe_eval run -m anthropic/claude-opus-4.5 -c all
python -m vibe_eval diagnose --results-dir results --output-dir reports
python -m vibe_eval list-cases
=============================================================================
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables
load_dotenv()

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Vibe Code Bench - Benchmark Harness for Evaluating LLM Coding Tasks

    Evaluates how well AI models build complete, working applications from natural language
    specifications through multi-turn agentic sessions with tool use, validation, testing, and judging.

    See the README.md for detailed overview and usage examples.
    """


@cli.command()
@click.option(
    '--models', '-m', 
    required=True, 
    help='Comma-separated list of models (e.g., claude-sonnet-4,gpt-4o,gemini-2.5-pro)'
)
@click.option(
    '--cases', '-c', 
    default='all', 
    help='Case filter: "all" or comma-separated case names'
)
@click.option(
    '--timeout', '-t', 
    default=20, 
    type=int,
    help='Timeout in minutes per case per model'
)
@click.option(
    '--cases-dir', '-d',
    default='eval_cases',
    type=click.Path(exists=True),
    help='Directory containing eval cases'
)
@click.option(
    '--output', '-o', 
    default='results', 
    type=click.Path(),
    help='Output directory for results'
)
@click.option(
    '--judge', '-j',
    default='anthropic/claude-opus-4.5',
    help='Judge model for scoring (used in single-judge mode, via OpenRouter)'
)
@click.option(
    '--single-judge', '-s',
    is_flag=True,
    default=False,
    help='Use single judge instead of multi-judge arbitration'
)
@click.option(
    '--no-validation',
    is_flag=True,
    default=False,
    help='Disable runtime execution validation'
)
@click.option(
    '--head-to-head',
    is_flag=True,
    default=False,
    help='Enable head-to-head comparisons (O(n²), off by default)'
)
@click.option(
    '--suite',
    type=click.Choice(['full', 'fast']),
    default='full',
    help='Evaluation suite: full (default) or fast (high-signal subset)'
)
def run(models, cases, timeout, cases_dir, output, judge, single_judge, no_validation, head_to_head, suite):
    """Run evaluation across models and cases."""
    from .runner import EvalRunner
    from .reporting.leaderboard import print_leaderboard
    
    # Parse models
    model_list = [m.strip() for m in models.split(',')]
    
    # Parse cases filter
    case_filter = None
    if cases.lower() != 'all':
        case_filter = [c.strip() for c in cases.split(',')]
    elif suite == "fast":
        from .fast_suite import get_fast_suite_cases
        case_filter = get_fast_suite_cases()
    
    # Check API keys
    _check_api_keys(model_list)
    
    # Run evaluation
    # V2: Multi-judge is default, single-judge is opt-in
    # V2: Head-to-head is opt-in (O(n²) cost)
    runner = EvalRunner(
        models=model_list,
        cases_dir=Path(cases_dir),
        case_filter=case_filter,
        timeout_minutes=timeout,
        results_dir=Path(output),
        judge_model=judge,
        multi_judge=not single_judge,
        validate_execution=not no_validation,
        run_comparisons=head_to_head,  # V2: Off by default
        suite_mode=suite,
    )
    
    results = runner.run()
    
    # Print leaderboard
    console.print()
    print_leaderboard(results, console)


@cli.command()
@click.argument('results_file', type=click.Path(exists=True))
def show(results_file):
    """Show results from a previous run."""
    from .judge.absolute import AbsoluteScore, DimensionScore
    from .judge.comparative import ComparisonResult
    from .reporting.leaderboard import EvalRun, CaseResult, print_leaderboard
    
    filepath = Path(results_file)
    data = json.loads(filepath.read_text())
    
    # Reconstruct EvalRun from JSON
    case_results = {}
    for case_name, cr_data in data.get("case_results", {}).items():
        # Reconstruct absolute scores
        absolute_scores = {}
        for model, score_data in cr_data.get("absolute_scores", {}).items():
            absolute_scores[model] = AbsoluteScore(
                executes=DimensionScore(score_data["executes"]["score"], score_data["executes"]["reason"]),
                features_complete=DimensionScore(score_data["features_complete"]["score"], score_data["features_complete"]["reason"]),
                output_quality=DimensionScore(score_data["output_quality"]["score"], score_data["output_quality"]["reason"]),
                direction_following=DimensionScore(score_data["direction_following"]["score"], score_data["direction_following"]["reason"]),
                code_quality=DimensionScore(score_data["code_quality"]["score"], score_data["code_quality"]["reason"]),
                elegance=DimensionScore(score_data["elegance"]["score"], score_data["elegance"]["reason"]),
            )
        
        # Reconstruct comparisons
        comparisons = [
            ComparisonResult(
                winner=c["winner"],
                confidence=c["confidence"],
                reasoning=c["reasoning"],
                model_a=c["model_a"],
                model_b=c["model_b"]
            )
            for c in cr_data.get("comparisons", [])
        ]
        
        case_results[case_name] = CaseResult(
            case_name=case_name,
            absolute_scores=absolute_scores,
            comparisons=comparisons
        )
    
    run = EvalRun(
        timestamp=datetime.fromisoformat(data["timestamp"]),
        models=data["models"],
        cases=data["cases"],
        case_results=case_results,
        timeout_minutes=data.get("timeout_minutes", 20),
        suite_mode=data.get("suite", "full"),
    )
    
    print_leaderboard(run, console)


@cli.command()
@click.option(
    '--results-dir',
    default='results',
    type=click.Path(exists=True),
    help='Directory containing result JSON files'
)
@click.option(
    '--output-dir',
    default='reports',
    type=click.Path(),
    help='Directory to write diagnostics reports'
)
def diagnose(results_dir, output_dir):
    """Generate variance and runtime diagnostics reports."""
    from .reporting.differentiation import generate_reports

    results_path = Path(results_dir)
    output_path = Path(output_dir)
    generate_reports(results_path, output_path)
    console.print(f"[green]✓ Wrote diagnostics to {output_path}[/green]")


@cli.command('add-case')
@click.option('--name', '-n', required=True, help='Case name (will be folder name)')
@click.option('--spec', '-s', required=True, type=click.Path(exists=True), help='Path to spec.md file')
@click.option('--criteria', type=click.Path(exists=True), help='Optional path to judge_criteria.md')
@click.option('--cases-dir', '-d', default='eval_cases', help='Cases directory')
def add_case(name, spec, criteria, cases_dir):
    """Add a new eval case."""
    case_dir = Path(cases_dir) / name
    
    if case_dir.exists():
        console.print(f"[red]Error: Case '{name}' already exists[/red]")
        return
    
    case_dir.mkdir(parents=True)
    shutil.copy(spec, case_dir / 'spec.md')
    
    if criteria:
        shutil.copy(criteria, case_dir / 'judge_criteria.md')
    
    console.print(f"[green]✓ Created case: {case_dir}[/green]")


@cli.command('list-cases')
@click.option('--cases-dir', '-d', default='eval_cases', help='Cases directory')
def list_cases(cases_dir):
    """List available eval cases."""
    cases_path = Path(cases_dir)
    
    if not cases_path.exists():
        console.print(f"[yellow]Cases directory not found: {cases_dir}[/yellow]")
        return
    
    cases = sorted([
        d.name for d in cases_path.iterdir() 
        if d.is_dir() and not d.name.startswith('.')
    ])
    
    if not cases:
        console.print("[yellow]No eval cases found[/yellow]")
        return
    
    console.print(f"\n[bold]Available Cases ({len(cases)}):[/bold]")
    for case in cases:
        spec_path = cases_path / case / "spec.md"
        if spec_path.exists():
            # Show first line of spec as description
            first_line = spec_path.read_text().split('\n')[0].strip('# ')
            console.print(f"  • {case}: [dim]{first_line[:50]}[/dim]")
        else:
            console.print(f"  • {case} [red](missing spec.md)[/red]")


@cli.command('dashboard')
@click.argument('results_file', required=False, type=click.Path(exists=True))
@click.option('--output', '-o', default='results', help='Results directory to find latest')
def dashboard(results_file, output):
    """Show detailed metrics dashboard for a run.
    
    If no results file is specified, shows the most recent run.
    """
    from rich.table import Table
    from rich.panel import Panel
    
    # Find results file
    if results_file:
        filepath = Path(results_file)
    else:
        results_dir = Path(output)
        if not results_dir.exists():
            console.print("[red]No results directory found[/red]")
            return
        
        json_files = list(results_dir.glob('*_results.json'))
        if not json_files:
            console.print("[yellow]No results files found[/yellow]")
            return
        
        filepath = max(json_files)  # Most recent
    
    data = json.loads(filepath.read_text())
    
    # Get detailed metrics
    details = data.get('case_results_details', data.get('case_results', {}))
    
    # Header
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]📊 EVALUATION DASHBOARD[/bold cyan]\n"
        f"[dim]{filepath.name}[/dim]\n"
        f"[dim]{data.get('timestamp', 'Unknown')}[/dim]",
        border_style="cyan"
    ))
    console.print()
    
    # Main metrics table
    table = Table(title="Case-by-Case Metrics", show_header=True, header_style="bold")
    table.add_column("Case", style="cyan", max_width=25)
    table.add_column("Score", justify="right")
    table.add_column("Time", justify="right")
    table.add_column("Turns", justify="right")
    table.add_column("Files", justify="right")
    table.add_column("Tokens", justify="right")
    
    total_time = 0
    total_input = 0
    total_output = 0
    total_score = 0
    count = 0
    
    for case_name in data.get('cases', []):
        case = details.get(case_name, {})
        abs_scores = case.get('absolute_scores', {})
        
        for model, score_data in abs_scores.items():
            score = score_data.get('total_score', 0) if isinstance(score_data, dict) else 0
            
            metrics = case.get('model_metrics', {}).get(model, {})
            time_s = metrics.get('time_seconds', 0)
            turns = metrics.get('turns', 0)
            inp_tok = metrics.get('input_tokens', 0)
            out_tok = metrics.get('output_tokens', 0)
            files = metrics.get('files_created', 0)
            
            total_time += time_s
            total_input += inp_tok
            total_output += out_tok
            total_score += score
            count += 1
            
            # Color code score
            if score >= 80:
                score_str = f"[green]{score:.1f}[/green]"
            elif score >= 50:
                score_str = f"[yellow]{score:.1f}[/yellow]"
            else:
                score_str = f"[red]{score:.1f}[/red]"
            
            table.add_row(
                case_name[:25],
                score_str,
                f"{time_s:.0f}s",
                str(turns),
                str(files),
                f"{inp_tok + out_tok:,}"
            )
    
    console.print(table)
    console.print()
    
    # Summary table
    summary = Table(title="Summary", show_header=True, header_style="bold")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", justify="right")
    
    avg_score = total_score / count if count else 0
    total_tokens = total_input + total_output
    
    # Estimate cost (approximate rates)
    models = data.get('models', [])
    model_name = models[0].lower() if models else ''
    if 'claude' in model_name:
        cost = (total_input/1e6)*3.0 + (total_output/1e6)*15.0
    elif 'gpt-4o' in model_name:
        cost = (total_input/1e6)*2.5 + (total_output/1e6)*10.0
    elif 'llama' in model_name or 'openrouter' in model_name:
        cost = (total_input/1e6)*0.1 + (total_output/1e6)*0.3
    else:
        cost = (total_input/1e6)*1.0 + (total_output/1e6)*3.0
    
    summary.add_row("Average Score", f"{avg_score:.1f}/100")
    summary.add_row("Total Time", f"{total_time:.0f}s ({total_time/60:.1f} min)")
    summary.add_row("Total Tokens", f"{total_tokens:,}")
    summary.add_row("Input Tokens", f"{total_input:,}")
    summary.add_row("Output Tokens", f"{total_output:,}")
    summary.add_row("Estimated Cost", f"${cost:.4f}")
    summary.add_row("Cases", str(count))
    summary.add_row("Models", ", ".join(models))
    
    console.print(summary)
    console.print()


@cli.command('list-models')
def list_models():
    """List supported models (all via OpenRouter)."""
    console.print("\n[bold]Supported Models (V2 - All via OpenRouter)[/bold]")
    console.print("[dim]Use full OpenRouter model IDs or shorthand names[/dim]\n")

    models = {
        "Anthropic": [
            ("claude-sonnet-4.5", "anthropic/claude-sonnet-4.5"),
            ("claude-opus-4.5", "anthropic/claude-opus-4.5"),
            ("claude-haiku-4.5", "anthropic/claude-haiku-4.5"),
        ],
        "OpenAI": [
            ("gpt-4o", "openai/gpt-4o"),
            ("gpt-4o-mini", "openai/gpt-4o-mini"),
            ("o1", "openai/o1"),
            ("o3-mini", "openai/o3-mini"),
        ],
        "Google": [
            ("gemini-2.0-flash", "google/gemini-2.0-flash-001"),
            ("gemini-2.5-pro", "google/gemini-2.5-pro-preview-06-05"),
            ("gemini-3-flash", "google/gemini-3-flash"),
        ],
        "Meta": [
            ("llama-3.1-8b", "meta-llama/llama-3.1-8b-instruct"),
            ("llama-3.1-70b", "meta-llama/llama-3.1-70b-instruct"),
        ],
        "Other (use full OpenRouter ID)": [
            ("qwen3-coder", "qwen/qwen3-coder"),
            ("kimi-k2", "moonshotai/kimi-k2-0905@Groq"),
            ("gpt-oss-120b", "openai/gpt-oss-120b@Cerebras"),
        ],
    }

    for provider, model_list in models.items():
        console.print(f"  [cyan]{provider}[/cyan]")
        for shorthand, full_id in model_list:
            console.print(f"    • {shorthand} → {full_id}")
        console.print()


def _check_api_keys(models: list[str]):
    """Check that required API keys are set.

    V2: All models and judges use OpenRouter - only OPENROUTER_API_KEY needed.
    """
    # V2: Only OpenRouter key needed (all models + judges route through it)
    if not os.environ.get("OPENROUTER_API_KEY"):
        console.print("[red]Missing API key:[/red]")
        console.print("  • OPENROUTER_API_KEY")
        console.print("\n[dim]Set in .env file or environment[/dim]")
        console.print("[dim]All models and judges use OpenRouter in V2[/dim]")
        raise click.Abort()


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
