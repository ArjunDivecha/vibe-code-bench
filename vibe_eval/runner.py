"""
=============================================================================
SCRIPT NAME: runner.py
=============================================================================

Main evaluation runner - orchestrates models, cases, and judges.

VERSION: 3.0
LAST UPDATED: 2026-01-27

CHANGES IN V3:
- Integrated functional test runner
- New scoring module with auto/static/judge aggregation
- Enhanced agent metrics tracking
- Tiered case support (Tier 1, 2, 3)

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
    tier: int = 1  # V3: Case tier (1=simple, 2=complex, 3=agentic)
    has_tests: bool = False  # V3: Whether tests.py exists


def load_case(case_dir: Path) -> EvalCase:
    """
    Load an eval case from a directory.
    
    Expects:
    - spec.md: Task specification
    - judge_criteria.md (optional): Additional evaluation criteria
    - tests.py (V3, optional): Functional tests
    """
    spec_path = case_dir / "spec.md"
    criteria_path = case_dir / "judge_criteria.md"
    tests_path = case_dir / "tests.py"
    
    if not spec_path.exists():
        raise ValueError(f"No spec.md found in {case_dir}")
    
    spec = spec_path.read_text()
    criteria = criteria_path.read_text() if criteria_path.exists() else None
    
    # V3: Determine tier from case name
    tier = 1
    case_name = case_dir.name
    if case_name.startswith("case_2"):
        tier = 2
    elif case_name.startswith("case_3"):
        tier = 3
    
    return EvalCase(
        name=case_name,
        spec=spec,
        criteria=criteria,
        tier=tier,
        has_tests=tests_path.exists()
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

    V3: Integrated functional tests and new scoring system.
    """

    def __init__(
        self,
        models: list[str],
        cases_dir: Path,
        case_filter: Optional[list[str]] = None,
        timeout_minutes: int = 20,
        results_dir: Path = Path("results"),
        judge_model: str = "claude-opus-4.5",
        multi_judge: bool = True,
        validate_execution: bool = True,
        run_comparisons: bool = False,
        run_functional_tests: bool = True,  # V3: Enable functional tests
        use_v3_scoring: bool = False,  # V3: Use new scoring system
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
            run_functional_tests: Run functional tests if available (V3)
            use_v3_scoring: Use V3 scoring aggregator (default False for compatibility)
        """
        self.models = models
        self.cases_dir = Path(cases_dir)
        self.cases = load_cases(cases_dir, case_filter)
        self.timeout_minutes = timeout_minutes
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.validate_execution = validate_execution
        self.run_comparisons = run_comparisons
        self.run_functional_tests = run_functional_tests
        self.use_v3_scoring = use_v3_scoring

        # Initialize judges
        self.multi_judge_enabled = multi_judge
        if multi_judge:
            self.multi_judge = create_multi_judge()
            self.absolute_judge = None
        else:
            self.multi_judge = None
            self.absolute_judge = AbsoluteJudge(judge_model=judge_model)

        # Only init comparative judge if needed
        self.comparative_judge = ComparativeJudge(judge_model=judge_model) if run_comparisons else None

        # Execution validator
        self.validator = ExecutionValidator(timeout=30) if validate_execution else None

        # V3: Functional test runner
        self.test_runner = None
        if run_functional_tests:
            from .sandbox.test_runner import FunctionalTestRunner
            self.test_runner = FunctionalTestRunner(timeout=30)

        self.console = Console()
    
    def run(self) -> EvalRun:
        """
        Run the complete evaluation.
        
        Returns:
            EvalRun with all results
        """
        timestamp = datetime.now()
        case_results = {}
        
        self.console.print(f"\n[bold cyan]Starting Vibe Eval V3[/bold cyan]")
        self.console.print(f"Models: {', '.join(self.models)}")
        self.console.print(f"Cases: {len(self.cases)}")
        self.console.print(f"Timeout: {self.timeout_minutes} min/case/model")
        self.console.print(f"Functional tests: {'enabled' if self.run_functional_tests else 'disabled'}\n")
        
        for case in self.cases:
            tier_label = f"[T{case.tier}]" if case.tier > 1 else ""
            self.console.print(f"\n[bold]Case: {case.name} {tier_label}[/bold]")
            
            # Run each model on this case
            workspaces = {}
            absolute_scores = {}
            metrics = {}
            agent_results = {}
            test_results = {}
            
            for model_id in self.models:
                self.console.print(f"  Running {model_id}...", end=" ")
                
                # Create workspace
                workspace = self.results_dir / timestamp.strftime("%Y%m%d_%H%M%S") / case.name / model_id.replace("/", "_").replace(".", "_")
                workspace.mkdir(parents=True, exist_ok=True)
                
                # Run agent loop
                try:
                    model = get_model(model_id)
                    agent = AgentLoop(
                        model=model,
                        spec=case.spec,
                        timeout_minutes=self.timeout_minutes,
                        workspace=workspace,
                        enable_tools=True  # V3: Enable extended tools
                    )
                    result = agent.run()
                    agent_results[model_id] = result
                    
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
                    
                    # Capture metrics (V3: include agent metrics)
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
            
            # V3: Run functional tests (if available)
            if self.run_functional_tests and case.has_tests:
                self.console.print("  Running tests...", end=" ")
                test_file = self.cases_dir / case.name / "tests.py"
                
                for model_id, workspace in workspaces.items():
                    try:
                        test_result = self.test_runner.run_tests(workspace, test_file)
                        test_results[model_id] = test_result
                    except Exception as e:
                        self.console.print(f"\n    [yellow]{model_id}: test error - {e}[/yellow]", end="")
                
                self.console.print("[green]done[/green]")
                
                # Show test summary
                for model_id, tr in test_results.items():
                    if tr.total_tests > 0:
                        pass_pct = tr.pass_rate * 100
                        self.console.print(f"    {model_id}: {tr.passed}/{tr.total_tests} tests ({pass_pct:.0f}%)")
            
            # Run execution validation
            execution_reports = {}
            if self.validator:
                self.console.print("  Validating execution...", end=" ")
                for model_id, workspace in workspaces.items():
                    exec_report = self.validator.validate(workspace)
                    execution_reports[model_id] = exec_report
                    if not exec_report.executed:
                        self.console.print(f"\n    [yellow]{model_id}: execution failed[/yellow]", end="")
                self.console.print(" [green]done[/green]")

            # Score with judge
            self.console.print("  Scoring...", end=" ")
            
            if self.use_v3_scoring:
                # V3: Use new scoring aggregator
                self._score_v3(
                    case, workspaces, absolute_scores, metrics,
                    agent_results, test_results, execution_reports
                )
            else:
                # V2: Use existing judge system
                self._score_v2(
                    case, workspaces, absolute_scores, metrics,
                    execution_reports
                )
            
            self.console.print("[green]done[/green]")

            # Head-to-head comparisons (opt-in)
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
                winner=None
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

        # Cleanup
        self._cleanup()

        return eval_run

    def _score_v2(
        self,
        case: EvalCase,
        workspaces: dict,
        absolute_scores: dict,
        metrics: dict,
        execution_reports: dict,
    ):
        """V2 scoring using multi-judge or single judge."""
        for model_id, workspace in workspaces.items():
            multi_score = None
            if self.multi_judge_enabled:
                multi_score = self.multi_judge.score(
                    spec=case.spec,
                    workspace=workspace,
                    criteria=case.criteria
                )
                dims = multi_score.aggregated_dimensions
                score = AbsoluteScore(
                    executes=DimensionScore(int(dims.get("executes", 0)), "Multi-judge aggregated"),
                    features_complete=DimensionScore(int(dims.get("features_complete", 0)), "Multi-judge aggregated"),
                    output_quality=DimensionScore(int(dims.get("output_quality", 0)), "Multi-judge aggregated"),
                    direction_following=DimensionScore(int(dims.get("direction_following", 0)), "Multi-judge aggregated"),
                    code_quality=DimensionScore(int(dims.get("code_quality", 0)), "Multi-judge aggregated"),
                )

                if model_id in execution_reports and not execution_reports[model_id].executed:
                    score = AbsoluteScore(
                        executes=DimensionScore(min(score.executes.score, 2), f"Execution failed"),
                        features_complete=score.features_complete,
                        output_quality=score.output_quality,
                        direction_following=score.direction_following,
                        code_quality=score.code_quality,
                    )
            else:
                score = self.absolute_judge.score(
                    spec=case.spec,
                    workspace=workspace,
                    criteria=case.criteria
                )

                if model_id in execution_reports and not execution_reports[model_id].executed:
                    score = AbsoluteScore(
                        executes=DimensionScore(min(score.executes.score, 2), f"Execution failed"),
                        features_complete=score.features_complete,
                        output_quality=score.output_quality,
                        direction_following=score.direction_following,
                        code_quality=score.code_quality,
                    )

            absolute_scores[model_id] = score

            if model_id in metrics:
                if self.multi_judge_enabled and multi_score:
                    metrics[model_id].judge_tokens = multi_score.total_judge_tokens
                    metrics[model_id].judge_cost = multi_score.total_judge_cost
                elif score.judge_metrics:
                    metrics[model_id].judge_tokens = score.judge_metrics.total_tokens
                    metrics[model_id].judge_cost = score.judge_metrics.estimated_cost()

    def _score_v3(
        self,
        case: EvalCase,
        workspaces: dict,
        absolute_scores: dict,
        metrics: dict,
        agent_results: dict,
        test_results: dict,
        execution_reports: dict,
    ):
        """V3 scoring using aggregator with tests + static + judge."""
        from .scoring import ScoreAggregator, AutoScore
        from .scoring.static_scorer import StaticAnalyzer
        
        aggregator = ScoreAggregator(use_judge=True)
        analyzer = StaticAnalyzer()
        
        for model_id, workspace in workspaces.items():
            # Get auto score from test results
            auto_score = None
            if model_id in test_results:
                tr = test_results[model_id]
                auto_score = AutoScore(
                    test_pass_rate=tr.pass_rate,
                    tests_passed=tr.passed,
                    tests_failed=tr.failed,
                    tests_total=tr.total_tests,
                    execution_success=model_id not in execution_reports or execution_reports[model_id].executed,
                )
            
            # Get static analysis
            static_report = analyzer.analyze(workspace)
            
            # Get judge score
            judge_score = None
            if self.multi_judge_enabled:
                multi_score = self.multi_judge.score(
                    spec=case.spec,
                    workspace=workspace,
                    criteria=case.criteria
                )
                dims = multi_score.aggregated_dimensions
                judge_score = AbsoluteScore(
                    executes=DimensionScore(int(dims.get("executes", 0)), "Multi-judge"),
                    features_complete=DimensionScore(int(dims.get("features_complete", 0)), "Multi-judge"),
                    output_quality=DimensionScore(int(dims.get("output_quality", 0)), "Multi-judge"),
                    direction_following=DimensionScore(int(dims.get("direction_following", 0)), "Multi-judge"),
                    code_quality=DimensionScore(int(dims.get("code_quality", 0)), "Multi-judge"),
                )
            elif self.absolute_judge:
                judge_score = self.absolute_judge.score(
                    spec=case.spec,
                    workspace=workspace,
                    criteria=case.criteria
                )
            
            # Get agent metrics
            agent_metrics_dict = None
            if model_id in agent_results and agent_results[model_id].metrics:
                agent_metrics_dict = agent_results[model_id].metrics.to_dict()
            
            # Aggregate
            final_score = aggregator.aggregate(
                auto_score=auto_score,
                static_report=static_report,
                judge_score=judge_score,
                agent_metrics=agent_metrics_dict,
            )
            
            # Convert to AbsoluteScore for compatibility
            absolute_scores[model_id] = AbsoluteScore(
                executes=DimensionScore(
                    final_score.dimensions.get("executes", DimensionResult("executes", 5, 0.15, "")).score,
                    "V3 aggregated"
                ),
                features_complete=DimensionScore(
                    final_score.dimensions.get("features_complete", DimensionResult("features_complete", 5, 0.20, "")).score,
                    "V3 aggregated"
                ),
                output_quality=DimensionScore(
                    final_score.dimensions.get("edge_cases", DimensionResult("edge_cases", 5, 0.10, "")).score,
                    "V3 aggregated"
                ),
                direction_following=DimensionScore(
                    final_score.dimensions.get("direction_following", DimensionResult("direction_following", 5, 0.10, "")).score,
                    "V3 aggregated"
                ),
                code_quality=DimensionScore(
                    final_score.dimensions.get("code_quality", DimensionResult("code_quality", 5, 0.10, "")).score,
                    "V3 aggregated"
                ),
            )

    def _cleanup(self):
        """Clean up shared resources after evaluation run."""
        from .judge.absolute import clear_file_cache
        clear_file_cache()

        if self.validator:
            ExecutionValidator.cleanup()
        
        # V3: Clean up test runner
        if self.test_runner:
            from .sandbox.test_runner import FunctionalTestRunner
            FunctionalTestRunner.cleanup()
    
    def _save_results(self, run: EvalRun):
        """Save results to JSON file."""
        filename = f"{run.timestamp.strftime('%Y%m%d_%H%M%S')}_results.json"
        filepath = self.results_dir / filename
        
        data = {
            "timestamp": run.timestamp.isoformat(),
            "version": "3.0",  # V3 marker
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


# Import for V3 scoring compatibility
from .scoring.aggregator import DimensionResult
