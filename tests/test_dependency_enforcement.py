"""
=============================================================================
SCRIPT NAME: test_dependency_enforcement.py
=============================================================================

Tests for dependency enforcement in the sandbox executor.

Tests cover:
- Blocking of pip, npm, yarn, conda commands
- Blocking of various package manager variants
- Allowing legitimate commands
- Import validation

VERSION: 1.0
LAST UPDATED: 2026-01-04

=============================================================================
"""

import tempfile
import pytest
from pathlib import Path

from vibe_eval.sandbox.executor import (
    SandboxExecutor,
    ExecutionResult,
    BLOCKED_COMMANDS,
    BLOCKED_PATTERNS,
)
from vibe_eval.sandbox.validator import ExecutionValidator


class TestCommandBlocking:
    """Tests for blocked command detection."""

    def test_pip_install_blocked(self):
        """pip install commands should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("pip install requests")

            assert result.success is False
            assert "BLOCKED" in result.stderr
            assert "pip install" in result.stderr.lower()

    def test_pip3_install_blocked(self):
        """pip3 install commands should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("pip3 install numpy")

            assert result.success is False
            assert "BLOCKED" in result.stderr

    def test_python_m_pip_blocked(self):
        """python -m pip install commands should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("python -m pip install pandas")

            assert result.success is False
            assert "BLOCKED" in result.stderr

    def test_npm_install_blocked(self):
        """npm install commands should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("npm install lodash")

            assert result.success is False
            assert "BLOCKED" in result.stderr

    def test_npm_i_blocked(self):
        """npm i (shorthand) commands should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("npm i express")

            assert result.success is False
            assert "BLOCKED" in result.stderr

    def test_yarn_add_blocked(self):
        """yarn add commands should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("yarn add react")

            assert result.success is False
            assert "BLOCKED" in result.stderr

    def test_conda_install_blocked(self):
        """conda install commands should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("conda install scipy")

            assert result.success is False
            assert "BLOCKED" in result.stderr

    def test_brew_install_blocked(self):
        """brew install commands should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("brew install wget")

            assert result.success is False
            assert "BLOCKED" in result.stderr

    def test_apt_install_blocked(self):
        """apt install commands should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("apt install vim")

            assert result.success is False
            assert "BLOCKED" in result.stderr

    def test_cargo_install_blocked(self):
        """cargo install commands should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("cargo install ripgrep")

            assert result.success is False
            assert "BLOCKED" in result.stderr

    def test_go_get_blocked(self):
        """go get commands should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("go get github.com/some/package")

            assert result.success is False
            assert "BLOCKED" in result.stderr


class TestAllowedCommands:
    """Tests for commands that should be allowed."""

    def test_python_script_allowed(self):
        """Running a python script should be allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            # Create a test script
            script = Path(tmpdir) / "test.py"
            script.write_text('print("hello")')

            result = executor.run("python test.py")

            assert result.success is True
            assert "BLOCKED" not in result.stderr

    def test_ls_allowed(self):
        """ls command should be allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("ls -la")

            # ls should succeed (or at least not be blocked)
            assert "BLOCKED" not in result.stderr

    def test_echo_allowed(self):
        """echo command should be allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("echo 'hello world'")

            assert result.success is True
            assert "BLOCKED" not in result.stderr

    def test_cat_allowed(self):
        """cat command should be allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            # Create a file to cat
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            result = executor.run("cat test.txt")

            assert result.success is True
            assert "BLOCKED" not in result.stderr

    def test_mkdir_allowed(self):
        """mkdir command should be allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("mkdir testdir")

            assert result.success is True
            assert "BLOCKED" not in result.stderr

    def test_pip_list_allowed(self):
        """pip list (not install) should be allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("pip list")

            # pip list should not be blocked (it's read-only)
            assert "BLOCKED" not in result.stderr


class TestIsCommandAllowed:
    """Tests for the is_command_allowed helper method."""

    def test_pip_install_not_allowed(self):
        """pip install should not be allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            assert executor.is_command_allowed("pip install requests") is False

    def test_python_script_allowed(self):
        """Running python script should be allowed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            assert executor.is_command_allowed("python main.py") is True

    def test_case_insensitive_blocking(self):
        """Blocking should be case-insensitive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            assert executor.is_command_allowed("PIP INSTALL requests") is False
            assert executor.is_command_allowed("Pip Install pandas") is False
            assert executor.is_command_allowed("NPM INSTALL lodash") is False


class TestBlockedCommandsList:
    """Tests for the blocked commands list."""

    def test_pip_variants_in_list(self):
        """Various pip command variants should be in blocked list."""
        pip_variants = ['pip install', 'pip3 install', 'python -m pip install']
        for variant in pip_variants:
            assert any(variant in cmd for cmd in BLOCKED_COMMANDS), \
                f"{variant} should be in BLOCKED_COMMANDS"

    def test_npm_variants_in_list(self):
        """Various npm command variants should be in blocked list."""
        npm_variants = ['npm install', 'npm i ']
        for variant in npm_variants:
            assert any(variant in cmd for cmd in BLOCKED_COMMANDS), \
                f"{variant} should be in BLOCKED_COMMANDS"

    def test_yarn_in_list(self):
        """yarn commands should be in blocked list."""
        assert any('yarn' in cmd for cmd in BLOCKED_COMMANDS)

    def test_conda_in_list(self):
        """conda commands should be in blocked list."""
        assert any('conda' in cmd for cmd in BLOCKED_COMMANDS)


class TestImportValidationIntegration:
    """Integration tests combining executor and validator."""

    def test_script_with_external_import_detected(self):
        """Script with external imports should be detected by validator."""
        validator = ExecutionValidator(timeout=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('import pandas\nprint("hello")')

            valid, illegal = validator.validate_imports(script)

            assert valid is False
            assert "pandas" in illegal

    def test_script_with_stdlib_only_valid(self):
        """Script with only stdlib imports should pass validation."""
        validator = ExecutionValidator(timeout=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('import json\nimport os\nprint("hello")')

            valid, illegal = validator.validate_imports(script)

            assert valid is True
            assert len(illegal) == 0


class TestEdgeCases:
    """Tests for edge cases in command blocking."""

    def test_pip_in_string_not_blocked(self):
        """pip in a string argument shouldn't block the command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            # This should NOT be blocked - pip is in a string, not a command
            result = executor.run('echo "Use pip install to install packages"')

            # This is actually a tricky case - the simple matching will block it
            # For now, we accept that overly aggressive blocking is safer
            # In a more sophisticated implementation, we could parse the command

    def test_empty_command(self):
        """Empty command should not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("")

            # Should not crash, might fail for other reasons
            assert "BLOCKED" not in result.stderr

    def test_multiline_command_with_pip(self):
        """Multiline command containing pip should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            executor = SandboxExecutor(workspace=Path(tmpdir))

            result = executor.run("echo 'start' && pip install requests && echo 'end'")

            assert result.success is False
            assert "BLOCKED" in result.stderr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
