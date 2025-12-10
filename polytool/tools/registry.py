"""Unified tool registry for PolyTool."""

from __future__ import annotations

from typing import Any, Callable

from polytool.core.types import Tool, ToolSource
from polytool.core.exceptions import ToolError
from polytool.tools.decorator import get_tool_from_func


class ToolRegistry:
    """
    Unified registry for tools from all sources.
    
    Combines native @tool decorated functions, MCP server tools,
    and LangChain tools into a single registry.
    """
    
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool_or_func: Tool | Callable[..., Any]) -> Tool:
        """
        Register a tool or decorated function.
        
        Args:
            tool_or_func: Either a Tool object or a @tool decorated function
        
        Returns:
            The registered Tool
        
        Raises:
            ToolError: If tool name already exists or invalid input
        """
        if isinstance(tool_or_func, Tool):
            tool = tool_or_func
        elif callable(tool_or_func):
            tool = get_tool_from_func(tool_or_func)
            if tool is None:
                raise ToolError(
                    f"Function {tool_or_func.__name__} is not decorated with @tool",
                    tool_name=getattr(tool_or_func, "__name__", None),
                )
        else:
            raise ToolError(f"Cannot register {type(tool_or_func)}")
        
        if tool.name in self._tools:
            raise ToolError(
                f"Tool '{tool.name}' already registered",
                tool_name=tool.name,
            )
        
        self._tools[tool.name] = tool
        return tool
    
    def register_many(self, tools: list[Tool | Callable[..., Any]]) -> list[Tool]:
        """Register multiple tools at once."""
        return [self.register(t) for t in tools]
    
    def get(self, name: str) -> Tool:
        """
        Get a tool by name.
        
        Raises:
            ToolError: If tool not found
        """
        if name not in self._tools:
            available = ", ".join(self._tools.keys())
            raise ToolError(
                f"Tool '{name}' not found. Available: {available}",
                tool_name=name,
            )
        return self._tools[name]
    
    def get_all(self) -> list[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_by_source(self, source: ToolSource) -> list[Tool]:
        """Get tools from a specific source."""
        return [t for t in self._tools.values() if t.source == source]
    
    def has(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
    
    def remove(self, name: str) -> None:
        """Remove a tool from the registry."""
        if name in self._tools:
            del self._tools[name]
    
    def clear(self) -> None:
        """Remove all tools."""
        self._tools.clear()
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self._tools
    
    def __iter__(self):
        return iter(self._tools.values())
    
    async def execute(self, name: str, **kwargs: Any) -> Any:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            **kwargs: Tool arguments
        
        Returns:
            Tool execution result
        """
        tool = self.get(name)
        return await tool.execute(**kwargs)
    
    def get_for_llm(self) -> list[dict[str, Any]]:
        """
        Get all tools in OpenAI function calling format.
        
        Returns:
            List of tool schemas for LLM
        """
        return [tool.to_openai_schema() for tool in self._tools.values()]
    
    def get_signatures(self) -> str:
        """
        Get Python-style signatures for all tools.
        
        Used in system prompts for execute_code.
        """
        lines = []
        for tool in self._tools.values():
            sig = tool.get_signature()
            desc = tool.description.split("\n")[0]  # First line only
            lines.append(f"{sig}\n    '''{desc}'''")
        return "\n\n".join(lines)
    
    def get_names(self) -> list[str]:
        """Get list of all tool names."""
        return list(self._tools.keys())


# Global default registry
_default_registry: ToolRegistry | None = None


def get_default_registry() -> ToolRegistry:
    """Get the default global registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry


