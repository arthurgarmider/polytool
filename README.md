# PolyTool

Universal tool orchestration for LLMs with Programmatic Tool Calling.

PolyTool brings [Anthropic's Programmatic Tool Calling](https://www.anthropic.com/engineering/advanced-tool-use) to any LLM provider. Instead of multiple inference passes for tool calls, the LLM generates code that orchestrates tools in a single pass—saving tokens on complex workflows.

## Features

- **Multi-Provider**: Works with OpenAI, Anthropic, Google, Ollama, and 100+ more via LiteLLM
- **Multi-Source Tools**: Combine native tools, MCP servers, and LangChain tools
- **Smart Execution**: LLM decides when to use direct calls vs code generation
- **Secure Sandboxing**: E2B cloud sandbox for production, local sandbox for dev

## Installation

```bash
pip install polytool

# With extras
pip install polytool[mcp]       # MCP server support
pip install polytool[langchain] # LangChain tools
pip install polytool[e2b]       # E2B cloud sandbox
```

## Usage

```python
import asyncio
from polytool import Agent, tool

@tool
async def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"72°F, sunny in {city}"

@tool
async def search_files(pattern: str) -> list[str]:
    """Search for files."""
    import glob
    return glob.glob(pattern)

agent = Agent(model="gpt-4o", tools=[get_weather, search_files])

async def main():
    # Simple task -> direct tool call
    result = await agent.run("What's the weather in Tokyo?")
    print(result.output)
    
    # Complex task -> generates code
    result = await agent.run("Find all Python files and count lines")
    print(result.output)

asyncio.run(main())
```

## MCP Server Tools

```python
from polytool import Agent, from_mcp

github_tools = await from_mcp(
    command=["npx", "@modelcontextprotocol/server-github"],
    env={"GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]}
)

agent = Agent(model="gpt-4o", tools=github_tools)
```

## LangChain Tools

```python
from polytool import Agent, from_langchain
from langchain_community.tools import WikipediaQueryRun

wiki = from_langchain(WikipediaQueryRun())
agent = Agent(model="gpt-4o", tools=[wiki])
```

## Framework Integration

Use PolyTool with existing agent frameworks:

```python
from polytool import create_execute_code_tool, tool

@tool
async def search_files(pattern: str) -> list[str]:
    import glob
    return glob.glob(pattern)

# Export for LangChain
ptc = create_execute_code_tool(tools=[search_files], export_as="langchain")

# Or use with LiteLLM directly
ptc = create_execute_code_tool(tools=[search_files])
response = await litellm.acompletion(model="gpt-4o", tools=[ptc.schema], messages=[...])
```

## How It Works

Traditional tool calling requires multiple LLM passes:
1. LLM calls tool A -> result A
2. LLM processes, calls tool B -> result B  
3. Final answer

For complex tasks, PolyTool lets the LLM generate code instead:

```python
# LLM generates and runs this
files = await search_files("*.py")
total = 0
for f in files:
    content = await read_file(f)
    total += len(content.splitlines())
print(f"Total: {total} lines")
```

One inference pass instead of N tool calls.

## Configuration

```bash
POLYTOOL_DEFAULT_MODEL=gpt-4o
POLYTOOL_SANDBOX_TYPE=restricted  # or e2b, docker
OPENAI_API_KEY=your-key
```

## License

MIT
