"""
=============================================================================
SCRIPT NAME: absolute.py
=============================================================================

Absolute scoring judge - scores individual outputs on 0-100 scale.

VERSION: 2.0
LAST UPDATED: 2026-01-04

CHANGES IN V2:
- Rebalanced scoring weights (executes increased, elegance removed)
- Added execution gate (non-running code capped at 30)
- Integrated with execution validator

=============================================================================
"""

import json
import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

from ..models.base import get_model, Message

# V2: Global cache for file reads to avoid repeated rglob
_file_cache: dict[str, dict[str, str]] = {}


@dataclass
class DimensionScore:
    """Score for a single evaluation dimension."""
    score: int  # 0-10
    reason: str


@dataclass
class JudgeMetrics:
    """Metrics for judge API usage."""
    input_tokens: int = 0
    output_tokens: int = 0
    judge_model: str = ""

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def estimated_cost(self) -> float:
        """Estimate cost in USD based on judge model pricing (OpenRouter rates)."""
        # OpenRouter pricing per 1M tokens (input, output) - updated Jan 2026
        pricing = {
            "anthropic/claude-opus-4.5": (5.0, 25.0),      # $5/$25 per M tokens
            "anthropic/claude-sonnet-4": (3.0, 15.0),     # $3/$15 per M tokens
            "openai/gpt-4o": (3.0, 10.0),                 # $3/$10 per M tokens
            "google/gemini-3-flash": (0.075, 0.3),        # $0.075/$0.30 per M tokens
            "google/gemini-2.0-flash": (0.075, 0.3),      # Same as 3-flash
            # Fallback rates (assume mid-tier model)
            "default": (3.0, 15.0),
        }
        # Normalize model name for lookup
        model_key = self.judge_model.lower()
        input_rate, output_rate = pricing.get(model_key, pricing["default"])
        cost = (self.input_tokens / 1_000_000) * input_rate
        cost += (self.output_tokens / 1_000_000) * output_rate
        return round(cost, 6)

    def to_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "judge_model": self.judge_model,
            "estimated_cost": self.estimated_cost(),
        }


@dataclass
class AbsoluteScore:
    """Complete absolute score with all dimensions."""
    executes: DimensionScore
    features_complete: DimensionScore
    output_quality: DimensionScore
    direction_following: DimensionScore
    code_quality: DimensionScore
    # V2: Track judge API usage
    judge_metrics: Optional[JudgeMetrics] = field(default=None)

    # V2: Rebalanced weights (elegance removed, executes increased)
    # Weights must sum to 100
    WEIGHTS = {
        "executes": 25,              # Increased from 15 - broken code should fail harder
        "features_complete": 30,     # Unchanged - core requirement
        "output_quality": 20,        # Reduced from 25 - balanced with execution
        "direction_following": 10,   # Reduced from 15 - less critical than execution
        "code_quality": 15,          # Increased from 10 - production code matters
        # "elegance" removed - too subjective, added noise
    }

    # Execution gate: if executes < 3, cap total at this value
    EXECUTION_GATE_THRESHOLD = 3
    EXECUTION_GATE_CAP = 30

    @property
    def total_score(self) -> float:
        """Compute weighted total score (0-100) with execution gate."""
        total = 0.0
        for dim, weight in self.WEIGHTS.items():
            dim_score = getattr(self, dim).score
            # Each dimension is 0-10, weight is the contribution to 100
            total += (dim_score / 10.0) * weight

        # V2: Apply execution gate - non-running code capped at 30
        if self.executes.score < self.EXECUTION_GATE_THRESHOLD:
            total = min(total, self.EXECUTION_GATE_CAP)

        return round(total, 1)

    @property
    def execution_gated(self) -> bool:
        """Check if score was capped due to execution gate."""
        return self.executes.score < self.EXECUTION_GATE_THRESHOLD

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "executes": {"score": self.executes.score, "reason": self.executes.reason},
            "features_complete": {"score": self.features_complete.score, "reason": self.features_complete.reason},
            "output_quality": {"score": self.output_quality.score, "reason": self.output_quality.reason},
            "direction_following": {"score": self.direction_following.score, "reason": self.direction_following.reason},
            "code_quality": {"score": self.code_quality.score, "reason": self.code_quality.reason},
            "total_score": self.total_score,
            "execution_gated": self.execution_gated,
        }
        # V2: Include judge metrics if available
        if self.judge_metrics:
            result["judge_metrics"] = self.judge_metrics.to_dict()
        return result


def collect_code_files(workspace: Path, max_files: int = 20) -> dict[str, str]:
    """
    Collect code files from workspace.

    V2: Uses global cache to avoid repeated rglob calls for same workspace.

    Args:
        workspace: Directory to scan
        max_files: Maximum number of files to include

    Returns:
        Dict mapping relative paths to file contents
    """
    # V2: Check cache first
    cache_key = str(workspace.resolve())
    if cache_key in _file_cache:
        cached = _file_cache[cache_key]
        # Return up to max_files from cache
        return dict(list(cached.items())[:max_files])

    code_extensions = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css",
        ".json", ".yaml", ".yml", ".toml", ".md", ".txt",
        ".sh", ".bash", ".sql", ".go", ".rs", ".java"
    }

    files = {}
    for path in sorted(workspace.rglob("*")):
        if path.is_file() and path.suffix in code_extensions:
            if len(files) >= max_files:
                break
            try:
                content = path.read_text()
                # Truncate very large files
                if len(content) > 100000:
                    content = content[:100000] + "\n\n... (truncated)"
                files[str(path.relative_to(workspace))] = content
            except Exception:
                pass

    # V2: Cache results for this workspace
    _file_cache[cache_key] = files

    return files


def clear_file_cache():
    """Clear the file cache. Call between eval runs if needed."""
    _file_cache.clear()


def format_code_files(files: dict[str, str]) -> str:
    """Format code files for inclusion in prompt."""
    parts = []
    for path, content in files.items():
        parts.append(f"### {path}\n```\n{content}\n```")
    return "\n\n".join(parts)


def extract_json(text: str) -> str:
    """Extract JSON from text, handling markdown code blocks."""
    # Try to find JSON in code block
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    
    # Try to find raw JSON object
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    return text


class AbsoluteJudge:
    """
    Judge that scores a single model output on a 0-100 scale.
    
    Uses Claude Opus as the judge model by default.
    """
    
    def __init__(
        self,
        judge_model: str = "claude-opus-4.5",
        temperature: float = 0.0
    ):
        """
        Initialize absolute judge.

        Args:
            judge_model: Model to use for judging
            temperature: Sampling temperature (0 for determinism)
        """
        self.judge_model_name = judge_model  # Store for cost tracking
        self.model = get_model(judge_model)
        # Force low temperature for judging if supported
        if hasattr(self.model, 'temperature'):
            self.model.temperature = temperature
    
    def score(
        self, 
        spec: str, 
        workspace: Path,
        criteria: Optional[str] = None
    ) -> AbsoluteScore:
        """
        Score the output of a model run.
        
        Args:
            spec: Original task specification
            workspace: Directory containing generated code
            criteria: Optional additional evaluation criteria
            
        Returns:
            AbsoluteScore with dimension breakdowns
        """
        code_files = collect_code_files(workspace)
        
        if not code_files:
            # No files generated - minimum scores
            return AbsoluteScore(
                executes=DimensionScore(0, "No files were generated"),
                features_complete=DimensionScore(0, "No implementation"),
                output_quality=DimensionScore(0, "No output"),
                direction_following=DimensionScore(0, "No attempt"),
                code_quality=DimensionScore(0, "No code"),
            )
        
        criteria_section = ""
        if criteria:
            criteria_section = f"\n\n## Additional Evaluation Criteria:\n{criteria}"
        
        prompt = f"""You are a STRICT code reviewer evaluating AI-generated code. Your job is to find problems and score harshly but fairly.

## Original Spec:
{spec}
{criteria_section}

## Generated Code:
{format_code_files(code_files)}

## CRITICAL: Scoring Guidelines

Score STRICTLY on a 0-10 scale. Most implementations should score 4-7. Only exceptional, production-ready code gets 8+.

**Score anchors:**
- 0-2: Broken, won't run, or completely wrong approach
- 3-4: Partially works but has significant issues or missing features
- 5-6: Works for basic cases but has bugs, edge cases fail, or missing features
- 7-8: Solid implementation, works correctly, minor issues only
- 9-10: Production-quality, handles edge cases, excellent code - RARE

**Be harsh on:**
- Missing error handling → penalize heavily
- Missing features from spec → each missing feature = -2 points minimum
- Code that looks plausible but wouldn't actually work → low EXECUTES score
- Hardcoded values or shortcuts that bypass the real requirement
- Incomplete implementations (e.g., TODO comments, placeholder functions)
- External dependencies (pip install, npm install) → AUTOMATIC score of 0 for EXECUTES

## Dimensions to score (5 dimensions):

1. EXECUTES (0-10): Would this ACTUALLY run without errors? Check imports, syntax, API usage.
   - If obvious runtime errors, score ≤3
   - If uses external packages not in Python stdlib, score 0
   - CRITICAL: This dimension has highest weight (25%)

2. FEATURES_COMPLETE (0-10): Check EACH feature in the spec.
   - Missing ANY feature = max score of 6
   - Missing HALF = max score of 3

3. OUTPUT_QUALITY (0-10): Would output actually match expectations?
   - Verify the logic produces correct results

4. DIRECTION_FOLLOWING (0-10): Did they build EXACTLY what was asked?
   - Wrong framework, extra unwanted features, or misinterpreting the spec = penalize

5. CODE_QUALITY (0-10): Is it readable, well-organized, idiomatic?
   - No error handling = max 5
   - Poor structure = max 6

Respond ONLY with JSON:
{{
  "executes": {{"score": N, "reason": "..."}},
  "features_complete": {{"score": N, "reason": "..."}},
  "output_quality": {{"score": N, "reason": "..."}},
  "direction_following": {{"score": N, "reason": "..."}},
  "code_quality": {{"score": N, "reason": "..."}}
}}
"""
        
        response = self.model.complete([Message(role="user", content=prompt)])

        # V2: Track judge token usage
        judge_metrics = JudgeMetrics(
            input_tokens=response.usage.get("input_tokens", 0) if response.usage else 0,
            output_tokens=response.usage.get("output_tokens", 0) if response.usage else 0,
            judge_model=self.judge_model_name,
        )

        try:
            raw_json = extract_json(response.content)
            scores = json.loads(raw_json)

            return AbsoluteScore(
                executes=DimensionScore(
                    scores["executes"]["score"],
                    scores["executes"]["reason"]
                ),
                features_complete=DimensionScore(
                    scores["features_complete"]["score"],
                    scores["features_complete"]["reason"]
                ),
                output_quality=DimensionScore(
                    scores["output_quality"]["score"],
                    scores["output_quality"]["reason"]
                ),
                direction_following=DimensionScore(
                    scores["direction_following"]["score"],
                    scores["direction_following"]["reason"]
                ),
                code_quality=DimensionScore(
                    scores["code_quality"]["score"],
                    scores["code_quality"]["reason"]
                ),
                judge_metrics=judge_metrics,
            )

        except (json.JSONDecodeError, KeyError) as e:
            # Return error-state scores if parsing fails
            return AbsoluteScore(
                executes=DimensionScore(0, f"Judge parsing error: {e}"),
                features_complete=DimensionScore(0, "Could not parse"),
                output_quality=DimensionScore(0, "Could not parse"),
                direction_following=DimensionScore(0, "Could not parse"),
                code_quality=DimensionScore(0, "Could not parse"),
                judge_metrics=judge_metrics,  # Still track tokens even on parse error
            )
