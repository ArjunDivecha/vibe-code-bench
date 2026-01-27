"""
Functional tests for Git Stats Infographic (case_16_repostats).

Tests verify Python script produces correct HTML output.
"""
import subprocess
import sys
import os
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


def test_script_runs(workspace: Path, main_file: Path):
    """Script should run without errors."""
    # Create a temp git repo for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)
        
        # Create a file and commit
        Path(tmpdir, "test.txt").write_text("hello")
        subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "test"], cwd=tmpdir, capture_output=True)
        
        # Run script
        result = subprocess.run(
            [sys.executable, str(main_file), tmpdir],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(workspace)
        )
        
        # Should not crash (exit code 0 or produces output)
        assert result.returncode == 0 or len(result.stdout) > 0, \
            f"Script failed: {result.stderr}"


def test_produces_html(workspace: Path, main_file: Path):
    """Script should produce HTML output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)
        Path(tmpdir, "test.py").write_text("print('hello')")
        subprocess.run(["git", "add", "."], cwd=tmpdir, capture_output=True)
        subprocess.run(["git", "commit", "-m", "test"], cwd=tmpdir, capture_output=True)
        
        result = subprocess.run(
            [sys.executable, str(main_file), tmpdir],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(workspace)
        )
        
        output = result.stdout.lower()
        has_html = '<html' in output or '<!doctype' in output or '<div' in output
        
        # Or check for HTML file created
        html_files = list(workspace.glob("*.html")) + list(Path(tmpdir).glob("*.html"))
        
        assert has_html or len(html_files) > 0, "No HTML output produced"


def test_uses_stdlib_only(workspace: Path, main_file: Path):
    """Should use only Python standard library."""
    content = main_file.read_text()
    
    forbidden = ['import requests', 'import pandas', 'import numpy', 'from bs4']
    violations = [imp for imp in forbidden if imp in content]
    
    assert len(violations) == 0, f"Uses external libraries: {violations}"


def test_has_git_commands(workspace: Path, main_file: Path):
    """Should use git commands to get stats."""
    content = main_file.read_text().lower()
    
    has_git = any(term in content for term in [
        'git log', 'git show', 'git diff', 'subprocess', 'os.popen'
    ])
    assert has_git, "No git commands found"


def test_includes_commit_count(workspace: Path, main_file: Path):
    """Output should include commit count."""
    content = main_file.read_text().lower()
    
    has_commits = any(term in content for term in [
        'commit', 'commits', 'total', 'count'
    ])
    assert has_commits, "No commit counting logic"


def test_includes_author_stats(workspace: Path, main_file: Path):
    """Should include author/contributor stats."""
    content = main_file.read_text().lower()
    
    has_authors = any(term in content for term in [
        'author', 'contributor', 'user', 'name'
    ])
    assert has_authors, "No author stats logic"
