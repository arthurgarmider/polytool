"""PolyTool + LangChain agent integration example."""

import asyncio
from polytool import create_execute_code_tool, tool

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_openai_tools_agent, AgentExecutor


@tool
async def search_files(pattern: str) -> list[str]:
    """Search for files matching a glob pattern."""
    import glob
    return glob.glob(pattern, recursive=True)


@tool
async def read_file(path: str) -> str:
    """Read contents of a file."""
    with open(path) as f:
        return f.read()


@tool
async def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


async def main():
    print("=== PolyTool + LangChain Integration ===\n")
    
    ptc_tool = create_execute_code_tool(
        tools=[search_files, read_file, count_words],
        export_as="langchain"
    )
    
    print(f"Created PTC tool: {ptc_tool.name}")
    print(f"Description: {ptc_tool.description[:100]}...\n")
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant with access to tools.

For simple tasks (1-2 tool calls), call tools directly.
For complex tasks (multiple tools, data processing), use execute_code.

Available in execute_code:
- search_files(pattern), read_file(path), count_words(text)

Use print() for output."""),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    
    all_tools = [ptc_tool, search_files.tool, read_file.tool, count_words.tool]
    agent = create_openai_tools_agent(llm, all_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=True)
    
    print("--- Simple Query ---")
    result = await agent_executor.ainvoke({"input": "Count the words in 'Hello world, this is a test'"})
    print(f"Result: {result['output']}\n")
    
    print("--- Complex Query ---")
    result = await agent_executor.ainvoke({"input": "Find all Python files in the current directory and count total words"})
    print(f"Result: {result['output']}")


if __name__ == "__main__":
    asyncio.run(main())
