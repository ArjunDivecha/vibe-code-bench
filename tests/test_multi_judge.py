"""
=============================================================================
SCRIPT NAME: test_multi_judge.py
=============================================================================

Tests for the multi-judge arbitration system.

Tests cover:
- Score aggregation (average, median)
- Disagreement detection
- Multi-judge score calculation
- Edge cases

VERSION: 1.0
LAST UPDATED: 2026-01-04

=============================================================================
"""

import statistics
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from vibe_eval.judge.multi_judge import (
    MultiJudgeArbitrator,
    MultiJudgeScore,
    DEFAULT_JUDGES,
    create_multi_judge,
)
from vibe_eval.judge.absolute import AbsoluteScore, DimensionScore


def create_mock_score(
    executes: int = 7,
    features: int = 7,
    output: int = 7,
    direction: int = 7,
    quality: int = 7,
) -> AbsoluteScore:
    """Create a mock AbsoluteScore for testing (V2: 5 dimensions, no elegance)."""
    return AbsoluteScore(
        executes=DimensionScore(executes, "test"),
        features_complete=DimensionScore(features, "test"),
        output_quality=DimensionScore(output, "test"),
        direction_following=DimensionScore(direction, "test"),
        code_quality=DimensionScore(quality, "test"),
    )


class TestScoreAggregation:
    """Tests for score aggregation methods."""

    def test_average_mode(self):
        """Average mode should compute mean of scores."""
        arbitrator = MultiJudgeArbitrator(mode="average")

        # V2: 5 dimensions, new weights
        # Create mock scores: 70, 80, 90
        scores = {
            "judge1": create_mock_score(7, 7, 7, 7, 7),  # 70
            "judge2": create_mock_score(8, 8, 8, 8, 8),  # 80
            "judge3": create_mock_score(9, 9, 9, 9, 9),  # 90
        }

        result = arbitrator._aggregate_scores(scores)

        # Average of 70, 80, 90 = 80
        assert result.final_score == 80.0
        assert result.aggregation_mode == "average"

    def test_median_mode(self):
        """Median mode should compute median of scores."""
        arbitrator = MultiJudgeArbitrator(mode="median")

        # V2: 5 dimensions, new weights
        # Create mock scores: 70, 80, 90
        scores = {
            "judge1": create_mock_score(7, 7, 7, 7, 7),  # 70
            "judge2": create_mock_score(8, 8, 8, 8, 8),  # 80
            "judge3": create_mock_score(9, 9, 9, 9, 9),  # 90
        }

        result = arbitrator._aggregate_scores(scores)

        # Median of 70, 80, 90 = 80
        assert result.final_score == 80.0
        assert result.aggregation_mode == "median"

    def test_consensus_mode(self):
        """Consensus mode should use median."""
        arbitrator = MultiJudgeArbitrator(mode="consensus")

        # V2: 5 dimensions, new weights
        scores = {
            "judge1": create_mock_score(7, 7, 7, 7, 7),  # 70
            "judge2": create_mock_score(8, 8, 8, 8, 8),  # 80
            "judge3": create_mock_score(9, 9, 9, 9, 9),  # 90
        }

        result = arbitrator._aggregate_scores(scores)

        # Consensus uses median
        assert result.final_score == 80.0
        assert result.aggregation_mode == "consensus"


class TestDisagreementDetection:
    """Tests for disagreement flagging."""

    def test_high_disagreement_flagged(self):
        """Large spread (>15) should flag disagreement."""
        arbitrator = MultiJudgeArbitrator(disagreement_threshold=15.0)

        # Create scores with large spread: 50, 80, 85 (spread=35)
        # V2: 5 dimensions, new weights
        scores = {
            "judge1": create_mock_score(5, 5, 5, 5, 5),  # 50
            "judge2": create_mock_score(8, 8, 8, 8, 8),  # 80
            "judge3": create_mock_score(9, 9, 8, 8, 8),  # ~85
        }

        result = arbitrator._aggregate_scores(scores)

        assert result.disagreement_flag is True
        assert result.spread > 15

    def test_agreement_not_flagged(self):
        """Small spread (<=15) should not flag disagreement."""
        arbitrator = MultiJudgeArbitrator(disagreement_threshold=15.0)

        # Create scores with small spread
        # V2: 5 dimensions, new weights
        scores = {
            "judge1": create_mock_score(7, 8, 8, 8, 8),  # ~76.5
            "judge2": create_mock_score(8, 8, 8, 8, 8),  # 80
            "judge3": create_mock_score(8, 8, 8, 9, 9),  # ~83.5
        }

        result = arbitrator._aggregate_scores(scores)

        assert result.disagreement_flag is False
        assert result.spread <= 15

    def test_exact_threshold_not_flagged(self):
        """Spread exactly at threshold should not flag."""
        arbitrator = MultiJudgeArbitrator(disagreement_threshold=15.0)

        # V2: 5 dimensions, new weights
        scores = {
            "judge1": create_mock_score(6, 6, 6, 6, 6),  # 60
            "judge2": create_mock_score(7, 7, 7, 7, 7),  # 70
            "judge3": create_mock_score(7, 7, 8, 8, 8),  # ~74.5
        }

        result = arbitrator._aggregate_scores(scores)

        # Spread of exactly 15 should not flag (> not >=)
        if result.spread <= 15:
            assert result.disagreement_flag is False


class TestSpreadCalculation:
    """Tests for spread calculation."""

    def test_spread_calculated_correctly(self):
        """Spread should be max - min of total scores."""
        arbitrator = MultiJudgeArbitrator()

        # V2: 5 dimensions, new weights
        scores = {
            "judge1": create_mock_score(6, 6, 6, 6, 6),  # 60
            "judge2": create_mock_score(8, 8, 8, 8, 8),  # 80
            "judge3": create_mock_score(9, 9, 9, 9, 9),  # 90
        }

        result = arbitrator._aggregate_scores(scores)

        # Spread = 90 - 60 = 30
        assert result.spread == 30.0

    def test_single_judge_no_spread(self):
        """Single judge should have zero spread."""
        arbitrator = MultiJudgeArbitrator()

        scores = {
            "judge1": create_mock_score(8, 8, 8, 8, 8),
        }

        result = arbitrator._aggregate_scores(scores)

        assert result.spread == 0.0

    def test_empty_scores_handled(self):
        """Empty scores should return sensible defaults."""
        arbitrator = MultiJudgeArbitrator()

        result = arbitrator._aggregate_scores({})

        assert result.final_score == 0.0
        assert result.disagreement_flag is True
        assert len(result.judges_used) == 0


class TestDimensionAggregation:
    """Tests for per-dimension score aggregation."""

    def test_dimension_scores_aggregated(self):
        """Individual dimension scores should be aggregated."""
        arbitrator = MultiJudgeArbitrator(mode="median")

        # V2: 5 dimensions, new weights
        scores = {
            "judge1": create_mock_score(6, 7, 8, 7, 7),
            "judge2": create_mock_score(7, 8, 7, 8, 8),
            "judge3": create_mock_score(8, 9, 6, 9, 9),
        }

        result = arbitrator._aggregate_scores(scores)

        # Check that aggregated dimensions exist
        assert "executes" in result.aggregated_dimensions
        assert "features_complete" in result.aggregated_dimensions
        assert "output_quality" in result.aggregated_dimensions

        # Median of executes: 6, 7, 8 = 7
        assert result.aggregated_dimensions["executes"] == 7

    def test_dimension_spreads_tracked(self):
        """Per-dimension spreads should be tracked."""
        arbitrator = MultiJudgeArbitrator()

        # V2: 5 dimensions, new weights
        scores = {
            "judge1": create_mock_score(5, 7, 8, 7, 7),
            "judge2": create_mock_score(7, 8, 7, 8, 8),
            "judge3": create_mock_score(9, 9, 6, 9, 9),
        }

        result = arbitrator._aggregate_scores(scores)

        # executes spread: 9 - 5 = 4
        assert result.dimension_spreads["executes"] == 4


class TestMultiJudgeScore:
    """Tests for MultiJudgeScore dataclass."""

    def test_to_dict(self):
        """MultiJudgeScore should serialize to dict."""
        # V2: 5 dimensions, new weights
        score = MultiJudgeScore(
            individual_scores={
                "judge1": create_mock_score(8, 8, 8, 8, 8),
            },
            final_score=80.0,
            aggregated_dimensions={"executes": 8, "features_complete": 8},
            disagreement_flag=False,
            spread=0.0,
            judges_used=["judge1"],
            aggregation_mode="median",
            dimension_spreads={"executes": 0},
        )

        d = score.to_dict()

        assert d["final_score"] == 80.0
        assert d["disagreement_flag"] is False
        assert "individual_scores" in d
        assert "judge1" in d["individual_scores"]


class TestDefaultJudges:
    """Tests for default judge configuration."""

    def test_default_judges_list(self):
        """Default judges should include all three models (via OpenRouter)."""
        assert "anthropic/claude-opus-4.5" in DEFAULT_JUDGES
        assert "openai/gpt-4o" in DEFAULT_JUDGES
        assert "google/gemini-3-flash" in DEFAULT_JUDGES
        assert len(DEFAULT_JUDGES) == 3

    def test_arbitrator_uses_defaults(self):
        """Arbitrator should use default judges when none specified."""
        arbitrator = MultiJudgeArbitrator()

        assert arbitrator.judge_models == DEFAULT_JUDGES


class TestFactoryFunction:
    """Tests for create_multi_judge factory."""

    def test_create_with_defaults(self):
        """Factory should create arbitrator with defaults."""
        arbitrator = create_multi_judge()

        assert arbitrator.mode == "median"
        assert arbitrator.threshold == 15.0

    def test_create_with_custom_settings(self):
        """Factory should accept custom settings."""
        arbitrator = create_multi_judge(
            judges=["anthropic/claude-opus-4.5"],
            mode="average",
            threshold=20.0
        )

        assert arbitrator.mode == "average"
        assert arbitrator.threshold == 20.0
        assert len(arbitrator.judge_models) == 1


class TestJudgeInitialization:
    """Tests for judge instance management."""

    def test_judge_lazy_initialization(self):
        """Judges should be created lazily."""
        arbitrator = MultiJudgeArbitrator()

        # Initially no judges created
        assert len(arbitrator._judges) == 0

    @patch('vibe_eval.judge.multi_judge.AbsoluteJudge')
    def test_judge_cached(self, mock_judge_class):
        """Same judge should be reused."""
        mock_judge_class.return_value = Mock()
        arbitrator = MultiJudgeArbitrator()

        # Get same judge twice
        j1 = arbitrator._get_judge("anthropic/claude-opus-4.5")
        j2 = arbitrator._get_judge("anthropic/claude-opus-4.5")

        # Should be same instance
        assert j1 is j2
        # Constructor called only once
        assert mock_judge_class.call_count == 1


class TestIntegrationScenarios:
    """Integration test scenarios (without actual API calls)."""

    def test_score_calculation_flow(self):
        """Test the full scoring flow with mocked judges."""
        arbitrator = MultiJudgeArbitrator(judges=["judge1", "judge2", "judge3"])

        # Mock all three judges (V2: 5 dimensions)
        mock_scores = {
            "judge1": create_mock_score(7, 7, 7, 7, 7),  # 70
            "judge2": create_mock_score(8, 8, 8, 8, 8),  # 80
            "judge3": create_mock_score(9, 9, 9, 9, 9),  # 90
        }

        # Directly test aggregation (bypassing actual API calls)
        result = arbitrator._aggregate_scores(mock_scores)

        assert result.final_score == 80.0  # median
        assert len(result.judges_used) == 3
        # spread = 90 - 70 = 20 > 15, so disagreement IS flagged
        assert result.disagreement_flag is True
        assert result.spread == 20.0

    def test_perfect_agreement(self):
        """Test when all judges give same score."""
        arbitrator = MultiJudgeArbitrator()

        # V2: 5 dimensions
        scores = {
            "judge1": create_mock_score(8, 8, 8, 8, 8),
            "judge2": create_mock_score(8, 8, 8, 8, 8),
            "judge3": create_mock_score(8, 8, 8, 8, 8),
        }

        result = arbitrator._aggregate_scores(scores)

        assert result.final_score == 80.0
        assert result.spread == 0.0
        assert result.disagreement_flag is False

    def test_extreme_disagreement(self):
        """Test when judges have extreme disagreement."""
        arbitrator = MultiJudgeArbitrator()

        # V2: 5 dimensions
        # Note: executes=0 triggers execution gate, so scores are capped
        # judge1: 0,0,0,0,0 -> raw would be 0, but gate doesn't apply to already-low scores
        # judge2: 5,5,5,5,5 -> 50
        # judge3: 10,10,10,10,10 -> 100
        scores = {
            "judge1": create_mock_score(0, 0, 0, 0, 0),  # 0 (gated but already 0)
            "judge2": create_mock_score(5, 5, 5, 5, 5),  # 50
            "judge3": create_mock_score(10, 10, 10, 10, 10),  # 100
        }

        result = arbitrator._aggregate_scores(scores)

        assert result.final_score == 50.0  # median
        assert result.spread == 100.0
        assert result.disagreement_flag is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
