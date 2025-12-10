"""LangChain tool adapter."""

from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.tools import BaseTool

from polytool.core.types import Tool, ToolSource
from polytool.core.exceptions import ToolError


def from_langchain(lc_tool: BaseTool) -> Tool:
    """Adapt a LangChain tool to PolyTool format."""
    parameters: dict[str, Any] = {"type": "object", "properties": {}}
    
    if hasattr(lc_tool, "args_schema") and lc_tool.args_schema is not None:
        try:
            parameters = lc_tool.args_schema.model_json_schema()
        except Exception:
            pass
    elif hasattr(lc_tool, "args") and lc_tool.args:
        properties = {}
        for name, schema in lc_tool.args.items():
            if isinstance(schema, dict):
                properties[name] = schema
            else:
                properties[name] = {"type": "string", "description": str(schema)}
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
            raise ToolError(f"LangChain tool {lc_tool.name} has no invoke method", tool_name=lc_tool.name)
    
    tool.set_executor(executor)
    return tool


def from_langchain_many(lc_tools: list[BaseTool]) -> list[Tool]:
    """Adapt multiple LangChain tools."""
    return [from_langchain(t) for t in lc_tools]
