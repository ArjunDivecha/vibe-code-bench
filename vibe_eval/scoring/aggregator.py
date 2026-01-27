"""
Score aggregation for V3 evaluation system.

Combines automated scores with LLM judge scores into final weighted score.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .auto_scorer import AutoScore
from .static_scorer import StaticReport
from ..judge.absolute import AbsoluteScore


@dataclass
class DimensionResult:
    """Result for a single scoring dimension."""
    name: str
    score: int  # 0-10
    weight: float  # Weight as decimal (e.g., 0.20 for 20%)
    source: str  # "auto", "judge", "static", or "combined"
    reason: str = ""
    
    @property
    def weighted_contribution(self) -> float:
        """Contribution to final score (out of 100)."""
        return (self.score / 10.0) * self.weight * 100


@dataclass
class FinalScore:
    """
    Final aggregated score combining all scoring sources.
    
    V3 Scoring Dimensions:
    - executes (15%): Code runs without errors
    - test_pass_rate (20%): Functional tests passing
    - features_complete (20%): All spec features implemented
    - edge_cases (10%): Handles errors, validation
    - code_quality (10%): Readable, well-organized
    - efficiency (5%): Minimal turns, smart tool use
    - direction_following (10%): Built what was asked
    - robustness (10%): Works across scenarios
    """
    
    # Individual dimension results
    dimensions: dict[str, DimensionResult] = field(default_factory=dict)
    
    # Source scores
    auto_score: Optional[AutoScore] = None
    static_report: Optional[StaticReport] = None
    judge_score: Optional[AbsoluteScore] = None
    
    # Flags
    execution_gated: bool = False  # Score capped due to execution failure
    
    # V3 Weights (must sum to 1.0)
    WEIGHTS = {
        "executes": 0.15,
        "test_pass_rate": 0.20,
        "features_complete": 0.20,
        "edge_cases": 0.10,
        "code_quality": 0.10,
        "efficiency": 0.05,
        "direction_following": 0.10,
        "robustness": 0.10,
    }
    
    # Execution gate thresholds
    EXECUTION_GATE_THRESHOLD = 3
    EXECUTION_GATE_CAP = 30
    
    @property
    def total_score(self) -> float:
        """Calculate final weighted score (0-100)."""
        total = sum(dim.weighted_contribution for dim in self.dimensions.values())
        
        # Apply execution gate
        if self.execution_gated:
            total = min(total, self.EXECUTION_GATE_CAP)
        
        return round(total, 1)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_score": self.total_score,
            "execution_gated": self.execution_gated,
            "dimensions": {
                name: {
                    "score": dim.score,
                    "weight": dim.weight,
                    "weighted_contribution": round(dim.weighted_contribution, 1),
                    "source": dim.source,
                    "reason": dim.reason,
                }
                for name, dim in self.dimensions.items()
            },
            "auto_score": self.auto_score.to_dict() if self.auto_score else None,
            "static_report": self.static_report.to_dict() if self.static_report else None,
        }


class ScoreAggregator:
    """
    Aggregates scores from multiple sources into final score.
    
    Sources:
    - AutoScorer: Test pass rates, execution validation
    - StaticAnalyzer: Code quality metrics
    - AbsoluteJudge: LLM-based evaluation of features and quality
    """
    
    def __init__(self, use_judge: bool = True):
        """
        Initialize aggregator.
        
        Args:
            use_judge: Whether to include LLM judge scores
        """
        self.use_judge = use_judge
    
    def aggregate(
        self,
        auto_score: Optional[AutoScore] = None,
        static_report: Optional[StaticReport] = None,
        judge_score: Optional[AbsoluteScore] = None,
        agent_metrics: Optional[dict] = None,
    ) -> FinalScore:
        """
        Aggregate all scores into final result.
        
        Args:
            auto_score: Results from functional tests
            static_report: Results from static analysis
            judge_score: Results from LLM judge
            agent_metrics: Metrics from agent loop (for efficiency)
            
        Returns:
            FinalScore with all dimensions
        """
        final = FinalScore(
            auto_score=auto_score,
            static_report=static_report,
            judge_score=judge_score,
        )
        
        # 1. Executes (15%) - from auto scorer
        executes_score = 5  # Default
        if auto_score:
            executes_score = auto_score.execution_score
        final.dimensions["executes"] = DimensionResult(
            name="executes",
            score=executes_score,
            weight=FinalScore.WEIGHTS["executes"],
            source="auto",
            reason="Based on execution validation"
        )
        
        # 2. Test pass rate (20%) - from auto scorer
        test_score = 0
        if auto_score:
            test_score = auto_score.test_score
        final.dimensions["test_pass_rate"] = DimensionResult(
            name="test_pass_rate",
            score=test_score,
            weight=FinalScore.WEIGHTS["test_pass_rate"],
            source="auto",
            reason=f"{auto_score.tests_passed}/{auto_score.tests_total} tests passed" if auto_score else "No tests"
        )
        
        # 3. Features complete (20%) - from judge
        features_score = 5  # Default
        if judge_score:
            features_score = judge_score.features_complete.score
        final.dimensions["features_complete"] = DimensionResult(
            name="features_complete",
            score=features_score,
            weight=FinalScore.WEIGHTS["features_complete"],
            source="judge",
            reason=judge_score.features_complete.reason if judge_score else "No judge score"
        )
        
        # 4. Edge cases (10%) - combined from tests and judge
        edge_score = 5  # Default
        if auto_score and auto_score.tests_total > 0:
            # If we have edge case tests, weight toward test results
            edge_score = auto_score.test_score
        elif judge_score:
            # Fall back to judge output quality
            edge_score = judge_score.output_quality.score
        final.dimensions["edge_cases"] = DimensionResult(
            name="edge_cases",
            score=edge_score,
            weight=FinalScore.WEIGHTS["edge_cases"],
            source="combined",
            reason="Based on test results and output quality"
        )
        
        # 5. Code quality (10%) - from static analysis and judge
        quality_score = 5  # Default
        if static_report:
            quality_score = static_report.quality_score
            # Blend with judge if available
            if judge_score:
                quality_score = (quality_score + judge_score.code_quality.score) // 2
        elif judge_score:
            quality_score = judge_score.code_quality.score
        final.dimensions["code_quality"] = DimensionResult(
            name="code_quality",
            score=quality_score,
            weight=FinalScore.WEIGHTS["code_quality"],
            source="combined" if static_report and judge_score else ("static" if static_report else "judge"),
            reason="Based on static analysis and code review"
        )
        
        # 6. Efficiency (5%) - from agent metrics
        efficiency_score = 7  # Default (decent)
        if agent_metrics:
            turns = agent_metrics.get("turns", 1)
            backtrack = agent_metrics.get("backtrack_count", 0)
            
            # Score based on turns (1 turn = 10, >5 turns = lower)
            if turns == 1:
                efficiency_score = 10
            elif turns <= 3:
                efficiency_score = 8
            elif turns <= 5:
                efficiency_score = 6
            else:
                efficiency_score = max(3, 10 - turns)
            
            # Penalize backtracking
            efficiency_score = max(0, efficiency_score - backtrack)
            
        final.dimensions["efficiency"] = DimensionResult(
            name="efficiency",
            score=efficiency_score,
            weight=FinalScore.WEIGHTS["efficiency"],
            source="metrics",
            reason=f"Based on {agent_metrics.get('turns', '?')} turns" if agent_metrics else "No metrics"
        )
        
        # 7. Direction following (10%) - from judge
        direction_score = 5  # Default
        if judge_score:
            direction_score = judge_score.direction_following.score
        final.dimensions["direction_following"] = DimensionResult(
            name="direction_following",
            score=direction_score,
            weight=FinalScore.WEIGHTS["direction_following"],
            source="judge",
            reason=judge_score.direction_following.reason if judge_score else "No judge score"
        )
        
        # 8. Robustness (10%) - from tests (edge cases, error handling)
        robustness_score = 5  # Default
        if auto_score:
            # Higher test pass rate = more robust
            robustness_score = auto_score.test_score
        if static_report and static_report.has_error_handling:
            # Bonus for error handling
            robustness_score = min(10, robustness_score + 1)
        final.dimensions["robustness"] = DimensionResult(
            name="robustness",
            score=robustness_score,
            weight=FinalScore.WEIGHTS["robustness"],
            source="combined",
            reason="Based on test coverage and error handling"
        )
        
        # Apply execution gate
        if executes_score < FinalScore.EXECUTION_GATE_THRESHOLD:
            final.execution_gated = True
        if test_score < FinalScore.EXECUTION_GATE_THRESHOLD and auto_score and auto_score.tests_total > 0:
            final.execution_gated = True
        
        return final
    
    def score_workspace(
        self,
        workspace: Path,
        case_dir: Optional[Path] = None,
        spec: Optional[str] = None,
        agent_metrics: Optional[dict] = None,
    ) -> FinalScore:
        """
        Convenience method to score a workspace with all available methods.
        
        Args:
            workspace: Directory containing generated code
            case_dir: Case directory with tests.py
            spec: Original specification (for judge)
            agent_metrics: Metrics from agent run
            
        Returns:
            FinalScore with all dimensions
        """
        from .auto_scorer import AutoScorer
        from .static_scorer import StaticAnalyzer
        
        # Run auto scorer
        auto_scorer = AutoScorer()
        auto_score = auto_scorer.score(workspace, case_dir=case_dir)
        
        # Run static analyzer
        analyzer = StaticAnalyzer()
        static_report = analyzer.analyze(workspace)
        
        # Get judge score if enabled and spec provided
        judge_score = None
        if self.use_judge and spec:
            from ..judge.absolute import AbsoluteJudge
            judge = AbsoluteJudge()
            judge_score = judge.score(spec, workspace)
        
        return self.aggregate(
            auto_score=auto_score,
            static_report=static_report,
            judge_score=judge_score,
            agent_metrics=agent_metrics,
        )
