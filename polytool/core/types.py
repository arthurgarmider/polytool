"""Core types."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Awaitable
from pydantic import BaseModel, Field


class ToolSource(str, Enum):
    NATIVE = "native"
    MCP = "mcp"
    LANGCHAIN = "langchain"


class Tool(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    source: ToolSource = ToolSource.NATIVE
    
    _executor: Callable[..., Awaitable[Any]] | Callable[..., Any] | None = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def model_post_init(self, __context: Any) -> None:
        pass
    
    async def execute(self, **kwargs: Any) -> Any:
        if self._executor is None:
            raise ValueError(f"Tool '{self.name}' has no executor")
        result = self._executor(**kwargs)
        if hasattr(result, "__await__"):
            return await result
        return result
    
    def set_executor(self, executor: Callable[..., Any]) -> None:
        object.__setattr__(self, "_executor", executor)
    
    def to_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }
    
    def get_signature(self) -> str:
        params = []
        properties = self.parameters.get("properties", {})
        required = set(self.parameters.get("required", []))
        
        for name, schema in properties.items():
            type_hint = _json_type_to_python(schema.get("type", "Any"))
            if name in required:
                params.append(f"{name}: {type_hint}")
            else:
                default = schema.get("default", "None")
                params.append(f"{name}: {type_hint} = {repr(default)}")
        
        return f"async def {self.name}({', '.join(params)}) -> Any"


def _json_type_to_python(json_type: str) -> str:
    mapping = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
    }
    return mapping.get(json_type, "Any")


class CodeBlock(BaseModel):
    code: str
    description: str = ""
    tools_used: list[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    return_value: Any = None
    error: str | None = None
    execution_time_ms: float = 0


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    tool_calls: int = 0
    ptc_executions: int = 0
    estimated_cost_usd: float = 0.0
    execution_time_ms: float = 0
    estimated_direct_tokens: int | None = None
    
    @property
    def token_savings_percent(self) -> float | None:
        if self.estimated_direct_tokens is None or self.estimated_direct_tokens == 0:
            return None
        savings = (self.estimated_direct_tokens - self.total_tokens) / self.estimated_direct_tokens
        return round(savings * 100, 1)


class Message(BaseModel):
    role: str
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None
