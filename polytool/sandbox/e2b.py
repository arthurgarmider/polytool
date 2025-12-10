"""E2B cloud sandbox for PolyTool."""

from __future__ import annotations

import json
import time
from typing import Any

from polytool.core.types import ExecutionResult, Tool
from polytool.core.config import get_settings
from polytool.core.exceptions import SandboxError

# E2B is optional
try:
    from e2b_code_interpreter import Sandbox as E2BSandboxBase
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False
    E2BSandboxBase = None  # type: ignore


class E2BSandbox:
    """
    Cloud sandbox using E2B Code Interpreter.
    
    Provides secure, isolated code execution in cloud VMs.
    Recommended for production use.
    """
    
    def __init__(self, timeout: float | None = None, api_key: str | None = None):
        if not E2B_AVAILABLE:
            raise SandboxError(
                "E2B not installed. Install with: pip install polytool[e2b]"
            )
        
        settings = get_settings()
        self.timeout = timeout or settings.sandbox_timeout_seconds
        self.api_key = api_key or settings.e2b_api_key
        self._sandbox: Any = None
    
    async def __aenter__(self) -> "E2BSandbox":
        """Create and enter the sandbox."""
        self._sandbox = E2BSandboxBase(api_key=self.api_key)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close the sandbox."""
        if self._sandbox:
            self._sandbox.close()
            self._sandbox = None
    
    async def execute(
        self,
        code: str,
        tools: list[Tool] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        """
        Execute code in the E2B sandbox.
        
        Args:
            code: Python code to execute
            tools: Tools to make available (injected as callable functions)
            timeout: Execution timeout
        
        Returns:
            ExecutionResult with stdout and results
        """
        timeout = timeout or self.timeout
        start_time = time.time()
        
        # Create sandbox if not in context
        sandbox = self._sandbox
        own_sandbox = False
        if sandbox is None:
            sandbox = E2BSandboxBase(api_key=self.api_key)
            own_sandbox = True
        
        try:
            # If we have tools, we need to inject them
            # This is done by generating wrapper code
            if tools:
                wrapper_code = self._generate_tool_wrappers(tools)
                full_code = f"{wrapper_code}\n\n{code}"
            else:
                full_code = code
            
            # Execute in sandbox
            execution = sandbox.run_code(full_code, timeout=timeout)
            
            # Extract results
            stdout = ""
            stderr = ""
            
            if execution.logs:
                stdout = "\n".join(
                    line.line for line in (execution.logs.stdout or [])
                )
                stderr = "\n".join(
                    line.line for line in (execution.logs.stderr or [])
                )
            
            # Check for errors
            if execution.error:
                return ExecutionResult(
                    success=False,
                    stdout=stdout,
                    stderr=stderr,
                    error=f"{execution.error.name}: {execution.error.value}",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
            
            # Get return value from results
            return_value = None
            if execution.results:
                # Take the last result
                last_result = execution.results[-1]
                if hasattr(last_result, "text"):
                    return_value = last_result.text
                elif hasattr(last_result, "data"):
                    return_value = last_result.data
            
            return ExecutionResult(
                success=True,
                stdout=stdout,
                stderr=stderr,
                return_value=return_value,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        
        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"E2B error: {e}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        
        finally:
            if own_sandbox and sandbox:
                sandbox.close()
    
    def _generate_tool_wrappers(self, tools: list[Tool]) -> str:
        """
        Generate Python code that creates tool wrappers.
        
        Since E2B runs in a separate environment, we can't directly
        inject Python functions. Instead, we generate code that
        makes HTTP calls back to our server (in a full implementation)
        or simulates tool behavior.
        
        For now, this creates placeholder functions that print
        what would be called.
        """
        lines = [
            "# Tool wrappers (placeholder implementation)",
            "import json",
            "",
        ]
        
        for tool in tools:
            # Generate a simple wrapper that shows the call
            # In production, this would make HTTP calls back
            lines.append(f"async def {tool.name}(**kwargs):")
            lines.append(f'    """')
            lines.append(f"    {tool.description}")
            lines.append(f'    """')
            lines.append(f"    print(f'[TOOL CALL] {tool.name}({{kwargs}})')")
            lines.append(f"    return f'Result of {tool.name}'")
            lines.append("")
        
        return "\n".join(lines)


