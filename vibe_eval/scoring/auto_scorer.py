"""
Automated scoring based on functional test results.

V3: Scores outputs objectively based on test pass rates.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..sandbox.test_runner import FunctionalTestRunner, TestRunResult


@dataclass
class AutoScore:
    """
    Automated scoring results.
    
    Based on functional test execution - no LLM judgment involved.
    """
    test_pass_rate: float  # 0.0 - 1.0
    tests_passed: int
    tests_failed: int
    tests_total: int
    execution_success: bool  # Did code run at all?
    test_details: list[dict] = field(default_factory=list)
    
    @property
    def test_score(self) -> float:
        """Convert pass rate to 0-10 score (float for granularity)."""
        return self.test_pass_rate * 10
    
    @property
    def execution_score(self) -> int:
        """Execution score (0-10)."""
        if not self.execution_success:
            return 0
        # If execution worked, base score on whether we could run tests
        if self.tests_total == 0:
            return 5  # Code runs but no tests available
        return 10 if self.test_pass_rate > 0.5 else 7
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "test_pass_rate": round(self.test_pass_rate, 3),
            "tests_passed": self.tests_passed,
            "tests_failed": self.tests_failed,
            "tests_total": self.tests_total,
            "test_score": self.test_score,
            "execution_success": self.execution_success,
            "execution_score": self.execution_score,
            "test_details": self.test_details[:10],  # Limit details
        }


class AutoScorer:
    """
    Automatic scorer using functional tests.
    
    Runs the test suite for a case and scores based on pass rate.
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize auto scorer.
        
        Args:
            timeout: Timeout per test in seconds
        """
        self.runner = FunctionalTestRunner(timeout=timeout)
    
    def score(
        self,
        workspace: Path,
        test_file: Optional[Path] = None,
        case_dir: Optional[Path] = None,
    ) -> AutoScore:
        """
        Score workspace output using functional tests.
        
        Args:
            workspace: Directory containing generated code
            test_file: Path to tests.py (auto-detected if case_dir provided)
            case_dir: Case directory containing tests.py
            
        Returns:
            AutoScore with test results
        """
        workspace = Path(workspace)
        
        # Find test file
        if test_file is None and case_dir is not None:
            test_file = Path(case_dir) / "tests.py"
        
        if test_file is None or not test_file.exists():
            # No tests available - return partial score
            return AutoScore(
                test_pass_rate=0.0,
                tests_passed=0,
                tests_failed=0,
                tests_total=0,
                execution_success=self._check_execution(workspace),
            )
        
        # Run tests
        result = self.runner.run_tests(workspace, test_file)
        
        return AutoScore(
            test_pass_rate=result.pass_rate,
            tests_passed=result.passed,
            tests_failed=result.failed,
            tests_total=result.total_tests,
            execution_success=result.passed > 0 or result.total_tests == 0,
            test_details=[
                {"name": r.name, "passed": r.passed, "error": r.error}
                for r in result.results
            ],
        )
    
    def _check_execution(self, workspace: Path) -> bool:
        """
        Check if code executes at all (basic sanity check).
        """
        from ..sandbox.validator import ExecutionValidator
        
        validator = ExecutionValidator(timeout=15)
        report = validator.validate(workspace)
        return report.executed
    
    @classmethod
    def cleanup(cls):
        """Clean up shared resources."""
        FunctionalTestRunner.cleanup()
