"""Filesystem tools for PolyTool."""

from __future__ import annotations

import glob as glob_module
from pathlib import Path
from typing import Annotated

from polytool.tools.decorator import tool


@tool
async def read_file(
    path: Annotated[str, "Path to file to read"],
    encoding: Annotated[str, "File encoding"] = "utf-8",
) -> str:
    """Read the contents of a file."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return file_path.read_text(encoding=encoding)


@tool
async def write_file(
    path: Annotated[str, "Path to file to write"],
    content: Annotated[str, "Content to write"],
    encoding: Annotated[str, "File encoding"] = "utf-8",
) -> str:
    """Write content to a file. Creates parent directories if needed."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding=encoding)
    return f"Written {len(content)} bytes to {path}"


@tool
async def list_dir(
    path: Annotated[str, "Directory path"] = ".",
    pattern: Annotated[str | None, "Optional glob pattern to filter"] = None,
) -> list[dict[str, str | int | bool]]:
    """
    List contents of a directory.
    
    Returns a list of dicts with 'name', 'type', and 'size' for each entry.
    """
    dir_path = Path(path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")
    
    entries = []
    for entry in dir_path.iterdir():
        if pattern and not entry.match(pattern):
            continue
        entries.append({
            "name": entry.name,
            "type": "directory" if entry.is_dir() else "file",
            "size": entry.stat().st_size if entry.is_file() else 0,
            "is_dir": entry.is_dir(),
        })
    
    return sorted(entries, key=lambda x: (not x["is_dir"], x["name"]))


@tool
async def glob_files(
    pattern: Annotated[str, "Glob pattern (e.g., '**/*.py')"],
    root: Annotated[str, "Root directory to search from"] = ".",
) -> list[str]:
    """
    Find files matching a glob pattern.
    
    Supports recursive patterns with '**'.
    """
    root_path = Path(root)
    if not root_path.exists():
        raise FileNotFoundError(f"Root directory not found: {root}")
    
    # Use glob
    matches = list(root_path.glob(pattern))
    return [str(m) for m in matches]


