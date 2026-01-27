"""
File operation tools for the agent.

Provides read_file and list_files capabilities.
"""

from pathlib import Path
from typing import Optional


def read_file_tool(workspace: Path, filepath: str) -> dict:
    """
    Read contents of a file in the workspace.
    
    Args:
        workspace: Base workspace directory
        filepath: Relative path to file
        
    Returns:
        Dict with success status and content/error
    """
    try:
        full_path = workspace / filepath
        
        # Security: Ensure path is within workspace
        full_path = full_path.resolve()
        workspace_resolved = workspace.resolve()
        
        if not str(full_path).startswith(str(workspace_resolved)):
            return {
                "success": False,
                "error": "Access denied: Path outside workspace"
            }
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"File not found: {filepath}"
            }
        
        if not full_path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {filepath}"
            }
        
        # Read file with size limit
        if full_path.stat().st_size > 100000:  # 100KB limit
            content = full_path.read_text()[:100000] + "\n... (truncated)"
        else:
            content = full_path.read_text()
        
        return {
            "success": True,
            "content": content,
            "path": filepath,
            "size": full_path.stat().st_size
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def list_files_tool(workspace: Path, directory: str = ".") -> dict:
    """
    List files in a directory within the workspace.
    
    Args:
        workspace: Base workspace directory
        directory: Relative path to directory (default: workspace root)
        
    Returns:
        Dict with success status and file list/error
    """
    try:
        full_path = (workspace / directory).resolve()
        workspace_resolved = workspace.resolve()
        
        # Security: Ensure path is within workspace
        if not str(full_path).startswith(str(workspace_resolved)):
            return {
                "success": False,
                "error": "Access denied: Path outside workspace"
            }
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}"
            }
        
        if not full_path.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {directory}"
            }
        
        files = []
        dirs = []
        
        for item in sorted(full_path.iterdir()):
            rel_path = str(item.relative_to(workspace_resolved))
            if item.is_dir():
                dirs.append({"name": item.name, "path": rel_path, "type": "directory"})
            else:
                files.append({
                    "name": item.name,
                    "path": rel_path,
                    "type": "file",
                    "size": item.stat().st_size
                })
        
        return {
            "success": True,
            "directory": directory,
            "directories": dirs,
            "files": files,
            "total": len(dirs) + len(files)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
