"""
Functional tests for Data Pipeline (case_35_data_pipeline).

Tests verify the pipeline processes data correctly.
"""
import json
import subprocess
import sys
from pathlib import Path


def test_pipeline_file_exists(workspace: Path, main_file: Path):
    """pipeline.py should exist."""
    pipeline_file = workspace / "pipeline.py"
    assert pipeline_file.exists() or main_file.name == "pipeline.py", \
        "pipeline.py not found"


def test_pipeline_runs_without_error(workspace: Path, main_file: Path):
    """Pipeline should execute successfully."""
    result = subprocess.run(
        [sys.executable, str(main_file)],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=30
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"


def test_creates_valid_employees_file(workspace: Path, main_file: Path):
    """Should create valid_employees.json."""
    # Run pipeline first
    subprocess.run(
        [sys.executable, str(main_file)],
        capture_output=True,
        cwd=str(workspace),
        timeout=30
    )
    
    output_file = workspace / "valid_employees.json"
    assert output_file.exists(), "valid_employees.json not created"


def test_creates_invalid_records_file(workspace: Path, main_file: Path):
    """Should create invalid_records.json."""
    subprocess.run(
        [sys.executable, str(main_file)],
        capture_output=True,
        cwd=str(workspace),
        timeout=30
    )
    
    output_file = workspace / "invalid_records.json"
    assert output_file.exists(), "invalid_records.json not created"


def test_creates_department_summary_file(workspace: Path, main_file: Path):
    """Should create department_summary.json."""
    subprocess.run(
        [sys.executable, str(main_file)],
        capture_output=True,
        cwd=str(workspace),
        timeout=30
    )
    
    output_file = workspace / "department_summary.json"
    assert output_file.exists(), "department_summary.json not created"


def test_valid_employees_has_transformations(workspace: Path, main_file: Path):
    """Valid employees should have transformation fields."""
    subprocess.run(
        [sys.executable, str(main_file)],
        capture_output=True,
        cwd=str(workspace),
        timeout=30
    )
    
    output_file = workspace / "valid_employees.json"
    if output_file.exists():
        data = json.loads(output_file.read_text())
        if len(data) > 0:
            first = data[0]
            # Should have transformed fields
            has_domain = "email_domain" in first or "domain" in first
            has_band = "salary_band" in first or "band" in first
            assert has_domain or has_band, \
                "Missing transformation fields (email_domain, salary_band)"


def test_invalid_records_has_errors(workspace: Path, main_file: Path):
    """Invalid records should include error reasons."""
    subprocess.run(
        [sys.executable, str(main_file)],
        capture_output=True,
        cwd=str(workspace),
        timeout=30
    )
    
    output_file = workspace / "invalid_records.json"
    if output_file.exists():
        data = json.loads(output_file.read_text())
        if len(data) > 0:
            first = data[0]
            has_errors = "errors" in first or "error" in first or "reason" in first
            assert has_errors, "Invalid records missing error reasons"


def test_catches_invalid_email(workspace: Path, main_file: Path):
    """Should catch invalid email formats."""
    subprocess.run(
        [sys.executable, str(main_file)],
        capture_output=True,
        cwd=str(workspace),
        timeout=30
    )
    
    output_file = workspace / "invalid_records.json"
    if output_file.exists():
        content = output_file.read_text().lower()
        # Jane Doe or Henry Taylor have invalid emails
        has_email_error = "email" in content or "jane" in content or "henry" in content
        assert has_email_error, "Did not catch invalid email"


def test_catches_invalid_age(workspace: Path, main_file: Path):
    """Should catch invalid age (negative)."""
    subprocess.run(
        [sys.executable, str(main_file)],
        capture_output=True,
        cwd=str(workspace),
        timeout=30
    )
    
    output_file = workspace / "invalid_records.json"
    if output_file.exists():
        content = output_file.read_text().lower()
        # Eve Johnson has age -5
        has_age_error = "age" in content or "eve" in content
        assert has_age_error, "Did not catch invalid age"


def test_department_summary_has_aggregates(workspace: Path, main_file: Path):
    """Department summary should have aggregated stats."""
    subprocess.run(
        [sys.executable, str(main_file)],
        capture_output=True,
        cwd=str(workspace),
        timeout=30
    )
    
    output_file = workspace / "department_summary.json"
    if output_file.exists():
        data = json.loads(output_file.read_text())
        # Should have departments with counts
        has_aggregates = any(
            isinstance(v, dict) and ("count" in v or "avg" in str(v).lower())
            for v in data.values()
        ) if isinstance(data, dict) else False
        assert has_aggregates or len(data) > 0, \
            "Department summary missing aggregates"
