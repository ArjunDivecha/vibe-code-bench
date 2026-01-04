"""
=============================================================================
SCRIPT NAME: test_validator.py
=============================================================================

Tests for the ExecutionValidator class.

Tests cover:
- Python script execution validation
- HTML file validation
- Import extraction and validation
- Error handling

VERSION: 1.0
LAST UPDATED: 2026-01-04

=============================================================================
"""

import tempfile
import pytest
from pathlib import Path

from vibe_eval.sandbox.validator import (
    ExecutionValidator,
    ExecutionReport,
    STDLIB_MODULES
)


class TestPythonValidation:
    """Tests for Python script validation."""

    def test_valid_python_executes(self):
        """Script that prints 'hello' should execute successfully."""
        validator = ExecutionValidator(timeout=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('print("hello")')

            result = validator.validate_python(script, Path(tmpdir))

            assert result.executed is True
            assert result.exit_code == 0
            assert "hello" in result.stdout
            assert result.file_type == "python"

    def test_invalid_python_syntax_fails(self):
        """Script with syntax error should fail."""
        validator = ExecutionValidator(timeout=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('print("hello"')  # Missing closing paren

            result = validator.validate_python(script, Path(tmpdir))

            assert result.executed is False
            assert len(result.errors) > 0
            assert "Syntax error" in result.errors[0]

    def test_runtime_error_fails(self):
        """Script that raises exception should fail."""
        validator = ExecutionValidator(timeout=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('raise ValueError("test error")')

            result = validator.validate_python(script, Path(tmpdir))

            assert result.executed is False
            assert result.exit_code != 0
            assert "ValueError" in result.stderr

    def test_timeout_fails(self):
        """Script that runs too long should timeout."""
        validator = ExecutionValidator(timeout=2)

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('import time; time.sleep(10)')

            result = validator.validate_python(script, Path(tmpdir))

            assert result.executed is False
            assert "timed out" in str(result.errors).lower()

    def test_missing_module_fails(self):
        """Script importing non-existent module should fail."""
        validator = ExecutionValidator(timeout=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('import nonexistent_module_xyz')

            result = validator.validate_python(script, Path(tmpdir))

            assert result.executed is False
            assert "ModuleNotFoundError" in result.stderr or len(result.illegal_imports) > 0


class TestImportExtraction:
    """Tests for import extraction."""

    def test_extract_simple_import(self):
        """Should extract simple import statements."""
        validator = ExecutionValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('import os\nimport sys')

            imports = validator.extract_imports(script)

            assert "os" in imports
            assert "sys" in imports

    def test_extract_from_import(self):
        """Should extract 'from X import Y' statements."""
        validator = ExecutionValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('from pathlib import Path\nfrom json import loads')

            imports = validator.extract_imports(script)

            assert "pathlib" in imports
            assert "json" in imports

    def test_extract_nested_import(self):
        """Should extract top-level module from nested imports."""
        validator = ExecutionValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('import os.path\nfrom urllib.parse import urlparse')

            imports = validator.extract_imports(script)

            assert "os" in imports
            assert "urllib" in imports

    def test_ignore_relative_imports(self):
        """Should ignore relative imports (from . import)."""
        validator = ExecutionValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('from . import utils\nfrom .helpers import foo')

            imports = validator.extract_imports(script)

            assert len(imports) == 0

    def test_stdlib_import_valid(self):
        """Stdlib imports should be valid."""
        validator = ExecutionValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('import json\nimport os\nimport sys\nimport pathlib')

            valid, illegal = validator.validate_imports(script)

            assert valid is True
            assert len(illegal) == 0

    def test_external_import_invalid(self):
        """Non-stdlib imports should be detected."""
        validator = ExecutionValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('import pandas\nimport numpy\nimport os')

            valid, illegal = validator.validate_imports(script)

            assert valid is False
            assert "pandas" in illegal
            assert "numpy" in illegal
            assert "os" not in illegal

    def test_requests_import_invalid(self):
        """Common third-party packages should be detected."""
        validator = ExecutionValidator()

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('import requests\nfrom requests.auth import HTTPBasicAuth')

            valid, illegal = validator.validate_imports(script)

            assert valid is False
            assert "requests" in illegal


class TestHTMLValidation:
    """Tests for HTML validation."""

    def test_valid_html_basic(self):
        """Valid HTML file should pass basic validation."""
        validator = ExecutionValidator(timeout=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "index.html"
            html_file.write_text('''<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body><h1>Hello World</h1></body>
</html>''')

            result = validator.validate_html(html_file)

            assert result.executed is True
            assert result.file_type == "html"

    def test_missing_html_tag(self):
        """HTML without proper tags should fail basic validation."""
        validator = ExecutionValidator(timeout=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "index.html"
            html_file.write_text('<div>No HTML tags</div>')

            # This uses basic validation which checks for <html> and <body>
            result = validator._validate_html_basic(html_file)

            assert result.executed is False
            assert any("html" in e.lower() for e in result.errors)

    def test_html_file_not_found(self):
        """Non-existent file should return error."""
        validator = ExecutionValidator(timeout=10)

        result = validator.validate_html(Path("/nonexistent/file.html"))

        assert result.executed is False
        assert any("not found" in e.lower() for e in result.errors)


class TestWorkspaceValidation:
    """Tests for full workspace validation."""

    def test_workspace_with_python(self):
        """Workspace with Python files should validate Python."""
        validator = ExecutionValidator(timeout=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "main.py"
            script.write_text('print("hello from workspace")')

            result = validator.validate(Path(tmpdir))

            assert result.executed is True
            assert result.file_type == "python"

    def test_workspace_with_html(self):
        """Workspace with only HTML should validate HTML."""
        validator = ExecutionValidator(timeout=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            html_file = Path(tmpdir) / "index.html"
            html_file.write_text('''<!DOCTYPE html>
<html><body>Test</body></html>''')

            result = validator.validate(Path(tmpdir))

            assert result.file_type == "html"

    def test_empty_workspace(self):
        """Empty workspace should return error."""
        validator = ExecutionValidator(timeout=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = validator.validate(Path(tmpdir))

            assert result.executed is False
            assert "No Python or HTML files" in str(result.errors)

    def test_finds_main_py_priority(self):
        """Should prefer main.py over other Python files."""
        validator = ExecutionValidator(timeout=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple Python files
            (Path(tmpdir) / "other.py").write_text('print("other")')
            (Path(tmpdir) / "main.py").write_text('print("main")')

            result = validator.validate(Path(tmpdir))

            assert result.executed is True
            assert "main" in result.stdout


class TestStdlibModules:
    """Tests for stdlib module list."""

    def test_common_stdlib_included(self):
        """Common stdlib modules should be in the list."""
        common = ['os', 'sys', 'json', 'pathlib', 'datetime', 'collections',
                  'itertools', 'functools', 're', 'math', 'random', 'sqlite3',
                  'http', 'urllib', 'csv', 'xml', 'logging', 'unittest']

        for module in common:
            assert module in STDLIB_MODULES, f"{module} should be in STDLIB_MODULES"

    def test_common_external_excluded(self):
        """Common external packages should NOT be in the list."""
        external = ['numpy', 'pandas', 'requests', 'flask', 'django',
                    'tensorflow', 'torch', 'scipy', 'matplotlib', 'sklearn']

        for module in external:
            assert module not in STDLIB_MODULES, f"{module} should NOT be in STDLIB_MODULES"


class TestExecutionReport:
    """Tests for ExecutionReport dataclass."""

    def test_to_dict(self):
        """ExecutionReport should serialize to dict."""
        report = ExecutionReport(
            executed=True,
            exit_code=0,
            stdout="hello",
            stderr="",
            execution_time=1.5,
            errors=[],
            illegal_imports=[],
            file_type="python"
        )

        d = report.to_dict()

        assert d["executed"] is True
        assert d["exit_code"] == 0
        assert d["stdout"] == "hello"
        assert d["file_type"] == "python"

    def test_to_dict_truncates_long_output(self):
        """Long stdout/stderr should be truncated in dict."""
        long_text = "x" * 10000
        report = ExecutionReport(
            executed=True,
            stdout=long_text,
            stderr=long_text,
            file_type="python"
        )

        d = report.to_dict()

        assert len(d["stdout"]) <= 5000
        assert len(d["stderr"]) <= 5000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
