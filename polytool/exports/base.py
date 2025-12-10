"""Portable PTC tool for any framework."""

from __future__ import annotations

import asyncio
from typing import Any, Literal

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun

from polytool.core.types import Tool, ToolSource
from polytool.core.exceptions import SandboxError
from polytool.sandbox.base import get_sandbox
from polytool.tools.universal import normalize_tools
from polytool.codegen.prompts import EXECUTE_CODE_DESCRIPTION


class ExecuteCodeInput(BaseModel):
    code: str = Field(description="Python code to execute")


class ExecuteCodeExport:
    """Portable execute_code tool that works with LangChain, LiteLLM, OpenAI, etc."""
    
    def __init__(self, tools: list[Tool], sandbox_type: str = "restricted"):
        self.tools = tools
        self.sandbox_type = sandbox_type
        self._langchain_tool: Any = None
    
    async def run(self, code: str) -> str:
        """Execute code in sandbox."""
        sandbox = get_sandbox(self.sandbox_type)
        
        async with sandbox:
            result = await sandbox.execute(code, tools=self.tools)
        
        if not result.success:
            error_msg = result.error or "Unknown error"
            if result.stderr:
                error_msg += f"\nStderr: {result.stderr}"
            raise SandboxError(f"Code execution failed: {error_msg}", code=code, stderr=result.stderr)
        
        output = result.stdout.strip()
        if not output and result.return_value is not None:
            output = str(result.return_value)
        
        return output or "(no output)"
    
    def run_sync(self, code: str) -> str:
        """Sync wrapper for run()."""
        return asyncio.run(self.run(code))
    
    @property
    def schema(self) -> dict[str, Any]:
        return self.as_openai_schema()
    
    @property
    def name(self) -> str:
        return "execute_code"
    
    @property
    def description(self) -> str:
        base = EXECUTE_CODE_DESCRIPTION
        if self.tools:
            sigs = []
            for t in self.tools:
                sig = t.get_signature()
                desc = t.description.split("\n")[0]
                sigs.append(f"{sig}\n    '''{desc}'''")
            base += "\n\nAvailable tools:\n```python\n" + "\n\n".join(sigs) + "\n```"
        return base
    
    def as_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute. Use await for tool calls.",
                        },
                    },
                    "required": ["code"],
                },
            },
        }
    
    def as_litellm_tool(self) -> dict[str, Any]:
        return self.as_openai_schema()
    
    def as_langchain(self) -> BaseTool:
        """Export as LangChain BaseTool."""
        if self._langchain_tool is None:
            self._langchain_tool = _create_langchain_tool(self)
        return self._langchain_tool
    
    def as_polytool(self) -> Tool:
        tool = Tool(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                },
                "required": ["code"],
            },
            source=ToolSource.NATIVE,
        )
        tool.set_executor(self.run)
        return tool


def _create_langchain_tool(export: ExecuteCodeExport) -> BaseTool:
    class PolyToolExecuteCode(BaseTool):
        name: str = "execute_code"
        description: str = export.description
        args_schema: type = ExecuteCodeInput
        _export: ExecuteCodeExport = export
        
        def __init__(self, **kwargs: Any):
            super().__init__(**kwargs)
            object.__setattr__(self, "_export", export)
        
        def _run(self, code: str, run_manager: CallbackManagerForToolRun | None = None) -> str:
            return self._export.run_sync(code)
        
        async def _arun(self, code: str, run_manager: AsyncCallbackManagerForToolRun | None = None) -> str:
            return await self._export.run(code)
    
    return PolyToolExecuteCode()


def create_execute_code_tool(
    tools: list[Any],
    *,
    sandbox_type: str = "restricted",
    export_as: Literal["polytool", "langchain", "openai", "litellm"] = "polytool",
) -> ExecuteCodeExport | Tool | Any:
    """Create a portable execute_code tool for any agent framework."""
    normalized_tools = normalize_tools(tools)
    export = ExecuteCodeExport(tools=normalized_tools, sandbox_type=sandbox_type)
    
    if export_as == "langchain":
        return export.as_langchain()
    elif export_as in ("openai", "litellm"):
        return export
    else:
        return export
