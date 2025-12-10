"""LiteLLM provider implementation for PolyTool."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import litellm
from litellm import acompletion

from polytool.core.types import Message, Tool, Usage
from polytool.core.config import get_settings
from polytool.core.exceptions import ProviderError


class LiteLLMProvider:
    """
    LLM provider using LiteLLM for 100+ model support.
    
    Supports OpenAI, Anthropic, Google, Azure, Bedrock, Ollama, and more.
    """
    
    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ):
        settings = get_settings()
        
        self.model = model or settings.default_model
        self.temperature = temperature if temperature is not None else settings.default_temperature
        self.max_tokens = max_tokens or settings.default_max_tokens
        self.extra_kwargs = kwargs
        
        # Set API key if provided
        if api_key:
            # LiteLLM will pick this up based on model prefix
            litellm.api_key = api_key
    
    async def generate(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> tuple[Message, Usage]:
        """
        Generate a response from the LLM.
        
        Args:
            messages: Conversation history
            tools: Available tools for function calling
            **kwargs: Additional LiteLLM options
        
        Returns:
            Tuple of (assistant message, usage stats)
        """
        # Convert messages to LiteLLM format
        litellm_messages = [self._message_to_dict(m) for m in messages]
        
        # Convert tools to OpenAI format
        litellm_tools = None
        if tools:
            litellm_tools = [t.to_openai_schema() for t in tools]
        
        try:
            response = await acompletion(
                model=self.model,
                messages=litellm_messages,
                tools=litellm_tools,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **{**self.extra_kwargs, **kwargs},
            )
            
            # Extract response
            choice = response.choices[0]
            assistant_message = self._response_to_message(choice.message)
            
            # Extract usage
            usage = Usage(
                input_tokens=response.usage.prompt_tokens if response.usage else 0,
                output_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            )
            
            return assistant_message, usage
        
        except Exception as e:
            raise ProviderError(
                f"LiteLLM error: {e}",
                provider="litellm",
                model=self.model,
            ) from e
    
    async def generate_stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a response from the LLM."""
        litellm_messages = [self._message_to_dict(m) for m in messages]
        litellm_tools = [t.to_openai_schema() for t in tools] if tools else None
        
        try:
            response = await acompletion(
                model=self.model,
                messages=litellm_messages,
                tools=litellm_tools,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
                **{**self.extra_kwargs, **kwargs},
            )
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            raise ProviderError(
                f"LiteLLM streaming error: {e}",
                provider="litellm",
                model=self.model,
            ) from e
    
    def _message_to_dict(self, message: Message) -> dict[str, Any]:
        """Convert Message to LiteLLM dict format."""
        result: dict[str, Any] = {"role": message.role}
        
        if message.content is not None:
            result["content"] = message.content
        
        if message.tool_calls:
            result["tool_calls"] = message.tool_calls
        
        if message.tool_call_id:
            result["tool_call_id"] = message.tool_call_id
        
        if message.name:
            result["name"] = message.name
        
        return result
    
    def _response_to_message(self, response_message: Any) -> Message:
        """Convert LiteLLM response to Message."""
        tool_calls = None
        if hasattr(response_message, "tool_calls") and response_message.tool_calls:
            tool_calls = []
            for tc in response_message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                })
        
        return Message(
            role="assistant",
            content=response_message.content,
            tool_calls=tool_calls,
        )


