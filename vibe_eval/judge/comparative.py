"""Comparative judge - head-to-head comparison between model outputs."""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .absolute import collect_code_files, format_code_files, extract_json
from ..models.base import get_model, Message


@dataclass
class ComparisonResult:
    """Result of a head-to-head comparison."""
    winner: Literal["A", "B", "TIE"]
    confidence: Literal["high", "medium", "low"]
    reasoning: str
    model_a: str
    model_b: str
    
    def get_winner_name(self) -> str:
        """Get the name of the winning model."""
        if self.winner == "A":
            return self.model_a
        elif self.winner == "B":
            return self.model_b
        else:
            return "TIE"


class ComparativeJudge:
    """
    Judge that compares two model outputs head-to-head.
    
    Returns a winner (A, B, or TIE) with reasoning.
    """
    
    def __init__(
        self, 
        judge_model: str = "claude-opus-4.5",
        temperature: float = 0.0
    ):
        """
        Initialize comparative judge.
        
        Args:
            judge_model: Model to use for judging
            temperature: Sampling temperature (0 for determinism)
        """
        self.model = get_model(judge_model)
        # Force low temperature for judging if supported
        if hasattr(self.model, 'temperature'):
            self.model.temperature = temperature
    
    def compare(
        self,
        spec: str,
        workspace_a: Path,
        workspace_b: Path,
        model_a_name: str,
        model_b_name: str
    ) -> ComparisonResult:
        """
        Compare two implementations head-to-head.
        
        Args:
            spec: Original task specification
            workspace_a: Directory containing Model A's code
            workspace_b: Directory containing Model B's code
            model_a_name: Name/identifier for Model A
            model_b_name: Name/identifier for Model B
            
        Returns:
            ComparisonResult with winner and reasoning
        """
        code_a = collect_code_files(workspace_a)
        code_b = collect_code_files(workspace_b)
        
        # Handle edge cases
        if not code_a and not code_b:
            return ComparisonResult(
                winner="TIE",
                confidence="high",
                reasoning="Neither model produced any code",
                model_a=model_a_name,
                model_b=model_b_name
            )
        elif not code_a:
            return ComparisonResult(
                winner="B",
                confidence="high",
                reasoning="Model A produced no code",
                model_a=model_a_name,
                model_b=model_b_name
            )
        elif not code_b:
            return ComparisonResult(
                winner="A",
                confidence="high",
                reasoning="Model B produced no code",
                model_a=model_a_name,
                model_b=model_b_name
            )
        
        prompt = f"""You are comparing two AI-generated codebases for the same specification.

## Specification:
{spec}

## Implementation A:
{format_code_files(code_a)}

## Implementation B:
{format_code_files(code_b)}

## Your Task:
Determine which implementation better fulfills the specification. Consider:
1. Completeness - Does it implement all requested features?
2. Correctness - Would it actually work as intended?
3. Code Quality - Is it well-organized and readable?
4. Direction Following - Did it build what was asked?

Respond ONLY with JSON in this exact format:
{{
  "winner": "A" or "B" or "TIE",
  "confidence": "high" or "medium" or "low",
  "reasoning": "Brief explanation of why this implementation is better (2-3 sentences)"
}}
"""
        
        response = self.model.complete([Message(role="user", content=prompt)])
        
        try:
            raw_json = extract_json(response.content)
            result = json.loads(raw_json)
            
            # Normalize winner value
            winner = result["winner"].upper()
            if winner not in ("A", "B", "TIE"):
                winner = "TIE"
            
            # Normalize confidence
            confidence = result.get("confidence", "medium").lower()
            if confidence not in ("high", "medium", "low"):
                confidence = "medium"
            
            return ComparisonResult(
                winner=winner,
                confidence=confidence,
                reasoning=result.get("reasoning", "No reasoning provided"),
                model_a=model_a_name,
                model_b=model_b_name
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            # Default to tie if parsing fails
            return ComparisonResult(
                winner="TIE",
                confidence="low",
                reasoning=f"Judge parsing error: {e}",
                model_a=model_a_name,
                model_b=model_b_name
            )


def run_all_comparisons(
    spec: str,
    workspaces: dict[str, Path],
    judge: ComparativeJudge
) -> list[ComparisonResult]:
    """
    Run all pairwise comparisons between models.
    
    Args:
        spec: Task specification
        workspaces: Dict mapping model names to workspace paths
        judge: ComparativeJudge instance
        
    Returns:
        List of all comparison results
    """
    models = list(workspaces.keys())
    results = []
    
    # Generate all pairs
    for i, model_a in enumerate(models):
        for model_b in models[i + 1:]:
            result = judge.compare(
                spec=spec,
                workspace_a=workspaces[model_a],
                workspace_b=workspaces[model_b],
                model_a_name=model_a,
                model_b_name=model_b
            )
            results.append(result)
    
    return results
