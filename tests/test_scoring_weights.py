"""
=============================================================================
SCRIPT NAME: test_scoring_weights.py
=============================================================================

Tests for rebalanced scoring weights and execution gate.

Tests cover:
- New weight calculations (elegance removed)
- Execution gate (non-running code capped at 30)
- Weight sum verification
- Score calculation edge cases

VERSION: 1.0
LAST UPDATED: 2026-01-04

=============================================================================
"""

import pytest
from vibe_eval.judge.absolute import AbsoluteScore, DimensionScore


def create_score(
    executes: int = 7,
    features: int = 7,
    output: int = 7,
    direction: int = 7,
    quality: int = 7,
) -> AbsoluteScore:
    """Create an AbsoluteScore for testing."""
    return AbsoluteScore(
        executes=DimensionScore(executes, "test"),
        features_complete=DimensionScore(features, "test"),
        output_quality=DimensionScore(output, "test"),
        direction_following=DimensionScore(direction, "test"),
        code_quality=DimensionScore(quality, "test"),
    )


class TestWeightConfiguration:
    """Tests for weight configuration."""

    def test_weights_sum_to_100(self):
        """All weights should sum to exactly 100."""
        total = sum(AbsoluteScore.WEIGHTS.values())
        assert total == 100, f"Weights sum to {total}, expected 100"

    def test_elegance_removed(self):
        """Elegance dimension should not be in weights."""
        assert "elegance" not in AbsoluteScore.WEIGHTS

    def test_five_dimensions(self):
        """Should have exactly 5 dimensions."""
        assert len(AbsoluteScore.WEIGHTS) == 5

    def test_executes_weight_increased(self):
        """Executes weight should be 25 (increased from 15)."""
        assert AbsoluteScore.WEIGHTS["executes"] == 25

    def test_code_quality_weight_increased(self):
        """Code quality weight should be 15 (increased from 10)."""
        assert AbsoluteScore.WEIGHTS["code_quality"] == 15

    def test_output_quality_weight_reduced(self):
        """Output quality weight should be 20 (reduced from 25)."""
        assert AbsoluteScore.WEIGHTS["output_quality"] == 20

    def test_direction_following_weight_reduced(self):
        """Direction following weight should be 10 (reduced from 15)."""
        assert AbsoluteScore.WEIGHTS["direction_following"] == 10

    def test_features_complete_weight_unchanged(self):
        """Features complete weight should still be 30."""
        assert AbsoluteScore.WEIGHTS["features_complete"] == 30


class TestScoreCalculation:
    """Tests for total score calculation."""

    def test_perfect_score_is_100(self):
        """All 10s should give total of 100."""
        score = create_score(10, 10, 10, 10, 10)
        assert score.total_score == 100.0

    def test_all_zeros_is_0(self):
        """All 0s should give total of 0."""
        score = create_score(0, 0, 0, 0, 0)
        assert score.total_score == 0.0

    def test_all_fives_is_50(self):
        """All 5s should give total of 50."""
        score = create_score(5, 5, 5, 5, 5)
        assert score.total_score == 50.0

    def test_executes_weight_contribution(self):
        """Executes=10, rest=0 should give 25 (25% weight)."""
        score = create_score(10, 0, 0, 0, 0)
        # But execution gate will cap this since other dims are 0?
        # No - gate is only if executes < 3
        assert score.total_score == 25.0

    def test_features_weight_contribution(self):
        """Features=10, rest=0 should give 30 (30% weight)."""
        # executes=0 triggers gate, so we need executes >= 3
        score = create_score(0, 10, 0, 0, 0)
        # This triggers execution gate, capped at 30
        # But 30 * (10/10) = 30, so it's exactly at cap
        assert score.total_score == 30.0  # capped at 30 due to gate

    def test_mixed_scores_calculation(self):
        """Mixed scores should calculate correctly."""
        # executes=8 (8/10 * 25 = 20)
        # features=7 (7/10 * 30 = 21)
        # output=6 (6/10 * 20 = 12)
        # direction=5 (5/10 * 10 = 5)
        # quality=9 (9/10 * 15 = 13.5)
        # Total = 20 + 21 + 12 + 5 + 13.5 = 71.5
        score = create_score(8, 7, 6, 5, 9)
        assert score.total_score == 71.5

    def test_score_rounded_to_one_decimal(self):
        """Score should be rounded to one decimal place."""
        score = create_score(7, 7, 7, 7, 7)
        # 7/10 * 100 = 70.0
        assert isinstance(score.total_score, float)
        assert str(score.total_score).count('.') <= 1


class TestExecutionGate:
    """Tests for execution gate functionality."""

    def test_low_executes_capped(self):
        """Executes < 3 should cap total at 30."""
        # executes=2, all others=10
        # Without gate: 2/10*25 + 10/10*30 + 10/10*20 + 10/10*10 + 10/10*15 = 5+30+20+10+15 = 80
        # With gate: capped at 30
        score = create_score(2, 10, 10, 10, 10)
        assert score.total_score == 30.0

    def test_zero_executes_capped(self):
        """Executes=0 should cap total at 30."""
        score = create_score(0, 10, 10, 10, 10)
        assert score.total_score == 30.0

    def test_executes_3_not_capped(self):
        """Executes=3 exactly should NOT be capped."""
        # 3/10*25 + 10/10*30 + 10/10*20 + 10/10*10 + 10/10*15 = 7.5+30+20+10+15 = 82.5
        score = create_score(3, 10, 10, 10, 10)
        assert score.total_score == 82.5
        assert score.execution_gated is False

    def test_passing_executes_not_capped(self):
        """High executes score should not be capped."""
        score = create_score(8, 10, 10, 10, 10)
        # 8/10*25 + 10/10*30 + 10/10*20 + 10/10*10 + 10/10*15 = 20+30+20+10+15 = 95
        assert score.total_score == 95.0
        assert score.execution_gated is False

    def test_execution_gated_flag_set(self):
        """execution_gated should be True when executes < 3."""
        score = create_score(2, 10, 10, 10, 10)
        assert score.execution_gated is True

    def test_execution_gated_flag_not_set(self):
        """execution_gated should be False when executes >= 3."""
        score = create_score(5, 5, 5, 5, 5)
        assert score.execution_gated is False

    def test_gate_threshold_is_3(self):
        """Gate threshold should be 3."""
        assert AbsoluteScore.EXECUTION_GATE_THRESHOLD == 3

    def test_gate_cap_is_30(self):
        """Gate cap should be 30."""
        assert AbsoluteScore.EXECUTION_GATE_CAP == 30

    def test_edge_case_executes_2(self):
        """Executes=2 is the highest score that triggers gate."""
        score = create_score(2, 10, 10, 10, 10)
        assert score.execution_gated is True
        assert score.total_score <= 30

    def test_low_score_below_cap(self):
        """If raw score is below cap, don't artificially raise it."""
        # All 2s: 2/10 * 100 = 20
        # 20 < 30, so stays at 20
        score = create_score(2, 2, 2, 2, 2)
        assert score.total_score == 20.0


class TestToDict:
    """Tests for to_dict serialization."""

    def test_to_dict_has_all_dimensions(self):
        """to_dict should include all 5 dimensions."""
        score = create_score(7, 7, 7, 7, 7)
        d = score.to_dict()

        assert "executes" in d
        assert "features_complete" in d
        assert "output_quality" in d
        assert "direction_following" in d
        assert "code_quality" in d

    def test_to_dict_no_elegance(self):
        """to_dict should NOT include elegance."""
        score = create_score(7, 7, 7, 7, 7)
        d = score.to_dict()

        assert "elegance" not in d

    def test_to_dict_has_execution_gated(self):
        """to_dict should include execution_gated flag."""
        score = create_score(2, 7, 7, 7, 7)
        d = score.to_dict()

        assert "execution_gated" in d
        assert d["execution_gated"] is True

    def test_to_dict_has_total_score(self):
        """to_dict should include total_score."""
        score = create_score(7, 7, 7, 7, 7)
        d = score.to_dict()

        assert "total_score" in d
        assert d["total_score"] == 70.0

    def test_to_dict_dimension_format(self):
        """Each dimension should have score and reason."""
        score = create_score(7, 7, 7, 7, 7)
        d = score.to_dict()

        for dim in ["executes", "features_complete", "output_quality",
                   "direction_following", "code_quality"]:
            assert "score" in d[dim]
            assert "reason" in d[dim]


class TestEdgeCases:
    """Tests for edge cases."""

    def test_all_dimensions_at_boundary_low(self):
        """Test with all dimensions at 0."""
        score = create_score(0, 0, 0, 0, 0)
        assert score.total_score == 0.0
        assert score.execution_gated is True

    def test_all_dimensions_at_boundary_high(self):
        """Test with all dimensions at 10."""
        score = create_score(10, 10, 10, 10, 10)
        assert score.total_score == 100.0
        assert score.execution_gated is False

    def test_only_executes_passing(self):
        """Only executes passes, rest fail."""
        score = create_score(10, 0, 0, 0, 0)
        # 10/10 * 25 = 25
        assert score.total_score == 25.0
        assert score.execution_gated is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
