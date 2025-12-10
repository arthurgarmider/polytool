"""
PolyTool LangChain Integration Example

This example shows how to use LangChain tools with PolyTool.
Requires the langchain extra: pip install polytool[langchain]
"""

import asyncio
from polytool import Agent, from_langchain

# Check if LangChain is available
try:
    from langchain_community.tools import WikipediaQueryRun
    from langchain_community.utilities import WikipediaAPIWrapper
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


async def main():
    if not LANGCHAIN_AVAILABLE:
        print("Install LangChain to run this example:")
        print("  pip install polytool[langchain] langchain-community wikipedia")
        return
    
    # Create LangChain tool
    wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    
    # Adapt to PolyTool
    wiki_tool = from_langchain(wikipedia)
    print(f"Adapted LangChain tool: {wiki_tool.name}")
    print()
    
    # Create agent
    agent = Agent(
        model="gpt-4o",
        tools=[wiki_tool],
    )
    
    # Run a query
    result = await agent.run("What is the history of Python programming language?")
    print(f"Output: {result.output[:500]}...")
    print()
    print(f"Token usage: {result.usage.total_tokens}")


if __name__ == "__main__":
    asyncio.run(main())


