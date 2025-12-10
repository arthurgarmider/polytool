"""Restricted Python sandbox for PolyTool (local fallback)."""

from __future__ import annotations

import ast
import asyncio
import sys
import time
from io import StringIO
from typing import Any

from polytool.core.types import ExecutionResult, Tool
from polytool.core.config import get_settings
from polytool.core.exceptions import SandboxError


class RestrictedSandbox:
    """
    Local sandbox using restricted Python execution.
    
    This is a development/fallback sandbox that runs code locally
    with some restrictions. For production, use E2B.
    
    Limitations:
    - Cannot fully isolate code
    - Some imports may be blocked
    - Not suitable for untrusted code
    """
    
    def __init__(self, timeout: float | None = None):
        settings = get_settings()
        self.timeout = timeout or settings.sandbox_timeout_seconds
    
    async def __aenter__(self) -> "RestrictedSandbox":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass
    
    async def execute(
        self,
        code: str,
        tools: list[Tool] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        """
        Execute code in the restricted sandbox.
        
        Args:
            code: Python code to execute
            tools: Tools to make available
            timeout: Execution timeout
        
        Returns:
            ExecutionResult with stdout and any errors
        """
        timeout = timeout or self.timeout
        start_time = time.time()
        
        # Validate syntax
        try:
            ast.parse(code)
        except SyntaxError as e:
            return ExecutionResult(
                success=False,
                error=f"Syntax error: {e}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        
        # Build execution namespace with tools
        namespace = self._build_namespace(tools or [])
        
        # Capture stdout/stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_code(code, namespace),
                timeout=timeout,
            )
            
            return ExecutionResult(
                success=True,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                return_value=result,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        
        except asyncio.TimeoutError:
            return ExecutionResult(
                success=False,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                error=f"Execution timed out after {timeout}s",
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                error=f"{type(e).__name__}: {e}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    async def _execute_code(self, code: str, namespace: dict[str, Any]) -> Any:
        """Execute code and return result."""
        # Wrap code in async function to support await
        # Add a pass statement in case the code is empty or has trailing newlines
        indented = _indent(code.rstrip(), 4)
        if not indented.strip():
            indented = "    pass"
        wrapped_code = f"async def __polytool_main__():\n{indented}\n    pass\n"
        
        # Compile and exec to define the function
        exec(compile(wrapped_code, "<sandbox>", "exec"), namespace)
        
        # Get the function and await it
        main_func = namespace["__polytool_main__"]
        return await main_func()
    
    def _build_namespace(self, tools: list[Tool]) -> dict[str, Any]:
        """Build execution namespace with tools and safe builtins."""
        namespace: dict[str, Any] = {
            # Safe builtins
            "print": print,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "any": any,
            "all": all,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,
            "setattr": setattr,
            # Common imports
            "json": __import__("json"),
            "asyncio": asyncio,
        }
        
        # Add tools as async functions
        for tool in tools:
            namespace[tool.name] = self._make_tool_wrapper(tool)
        
        return namespace
    
    def _make_tool_wrapper(self, tool: Tool):
        """Create an async wrapper for a tool."""
        async def wrapper(**kwargs):
            return await tool.execute(**kwargs)
        wrapper.__name__ = tool.name
        wrapper.__doc__ = tool.description
        return wrapper


def _indent(code: str, spaces: int) -> str:
    """Indent code by specified spaces."""
    prefix = " " * spaces
    lines = code.split("\n")
    return "\n".join(prefix + line if line.strip() else line for line in lines)

