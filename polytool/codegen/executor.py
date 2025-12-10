"""execute_code tool implementation."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from polytool.core.types import Tool, ToolSource, ExecutionResult
from polytool.core.exceptions import SandboxError
from polytool.sandbox.base import get_sandbox
from polytool.codegen.prompts import EXECUTE_CODE_DESCRIPTION

if TYPE_CHECKING:
    from polytool.tools.registry import ToolRegistry


class ExecuteCodeTool:
    """
    The execute_code tool for PTC.
    
    This tool allows the LLM to generate and execute Python code
    that orchestrates other tools in a sandbox.
    """
    
    def __init__(
        self,
        registry: "ToolRegistry",
        sandbox_type: str | None = None,
    ):
        self.registry = registry
        self.sandbox_type = sandbox_type
        self._tool: Tool | None = None
    
    def get_tool(self) -> Tool:
        """Get the execute_code Tool object."""
        if self._tool is None:
            self._tool = Tool(
                name="execute_code",
                description=EXECUTE_CODE_DESCRIPTION,
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": (
                                "Python code to execute. Use await for tool calls. "
                                "Use print() for output."
                            ),
                        },
                    },
                    "required": ["code"],
                },
                source=ToolSource.NATIVE,
            )
            self._tool.set_executor(self.execute)
        
        return self._tool
    
    async def execute(self, code: str) -> str:
        """
        Execute code in the sandbox with tools available.
        
        Args:
            code: Python code to execute
        
        Returns:
            stdout from the code execution
        """
        # Get all tools except execute_code itself
        tools = [t for t in self.registry.get_all() if t.name != "execute_code"]
        
        # Get sandbox
        sandbox = get_sandbox(self.sandbox_type)
        
        async with sandbox:
            result = await sandbox.execute(code, tools=tools)
        
        if not result.success:
            error_msg = result.error or "Unknown error"
            if result.stderr:
                error_msg += f"\nStderr: {result.stderr}"
            raise SandboxError(
                f"Code execution failed: {error_msg}",
                code=code,
                stderr=result.stderr,
            )
        
        # Return stdout (this is what the LLM sees)
        output = result.stdout.strip()
        if not output and result.return_value is not None:
            output = str(result.return_value)
        
        return output or "(no output)"


