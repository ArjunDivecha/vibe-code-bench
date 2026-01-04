"""
=============================================================================
SCRIPT NAME: validator.py
=============================================================================

Validates that generated code actually executes without errors and enforces
the zero-dependency constraint.

INPUT:
- workspace_path: Path to directory containing generated code files

OUTPUT:
- ExecutionReport: Dataclass with execution status, errors, and details

VERSION: 1.0
LAST UPDATED: 2026-01-04

DESCRIPTION:
This module provides runtime validation for generated code. It:
1. Runs Python scripts and captures exit codes/errors
2. Validates HTML files load without JS errors using Playwright
3. Extracts and validates imports against Python stdlib whitelist

DEPENDENCIES:
- ast (stdlib)
- subprocess (stdlib)
- pathlib (stdlib)
- dataclasses (stdlib)
- playwright (for HTML validation)

=============================================================================
"""

import ast
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Complete Python 3.11 stdlib modules list
STDLIB_MODULES = {
    # Built-in modules
    '__future__', '__main__', '_thread', 'abc', 'aifc', 'argparse',
    'array', 'ast', 'asynchat', 'asyncio', 'asyncore', 'atexit',
    'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect',
    'builtins', 'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath',
    'cmd', 'code', 'codecs', 'codeop', 'collections', 'colorsys',
    'compileall', 'concurrent', 'configparser', 'contextlib',
    'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
    'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal',
    'difflib', 'dis', 'distutils', 'doctest', 'email', 'encodings',
    'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput',
    'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt',
    'getpass', 'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib',
    'heapq', 'hmac', 'html', 'http', 'idlelib', 'imaplib', 'imghdr',
    'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools',
    'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging',
    'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes',
    'mmap', 'modulefinder', 'multiprocessing', 'netrc', 'nis',
    'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev',
    'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil',
    'platform', 'plistlib', 'poplib', 'posix', 'posixpath', 'pprint',
    'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr',
    'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib',
    'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select',
    'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site',
    'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd',
    'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep',
    'struct', 'subprocess', 'sunau', 'symtable', 'sys', 'sysconfig',
    'syslog', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios',
    'test', 'textwrap', 'threading', 'time', 'timeit', 'tkinter',
    'token', 'tokenize', 'tomllib', 'trace', 'traceback', 'tracemalloc',
    'tty', 'turtle', 'turtledemo', 'types', 'typing', 'typing_extensions',
    'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv',
    'warnings', 'wave', 'weakref', 'webbrowser', 'winreg', 'winsound',
    'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile',
    'zipimport', 'zlib', 'zoneinfo',
    # Common sub-packages that should also be allowed
    'collections.abc', 'concurrent.futures', 'email.mime',
    'html.parser', 'http.client', 'http.server', 'http.cookies',
    'importlib.util', 'importlib.metadata', 'logging.handlers',
    'multiprocessing.pool', 'os.path', 'unittest.mock',
    'urllib.request', 'urllib.parse', 'urllib.error',
    'xml.etree', 'xml.etree.ElementTree', 'xml.dom', 'xml.sax',
}


@dataclass
class ExecutionReport:
    """Result of code execution validation."""
    executed: bool
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    execution_time: float = 0.0
    errors: list[str] = field(default_factory=list)
    illegal_imports: list[str] = field(default_factory=list)
    screenshot: Optional[bytes] = None  # For HTML validation
    file_type: str = ""  # 'python', 'html', etc.

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "executed": self.executed,
            "exit_code": self.exit_code,
            "stdout": self.stdout[:5000] if self.stdout else "",
            "stderr": self.stderr[:5000] if self.stderr else "",
            "execution_time": self.execution_time,
            "errors": self.errors,
            "illegal_imports": self.illegal_imports,
            "file_type": self.file_type,
        }


class ExecutionValidator:
    """
    Validates that generated code actually executes without errors.

    V2: Reuses Playwright browser instance across validations for speed.

    Provides methods for:
    - Running Python scripts and capturing results
    - Validating HTML files with Playwright (headless browser)
    - Extracting and validating imports
    """

    # V2: Shared browser instance for all validators
    _playwright = None
    _browser = None

    def __init__(self, timeout: int = 30):
        """
        Initialize validator.

        Args:
            timeout: Maximum seconds to run each validation
        """
        self.timeout = timeout

    @classmethod
    def _get_browser(cls):
        """
        Get or create a shared browser instance.

        V2: Reuses browser across validations for ~500ms savings per HTML file.
        """
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
        """
        Clean up shared browser instance.

        Call this at end of eval run to release resources.
        """
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

    def validate(self, workspace_path: Path) -> ExecutionReport:
        """
        Validate all code files in workspace.

        Finds main entry point and validates it.

        Args:
            workspace_path: Directory containing generated code

        Returns:
            ExecutionReport with combined validation results
        """
        workspace = Path(workspace_path)

        # Find primary entry point
        python_files = list(workspace.glob("**/*.py"))
        html_files = list(workspace.glob("**/*.html"))

        # Priority: main.py > app.py > index.py > first .py
        # For HTML: index.html > first .html

        if python_files:
            main_file = self._find_main_python(python_files, workspace)
            if main_file:
                return self.validate_python(main_file, workspace)

        if html_files:
            main_file = self._find_main_html(html_files, workspace)
            if main_file:
                return self.validate_html(main_file)

        # No files to validate
        return ExecutionReport(
            executed=False,
            errors=["No Python or HTML files found to validate"],
            file_type="none"
        )

    def _find_main_python(self, files: list[Path], workspace: Path) -> Optional[Path]:
        """Find the main Python entry point."""
        priority = ["main.py", "app.py", "index.py", "run.py", "server.py"]

        for name in priority:
            for f in files:
                if f.name == name:
                    return f

        # Return first file at root level, or just first file
        root_files = [f for f in files if f.parent == workspace]
        return root_files[0] if root_files else (files[0] if files else None)

    def _find_main_html(self, files: list[Path], workspace: Path = None) -> Optional[Path]:
        """Find the main HTML entry point."""
        priority = ["index.html", "main.html", "app.html"]

        for name in priority:
            for f in files:
                if f.name == name:
                    return f

        return files[0] if files else None

    def validate_python(self, filepath: Path, workspace: Path = None) -> ExecutionReport:
        """
        Validate a Python script by running it.

        Args:
            filepath: Path to Python file
            workspace: Working directory for execution

        Returns:
            ExecutionReport with execution results
        """
        import time

        filepath = Path(filepath)
        workspace = workspace or filepath.parent

        errors = []

        # Step 1: Check syntax
        try:
            source = filepath.read_text()
            ast.parse(source)
        except SyntaxError as e:
            return ExecutionReport(
                executed=False,
                errors=[f"Syntax error: {e}"],
                file_type="python"
            )

        # Step 2: Check imports
        illegal = self.extract_illegal_imports(filepath)
        if illegal:
            errors.append(f"Illegal imports detected: {', '.join(illegal)}")

        # Step 3: Try to run the script
        start_time = time.time()
        try:
            result = subprocess.run(
                [sys.executable, str(filepath)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(workspace),
                env={**subprocess.os.environ, "PYTHONUNBUFFERED": "1"}
            )
            elapsed = time.time() - start_time

            # Check for import errors in stderr (ModuleNotFoundError)
            if "ModuleNotFoundError" in result.stderr:
                errors.append(f"Missing module: {result.stderr.split('ModuleNotFoundError:')[1].split(chr(10))[0].strip()}")

            return ExecutionReport(
                executed=(result.returncode == 0 and len(illegal) == 0),
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                execution_time=elapsed,
                errors=errors if result.returncode != 0 else [],
                illegal_imports=illegal,
                file_type="python"
            )

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            return ExecutionReport(
                executed=False,
                exit_code=-1,
                errors=[f"Execution timed out after {self.timeout}s"],
                execution_time=elapsed,
                illegal_imports=illegal,
                file_type="python"
            )
        except Exception as e:
            return ExecutionReport(
                executed=False,
                exit_code=-1,
                errors=[f"Execution error: {str(e)}"],
                illegal_imports=illegal,
                file_type="python"
            )

    def validate_html(self, filepath: Path) -> ExecutionReport:
        """
        Validate an HTML file by loading it in a headless browser.

        V2: Uses shared browser instance for faster validation.

        Args:
            filepath: Path to HTML file

        Returns:
            ExecutionReport with browser validation results
        """
        import time

        filepath = Path(filepath)

        if not filepath.exists():
            return ExecutionReport(
                executed=False,
                errors=[f"File not found: {filepath}"],
                file_type="html"
            )

        # V2: Get shared browser instance
        browser = self._get_browser()
        if browser is None:
            # Playwright not available - do basic validation only
            return self._validate_html_basic(filepath)

        errors = []
        console_errors = []
        screenshot = None
        start_time = time.time()

        try:
            # V2: Create new page on shared browser (much faster than launching browser)
            page = browser.new_page()

            # Capture JS errors
            def handle_error(error):
                console_errors.append(f"JS Error: {str(error)}")

            def handle_console(msg):
                if msg.type == "error":
                    console_errors.append(f"Console error: {msg.text}")

            page.on("pageerror", handle_error)
            page.on("console", handle_console)

            # Load the file
            file_url = f"file://{filepath.absolute()}"
            page.goto(file_url, wait_until="networkidle", timeout=self.timeout * 1000)

            # Take screenshot
            screenshot = page.screenshot()

            # V2: Close page but NOT browser (reuse browser)
            page.close()

            elapsed = time.time() - start_time

            if console_errors:
                errors.extend(console_errors)

            return ExecutionReport(
                executed=(len(errors) == 0),
                exit_code=0 if len(errors) == 0 else 1,
                execution_time=elapsed,
                errors=errors,
                screenshot=screenshot,
                file_type="html"
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return ExecutionReport(
                executed=False,
                exit_code=-1,
                errors=[f"Browser validation error: {str(e)}"],
                execution_time=elapsed,
                file_type="html"
            )

    def _validate_html_basic(self, filepath: Path) -> ExecutionReport:
        """
        Basic HTML validation without Playwright.

        Just checks that file exists and is parseable.
        """
        import time

        start_time = time.time()

        try:
            content = filepath.read_text()

            # Basic checks
            errors = []

            if "<html" not in content.lower():
                errors.append("Missing <html> tag")

            if "<body" not in content.lower():
                errors.append("Missing <body> tag")

            elapsed = time.time() - start_time

            return ExecutionReport(
                executed=(len(errors) == 0),
                exit_code=0 if len(errors) == 0 else 1,
                execution_time=elapsed,
                errors=errors,
                file_type="html",
                stderr="Note: Playwright not installed - basic validation only"
            )

        except Exception as e:
            return ExecutionReport(
                executed=False,
                exit_code=-1,
                errors=[f"HTML read error: {str(e)}"],
                file_type="html"
            )

    def extract_imports(self, filepath: Path) -> set[str]:
        """
        Extract all import module names from a Python file.

        Args:
            filepath: Path to Python file

        Returns:
            Set of top-level module names imported
        """
        filepath = Path(filepath)

        try:
            source = filepath.read_text()
            tree = ast.parse(source)
        except (SyntaxError, FileNotFoundError):
            return set()

        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get top-level module (e.g., 'os' from 'os.path')
                    top_module = alias.name.split('.')[0]
                    imports.add(top_module)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Skip relative imports (they're local)
                    if node.level == 0:
                        top_module = node.module.split('.')[0]
                        imports.add(top_module)

        return imports

    def extract_illegal_imports(self, filepath: Path) -> list[str]:
        """
        Find imports that are not in the Python stdlib.

        Args:
            filepath: Path to Python file

        Returns:
            List of illegal (non-stdlib) import names
        """
        imports = self.extract_imports(filepath)
        illegal = []

        for module in imports:
            if module not in STDLIB_MODULES:
                illegal.append(module)

        return sorted(illegal)

    def validate_imports(self, filepath: Path) -> tuple[bool, list[str]]:
        """
        Check if all imports are from stdlib.

        Args:
            filepath: Path to Python file

        Returns:
            Tuple of (is_valid, list_of_illegal_imports)
        """
        illegal = self.extract_illegal_imports(filepath)
        return (len(illegal) == 0, illegal)
