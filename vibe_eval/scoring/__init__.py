"""
Scoring module for V3 evaluation system.

Combines automated scoring (tests, static analysis) with LLM judge scoring.
"""

from .auto_scorer import AutoScorer, AutoScore
from .static_scorer import StaticAnalyzer, StaticReport
from .aggregator import ScoreAggregator, FinalScore

__all__ = [
    "AutoScorer",
    "AutoScore",
    "StaticAnalyzer", 
    "StaticReport",
    "ScoreAggregator",
    "FinalScore",
]
