"""Absolute scoring judge - scores individual outputs on 0-100 scale."""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import anthropic


@dataclass
class DimensionScore:
    """Score for a single evaluation dimension."""
    score: int  # 0-10
    reason: str


@dataclass
class AbsoluteScore:
    """Complete absolute score with all dimensions."""
    executes: DimensionScore
    features_complete: DimensionScore
    output_quality: DimensionScore
    direction_following: DimensionScore
    code_quality: DimensionScore
    elegance: DimensionScore
    
    # Weights for each dimension (must sum to 100)
    WEIGHTS = {
        "executes": 15,
        "features_complete": 30,
        "output_quality": 25,
        "direction_following": 15,
        "code_quality": 10,
        "elegance": 5,
    }
    
    @property
    def total_score(self) -> float:
        """Compute weighted total score (0-100)."""
        total = 0.0
        for dim, weight in self.WEIGHTS.items():
            dim_score = getattr(self, dim).score
            # Each dimension is 0-10, weight is the contribution to 100
            total += (dim_score / 10.0) * weight
        return round(total, 1)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "executes": {"score": self.executes.score, "reason": self.executes.reason},
            "features_complete": {"score": self.features_complete.score, "reason": self.features_complete.reason},
            "output_quality": {"score": self.output_quality.score, "reason": self.output_quality.reason},
            "direction_following": {"score": self.direction_following.score, "reason": self.direction_following.reason},
            "code_quality": {"score": self.code_quality.score, "reason": self.code_quality.reason},
            "elegance": {"score": self.elegance.score, "reason": self.elegance.reason},
            "total_score": self.total_score,
        }


def collect_code_files(workspace: Path, max_files: int = 20) -> dict[str, str]:
    """
    Collect code files from workspace.
    
    Args:
        workspace: Directory to scan
        max_files: Maximum number of files to include
        
    Returns:
        Dict mapping relative paths to file contents
    """
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
    
    return files


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
        judge_model: str = "claude-opus-4-20250514",
        temperature: float = 0.0
    ):
        """
        Initialize absolute judge.
        
        Args:
            judge_model: Model to use for judging
            temperature: Sampling temperature (0 for determinism)
        """
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.model = judge_model
        self.temperature = temperature
    
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
                elegance=DimensionScore(0, "N/A"),
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

## Dimensions to score:

1. EXECUTES (0-10): Would this ACTUALLY run without errors? Check imports, syntax, API usage. If you see obvious runtime errors, score ≤3.

2. FEATURES_COMPLETE (0-10): Check EACH feature in the spec. Missing ANY feature = max score of 6. Missing HALF = max score of 3.

3. OUTPUT_QUALITY (0-10): Would output actually match expectations? Verify the logic produces correct results.

4. DIRECTION_FOLLOWING (0-10): Did they build EXACTLY what was asked? Wrong framework, extra unwanted features, or misinterpreting the spec = penalize.

5. CODE_QUALITY (0-10): Is it readable, well-organized, idiomatic? No error handling = max 5. Poor structure = max 6.

6. ELEGANCE (0-10): ONLY for exceptional solutions. Default to 5 for adequate code. 7+ requires genuinely clever or clean design.

Respond ONLY with JSON:
{{
  "executes": {{"score": N, "reason": "..."}},
  "features_complete": {{"score": N, "reason": "..."}},
  "output_quality": {{"score": N, "reason": "..."}},
  "direction_following": {{"score": N, "reason": "..."}},
  "code_quality": {{"score": N, "reason": "..."}},
  "elegance": {{"score": N, "reason": "..."}}
}}
"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            raw_json = extract_json(response.content[0].text)
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
                elegance=DimensionScore(
                    scores["elegance"]["score"],
                    scores["elegance"]["reason"]
                ),
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            # Return error-state scores if parsing fails
            return AbsoluteScore(
                executes=DimensionScore(0, f"Judge parsing error: {e}"),
                features_complete=DimensionScore(0, "Could not parse"),
                output_quality=DimensionScore(0, "Could not parse"),
                direction_following=DimensionScore(0, "Could not parse"),
                code_quality=DimensionScore(0, "Could not parse"),
                elegance=DimensionScore(0, "Could not parse"),
            )
