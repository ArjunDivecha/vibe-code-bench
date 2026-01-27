"""
Functional tests for Refactor task (case_33_refactor).

Tests verify the refactored package works correctly.
"""
import subprocess
import sys
from pathlib import Path


def test_package_structure_exists(workspace: Path, main_file: Path):
    """Should have inventory/ package directory."""
    inventory_dir = workspace / "inventory"
    assert inventory_dir.exists() and inventory_dir.is_dir(), \
        "inventory/ package directory not found"


def test_has_init_file(workspace: Path, main_file: Path):
    """Package should have __init__.py."""
    init_file = workspace / "inventory" / "__init__.py"
    assert init_file.exists(), "inventory/__init__.py not found"


def test_has_models_module(workspace: Path, main_file: Path):
    """Should have models.py module."""
    models_file = workspace / "inventory" / "models.py"
    assert models_file.exists(), "inventory/models.py not found"


def test_has_storage_module(workspace: Path, main_file: Path):
    """Should have storage.py module."""
    storage_file = workspace / "inventory" / "storage.py"
    assert storage_file.exists(), "inventory/storage.py not found"


def test_has_manager_module(workspace: Path, main_file: Path):
    """Should have manager.py module."""
    manager_file = workspace / "inventory" / "manager.py"
    assert manager_file.exists(), "inventory/manager.py not found"


def test_has_reports_module(workspace: Path, main_file: Path):
    """Should have reports.py module."""
    reports_file = workspace / "inventory" / "reports.py"
    assert reports_file.exists(), "inventory/reports.py not found"


def test_has_cli_module(workspace: Path, main_file: Path):
    """Should have cli.py module."""
    cli_file = workspace / "inventory" / "cli.py"
    assert cli_file.exists(), "inventory/cli.py not found"


def test_has_run_entry_point(workspace: Path, main_file: Path):
    """Should have run.py entry point."""
    run_file = workspace / "run.py"
    assert run_file.exists(), "run.py entry point not found"


def test_no_import_errors(workspace: Path, main_file: Path):
    """Package should import without errors."""
    result = subprocess.run(
        [sys.executable, "-c", "import inventory"],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=10
    )
    assert result.returncode == 0, f"Import error: {result.stderr}"


def test_cli_runs(workspace: Path, main_file: Path):
    """CLI should run with help."""
    run_file = workspace / "run.py"
    if not run_file.exists():
        run_file = main_file
    
    result = subprocess.run(
        [sys.executable, str(run_file)],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=10
    )
    
    output = result.stdout.lower() + result.stderr.lower()
    # Should show usage or help
    assert "usage" in output or "command" in output or result.returncode == 0, \
        f"CLI doesn't run: {output}"
