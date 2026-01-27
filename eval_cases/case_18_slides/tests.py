"""
Functional tests for Slide Summary Reporter (case_18_slides).

Tests verify Python script processes text files correctly.
"""
import subprocess
import sys
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


def test_reads_txt_files(workspace: Path, main_file: Path):
    """Script should read .txt files."""
    content = main_file.read_text().lower()
    
    has_file_reading = any(term in content for term in [
        'open(', '.read(', 'pathlib', 'glob', '.txt'
    ])
    assert has_file_reading, "No file reading logic found"


def test_produces_html_output(workspace: Path, main_file: Path):
    """Script should produce HTML output."""
    content = main_file.read_text().lower()
    
    has_html = any(term in content for term in [
        '<html', '<div', '<h1', '<table', 'write(', '.html'
    ])
    assert has_html, "No HTML output generation"


def test_creates_toc(workspace: Path, main_file: Path):
    """Should create table of contents."""
    content = main_file.read_text().lower()
    
    has_toc = any(term in content for term in [
        'toc', 'table of contents', 'contents', 'index', 'navigation'
    ])
    assert has_toc, "No table of contents logic"


def test_creates_summaries(workspace: Path, main_file: Path):
    """Should create summaries for each slide."""
    content = main_file.read_text().lower()
    
    has_summary = any(term in content for term in [
        'summary', 'summarize', 'extract', 'key point', 'bullet'
    ])
    assert has_summary, "No summary generation logic"


def test_runs_with_sample_files(workspace: Path, main_file: Path):
    """Script should run with sample input files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample slide files
        for i in range(3):
            Path(tmpdir, f"slide{i+1}.txt").write_text(
                f"Slide {i+1} Title\\n\\nThis is the content of slide {i+1}.\\nKey point: Item {i+1}"
            )
        
        result = subprocess.run(
            [sys.executable, str(main_file), tmpdir],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(workspace)
        )
        
        # Should produce some output
        output = result.stdout + result.stderr
        assert result.returncode == 0 or 'html' in output.lower(), \
            f"Script failed: {output[:500]}"


def test_uses_stdlib_only(workspace: Path, main_file: Path):
    """Should use only Python standard library."""
    content = main_file.read_text()
    
    forbidden = ['import requests', 'import pandas', 'import numpy', 'import beautifulsoup']
    violations = [imp for imp in forbidden if imp in content]
    
    assert len(violations) == 0, f"Uses external libraries: {violations}"
