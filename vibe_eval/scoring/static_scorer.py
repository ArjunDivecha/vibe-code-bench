"""
Static code analysis scoring.

V3: Analyzes code quality without execution.
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class StaticReport:
    """
    Static analysis report for code quality.
    """
    files_analyzed: int = 0
    total_lines: int = 0
    
    # Complexity metrics
    avg_function_length: float = 0.0
    max_function_length: int = 0
    cyclomatic_complexity: float = 0.0
    
    # Quality indicators
    has_docstrings: bool = False
    docstring_coverage: float = 0.0
    has_type_hints: bool = False
    type_hint_coverage: float = 0.0
    
    # Issues
    syntax_errors: int = 0
    long_lines: int = 0  # Lines > 120 chars
    todo_count: int = 0
    console_logs: int = 0  # console.log or print statements
    
    # Error handling
    has_error_handling: bool = False
    try_except_count: int = 0
    
    # Details
    issues: list[dict] = field(default_factory=list)
    
    @property
    def quality_score(self) -> int:
        """
        Calculate overall code quality score (0-10).
        """
        score = 10.0
        
        # Penalize syntax errors heavily
        if self.syntax_errors > 0:
            score -= min(5, self.syntax_errors * 2)
        
        # Penalize missing docstrings
        if self.docstring_coverage < 0.5:
            score -= 1
        
        # Penalize very long functions
        if self.max_function_length > 100:
            score -= 1
        elif self.max_function_length > 50:
            score -= 0.5
        
        # Penalize missing error handling
        if not self.has_error_handling and self.files_analyzed > 0:
            score -= 0.5
        
        # Penalize excessive console logs (likely debug code)
        if self.console_logs > 5:
            score -= 1
        
        # Penalize many TODOs (incomplete)
        if self.todo_count > 3:
            score -= 0.5
        
        # Penalize too many long lines
        if self.long_lines > 10:
            score -= 0.5
        
        return max(0, min(10, round(score)))
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "files_analyzed": self.files_analyzed,
            "total_lines": self.total_lines,
            "avg_function_length": round(self.avg_function_length, 1),
            "max_function_length": self.max_function_length,
            "cyclomatic_complexity": round(self.cyclomatic_complexity, 1),
            "docstring_coverage": round(self.docstring_coverage, 2),
            "type_hint_coverage": round(self.type_hint_coverage, 2),
            "has_error_handling": self.has_error_handling,
            "syntax_errors": self.syntax_errors,
            "long_lines": self.long_lines,
            "todo_count": self.todo_count,
            "console_logs": self.console_logs,
            "quality_score": self.quality_score,
            "issues": self.issues[:20],  # Limit issues
        }


class StaticAnalyzer:
    """
    Static code analyzer for quality metrics.
    
    Analyzes Python and JavaScript code without execution.
    """
    
    def analyze(self, workspace: Path) -> StaticReport:
        """
        Analyze all code files in workspace.
        
        Args:
            workspace: Directory containing code
            
        Returns:
            StaticReport with quality metrics
        """
        workspace = Path(workspace)
        report = StaticReport()
        
        # Find code files
        python_files = list(workspace.glob("**/*.py"))
        html_files = list(workspace.glob("**/*.html"))
        js_files = list(workspace.glob("**/*.js"))
        
        # Analyze Python files
        for filepath in python_files:
            self._analyze_python(filepath, report)
        
        # Analyze HTML/JS files
        for filepath in html_files + js_files:
            self._analyze_html_js(filepath, report)
        
        report.files_analyzed = len(python_files) + len(html_files) + len(js_files)
        
        return report
    
    def _analyze_python(self, filepath: Path, report: StaticReport):
        """Analyze a Python file."""
        try:
            content = filepath.read_text()
            lines = content.split('\n')
            report.total_lines += len(lines)
            
            # Check for syntax errors
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                report.syntax_errors += 1
                report.issues.append({
                    "file": filepath.name,
                    "line": e.lineno or 0,
                    "type": "syntax_error",
                    "message": str(e.msg)
                })
                return
            
            # Analyze functions
            functions = [node for node in ast.walk(tree) 
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
            
            function_lengths = []
            functions_with_docstring = 0
            functions_with_hints = 0
            
            for func in functions:
                # Calculate function length
                length = func.end_lineno - func.lineno + 1 if hasattr(func, 'end_lineno') else 10
                function_lengths.append(length)
                
                # Check for docstring
                if ast.get_docstring(func):
                    functions_with_docstring += 1
                
                # Check for type hints
                if func.returns or any(arg.annotation for arg in func.args.args):
                    functions_with_hints += 1
            
            if function_lengths:
                report.avg_function_length = sum(function_lengths) / len(function_lengths)
                report.max_function_length = max(report.max_function_length, max(function_lengths))
            
            if functions:
                report.docstring_coverage = functions_with_docstring / len(functions)
                report.type_hint_coverage = functions_with_hints / len(functions)
                report.has_docstrings = functions_with_docstring > 0
                report.has_type_hints = functions_with_hints > 0
            
            # Check for error handling
            for node in ast.walk(tree):
                if isinstance(node, ast.Try):
                    report.has_error_handling = True
                    report.try_except_count += 1
            
            # Line-by-line analysis
            for i, line in enumerate(lines, 1):
                # Long lines
                if len(line) > 120:
                    report.long_lines += 1
                
                # TODOs
                if 'TODO' in line or 'FIXME' in line:
                    report.todo_count += 1
                
                # Print statements (debug code)
                if re.search(r'\bprint\s*\(', line) and not line.strip().startswith('#'):
                    report.console_logs += 1
            
            # Calculate cyclomatic complexity (simplified)
            complexity = 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                    ast.With, ast.Assert, ast.comprehension)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            
            report.cyclomatic_complexity = complexity / max(1, len(functions))
            
        except Exception as e:
            report.issues.append({
                "file": filepath.name,
                "line": 0,
                "type": "analysis_error",
                "message": str(e)
            })
    
    def _analyze_html_js(self, filepath: Path, report: StaticReport):
        """Analyze HTML or JavaScript file."""
        try:
            content = filepath.read_text()
            lines = content.split('\n')
            report.total_lines += len(lines)
            
            # Check for console.log
            console_logs = len(re.findall(r'console\.(log|error|warn|debug)\s*\(', content))
            report.console_logs += console_logs
            
            # Check for TODO/FIXME
            report.todo_count += content.count('TODO') + content.count('FIXME')
            
            # Check for long lines
            for line in lines:
                if len(line) > 120:
                    report.long_lines += 1
            
            # Check for error handling in JS
            if 'try' in content and 'catch' in content:
                report.has_error_handling = True
            
            # Check for basic issues
            if filepath.suffix == '.html':
                if '<html' not in content.lower():
                    report.issues.append({
                        "file": filepath.name,
                        "line": 0,
                        "type": "warning",
                        "message": "Missing <html> tag"
                    })
                    
        except Exception as e:
            report.issues.append({
                "file": filepath.name,
                "line": 0,
                "type": "analysis_error",
                "message": str(e)
            })
