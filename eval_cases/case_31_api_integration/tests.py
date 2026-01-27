"""
Functional tests for Weather CLI (case_31_api_integration).

Tests verify the Python script works correctly.
Note: These tests run the Python file, not a browser.
"""
import subprocess
import sys
from pathlib import Path


def test_script_exists(workspace: Path, main_file: Path):
    """Weather script should exist."""
    weather_file = workspace / "weather.py"
    assert weather_file.exists() or main_file.name == "weather.py", \
        "weather.py not found"


def test_has_help_option(workspace: Path, main_file: Path):
    """Script should have --help option."""
    result = subprocess.run(
        [sys.executable, str(main_file), "--help"],
        capture_output=True,
        text=True,
        cwd=str(workspace),
        timeout=10
    )
    
    output = result.stdout.lower() + result.stderr.lower()
    assert "usage" in output or "help" in output or "weather" in output, \
        "No help output found"


def test_has_current_command(workspace: Path, main_file: Path):
    """Script should support 'current' command."""
    content = main_file.read_text().lower()
    assert "current" in content, "No 'current' command found in code"


def test_has_forecast_command(workspace: Path, main_file: Path):
    """Script should support 'forecast' command."""
    content = main_file.read_text().lower()
    assert "forecast" in content, "No 'forecast' command found in code"


def test_uses_open_meteo_api(workspace: Path, main_file: Path):
    """Should use Open-Meteo API."""
    content = main_file.read_text().lower()
    assert "open-meteo" in content or "api.open-meteo" in content, \
        "Open-Meteo API not referenced"


def test_uses_geocoding(workspace: Path, main_file: Path):
    """Should use geocoding to convert city names."""
    content = main_file.read_text().lower()
    has_geocoding = any(term in content for term in [
        "geocod", "latitude", "longitude", "lat", "lon", "coord"
    ])
    assert has_geocoding, "No geocoding logic found"


def test_has_error_handling(workspace: Path, main_file: Path):
    """Should have error handling."""
    content = main_file.read_text()
    has_try_except = "try:" in content and "except" in content
    has_error_check = "error" in content.lower() or "Error" in content
    assert has_try_except or has_error_check, "No error handling found"


def test_uses_argparse(workspace: Path, main_file: Path):
    """Should use argparse for CLI."""
    content = main_file.read_text()
    assert "argparse" in content or "sys.argv" in content, \
        "No CLI argument parsing found"


def test_uses_urllib_not_requests(workspace: Path, main_file: Path):
    """Should use urllib (stdlib), not requests."""
    content = main_file.read_text()
    assert "import requests" not in content, \
        "Should use urllib, not requests"
    assert "urllib" in content, "Should use urllib for HTTP requests"


def test_no_syntax_errors(workspace: Path, main_file: Path):
    """Script should have no syntax errors."""
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(main_file)],
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"
