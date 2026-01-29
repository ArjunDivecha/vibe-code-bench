"""
=============================================================================
SCRIPT NAME: multi_judge.py
=============================================================================

Multi-judge arbitration system - aggregates scores from multiple judges.

VERSION: 2.0
LAST UPDATED: 2026-01-04

CHANGES IN V2:
- Uses 3 default judges via OpenRouter
- Supports average, median, consensus aggregation modes
- Tracks disagreement flags when judges disagree significantly

=============================================================================
"""

import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List

from .absolute import AbsoluteJudge, AbsoluteScore

# V2: Default judges via OpenRouter
DEFAULT_JUDGES = [
    "anthropic/claude-opus-4.5",
    "openai/gpt-4o",
    "google/gemini-3-flash-preview",
]


@dataclass
class MultiJudgeScore:
    """Result from multi-judge arbitration."""
    individual_scores: Dict[str, AbsoluteScore]
    final_score: float
    aggregated_dimensions: Dict[str, int]
    disagreement_flag: bool
    spread: float
    judges_used: List[str]
    aggregation_mode: str
    dimension_spreads: Dict[str, int] = field(default_factory=dict)

    @property
    def total_judge_tokens(self) -> int:
        """Total tokens used across all judges."""
        total = 0
        for score in self.individual_scores.values():
            if score.judge_metrics:
                total += score.judge_metrics.total_tokens
        return total

    @property
    def total_judge_cost(self) -> float:
        """Total cost across all judges."""
        total = 0.0
        for score in self.individual_scores.values():
            if score.judge_metrics:
                total += score.judge_metrics.estimated_cost()
        return round(total, 6)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "individual_scores": {
                judge: score.to_dict() for judge, score in self.individual_scores.items()
            },
            "final_score": self.final_score,
            "aggregated_dimensions": self.aggregated_dimensions,
            "disagreement_flag": self.disagreement_flag,
            "spread": self.spread,
            "judges_used": self.judges_used,
            "aggregation_mode": self.aggregation_mode,
            "dimension_spreads": self.dimension_spreads,
        }


class MultiJudgeArbitrator:
    """
    Arbitrator that aggregates scores from multiple judges.
    
    Uses multiple AbsoluteJudge instances and aggregates their scores
    using median (default), average, or consensus mode.
    """
    
    def __init__(
        self,
        judges: Optional[List[str]] = None,
        mode: str = "median",
        disagreement_threshold: float = 15.0,
    ):
        """
        Initialize multi-judge arbitrator.
        
        Args:
            judges: List of judge model IDs (defaults to DEFAULT_JUDGES)
            mode: Aggregation mode - "median", "average", or "consensus"
            disagreement_threshold: Score spread threshold to flag disagreement
        """
        self.judge_models = judges or DEFAULT_JUDGES.copy()
        self.mode = mode
        self.threshold = disagreement_threshold
        self._judges: Dict[str, AbsoluteJudge] = {}
    
    def _get_judge(self, model_id: str) -> AbsoluteJudge:
        """Get or create judge instance (cached)."""
        if model_id not in self._judges:
            self._judges[model_id] = AbsoluteJudge(judge_model=model_id)
        return self._judges[model_id]
    
    def score(
        self,
        spec: str,
        workspace: Path,
        criteria: Optional[str] = None
    ) -> MultiJudgeScore:
        """
        Score workspace using multiple judges and aggregate results.
        
        Args:
            spec: Original task specification
            workspace: Directory containing generated code
            criteria: Optional additional evaluation criteria
            
        Returns:
            MultiJudgeScore with aggregated results
        """
        # Get scores from all judges
        individual_scores = {}
        for judge_model in self.judge_models:
            try:
                judge = self._get_judge(judge_model)
                score = judge.score(spec, workspace, criteria)
                individual_scores[judge_model] = score
            except Exception as e:
                # If a judge fails, skip it (but log)
                print(f"Warning: Judge {judge_model} failed: {e}")
                continue
        
        if not individual_scores:
            # All judges failed - return zero score
            return MultiJudgeScore(
                individual_scores={},
                final_score=0.0,
                aggregated_dimensions={},
                disagreement_flag=True,
                spread=0.0,
                judges_used=[],
                aggregation_mode=self.mode,
            )
        
        # Aggregate scores
        return self._aggregate_scores(individual_scores)
    
    def _aggregate_scores(self, scores: Dict[str, AbsoluteScore]) -> MultiJudgeScore:
        """
        Aggregate scores from multiple judges.
        
        Args:
            scores: Dictionary mapping judge model IDs to AbsoluteScore objects
            
        Returns:
            MultiJudgeScore with aggregated results
        """
        if not scores:
            return MultiJudgeScore(
                individual_scores={},
                final_score=0.0,
                aggregated_dimensions={},
                disagreement_flag=True,
                spread=0.0,
                judges_used=[],
                aggregation_mode=self.mode,
            )
        
        # Collect total scores
        total_scores = [score.total_score for score in scores.values()]
        
        # Calculate final score based on mode
        if self.mode == "average":
            final_score = statistics.mean(total_scores)
        elif self.mode == "consensus":
            # Consensus uses median
            final_score = statistics.median(total_scores)
        else:  # median (default)
            final_score = statistics.median(total_scores)
        
        # Calculate spread (max - min)
        spread = max(total_scores) - min(total_scores) if len(total_scores) > 1 else 0.0
        
        # Flag disagreement if spread exceeds threshold
        disagreement_flag = spread > self.threshold
        
        # Aggregate dimension scores (use median for each dimension)
        dimension_names = ["executes", "features_complete", "output_quality", 
                          "direction_following", "code_quality"]
        aggregated_dimensions = {}
        dimension_spreads = {}
        
        for dim_name in dimension_names:
            dim_scores = [getattr(score, dim_name).score for score in scores.values()]
            aggregated_dimensions[dim_name] = int(statistics.median(dim_scores))
            if len(dim_scores) > 1:
                dimension_spreads[dim_name] = max(dim_scores) - min(dim_scores)
            else:
                dimension_spreads[dim_name] = 0
        
        return MultiJudgeScore(
            individual_scores=scores,
            final_score=round(final_score, 1),
            aggregated_dimensions=aggregated_dimensions,
            disagreement_flag=disagreement_flag,
            spread=round(spread, 1),
            judges_used=list(scores.keys()),
            aggregation_mode=self.mode,
            dimension_spreads=dimension_spreads,
        )


def create_multi_judge(
    judges: Optional[List[str]] = None,
    mode: str = "median",
    threshold: float = 15.0,
) -> MultiJudgeArbitrator:
    """
    Factory function to create MultiJudgeArbitrator with defaults.
    
    Args:
        judges: List of judge model IDs (defaults to DEFAULT_JUDGES)
        mode: Aggregation mode - "median", "average", or "consensus"
        threshold: Score spread threshold to flag disagreement
        
    Returns:
        Configured MultiJudgeArbitrator instance
    """
    return MultiJudgeArbitrator(
        judges=judges,
        mode=mode,
        disagreement_threshold=threshold,
    )
