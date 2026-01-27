"""
Testing tools for the agent.

Provides run_tests and lint_code capabilities.
"""

import ast
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_tests_tool(workspace: Path, test_command: Optional[str] = None) -> dict:
    """
    Run tests in the workspace.
    
    Args:
        workspace: Base workspace directory
        test_command: Optional custom test command
        
    Returns:
        Dict with success status, output, and pass/fail counts
    """
    try:
        # Determine test command
        if test_command:
            cmd = test_command
        else:
            # Auto-detect test runner
            if (workspace / "test_calculator.py").exists():
                cmd = f"{sys.executable} -m unittest test_calculator -v"
            elif (workspace / "tests.py").exists():
                cmd = f"{sys.executable} -m pytest tests.py -v"
            elif list(workspace.glob("test_*.py")):
                test_files = list(workspace.glob("test_*.py"))
                cmd = f"{sys.executable} -m unittest {test_files[0].name} -v"
            else:
                return {
                    "success": False,
                    "error": "No test files found"
                }
        
        # Run tests
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=str(workspace),
            timeout=60
        )
        
        output = result.stdout + result.stderr
        
        # Parse results
        passed = output.count(" ok") + output.count("... ok") + output.count("PASSED")
        failed = output.count("FAIL") + output.count("ERROR") + output.count("FAILED")
        
        return {
            "success": result.returncode == 0,
            "output": output[-5000:],  # Limit output size
            "passed": passed,
            "failed": failed,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Tests timed out after 60 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def lint_code_tool(workspace: Path, filepath: Optional[str] = None) -> dict:
    """
    Check code for errors and style issues.
    
    Uses Python's ast module for syntax checking and basic linting.
    
    Args:
        workspace: Base workspace directory
        filepath: Optional specific file to lint (default: all Python files)
        
    Returns:
        Dict with issues found
    """
    issues = []
    files_checked = []
    
    try:
        # Determine files to check
        if filepath:
            files = [workspace / filepath]
        else:
            files = list(workspace.glob("**/*.py"))
        
        for file in files:
            if not file.exists():
                continue
                
            rel_path = str(file.relative_to(workspace))
            files_checked.append(rel_path)
            
            try:
                content = file.read_text()
                
                # Check syntax
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    issues.append({
                        "file": rel_path,
                        "line": e.lineno,
                        "type": "syntax_error",
                        "message": str(e.msg)
                    })
                    continue
                
                # Basic linting checks
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    # Check for print statements (debug code)
                    if 'print(' in line and not line.strip().startswith('#'):
                        if '__name__' not in content[:content.find(line)]:
                            issues.append({
                                "file": rel_path,
                                "line": i,
                                "type": "warning",
                                "message": "Possible debug print statement"
                            })
                    
                    # Check for very long lines
                    if len(line) > 120:
                        issues.append({
                            "file": rel_path,
                            "line": i,
                            "type": "style",
                            "message": f"Line too long ({len(line)} > 120)"
                        })
                    
                    # Check for TODO/FIXME
                    if 'TODO' in line or 'FIXME' in line:
                        issues.append({
                            "file": rel_path,
                            "line": i,
                            "type": "warning",
                            "message": "Unresolved TODO/FIXME"
                        })
                
                # Check for missing docstrings on classes/functions
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        if not ast.get_docstring(node):
                            issues.append({
                                "file": rel_path,
                                "line": node.lineno,
                                "type": "style",
                                "message": f"Missing docstring for {node.name}"
                            })
                            
            except Exception as e:
                issues.append({
                    "file": rel_path,
                    "line": 0,
                    "type": "error",
                    "message": f"Could not parse: {e}"
                })
        
        # Count by type
        syntax_errors = sum(1 for i in issues if i["type"] == "syntax_error")
        warnings = sum(1 for i in issues if i["type"] == "warning")
        style_issues = sum(1 for i in issues if i["type"] == "style")
        
        return {
            "success": syntax_errors == 0,
            "files_checked": files_checked,
            "issues": issues[:50],  # Limit issues
            "summary": {
                "syntax_errors": syntax_errors,
                "warnings": warnings,
                "style_issues": style_issues,
                "total": len(issues)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
