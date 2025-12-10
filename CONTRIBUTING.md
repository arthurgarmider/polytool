# Contributing

## Setup

```bash
git clone https://github.com/polytool/polytool
cd polytool
pip install -e ".[all]"
```

## Code Style

```bash
ruff check polytool
ruff format polytool
mypy polytool
```

## Project Structure

```
polytool/
├── core/           # Types and config
├── tools/          # Tool system (@tool, registry, adapters)
├── providers/      # LLM providers (LiteLLM)
├── sandbox/        # Code execution sandboxes
├── codegen/        # PTC code generation
├── agent/          # Agent class
└── exports/        # Framework exports
```

## Good First Issues

Look for issues tagged `good first issue`. Some ideas:

- Add a new built-in tool (see `polytool/tools/builtin/`)
- Improve error messages in sandbox execution
- Add example for a specific MCP server
- Write tests for edge cases

## Adding a Tool Source

```python
# polytool/tools/my_source.py
from polytool.core.types import Tool, ToolSource

def from_my_source(source_tool) -> Tool:
    return Tool(
        name=source_tool.name,
        description=source_tool.desc,
        parameters=source_tool.schema,
        source=ToolSource.NATIVE,
    )
```

## Adding a Sandbox

```python
# polytool/sandbox/my_sandbox.py
from polytool.sandbox.base import BaseSandbox

class MySandbox(BaseSandbox):
    async def execute(self, code: str, tools: dict) -> str:
        # Run code with tools available
        ...
```

## Pull Requests

1. Fork the repo
2. Create a branch (`git checkout -b fix/issue-123`)
3. Make changes
4. Run `ruff check && ruff format`
5. Submit PR with description

Small PRs are easier to review. If your change is large, open an issue first to discuss.
