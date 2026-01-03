"""Multi-turn agent loop for running coding sessions."""

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .models.base import BaseModel, Message, get_model
from .sandbox.executor import SandboxExecutor, create_workspace


# System prompt for the agent
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

2. RUN COMMANDS - Execute shell commands (NO package installs!):
<run_command>
python main.py --help
</run_command>

3. SIGNAL COMPLETION - When you're done:
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
class AgentAction:
    """Parsed action from agent response."""
    files_to_write: dict[str, str] = field(default_factory=dict)
    commands_to_run: list[str] = field(default_factory=list)
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


def parse_actions(response: str) -> AgentAction:
    """
    Parse structured actions from model response.
    
    Looks for:
    - <write_file path="...">content</write_file>
    - <run_command>command</run_command>
    - <done>message</done>
    """
    action = AgentAction()
    
    # Parse file writes
    file_pattern = r'<write_file\s+path="([^"]+)">(.*?)</write_file>'
    for match in re.finditer(file_pattern, response, re.DOTALL):
        path = match.group(1)
        content = match.group(2).strip()
        action.files_to_write[path] = content
    
    # Parse commands
    cmd_pattern = r'<run_command>(.*?)</run_command>'
    for match in re.finditer(cmd_pattern, response, re.DOTALL):
        command = match.group(1).strip()
        if command:
            action.commands_to_run.append(command)
    
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
    
    The agent iterates: get response → parse actions → execute → feedback
    until the agent signals done or timeout is reached.
    """
    
    def __init__(
        self,
        model: BaseModel,
        spec: str,
        timeout_minutes: int = 20,
        workspace: Optional[Path] = None,
        max_turns: int = 50
    ):
        """
        Initialize agent loop.
        
        Args:
            model: LLM model adapter to use
            spec: Task specification (natural language)
            timeout_minutes: Maximum time for entire session
            workspace: Working directory (created if not provided)
            max_turns: Maximum conversation turns
        """
        self.model = model
        self.spec = spec
        self.timeout = timeout_minutes * 60
        self.max_turns = max_turns
        
        # Set up workspace and executor
        self.workspace = workspace or create_workspace()
        self.executor = SandboxExecutor(self.workspace)
        
        # Initialize conversation
        self.conversation: list[Message] = []
    
    def run(self) -> AgentResult:
        """Execute the agent loop until done or timeout."""
        
        start_time = time.time()
        turns = 0
        completed = False
        error = None
        total_input_tokens = 0
        total_output_tokens = 0
        
        # Initialize conversation with system prompt and task
        self.conversation = [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=f"Build the following:\n\n{self.spec}")
        ]
        
        try:
            while time.time() - start_time < self.timeout and turns < self.max_turns:
                turns += 1
                
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
                
                # Execute actions FIRST (before checking done)
                # This is important because models often include <done> in the same
                # response as <write_file> and <run_command>
                feedback_parts = []
                
                # Handle file writes
                if actions.files_to_write:
                    for path, content in actions.files_to_write.items():
                        self.executor.write_file(path, content)
                    feedback_parts.append(
                        f"✓ Files written: {list(actions.files_to_write.keys())}"
                    )
                
                # Handle command execution
                for command in actions.commands_to_run:
                    result = self.executor.run(command)
                    
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
                
                # NOW check if done (after processing actions)
                if actions.is_done:
                    completed = True
                    break
                
                # If no actions were parsed, prompt to continue
                if not actions.files_to_write and not actions.commands_to_run:
                    feedback_parts.append(
                        "No actions detected. Please write files, run commands, "
                        "or signal <done> when complete."
                    )
                
                # Add feedback to conversation
                feedback = "\n\n".join(feedback_parts)
                self.conversation.append(
                    Message(role="user", content=feedback)
                )
                
        except Exception as e:
            error = str(e)
        
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
            error=error
        )


def run_agent(
    model_id: str,
    spec: str,
    timeout_minutes: int = 20,
    workspace: Optional[Path] = None
) -> AgentResult:
    """
    Convenience function to run an agent loop.
    
    Args:
        model_id: Model identifier (e.g., "claude-sonnet-4")
        spec: Task specification
        timeout_minutes: Session timeout
        workspace: Optional workspace directory
        
    Returns:
        AgentResult with session details
    """
    model = get_model(model_id)
    agent = AgentLoop(
        model=model,
        spec=spec,
        timeout_minutes=timeout_minutes,
        workspace=workspace
    )
    return agent.run()
