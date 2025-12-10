"""MCP server integration."""

from __future__ import annotations

import os
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from polytool.core.types import Tool, ToolSource
from polytool.core.exceptions import MCPError


async def from_mcp(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    server_name: str | None = None,
    namespace: bool = True,
) -> list[Tool]:
    """Import tools from an MCP server."""
    if server_name is None:
        for part in command:
            if "server-" in part:
                server_name = part.split("server-")[-1].split("/")[0]
                break
        if server_name is None:
            server_name = command[0] if command else "mcp"
    
    full_env = {**os.environ, **(env or {})}
    
    try:
        params = StdioServerParameters(command=command, env=full_env)
        
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                
                tools = []
                for mcp_tool in tools_response.tools:
                    tool_name = mcp_tool.name
                    if namespace:
                        tool_name = f"{server_name}.{mcp_tool.name}"
                    
                    tool = Tool(
                        name=tool_name,
                        description=mcp_tool.description or f"MCP tool: {mcp_tool.name}",
                        parameters=mcp_tool.inputSchema or {"type": "object", "properties": {}},
                        source=ToolSource.MCP,
                    )
                    
                    original_name = mcp_tool.name
                    
                    async def make_executor(name: str, cmd: list[str], environment: dict):
                        async def executor(**kwargs: Any) -> Any:
                            async with stdio_client(
                                StdioServerParameters(command=cmd, env=environment)
                            ) as (r, w):
                                async with ClientSession(r, w) as s:
                                    await s.initialize()
                                    result = await s.call_tool(name, kwargs)
                                    if result.content:
                                        for content in result.content:
                                            if hasattr(content, "text"):
                                                return content.text
                                        return result.content
                                    return None
                        return executor
                    
                    executor = await make_executor(original_name, command, full_env)
                    tool.set_executor(executor)
                    tools.append(tool)
                
                return tools
    
    except Exception as e:
        if isinstance(e, MCPError):
            raise
        raise MCPError(f"Failed to connect to MCP server: {e}", server=" ".join(command)) from e


class MCPConnection:
    """Persistent connection to an MCP server for better performance."""
    
    def __init__(self, command: list[str], env: dict[str, str] | None = None, server_name: str | None = None):
        self.command = command
        self.env = {**os.environ, **(env or {})}
        self.server_name = server_name
        self._session: ClientSession | None = None
        self._tools: list[Tool] | None = None
    
    async def __aenter__(self) -> "MCPConnection":
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()
    
    async def connect(self) -> None:
        pass
    
    async def disconnect(self) -> None:
        self._session = None
        self._tools = None
    
    async def get_tools(self) -> list[Tool]:
        if self._tools is None:
            self._tools = await from_mcp(self.command, env=self.env, server_name=self.server_name)
        return self._tools
