"""Base provider protocol for PolyTool."""

from __future__ import annotations

from typing import Any, Protocol, AsyncIterator

from polytool.core.types import Message, Tool


class Provider(Protocol):
    """Protocol for LLM providers."""
    
    async def generate(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> Message:
        """
        Generate a response from the LLM.
        
        Args:
            messages: Conversation history
            tools: Available tools for function calling
            **kwargs: Provider-specific options
        
        Returns:
            Assistant message (may include tool_calls)
        """
        ...
    
    async def generate_stream(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream a response from the LLM.
        
        Args:
            messages: Conversation history
            tools: Available tools
            **kwargs: Provider-specific options
        
        Yields:
            Response chunks
        """
        ...


