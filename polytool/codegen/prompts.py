"""System prompts for tool usage."""

from __future__ import annotations

from polytool.core.types import Tool


EXECUTE_CODE_DESCRIPTION = """Execute Python code that orchestrates multiple tools.

Use this when you need to:
- Call multiple tools and process results together
- Perform data aggregation or transformation
- Handle complex logic better expressed in code

Tools are async functions - use 'await' when calling them.
Use 'print()' to output the final result.

Example:
```python
files = await glob_files("**/*.py")
total = 0
for f in files[:10]:
    content = await read_file(f)
    total += len(content.splitlines())
print(f"Total lines: {total}")
```
"""


def build_system_prompt(tools: list[Tool], base_prompt: str | None = None) -> str:
    """Build system prompt with tool info."""
    parts = []
    
    if base_prompt:
        parts.append(base_prompt)
    else:
        parts.append("You are a helpful assistant with access to tools.")
    
    parts.append("""
## Tool Usage

For simple tasks (1-2 tool calls), call tools directly.
For complex tasks requiring multiple tools or data processing, use execute_code.
""")
    
    parts.append("## Available Tools\n```python")
    for tool in tools:
        if tool.name == "execute_code":
            continue
        sig = tool.get_signature()
        desc = tool.description.split("\n")[0]
        parts.append(f'{sig}\n    """{desc}"""')
        parts.append("")
    parts.append("```")
    
    return "\n".join(parts)
