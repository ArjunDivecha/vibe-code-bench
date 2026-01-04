"""
=============================================================================
SCRIPT NAME: runner.py
=============================================================================

Main evaluation runner - orchestrates models, cases, and judges.

VERSION: 2.0
LAST UPDATED: 2026-01-04

CHANGES IN V2:
- Multi-judge arbitration by default (Claude, GPT-4o, Gemini)
- Runtime execution validation integrated
- Dependency enforcement active

=============================================================================
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .agent_loop import AgentLoop
from .models.base import get_model
from .judge.absolute import AbsoluteJudge, AbsoluteScore, DimensionScore
from .judge.comparative import ComparativeJudge, run_all_comparisons
from .judge.multi_judge import MultiJudgeArbitrator, create_multi_judge
from .reporting.leaderboard import EvalRun, CaseResult, print_leaderboard, ModelMetrics
from .sandbox.executor import create_workspace
from .sandbox.validator import ExecutionValidator


@dataclass
class EvalCase:
    """An evaluation case with spec and criteria."""
    name: str
    spec: str
    criteria: Optional[str] = None


def load_case(case_dir: Path) -> EvalCase:
    """
    Load an eval case from a directory.
    
    Expects:
    - spec.md: Task specification
    - judge_criteria.md (optional): Additional evaluation criteria
    """
    spec_path = case_dir / "spec.md"
    criteria_path = case_dir / "judge_criteria.md"
    
    if not spec_path.exists():
        raise ValueError(f"No spec.md found in {case_dir}")
    
    spec = spec_path.read_text()
    criteria = criteria_path.read_text() if criteria_path.exists() else None
    
    return EvalCase(
        name=case_dir.name,
        spec=spec,
        criteria=criteria
    )


def load_cases(cases_dir: Path, filter_names: Optional[list[str]] = None) -> list[EvalCase]:
    """
    Load all eval cases from a directory.
    
    Args:
        cases_dir: Directory containing case folders
        filter_names: Optional list of case names to include (None = all)
        
    Returns:
        List of loaded cases
    """
    cases = []
    
    for case_path in sorted(cases_dir.iterdir()):
        if case_path.is_dir() and not case_path.name.startswith("."):
            if filter_names is None or case_path.name in filter_names:
                try:
                    cases.append(load_case(case_path))
                except ValueError as e:
                    print(f"Skipping {case_path.name}: {e}")
    
    return cases


class EvalRunner:
    """
    Main evaluation runner.

    Orchestrates running models on cases, judging results,
    and compiling the leaderboard.

    V2: Now uses multi-judge arbitration by default for unbiased scoring.
    """

    def __init__(
        self,
        models: list[str],
        cases_dir: Path,
        case_filter: Optional[list[str]] = None,
        timeout_minutes: int = 20,
        results_dir: Path = Path("results"),
        judge_model: str = "claude-opus-4.5",
        multi_judge: bool = True,  # V2: Multi-judge by default
        validate_execution: bool = True,  # V2: Execution validation
        run_comparisons: bool = False,  # V2: Head-to-head off by default
    ):
        """
        Initialize eval runner.

        Args:
            models: List of model IDs to evaluate
            cases_dir: Directory containing eval cases
            case_filter: Optional list of case names (None = all)
            timeout_minutes: Timeout per model per case
            results_dir: Directory to save results
            judge_model: Model to use for judging (fallback if single-judge)
            multi_judge: Use multi-judge arbitration (default True)
            validate_execution: Run execution validation (default True)
            run_comparisons: Run head-to-head comparisons (default False, O(n²))
        """
        self.models = models
        self.cases = load_cases(cases_dir, case_filter)
        self.timeout_minutes = timeout_minutes
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.validate_execution = validate_execution
        self.run_comparisons = run_comparisons  # V2: Off by default

        # V2: Initialize judges - multi-judge by default
        self.multi_judge_enabled = multi_judge
        if multi_judge:
            self.multi_judge = create_multi_judge()
            self.absolute_judge = None  # Not used in multi-judge mode
        else:
            self.multi_judge = None
            self.absolute_judge = AbsoluteJudge(judge_model=judge_model)

        # Only init comparative judge if needed
        self.comparative_judge = ComparativeJudge(judge_model=judge_model) if run_comparisons else None

        # V2: Execution validator
        self.validator = ExecutionValidator(timeout=30) if validate_execution else None

        self.console = Console()
    
    def run(self) -> EvalRun:
        """
        Run the complete evaluation.
        
        Returns:
            EvalRun with all results
        """
        timestamp = datetime.now()
        case_results = {}
        
        self.console.print(f"\n[bold cyan]Starting Vibe Eval[/bold cyan]")
        self.console.print(f"Models: {', '.join(self.models)}")
        self.console.print(f"Cases: {len(self.cases)}")
        self.console.print(f"Timeout: {self.timeout_minutes} min/case/model\n")
        
        for case in self.cases:
            self.console.print(f"\n[bold]Case: {case.name}[/bold]")
            
            # Run each model on this case
            workspaces = {}
            absolute_scores = {}
            metrics = {} # Initialize metrics dictionary
            
            for model_id in self.models:
                self.console.print(f"  Running {model_id}...", end=" ")
                
                # Create workspace for this model+case - save in results folder
                # so generated code is preserved for future comparison
                workspace = self.results_dir / timestamp.strftime("%Y%m%d_%H%M%S") / case.name / model_id.replace("/", "_").replace(".", "_")
                workspace.mkdir(parents=True, exist_ok=True)
                
                # Run agent loop
                try:
                    model = get_model(model_id)
                    agent = AgentLoop(
                        model=model,
                        spec=case.spec,
                        timeout_minutes=self.timeout_minutes,
                        workspace=workspace
                    )
                    result = agent.run()
                    
                    if result.error:
                        status = f"[red]error: {result.error}[/red]"
                    elif result.completed:
                        status = "[green]✓[/green]"
                    else:
                        status = "[yellow]timeout[/yellow]"
                        
                    self.console.print(
                        f"{status} "
                        f"({result.turns} turns, {result.elapsed_seconds:.0f}s, "
                        f"{len(result.files_created)} files)"
                    )
                    
                    workspaces[model_id] = result.workspace
                    
                    # Capture metrics
                    metrics[model_id] = ModelMetrics(
                        time_seconds=result.elapsed_seconds,
                        turns=result.turns,
                        files_created=len(result.files_created),
                        input_tokens=result.total_input_tokens,
                        output_tokens=result.total_output_tokens
                    )
                    
                except Exception as e:
                    self.console.print(f"[red]✗ Error: {e}[/red]")
                    workspaces[model_id] = workspace
            
            # V2: Run execution validation first (if enabled)
            execution_reports = {}
            if self.validator:
                self.console.print("  Validating execution...", end=" ")
                for model_id, workspace in workspaces.items():
                    exec_report = self.validator.validate(workspace)
                    execution_reports[model_id] = exec_report
                    if not exec_report.executed:
                        # Log execution failure
                        self.console.print(f"\n    [yellow]{model_id}: execution failed[/yellow]", end="")
                self.console.print(" [green]done[/green]")

            # Score with judge (multi-judge by default)
            self.console.print("  Scoring...", end=" ")
            for model_id, workspace in workspaces.items():
                multi_score = None  # Initialize for single-judge case
                if self.multi_judge_enabled:
                    # V2: Multi-judge arbitration
                    multi_score = self.multi_judge.score(
                        spec=case.spec,
                        workspace=workspace,
                        criteria=case.criteria
                    )
                    # Convert multi-judge score to AbsoluteScore for compatibility
                    # Use aggregated dimension scores
                    dims = multi_score.aggregated_dimensions
                    score = AbsoluteScore(
                        executes=DimensionScore(int(dims.get("executes", 0)), "Multi-judge aggregated"),
                        features_complete=DimensionScore(int(dims.get("features_complete", 0)), "Multi-judge aggregated"),
                        output_quality=DimensionScore(int(dims.get("output_quality", 0)), "Multi-judge aggregated"),
                        direction_following=DimensionScore(int(dims.get("direction_following", 0)), "Multi-judge aggregated"),
                        code_quality=DimensionScore(int(dims.get("code_quality", 0)), "Multi-judge aggregated"),
                    )

                    # V2: If execution validation failed, cap executes score
                    if model_id in execution_reports and not execution_reports[model_id].executed:
                        score = AbsoluteScore(
                            executes=DimensionScore(min(score.executes.score, 2), f"Execution failed: {execution_reports[model_id].errors}"),
                            features_complete=score.features_complete,
                            output_quality=score.output_quality,
                            direction_following=score.direction_following,
                            code_quality=score.code_quality,
                        )
                else:
                    # Single judge mode (legacy)
                    score = self.absolute_judge.score(
                        spec=case.spec,
                        workspace=workspace,
                        criteria=case.criteria
                    )

                    # V2: Apply execution validation cap
                    if model_id in execution_reports and not execution_reports[model_id].executed:
                        score = AbsoluteScore(
                            executes=DimensionScore(min(score.executes.score, 2), f"Execution failed: {execution_reports[model_id].errors}"),
                            features_complete=score.features_complete,
                            output_quality=score.output_quality,
                            direction_following=score.direction_following,
                            code_quality=score.code_quality,
                        )

                absolute_scores[model_id] = score

                # V2: Update metrics with judge cost
                if model_id in metrics:
                    if self.multi_judge_enabled and multi_score:
                        metrics[model_id].judge_tokens = multi_score.total_judge_tokens
                        metrics[model_id].judge_cost = multi_score.total_judge_cost
                    elif score.judge_metrics:
                        metrics[model_id].judge_tokens = score.judge_metrics.total_tokens
                        metrics[model_id].judge_cost = score.judge_metrics.estimated_cost()

            self.console.print("[green]done[/green]")

            # V2: Head-to-head comparisons (opt-in, O(n²))
            comparisons = []
            if self.run_comparisons and len(workspaces) > 1:
                self.console.print("  Comparing...", end=" ")
                comparisons = run_all_comparisons(
                    spec=case.spec,
                    workspaces=workspaces,
                    judge=self.comparative_judge
                )
                self.console.print("[green]done[/green]")

            # Store case result
            case_results[case.name] = CaseResult(
                case_name=case.name,
                absolute_scores=absolute_scores,
                comparisons=comparisons,
                model_metrics=metrics,
                winner=None # Will be computed
            )
        
        # Compile final results
        eval_run = EvalRun(
            timestamp=timestamp,
            models=self.models,
            cases=[c.name for c in self.cases],
            case_results=case_results,
            timeout_minutes=self.timeout_minutes
        )

        # Save results
        self._save_results(eval_run)

        # V2: Cleanup shared resources
        self._cleanup()

        return eval_run

    def _cleanup(self):
        """Clean up shared resources after evaluation run."""
        # V2: Clear file cache
        from .judge.absolute import clear_file_cache
        clear_file_cache()

        # V2: Clean up Playwright browser
        if self.validator:
            ExecutionValidator.cleanup()
    
    def _save_results(self, run: EvalRun):
        """Save results to JSON file."""
        filename = f"{run.timestamp.strftime('%Y%m%d_%H%M%S')}_results.json"
        filepath = self.results_dir / filename
        
        # Convert to serializable format
        data = {
            "timestamp": run.timestamp.isoformat(),
            "models": run.models,
            "cases": run.cases,
            "timeout_minutes": run.timeout_minutes,
            "case_results": {
                name: {
                    "absolute_scores": {
                        m: s.to_dict() for m, s in cr.absolute_scores.items()
                    },
                    "comparisons": [
                        {
                            "model_a": c.model_a,
                            "model_b": c.model_b,
                            "winner": c.winner,
                            "confidence": c.confidence,
                            "reasoning": c.reasoning
                        }
                        for c in cr.comparisons
                    ]
                }
                for name, cr in run.case_results.items()
            },
            "case_results_details": {
                 name: {
                    "absolute_scores": {
                        m: s.to_dict() for m, s in cr.absolute_scores.items()
                    },
                    "winner": cr.winner,
                    "model_metrics": {
                        m: {
                            "time_seconds": met.time_seconds,
                            "turns": met.turns,
                            "files_created": met.files_created,
                            "input_tokens": met.input_tokens,
                            "output_tokens": met.output_tokens,
                            # V2: Judge cost tracking
                            "judge_tokens": met.judge_tokens,
                            "judge_cost": met.judge_cost,
                        } for m, met in cr.model_metrics.items()
                    },
                    "comparisons": [
                        {
                            "model_a": c.model_a,
                            "model_b": c.model_b,
                            "winner": c.winner,
                            "confidence": c.confidence,
                            "reasoning": c.reasoning
                        }
                        for c in cr.comparisons
                    ]
                 } for name, cr in run.case_results.items()
            },
            "leaderboard": {
                "rankings": run.compute_leaderboard().rankings,
                "wins": run.compute_leaderboard().wins,
                "losses": run.compute_leaderboard().losses,
            },
            "absolute_averages": run.get_absolute_averages()
        }
        
        filepath.write_text(json.dumps(data, indent=2))
        self.console.print(f"\n[dim]Results saved to {filepath}[/dim]")
