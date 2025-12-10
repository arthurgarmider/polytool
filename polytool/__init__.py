"""PolyTool - Universal tool orchestration for LLMs."""

from polytool.core.types import Tool, ToolSource, CodeBlock, ExecutionResult, Usage
from polytool.core.exceptions import PolyToolError, ToolError, SandboxError, ProviderError
from polytool.tools.decorator import tool
from polytool.tools.registry import ToolRegistry
from polytool.tools.mcp import from_mcp
from polytool.tools.langchain import from_langchain
from polytool.tools.universal import normalize_tool, normalize_tools
from polytool.exports.base import create_execute_code_tool, ExecuteCodeExport
from polytool.agent.agent import Agent, AgentResult

__all__ = [
    # Core types
    "Tool",
    "ToolSource",
    "CodeBlock",
    "ExecutionResult",
    "Usage",
    # Exceptions
    "PolyToolError",
    "ToolError",
    "SandboxError",
    "ProviderError",
    # Tools
    "tool",
    "ToolRegistry",
    "from_mcp",
    "from_langchain",
    "normalize_tool",
    "normalize_tools",
    # Framework Exports (key feature!)
    "create_execute_code_tool",
    "ExecuteCodeExport",
    # Agent
    "Agent",
    "AgentResult",
]

__version__ = "0.1.0"

