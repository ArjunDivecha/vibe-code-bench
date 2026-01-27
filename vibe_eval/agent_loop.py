"""
Multi-turn agent loop for running coding sessions.

V3: Enhanced with expanded tool set and detailed metrics tracking.
"""

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .models.base import BaseModel, Message, get_model
from .sandbox.executor import SandboxExecutor, create_workspace


# V3: Enhanced system prompt with more tools
SYSTEM_PROMPT = """You are an AI coding assistant participating in a coding evaluation.
Your task is to build what is described in the specification.

CRITICAL RULES:
- DO NOT run pip install, npm install, or any package manager commands
- Use only Python standard library or write everything from scratch
- For web UIs, use plain HTML/CSS/JavaScript in single files
- Complete the ENTIRE solution in ONE response with all files

You have the following capabilities:

1. WRITE FILES - Create or edit files:
<write_file path="relative/path/to/file.py">
file content here
</write_file>

2. READ FILES - Read existing files:
<read_file path="relative/path/to/file.py"/>

3. LIST FILES - List directory contents:
<list_files path="."/>

4. RUN COMMANDS - Execute shell commands (NO package installs!):
<run_command>
python main.py --help
</run_command>

5. RUN TESTS - Execute test suite:
<run_tests/>

6. LINT CODE - Check code for errors:
<lint_code path="main.py"/>

7. WEB SEARCH - Search for documentation:
<web_search query="python argparse subcommands"/>

8. SIGNAL COMPLETION - When you're done:
<done>
Brief description of what was built
</done>

Guidelines:
- Write ALL files needed in your first response
- Use only Python stdlib (json, csv, os, sys, re, etc.)
- For web apps: create self-contained HTML files with embedded CSS/JS
- Signal <done> immediately after writing all files
- DO NOT run pip, npm, yarn, cargo, or any package manager
"""


@dataclass
class ToolCall:
    """Record of a tool invocation."""
    tool: str
    args: dict
    result: dict
    timestamp: float


@dataclass
class AgentMetrics:
    """
    Detailed metrics for agent session.
    
    V3: Tracks tool usage, errors, and iteration patterns.
    """
    turns: int = 0
    tool_calls: list[ToolCall] = field(default_factory=list)
    errors_encountered: int = 0
    errors_recovered: int = 0
    backtrack_count: int = 0  # Times model revised previous work
    planning_turns: int = 0   # Turns spent planning vs executing
    test_iterations: int = 0  # Times tests were run
    files_written: int = 0
    files_read: int = 0
    commands_run: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "turns": self.turns,
            "tool_calls": [
                {"tool": tc.tool, "args": tc.args, "success": tc.result.get("success", True)}
                for tc in self.tool_calls
            ],
            "errors_encountered": self.errors_encountered,
            "errors_recovered": self.errors_recovered,
            "backtrack_count": self.backtrack_count,
            "planning_turns": self.planning_turns,
            "test_iterations": self.test_iterations,
            "files_written": self.files_written,
            "files_read": self.files_read,
            "commands_run": self.commands_run,
        }


@dataclass
class AgentAction:
    """Parsed action from agent response."""
    files_to_write: dict[str, str] = field(default_factory=dict)
    files_to_read: list[str] = field(default_factory=list)
    dirs_to_list: list[str] = field(default_factory=list)
    commands_to_run: list[str] = field(default_factory=list)
    run_tests: bool = False
    lint_files: list[str] = field(default_factory=list)
    web_searches: list[str] = field(default_factory=list)
    is_done: bool = False
    done_message: str = ""


@dataclass
class AgentResult:
    """Result of an agent loop run."""
    workspace: Path
    conversation: list[Message]
    elapsed_seconds: float
    completed: bool
    turns: int
    files_created: list[str]
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    error: Optional[str] = None
    # V3: Add detailed metrics
    metrics: Optional[AgentMetrics] = None


def parse_actions(response: str) -> AgentAction:
    """
    Parse structured actions from model response.
    
    V3: Extended to parse new tool calls.
    """
    action = AgentAction()
    
    # Parse file writes
    file_pattern = r'<write_file\s+path="([^"]+)">(.*?)</write_file>'
    for match in re.finditer(file_pattern, response, re.DOTALL):
        path = match.group(1)
        content = match.group(2).strip()
        action.files_to_write[path] = content
    
    # V3: Parse file reads
    read_pattern = r'<read_file\s+path="([^"]+)"\s*/>'
    for match in re.finditer(read_pattern, response):
        action.files_to_read.append(match.group(1))
    
    # V3: Parse list files
    list_pattern = r'<list_files\s+path="([^"]+)"\s*/>'
    for match in re.finditer(list_pattern, response):
        action.dirs_to_list.append(match.group(1))
    
    # Parse commands
    cmd_pattern = r'<run_command>(.*?)</run_command>'
    for match in re.finditer(cmd_pattern, response, re.DOTALL):
        command = match.group(1).strip()
        if command:
            action.commands_to_run.append(command)
    
    # V3: Parse run_tests
    if '<run_tests/>' in response or '<run_tests>' in response:
        action.run_tests = True
    
    # V3: Parse lint_code
    lint_pattern = r'<lint_code\s+path="([^"]+)"\s*/>'
    for match in re.finditer(lint_pattern, response):
        action.lint_files.append(match.group(1))
    # Also support linting without path
    if '<lint_code/>' in response:
        action.lint_files.append("")  # Empty means all files
    
    # V3: Parse web_search
    search_pattern = r'<web_search\s+query="([^"]+)"\s*/>'
    for match in re.finditer(search_pattern, response):
        action.web_searches.append(match.group(1))
    
    # Parse done signal
    done_pattern = r'<done>(.*?)</done>'
    done_match = re.search(done_pattern, response, re.DOTALL)
    if done_match:
        action.is_done = True
        action.done_message = done_match.group(1).strip()
    
    return action


class AgentLoop:
    """
    Runs a multi-turn coding session with an LLM.
    
    V3: Enhanced with expanded tool set and detailed metrics.
    
    The agent iterates: get response → parse actions → execute → feedback
    until the agent signals done or timeout is reached.
    """
    
    def __init__(
        self,
        model: BaseModel,
        spec: str,
        timeout_minutes: int = 20,
        workspace: Optional[Path] = None,
        max_turns: int = 50,
        enable_tools: bool = True  # V3: Enable extended tools
    ):
        """
        Initialize agent loop.
        
        Args:
            model: LLM model adapter to use
            spec: Task specification (natural language)
            timeout_minutes: Maximum time for entire session
            workspace: Working directory (created if not provided)
            max_turns: Maximum conversation turns
            enable_tools: Enable V3 extended tools
        """
        self.model = model
        self.spec = spec
        self.timeout = timeout_minutes * 60
        self.max_turns = max_turns
        self.enable_tools = enable_tools
        
        # Set up workspace and executor
        self.workspace = workspace or create_workspace()
        self.executor = SandboxExecutor(self.workspace)
        
        # Initialize conversation
        self.conversation: list[Message] = []
        
        # V3: Initialize metrics
        self.metrics = AgentMetrics()
    
    def _record_tool_call(self, tool: str, args: dict, result: dict):
        """Record a tool invocation for metrics."""
        self.metrics.tool_calls.append(ToolCall(
            tool=tool,
            args=args,
            result=result,
            timestamp=time.time()
        ))
    
    def _execute_tools(self, actions: AgentAction) -> list[str]:
        """
        Execute all parsed tool actions and return feedback.
        
        V3: Handles extended tool set.
        """
        feedback_parts = []
        
        # Handle file reads (V3)
        if self.enable_tools:
            for filepath in actions.files_to_read:
                from .tools.file_tools import read_file_tool
                result = read_file_tool(self.workspace, filepath)
                self._record_tool_call("read_file", {"path": filepath}, result)
                self.metrics.files_read += 1
                
                if result["success"]:
                    feedback_parts.append(
                        f"✓ Read {filepath}:\n```\n{result['content'][:2000]}\n```"
                    )
                else:
                    feedback_parts.append(f"✗ Read {filepath}: {result['error']}")
                    self.metrics.errors_encountered += 1
        
        # Handle directory listings (V3)
        if self.enable_tools:
            for dirpath in actions.dirs_to_list:
                from .tools.file_tools import list_files_tool
                result = list_files_tool(self.workspace, dirpath)
                self._record_tool_call("list_files", {"path": dirpath}, result)
                
                if result["success"]:
                    items = [d["name"] + "/" for d in result["directories"]]
                    items += [f["name"] for f in result["files"]]
                    feedback_parts.append(
                        f"✓ Contents of {dirpath}: {items}"
                    )
                else:
                    feedback_parts.append(f"✗ List {dirpath}: {result['error']}")
        
        # Handle file writes
        if actions.files_to_write:
            for path, content in actions.files_to_write.items():
                self.executor.write_file(path, content)
                self._record_tool_call("write_file", {"path": path}, {"success": True})
                self.metrics.files_written += 1
            feedback_parts.append(
                f"✓ Files written: {list(actions.files_to_write.keys())}"
            )
        
        # Handle command execution
        for command in actions.commands_to_run:
            result = self.executor.run(command)
            self._record_tool_call("run_command", {"command": command}, {
                "success": result.success,
                "return_code": result.return_code
            })
            self.metrics.commands_run += 1
            
            output_lines = []
            if result.stdout:
                output_lines.append(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                output_lines.append(f"STDERR:\n{result.stderr}")
            
            status = "✓" if result.success else "✗"
            feedback_parts.append(
                f"{status} Command: {command}\n"
                f"Exit code: {result.return_code}\n"
                + "\n".join(output_lines)
            )
            
            if not result.success:
                self.metrics.errors_encountered += 1
        
        # Handle run_tests (V3)
        if self.enable_tools and actions.run_tests:
            from .tools.test_tools import run_tests_tool
            result = run_tests_tool(self.workspace)
            self._record_tool_call("run_tests", {}, result)
            self.metrics.test_iterations += 1
            
            if result["success"]:
                feedback_parts.append(
                    f"✓ Tests: {result.get('passed', 0)} passed, "
                    f"{result.get('failed', 0)} failed\n{result.get('output', '')[:1000]}"
                )
            else:
                feedback_parts.append(
                    f"✗ Tests failed:\n{result.get('output', result.get('error', ''))[:1000]}"
                )
                self.metrics.errors_encountered += 1
        
        # Handle lint_code (V3)
        if self.enable_tools:
            for filepath in actions.lint_files:
                from .tools.test_tools import lint_code_tool
                result = lint_code_tool(
                    self.workspace, 
                    filepath if filepath else None
                )
                self._record_tool_call("lint_code", {"path": filepath}, result)
                
                summary = result.get("summary", {})
                if result["success"]:
                    feedback_parts.append(
                        f"✓ Lint: {summary.get('total', 0)} issues "
                        f"({summary.get('syntax_errors', 0)} errors, "
                        f"{summary.get('warnings', 0)} warnings)"
                    )
                else:
                    issues = result.get("issues", [])[:5]
                    issue_text = "\n".join(
                        f"  {i['file']}:{i['line']}: {i['message']}" 
                        for i in issues
                    )
                    feedback_parts.append(f"✗ Lint errors:\n{issue_text}")
                    self.metrics.errors_encountered += 1
        
        # Handle web_search (V3)
        if self.enable_tools:
            for query in actions.web_searches:
                from .tools.search_tools import web_search_tool
                result = web_search_tool(query)
                self._record_tool_call("web_search", {"query": query}, result)
                
                if result["results"]:
                    docs = result["results"][0]
                    feedback_parts.append(
                        f"✓ Search '{query}':\n"
                        f"**{docs['title']}**\n{docs['snippet'][:1500]}"
                    )
                else:
                    feedback_parts.append(
                        f"ℹ Search '{query}': {result.get('message', 'No results')}"
                    )
        
        return feedback_parts
    
    def run(self) -> AgentResult:
        """Execute the agent loop until done or timeout."""
        
        start_time = time.time()
        turns = 0
        completed = False
        error = None
        total_input_tokens = 0
        total_output_tokens = 0
        
        # Track previous files for backtrack detection
        previous_files = set()
        
        # Initialize conversation with system prompt and task
        self.conversation = [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=f"Build the following:\n\n{self.spec}")
        ]
        
        try:
            while time.time() - start_time < self.timeout and turns < self.max_turns:
                turns += 1
                self.metrics.turns = turns
                
                # Get model response
                response = self.model.complete(self.conversation)
                self.conversation.append(
                    Message(role="assistant", content=response.content)
                )
                
                # Track token usage
                if response.usage:
                    total_input_tokens += response.usage.get("input_tokens", 0)
                    total_output_tokens += response.usage.get("output_tokens", 0)
                
                # Parse actions from response
                actions = parse_actions(response.content)
                
                # V3: Detect backtracking (rewriting files)
                current_files = set(actions.files_to_write.keys())
                if current_files & previous_files:
                    self.metrics.backtrack_count += 1
                previous_files.update(current_files)
                
                # Execute all tools and collect feedback
                feedback_parts = self._execute_tools(actions)
                
                # NOW check if done (after processing actions)
                if actions.is_done:
                    completed = True
                    break
                
                # If no actions were parsed, prompt to continue
                if not any([
                    actions.files_to_write, actions.commands_to_run,
                    actions.files_to_read, actions.dirs_to_list,
                    actions.run_tests, actions.lint_files, actions.web_searches
                ]):
                    feedback_parts.append(
                        "No actions detected. Please write files, run commands, "
                        "or signal <done> when complete."
                    )
                    self.metrics.planning_turns += 1
                
                # Add feedback to conversation
                feedback = "\n\n".join(feedback_parts)
                self.conversation.append(
                    Message(role="user", content=feedback)
                )
                
        except Exception as e:
            error = str(e)
            self.metrics.errors_encountered += 1
        
        elapsed = time.time() - start_time
        files = self.executor.list_files()
        
        return AgentResult(
            workspace=self.workspace,
            conversation=self.conversation,
            elapsed_seconds=elapsed,
            completed=completed,
            turns=turns,
            files_created=files,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            error=error,
            metrics=self.metrics
        )


def run_agent(
    model_id: str,
    spec: str,
    timeout_minutes: int = 20,
    workspace: Optional[Path] = None,
    enable_tools: bool = True
) -> AgentResult:
    """
    Convenience function to run an agent loop.
    
    Args:
        model_id: Model identifier (e.g., "claude-sonnet-4")
        spec: Task specification
        timeout_minutes: Session timeout
        workspace: Optional workspace directory
        enable_tools: Enable V3 extended tools
        
    Returns:
        AgentResult with session details
    """
    model = get_model(model_id)
    agent = AgentLoop(
        model=model,
        spec=spec,
        timeout_minutes=timeout_minutes,
        workspace=workspace,
        enable_tools=enable_tools
    )
    return agent.run()
