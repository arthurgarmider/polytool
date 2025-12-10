"""
PolyTool MCP Integration Example

This example shows how to import tools from MCP servers.
Requires the mcp extra: pip install polytool[mcp]
"""

import asyncio
import os
from polytool import Agent, from_mcp


async def main():
    # Check for GitHub token
    if "GITHUB_TOKEN" not in os.environ:
        print("Set GITHUB_TOKEN environment variable to run this example")
        return
    
    # Import tools from GitHub MCP server
    print("Connecting to GitHub MCP server...")
    github_tools = await from_mcp(
        command=["npx", "-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]},
        server_name="github",
    )
    
    print(f"Loaded {len(github_tools)} tools from GitHub:")
    for tool in github_tools[:5]:  # Show first 5
        print(f"  - {tool.name}: {tool.description[:50]}...")
    print()
    
    # Create agent with MCP tools
    agent = Agent(
        model="gpt-4o",
        tools=github_tools,
    )
    
    # Run a query
    result = await agent.run("List the top 5 most starred Python repositories")
    print(f"Output: {result.output}")


if __name__ == "__main__":
    asyncio.run(main())


