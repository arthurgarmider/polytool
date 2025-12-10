"""Shell command tools for PolyTool."""

from __future__ import annotations

import asyncio
import shlex
from typing import Annotated

from polytool.tools.decorator import tool
from polytool.core.exceptions import ToolError


@tool
async def run_command(
    command: Annotated[str, "Shell command to execute"],
    timeout: Annotated[float, "Timeout in seconds"] = 30.0,
    cwd: Annotated[str | None, "Working directory"] = None,
) -> dict[str, str | int]:
    """
    Execute a shell command.
    
    Returns a dict with 'stdout', 'stderr', and 'return_code'.
    
    WARNING: Be careful with user-provided commands.
    """
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise ToolError(
                f"Command timed out after {timeout}s: {command}",
                tool_name="run_command",
            )
        
        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "return_code": process.returncode or 0,
        }
    
    except Exception as e:
        if isinstance(e, ToolError):
            raise
        raise ToolError(
            f"Command failed: {e}",
            tool_name="run_command",
        ) from e


