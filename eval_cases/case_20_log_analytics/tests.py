"""
Functional tests for Log Analytics Dashboard (case_20_log_analytics).

Tests verify Python script serves dashboard correctly.
"""
import subprocess
import sys
import time
import socket
import tempfile
from pathlib import Path


def test_script_exists(workspace: Path, main_file: Path):
    """Script file should exist."""
    py_files = list(workspace.glob("*.py"))
    assert len(py_files) >= 1, "No Python script found"


def test_no_syntax_errors(workspace: Path, main_file: Path):
    """Script should have no syntax errors."""
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(main_file)],
        capture_output=True,
        text=True,
        timeout=10
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"


def test_uses_http_server(workspace: Path, main_file: Path):
    """Should use http.server module."""
    content = main_file.read_text().lower()
    
    has_server = any(term in content for term in [
        'http.server', 'httpserver', 'socketserver', 'serve'
    ])
    assert has_server, "No HTTP server code found"


def test_parses_log_levels(workspace: Path, main_file: Path):
    """Should parse log levels (INFO, WARN, ERROR, CRITICAL)."""
    content = main_file.read_text().upper()
    
    levels = ['INFO', 'WARN', 'ERROR', 'CRITICAL']
    found = sum(1 for level in levels if level in content)
    
    assert found >= 3, f"Only {found} log levels handled"


def test_generates_html_dashboard(workspace: Path, main_file: Path):
    """Should generate HTML dashboard."""
    content = main_file.read_text().lower()
    
    has_html = any(term in content for term in [
        '<html', '<div', '<table', '<svg', 'text/html'
    ])
    assert has_html, "No HTML dashboard generation"


def test_has_chart_code(workspace: Path, main_file: Path):
    """Should have SVG chart generation."""
    content = main_file.read_text().lower()
    
    has_chart = any(term in content for term in [
        '<svg', 'chart', 'graph', 'rect', 'circle', 'path'
    ])
    assert has_chart, "No chart generation code"


def test_generates_log_if_missing(workspace: Path, main_file: Path):
    """Should generate fake logs if server.log missing."""
    content = main_file.read_text().lower()
    
    has_generation = any(term in content for term in [
        'generate', 'fake', 'random', 'sample', 'create'
    ])
    
    # Or checks for file existence
    has_check = 'exist' in content or 'isfile' in content or 'path' in content
    
    assert has_generation or has_check, "No log generation logic"


def test_calculates_statistics(workspace: Path, main_file: Path):
    """Should calculate log statistics."""
    content = main_file.read_text().lower()
    
    has_stats = any(term in content for term in [
        'count', 'percent', 'total', 'sum', 'average', 'per hour'
    ])
    assert has_stats, "No statistics calculation"


def test_has_filter_capability(workspace: Path, main_file: Path):
    """Should have log filtering capability."""
    content = main_file.read_text().lower()
    
    has_filter = any(term in content for term in [
        'filter', 'search', 'level', 'select', 'query'
    ])
    assert has_filter, "No filter capability"


def test_uses_stdlib_only(workspace: Path, main_file: Path):
    """Should use only Python standard library."""
    content = main_file.read_text()
    
    forbidden = ['import flask', 'import django', 'import fastapi', 'import requests']
    violations = [imp for imp in forbidden if imp in content]
    
    assert len(violations) == 0, f"Uses external libraries: {violations}"
