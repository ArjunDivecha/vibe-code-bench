"""
=============================================================================
SCRIPT NAME: multi_judge.py
=============================================================================

Multi-judge arbitration system for unbiased evaluation.

Runs multiple judges (Claude Opus, GPT-4o, Gemini) and aggregates scores
to reduce single-model bias.

VERSION: 1.0
LAST UPDATED: 2026-01-04

DESCRIPTION:
This module provides a multi-judge system that:
1. Scores outputs using multiple LLM judges
2. Aggregates scores using average, median, or consensus
3. Flags disagreements when score spread exceeds threshold
4. Reduces potential bias from single-model judging

DEPENDENCIES:
- statistics (stdlib)
- dataclasses (stdlib)
- typing (stdlib)

=============================================================================
"""

import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from .absolute import AbsoluteJudge, AbsoluteScore, DimensionScore, JudgeMetrics


# Available judge models (via OpenRouter - only requires OPENROUTER_API_KEY)
JudgeModel = Literal[
    "anthropic/claude-opus-4.5",
    "openai/gpt-4o",
    "google/gemini-3-flash"
]

# V2: All judges go through OpenRouter (single API key)
DEFAULT_JUDGES = [
    "anthropic/claude-opus-4.5",       # Claude Opus 4.5
    "openai/gpt-4o",                   # GPT-4o
    "google/gemini-3-flash"            # Gemini 3 Flash
]

# Aggregation modes
AggregationMode = Literal["average", "median", "consensus"]


@dataclass
class MultiJudgeScore:
    """Result from multi-judge arbitration."""

    # Individual scores from each judge
    individual_scores: dict[str, AbsoluteScore]

    # Final aggregated score
    final_score: float

    # Aggregated dimension scores (for detailed breakdown)
    aggregated_dimensions: dict[str, float]

    # Whether judges disagreed significantly
    disagreement_flag: bool = False

    # Spread between highest and lowest total scores
    spread: float = 0.0

    # Which judges participated
    judges_used: list[str] = field(default_factory=list)

    # Aggregation mode used
    aggregation_mode: str = "median"

    # Detailed disagreement info (per-dimension spreads)
    dimension_spreads: dict[str, float] = field(default_factory=dict)

    # V2: Total judge cost across all judges
    total_judge_tokens: int = 0
    total_judge_cost: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "individual_scores": {
                judge: score.to_dict()
                for judge, score in self.individual_scores.items()
            },
            "final_score": self.final_score,
            "aggregated_dimensions": self.aggregated_dimensions,
            "disagreement_flag": self.disagreement_flag,
            "spread": self.spread,
            "judges_used": self.judges_used,
            "aggregation_mode": self.aggregation_mode,
            "dimension_spreads": self.dimension_spreads,
            # V2: Judge cost tracking
            "total_judge_tokens": self.total_judge_tokens,
            "total_judge_cost": self.total_judge_cost,
        }


class MultiJudgeArbitrator:
    """
    Multi-judge arbitration system for unbiased evaluation.

    Runs multiple judges and aggregates scores to reduce bias.

    Scoring modes:
    - 'average': Mean of all judge scores
    - 'median': Median score (robust to outliers) [DEFAULT]
    - 'consensus': Require agreement within threshold
    """

    def __init__(
        self,
        judges: Optional[list[str]] = None,
        mode: AggregationMode = "median",
        disagreement_threshold: float = 15.0,
        temperature: float = 0.0,
    ):
        """
        Initialize multi-judge arbitrator.

        Args:
            judges: List of judge model IDs. Defaults to all three.
            mode: Aggregation mode ('average', 'median', 'consensus')
            disagreement_threshold: Flag if scores differ by more than this
            temperature: Sampling temperature for judges
        """
        self.judge_models = judges or DEFAULT_JUDGES.copy()
        self.mode = mode
        self.threshold = disagreement_threshold
        self.temperature = temperature

        # Pre-initialize judge instances
        self._judges: dict[str, AbsoluteJudge] = {}

    def _get_judge(self, model_id: str) -> AbsoluteJudge:
        """Get or create a judge instance for a model."""
        if model_id not in self._judges:
            self._judges[model_id] = AbsoluteJudge(
                judge_model=model_id,
                temperature=self.temperature
            )
        return self._judges[model_id]

    def score(
        self,
        spec: str,
        workspace: Path,
        criteria: Optional[str] = None,
    ) -> MultiJudgeScore:
        """
        Score output using multiple judges and aggregate.

        Args:
            spec: Original task specification
            workspace: Directory containing generated code
            criteria: Optional additional evaluation criteria

        Returns:
            MultiJudgeScore with aggregated results
        """
        individual_scores: dict[str, AbsoluteScore] = {}

        # Get scores from each judge
        for model_id in self.judge_models:
            try:
                judge = self._get_judge(model_id)
                score = judge.score(spec, workspace, criteria)
                individual_scores[model_id] = score
            except Exception as e:
                # If a judge fails, continue with others
                # Create a zero score to indicate failure (V2: 5 dimensions)
                individual_scores[model_id] = AbsoluteScore(
                    executes=DimensionScore(0, f"Judge error: {e}"),
                    features_complete=DimensionScore(0, "Judge failed"),
                    output_quality=DimensionScore(0, "Judge failed"),
                    direction_following=DimensionScore(0, "Judge failed"),
                    code_quality=DimensionScore(0, "Judge failed"),
                )

        # Aggregate scores
        return self._aggregate_scores(individual_scores)

    def _aggregate_scores(
        self,
        scores: dict[str, AbsoluteScore]
    ) -> MultiJudgeScore:
        """
        Aggregate individual judge scores into final result.

        Args:
            scores: Dict mapping judge model to AbsoluteScore

        Returns:
            MultiJudgeScore with aggregated results
        """
        if not scores:
            return MultiJudgeScore(
                individual_scores={},
                final_score=0.0,
                aggregated_dimensions={},
                disagreement_flag=True,
                judges_used=[],
            )

        # Get total scores
        totals = [s.total_score for s in scores.values()]

        # Calculate spread
        spread = max(totals) - min(totals) if len(totals) > 1 else 0.0

        # Flag disagreement if spread exceeds threshold
        disagreement = spread > self.threshold

        # Calculate final score based on mode
        if self.mode == "average":
            final_score = statistics.mean(totals)
        elif self.mode == "median":
            final_score = statistics.median(totals)
        else:  # consensus
            final_score = self._consensus_score(totals)

        # Aggregate dimension scores (V2: elegance removed)
        dimensions = ["executes", "features_complete", "output_quality",
                     "direction_following", "code_quality"]

        aggregated_dims = {}
        dimension_spreads = {}

        for dim in dimensions:
            dim_scores = [getattr(s, dim).score for s in scores.values()]
            if self.mode == "average":
                aggregated_dims[dim] = statistics.mean(dim_scores)
            else:
                aggregated_dims[dim] = statistics.median(dim_scores)

            # Track per-dimension spread
            if len(dim_scores) > 1:
                dimension_spreads[dim] = max(dim_scores) - min(dim_scores)
            else:
                dimension_spreads[dim] = 0.0

        # V2: Calculate total judge cost across all judges
        total_tokens = 0
        total_cost = 0.0
        for score in scores.values():
            if score.judge_metrics:
                total_tokens += score.judge_metrics.total_tokens
                total_cost += score.judge_metrics.estimated_cost()

        return MultiJudgeScore(
            individual_scores=scores,
            final_score=round(final_score, 1),
            aggregated_dimensions=aggregated_dims,
            disagreement_flag=disagreement,
            spread=round(spread, 1),
            judges_used=list(scores.keys()),
            aggregation_mode=self.mode,
            dimension_spreads=dimension_spreads,
            total_judge_tokens=total_tokens,
            total_judge_cost=round(total_cost, 6),
        )

    def _consensus_score(self, totals: list[float]) -> float:
        """
        Calculate consensus score requiring agreement.

        If scores are within threshold, return median.
        Otherwise, return median but flag for manual review.

        Args:
            totals: List of total scores from judges

        Returns:
            Consensus score (median when in agreement)
        """
        # For consensus mode, we still use median but the disagreement
        # flag indicates if manual review is needed
        return statistics.median(totals)

    def score_single_judge(
        self,
        spec: str,
        workspace: Path,
        criteria: Optional[str] = None,
        judge_model: str = "claude-opus-4.5"
    ) -> AbsoluteScore:
        """
        Score using a single judge (fallback/legacy mode).

        Args:
            spec: Original task specification
            workspace: Directory containing generated code
            criteria: Optional additional evaluation criteria
            judge_model: Which judge to use

        Returns:
            AbsoluteScore from single judge
        """
        judge = self._get_judge(judge_model)
        return judge.score(spec, workspace, criteria)


def create_multi_judge(
    judges: Optional[list[str]] = None,
    mode: str = "median",
    threshold: float = 15.0
) -> MultiJudgeArbitrator:
    """
    Factory function to create a multi-judge arbitrator.

    Args:
        judges: List of judge models (defaults to all three)
        mode: Aggregation mode
        threshold: Disagreement threshold

    Returns:
        Configured MultiJudgeArbitrator
    """
    return MultiJudgeArbitrator(
        judges=judges,
        mode=mode,
        disagreement_threshold=threshold
    )
