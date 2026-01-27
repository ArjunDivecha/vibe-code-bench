"""
Functional tests for Test-Driven task (case_34_test_driven).

Tests verify the calculator implementation passes all tests.
"""
import subprocess
import sys
from pathlib import Path


def test_calculator_file_exists(workspace: Path, main_file: Path):
    """calculator.py should exist."""
    calc_file = workspace / "calculator.py"
    assert calc_file.exists(), "calculator.py not found"


def test_test_file_exists(workspace: Path, main_file: Path):
    """test_calculator.py should exist."""
    test_file = workspace / "test_calculator.py"
    assert test_file.exists(), "test_calculator.py not found"


def test_calculator_has_class(workspace: Path, main_file: Path):
    """Should define Calculator class."""
    calc_file = workspace / "calculator.py"
    if calc_file.exists():
        content = calc_file.read_text()
        assert "class Calculator" in content, "Calculator class not found"


def test_calculator_has_error_class(workspace: Path, main_file: Path):
    """Should define CalculatorError class."""
    calc_file = workspace / "calculator.py"
    if calc_file.exists():
        content = calc_file.read_text()
        assert "CalculatorError" in content, "CalculatorError not found"


def test_calculator_imports_without_error(workspace: Path, main_file: Path):
    """Calculator module should import cleanly."""
    result = subprocess.run(
        [sys.executable, "-c", "from calculator import Calculator, CalculatorError"],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=10
    )
    assert result.returncode == 0, f"Import error: {result.stderr}"


def test_initial_value_is_zero(workspace: Path, main_file: Path):
    """Test: initial value is zero."""
    result = subprocess.run(
        [sys.executable, "-c", 
         "from calculator import Calculator; c = Calculator(); assert c.value == 0"],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=10
    )
    assert result.returncode == 0, "Initial value is not zero"


def test_add_works(workspace: Path, main_file: Path):
    """Test: add method works."""
    result = subprocess.run(
        [sys.executable, "-c", 
         "from calculator import Calculator; c = Calculator(); c.add(5); assert c.value == 5"],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=10
    )
    assert result.returncode == 0, f"Add doesn't work: {result.stderr}"


def test_chaining_works(workspace: Path, main_file: Path):
    """Test: method chaining works."""
    result = subprocess.run(
        [sys.executable, "-c", 
         "from calculator import Calculator; c = Calculator(); r = c.add(5); assert r is c"],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=10
    )
    assert result.returncode == 0, "Method chaining doesn't work"


def test_divide_by_zero_raises(workspace: Path, main_file: Path):
    """Test: divide by zero raises CalculatorError."""
    code = """
from calculator import Calculator, CalculatorError
c = Calculator()
c.add(10)
try:
    c.divide(0)
    exit(1)  # Should have raised
except CalculatorError:
    exit(0)  # Correct behavior
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=10
    )
    assert result.returncode == 0, "Divide by zero doesn't raise CalculatorError"


def test_all_tests_pass(workspace: Path, main_file: Path):
    """All unit tests should pass."""
    test_file = workspace / "test_calculator.py"
    if not test_file.exists():
        return  # Skip if no test file
    
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "test_calculator", "-v"],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=30
    )
    
    # Check for OK or count passed tests
    output = result.stdout + result.stderr
    passed = output.count(" ok") + output.count("... ok")
    
    assert passed >= 8 or "OK" in output, \
        f"Not enough tests passed ({passed}/10): {output[-500:]}"
