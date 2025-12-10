"""PolyTool Agent."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from pydantic import BaseModel, Field

from polytool.core.types import Message, Tool, Usage
from polytool.core.exceptions import PolyToolError, ToolError
from polytool.tools.registry import ToolRegistry
from polytool.tools.decorator import get_tool_from_func
from polytool.providers.litellm import LiteLLMProvider
from polytool.codegen.executor import ExecuteCodeTool
from polytool.codegen.prompts import build_system_prompt


class AgentResult(BaseModel):
    output: str
    usage: Usage = Field(default_factory=Usage)
    messages: list[Message] = Field(default_factory=list)
    tool_calls_made: int = 0
    ptc_used: bool = False


class Agent:
    """Universal tool orchestration for LLMs."""
    
    def __init__(
        self,
        model: str = "gpt-4o",
        tools: list[Tool | Callable[..., Any]] | None = None,
        system_prompt: str | None = None,
        enable_ptc: bool = True,
        sandbox_type: str | None = None,
        max_iterations: int = 10,
        **provider_kwargs: Any,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.enable_ptc = enable_ptc
        self.sandbox_type = sandbox_type
        self.max_iterations = max_iterations
        
        self.provider = LiteLLMProvider(model=model, **provider_kwargs)
        self.registry = ToolRegistry()
        
        if tools:
            for t in tools:
                if isinstance(t, Tool):
                    self.registry.register(t)
                elif callable(t):
                    tool_obj = get_tool_from_func(t)
                    if tool_obj:
                        self.registry.register(tool_obj)
                    else:
                        raise ToolError(f"Function {t.__name__} is not decorated with @tool")
        
        if enable_ptc:
            self._execute_code = ExecuteCodeTool(self.registry, sandbox_type)
            self.registry.register(self._execute_code.get_tool())
    
    async def run(self, prompt: str, *, messages: list[Message] | None = None) -> AgentResult:
        """Run the agent with a prompt."""
        conversation = list(messages or [])
        
        if not conversation or conversation[0].role != "system":
            tools = self.registry.get_all()
            full_system = build_system_prompt(tools, self.system_prompt)
            conversation.insert(0, Message(role="system", content=full_system))
        
        conversation.append(Message(role="user", content=prompt))
        
        total_usage = Usage()
        tool_calls_made = 0
        ptc_used = False
        
        for _ in range(self.max_iterations):
            tools = self.registry.get_all()
            response, usage = await self.provider.generate(conversation, tools)
            
            total_usage.input_tokens += usage.input_tokens
            total_usage.output_tokens += usage.output_tokens
            total_usage.total_tokens += usage.total_tokens
            
            conversation.append(response)
            
            if not response.tool_calls:
                return AgentResult(
                    output=response.content or "",
                    usage=total_usage,
                    messages=conversation,
                    tool_calls_made=tool_calls_made,
                    ptc_used=ptc_used,
                )
            
            for tool_call in response.tool_calls:
                tool_calls_made += 1
                
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                tool_call_id = tool_call["id"]
                
                if func_name == "execute_code":
                    ptc_used = True
                    total_usage.ptc_executions += 1
                else:
                    total_usage.tool_calls += 1
                
                try:
                    result = await self.registry.execute(func_name, **func_args)
                    result_str = str(result) if not isinstance(result, str) else result
                except Exception as e:
                    result_str = f"Error: {e}"
                
                conversation.append(Message(
                    role="tool",
                    content=result_str,
                    tool_call_id=tool_call_id,
                    name=func_name,
                ))
        
        return AgentResult(
            output="[Max iterations reached]",
            usage=total_usage,
            messages=conversation,
            tool_calls_made=tool_calls_made,
            ptc_used=ptc_used,
        )
    
    def run_sync(self, prompt: str, **kwargs: Any) -> AgentResult:
        """Sync wrapper for run()."""
        return asyncio.run(self.run(prompt, **kwargs))
    
    def add_tool(self, tool: Tool | Callable[..., Any]) -> None:
        if isinstance(tool, Tool):
            self.registry.register(tool)
        elif callable(tool):
            tool_obj = get_tool_from_func(tool)
            if tool_obj:
                self.registry.register(tool_obj)
    
    def add_tools(self, tools: list[Tool | Callable[..., Any]]) -> None:
        for t in tools:
            self.add_tool(t)
    
    @property
    def tools(self) -> list[Tool]:
        return self.registry.get_all()
