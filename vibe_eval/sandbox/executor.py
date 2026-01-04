"""
=============================================================================
SCRIPT NAME: executor.py
=============================================================================

Sandbox executor for running code in isolated environment with dependency
enforcement.

VERSION: 2.0
LAST UPDATED: 2026-01-04

DESCRIPTION:
Executes generated code in a sandboxed environment. Now includes:
- Blocking of package manager commands (pip, npm, etc.)
- Zero-dependency enforcement for vibe-coding evaluation

=============================================================================
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# Package manager commands that are blocked
BLOCKED_COMMANDS = [
    # Python package managers
    'pip install', 'pip3 install', 'pip uninstall', 'pip3 uninstall',
    'python -m pip install', 'python3 -m pip install',
    'python -m pip uninstall', 'python3 -m pip uninstall',
    'conda install', 'conda create', 'mamba install',
    'poetry add', 'poetry install',
    'pipenv install', 'pdm add',
    # Node.js package managers
    'npm install', 'npm i ', 'npm ci', 'npm add',
    'yarn add', 'yarn install',
    'pnpm install', 'pnpm add',
    'bun install', 'bun add',
    # Other package managers
    'brew install', 'apt install', 'apt-get install',
    'yum install', 'dnf install', 'pacman -S',
    'cargo add', 'cargo install',
    'go get', 'go install',
    'gem install', 'bundle install',
    'composer require', 'composer install',
    'nuget install', 'dotnet add package',
]

# Patterns to detect in commands (more flexible matching)
BLOCKED_PATTERNS = [
    'pip install',
    'pip3 install',
    'npm install',
    'npm i ',
    'yarn add',
    'conda install',
]


@dataclass
class ExecutionResult:
    """Result of a command execution."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    timed_out: bool = False


class SandboxExecutor:
    """
    Execute code in an isolated temporary directory with timeout.
    
    Provides a sandboxed environment for running generated code
    during evaluation. Each command runs in the workspace directory.
    """
    
    def __init__(
        self, 
        workspace: Path,
        timeout: int = 60,
        max_output_chars: int = 10000
    ):
        """
        Initialize sandbox executor.
        
        Args:
            workspace: Working directory for code execution
            timeout: Maximum seconds per command
            max_output_chars: Truncate output beyond this length
        """
        self.workspace = Path(workspace)
        self.timeout = timeout
        self.max_output_chars = max_output_chars
        
        # Ensure workspace exists
        self.workspace.mkdir(parents=True, exist_ok=True)
    
    def run(self, command: str) -> ExecutionResult:
        """
        Run a command in the sandbox.

        Args:
            command: Shell command to execute

        Returns:
            ExecutionResult with success status and output

        Note:
            Package manager commands (pip, npm, etc.) are blocked
            to enforce the zero-dependency constraint.
        """
        # Check for blocked commands
        blocked = self._check_blocked_command(command)
        if blocked:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"BLOCKED: Package manager commands are not allowed. "
                       f"This benchmark requires zero external dependencies.\n"
                       f"Blocked command pattern: '{blocked}'",
                return_code=1,
                timed_out=False
            )

        try:
            # Set up environment with workspace in PATH-friendly way
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"

            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env
            )

            return ExecutionResult(
                success=result.returncode == 0,
                stdout=self._truncate(result.stdout),
                stderr=self._truncate(result.stderr),
                return_code=result.returncode,
                timed_out=False
            )

        except subprocess.TimeoutExpired as e:
            return ExecutionResult(
                success=False,
                stdout=self._truncate(e.stdout or "") if e.stdout else "",
                stderr=f"Command timed out after {self.timeout} seconds",
                return_code=-1,
                timed_out=True
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                return_code=-1,
                timed_out=False
            )

    def _check_blocked_command(self, command: str) -> Optional[str]:
        """
        Check if a command contains blocked package manager patterns.

        Args:
            command: Command string to check

        Returns:
            The blocked pattern found, or None if command is allowed
        """
        command_lower = command.lower()

        # Check against blocked commands list
        for blocked in BLOCKED_COMMANDS:
            if blocked.lower() in command_lower:
                return blocked

        # Check against patterns (more flexible)
        for pattern in BLOCKED_PATTERNS:
            if pattern.lower() in command_lower:
                return pattern

        return None

    def is_command_allowed(self, command: str) -> bool:
        """
        Check if a command is allowed (not blocked).

        Args:
            command: Command string to check

        Returns:
            True if allowed, False if blocked
        """
        return self._check_blocked_command(command) is None
    
    def _truncate(self, text: str) -> str:
        """Truncate text to max_output_chars."""
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="replace")
        if len(text) > self.max_output_chars:
            return text[:self.max_output_chars] + f"\n... (truncated, {len(text)} total chars)"
        return text
    
    def write_file(self, path: str, content: str) -> Path:
        """
        Write a file to the workspace.
        
        Args:
            path: Relative path within workspace
            content: File content
            
        Returns:
            Absolute path to written file
        """
        file_path = self.workspace / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path
    
    def read_file(self, path: str) -> Optional[str]:
        """
        Read a file from the workspace.
        
        Args:
            path: Relative path within workspace
            
        Returns:
            File content or None if not found
        """
        file_path = self.workspace / path
        if file_path.exists():
            return file_path.read_text()
        return None
    
    def list_files(self) -> list[str]:
        """List all files in workspace (relative paths)."""
        files = []
        for path in self.workspace.rglob("*"):
            if path.is_file():
                files.append(str(path.relative_to(self.workspace)))
        return sorted(files)
    
    def cleanup(self):
        """Remove all files from workspace."""
        import shutil
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
            self.workspace.mkdir(parents=True, exist_ok=True)


def create_workspace(base_dir: Optional[Path] = None) -> Path:
    """
    Create a new temporary workspace directory.
    
    Args:
        base_dir: Optional base directory (defaults to system temp)
        
    Returns:
        Path to new workspace
    """
    if base_dir:
        base_dir = Path(base_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        workspace = Path(tempfile.mkdtemp(dir=base_dir))
    else:
        workspace = Path(tempfile.mkdtemp(prefix="vibe_eval_"))
    return workspace
