"""Normalize tools from any source to PolyTool format."""

from __future__ import annotations

import asyncio
from typing import Any, Callable

from langchain_core.tools import BaseTool as LangChainBaseTool

from polytool.core.types import Tool, ToolSource
from polytool.tools.decorator import get_tool_from_func, _generate_schema


def normalize_tool(tool_input: Any, *, name: str | None = None, description: str | None = None) -> Tool:
    """Convert any tool type to a PolyTool Tool."""
    if isinstance(tool_input, Tool):
        return tool_input
    
    if hasattr(tool_input, "__polytool__") and hasattr(tool_input, "tool"):
        tool = get_tool_from_func(tool_input)
        if tool:
            return tool
    
    if isinstance(tool_input, LangChainBaseTool):
        return _normalize_langchain_tool(tool_input)
    
    if callable(tool_input):
        return _normalize_callable(tool_input, name=name, description=description)
    
    raise TypeError(f"Cannot normalize {type(tool_input).__name__}")


def normalize_tools(tools: list[Any]) -> list[Tool]:
    """Normalize a list of tools."""
    return [normalize_tool(t) for t in tools]


def _normalize_langchain_tool(lc_tool: Any) -> Tool:
    """Convert LangChain BaseTool to PolyTool Tool."""
    parameters: dict[str, Any] = {"type": "object", "properties": {}}
    
    if hasattr(lc_tool, "args_schema") and lc_tool.args_schema is not None:
        try:
            parameters = lc_tool.args_schema.model_json_schema()
        except Exception:
            pass
    elif hasattr(lc_tool, "args") and lc_tool.args:
        properties = {}
        for arg_name, schema in lc_tool.args.items():
            if isinstance(schema, dict):
                properties[arg_name] = schema
            else:
                properties[arg_name] = {"type": "string", "description": str(schema)}
        parameters = {"type": "object", "properties": properties}
    
    tool = Tool(
        name=lc_tool.name,
        description=lc_tool.description or f"LangChain tool: {lc_tool.name}",
        parameters=parameters,
        source=ToolSource.LANGCHAIN,
    )
    
    async def executor(**kwargs: Any) -> Any:
        if hasattr(lc_tool, "ainvoke"):
            return await lc_tool.ainvoke(kwargs)
        elif hasattr(lc_tool, "invoke"):
            return await asyncio.to_thread(lc_tool.invoke, kwargs)
        elif hasattr(lc_tool, "_arun"):
            return await lc_tool._arun(**kwargs)
        elif hasattr(lc_tool, "_run"):
            return await asyncio.to_thread(lc_tool._run, **kwargs)
        else:
            raise RuntimeError(f"LangChain tool {lc_tool.name} has no run method")
    
    tool.set_executor(executor)
    return tool


def _normalize_callable(func: Callable[..., Any], *, name: str | None = None, description: str | None = None) -> Tool:
    """Convert a raw callable to PolyTool Tool."""
    tool_name = name or getattr(func, "__name__", None)
    if not tool_name or tool_name == "<lambda>":
        raise ValueError("Lambda requires name= argument")
    
    tool_description = description or (func.__doc__ or "").strip() or f"Tool: {tool_name}"
    
    try:
        parameters = _generate_schema(func)
    except Exception:
        parameters = {"type": "object", "properties": {}}
    
    tool = Tool(
        name=tool_name,
        description=tool_description,
        parameters=parameters,
        source=ToolSource.NATIVE,
    )
    
    if asyncio.iscoroutinefunction(func):
        tool.set_executor(func)
    else:
        async def async_wrapper(**kwargs: Any) -> Any:
            return await asyncio.to_thread(func, **kwargs)
        tool.set_executor(async_wrapper)
    
    return tool
