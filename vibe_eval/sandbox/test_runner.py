"""
=============================================================================
SCRIPT NAME: test_runner.py
=============================================================================

Runs functional tests against generated code using Playwright.

INPUT:
- workspace_path: Path to directory containing generated code
- test_file: Path to tests.py file with test functions

OUTPUT:
- TestRunResult: Dataclass with pass/fail counts, details per test

VERSION: 3.0
LAST UPDATED: 2026-01-27

DESCRIPTION:
This module provides functional test execution for generated code. It:
1. Discovers test functions in tests.py files
2. Runs HTML apps in Playwright and executes assertions
3. Runs Python scripts and validates output
4. Returns detailed pass/fail results for scoring

DEPENDENCIES:
- ast (stdlib)
- importlib (stdlib)
- pathlib (stdlib)
- dataclasses (stdlib)
- playwright (for browser testing)

=============================================================================
"""

import ast
import importlib.util
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    passed: bool
    duration_ms: float = 0.0
    error: Optional[str] = None
    screenshot: Optional[bytes] = None


@dataclass
class TestRunResult:
    """Result of running all tests for a case."""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    pass_rate: float  # 0.0 - 1.0
    results: list[TestResult] = field(default_factory=list)
    execution_time: float = 0.0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "pass_rate": round(self.pass_rate, 3),
            "execution_time": round(self.execution_time, 2),
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "duration_ms": round(r.duration_ms, 2),
                    "error": r.error,
                }
                for r in self.results
            ],
            "errors": self.errors,
        }

    @property
    def score(self) -> int:
        """Convert pass rate to 0-10 score."""
        return round(self.pass_rate * 10)


class FunctionalTestRunner:
    """
    Runs functional tests against generated code.

    Supports:
    - HTML apps tested via Playwright
    - Python scripts tested via subprocess
    - Custom test fixtures and helpers
    """

    # Shared Playwright browser instance
    _playwright = None
    _browser = None

    def __init__(self, timeout: int = 30):
        """
        Initialize test runner.

        Args:
            timeout: Maximum seconds per test
        """
        self.timeout = timeout

    @classmethod
    def _get_browser(cls):
        """Get or create shared browser instance."""
        if cls._browser is None:
            try:
                from playwright.sync_api import sync_playwright
                cls._playwright = sync_playwright().start()
                cls._browser = cls._playwright.chromium.launch(headless=True)
            except ImportError:
                return None
            except Exception:
                return None
        return cls._browser

    @classmethod
    def cleanup(cls):
        """Clean up shared browser instance."""
        if cls._browser is not None:
            try:
                cls._browser.close()
            except Exception:
                pass
            cls._browser = None
        if cls._playwright is not None:
            try:
                cls._playwright.stop()
            except Exception:
                pass
            cls._playwright = None

    def run_tests(
        self,
        workspace: Path,
        test_file: Path,
    ) -> TestRunResult:
        """
        Run all tests from a test file against workspace code.

        Args:
            workspace: Directory containing generated code
            test_file: Path to tests.py with test functions

        Returns:
            TestRunResult with all test outcomes
        """
        workspace = Path(workspace).absolute()
        test_file = Path(test_file).absolute()

        if not test_file.exists():
            return TestRunResult(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                pass_rate=0.0,
                errors=[f"Test file not found: {test_file}"],
            )

        # Find main HTML or Python file
        html_files = list(workspace.glob("**/*.html"))
        python_files = list(workspace.glob("**/*.py"))

        main_file = None
        file_type = None

        # Prioritize HTML files
        if html_files:
            main_file = self._find_main_html(html_files)
            file_type = "html"
        elif python_files:
            main_file = self._find_main_python(python_files, workspace)
            file_type = "python"

        if main_file is None:
            return TestRunResult(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                pass_rate=0.0,
                errors=["No HTML or Python files found in workspace"],
            )

        # Load test functions
        test_functions = self._load_test_functions(test_file)

        if not test_functions:
            return TestRunResult(
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                pass_rate=0.0,
                errors=["No test functions found in test file"],
            )

        # Run tests based on file type
        if file_type == "html":
            return self._run_html_tests(main_file, test_functions)
        else:
            return self._run_python_tests(main_file, workspace, test_functions)

    def _find_main_html(self, files: list[Path]) -> Optional[Path]:
        """Find main HTML entry point."""
        priority = ["index.html", "main.html", "app.html"]
        for name in priority:
            for f in files:
                if f.name == name:
                    return f
        return files[0] if files else None

    def _find_main_python(self, files: list[Path], workspace: Path) -> Optional[Path]:
        """Find main Python entry point."""
        priority = ["main.py", "app.py", "index.py", "run.py", "server.py"]
        for name in priority:
            for f in files:
                if f.name == name:
                    return f
        root_files = [f for f in files if f.parent == workspace]
        return root_files[0] if root_files else (files[0] if files else None)

    def _load_test_functions(self, test_file: Path) -> list[tuple[str, Callable]]:
        """
        Load test functions from a test file.

        Returns list of (name, function) tuples for functions starting with 'test_'.
        """
        try:
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location("tests", test_file)
            if spec is None or spec.loader is None:
                return []
            
            module = importlib.util.module_from_spec(spec)
            sys.modules["tests"] = module
            spec.loader.exec_module(module)

            # Find test functions
            tests = []
            for name in dir(module):
                if name.startswith("test_"):
                    func = getattr(module, name)
                    if callable(func):
                        tests.append((name, func))

            return sorted(tests, key=lambda x: x[0])

        except Exception as e:
            return []

    def _run_html_tests(
        self,
        html_file: Path,
        test_functions: list[tuple[str, Callable]],
    ) -> TestRunResult:
        """
        Run tests against an HTML file using Playwright.

        Each test function receives a Playwright page object.
        """
        browser = self._get_browser()
        if browser is None:
            return TestRunResult(
                total_tests=len(test_functions),
                passed=0,
                failed=0,
                skipped=len(test_functions),
                pass_rate=0.0,
                errors=["Playwright not available - install with: pip install playwright && playwright install"],
            )

        results = []
        start_time = time.time()
        passed = 0
        failed = 0

        file_url = f"file://{html_file.absolute()}"
        
        # Create a single context for all tests (faster than new browser per test)
        context = None
        try:
            context = browser.new_context()
            # Set default timeout for all operations
            context.set_default_timeout(self.timeout * 1000)
        except Exception as e:
            return TestRunResult(
                total_tests=len(test_functions),
                passed=0,
                failed=0,
                skipped=len(test_functions),
                pass_rate=0.0,
                errors=[f"Failed to create browser context: {e}"],
            )

        for name, func in test_functions:
            test_start = time.time()
            page = None
            
            try:
                # Create fresh page for each test
                page = context.new_page()
                
                # Use 'load' instead of 'networkidle' - much faster and more reliable
                page.goto(file_url, wait_until="load", timeout=10000)

                # Brief wait for JS initialization (reduced from 500ms)
                page.wait_for_timeout(200)

                # Run the test
                func(page)

                # Test passed
                duration = (time.time() - test_start) * 1000
                results.append(TestResult(
                    name=name,
                    passed=True,
                    duration_ms=duration,
                ))
                passed += 1

            except AssertionError as e:
                duration = (time.time() - test_start) * 1000
                results.append(TestResult(
                    name=name,
                    passed=False,
                    duration_ms=duration,
                    error=str(e),
                ))
                failed += 1

            except Exception as e:
                duration = (time.time() - test_start) * 1000
                error_msg = str(e)
                # Truncate long timeout messages
                if len(error_msg) > 200:
                    error_msg = error_msg[:200] + "..."
                results.append(TestResult(
                    name=name,
                    passed=False,
                    duration_ms=duration,
                    error=f"{type(e).__name__}: {error_msg}",
                ))
                failed += 1

            finally:
                if page:
                    try:
                        page.close()
                    except Exception:
                        pass
        
        # Clean up context
        if context:
            try:
                context.close()
            except Exception:
                pass

        total_time = time.time() - start_time
        total = len(test_functions)
        pass_rate = passed / total if total > 0 else 0.0

        return TestRunResult(
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=0,
            pass_rate=pass_rate,
            results=results,
            execution_time=total_time,
        )

    def _run_python_tests(
        self,
        python_file: Path,
        workspace: Path,
        test_functions: list[tuple[str, Callable]],
    ) -> TestRunResult:
        """
        Run tests against a Python script.

        Each test function receives the workspace path and main file path.
        """
        import subprocess

        results = []
        start_time = time.time()
        passed = 0
        failed = 0

        for name, func in test_functions:
            test_start = time.time()

            try:
                # Run the test, passing workspace and file info
                func(workspace, python_file)

                duration = (time.time() - test_start) * 1000
                results.append(TestResult(
                    name=name,
                    passed=True,
                    duration_ms=duration,
                ))
                passed += 1

            except AssertionError as e:
                duration = (time.time() - test_start) * 1000
                results.append(TestResult(
                    name=name,
                    passed=False,
                    duration_ms=duration,
                    error=str(e),
                ))
                failed += 1

            except Exception as e:
                duration = (time.time() - test_start) * 1000
                results.append(TestResult(
                    name=name,
                    passed=False,
                    duration_ms=duration,
                    error=f"{type(e).__name__}: {str(e)}",
                ))
                failed += 1

        total_time = time.time() - start_time
        total = len(test_functions)
        pass_rate = passed / total if total > 0 else 0.0

        return TestRunResult(
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=0,
            pass_rate=pass_rate,
            results=results,
            execution_time=total_time,
        )


def run_functional_tests(
    workspace: Path,
    test_file: Path,
    timeout: int = 30,
) -> TestRunResult:
    """
    Convenience function to run functional tests.

    Args:
        workspace: Directory containing generated code
        test_file: Path to tests.py
        timeout: Timeout per test in seconds

    Returns:
        TestRunResult with all outcomes
    """
    runner = FunctionalTestRunner(timeout=timeout)
    return runner.run_tests(workspace, test_file)
