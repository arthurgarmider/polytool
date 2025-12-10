"""Exceptions for PolyTool."""

from __future__ import annotations


class PolyToolError(Exception):
    """Base exception for all PolyTool errors."""
    
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ToolError(PolyToolError):
    """Error related to tool definition or execution."""
    
    def __init__(self, message: str, tool_name: str | None = None, **kwargs):
        super().__init__(message, kwargs)
        self.tool_name = tool_name


class SandboxError(PolyToolError):
    """Error during sandbox code execution."""
    
    def __init__(
        self,
        message: str,
        code: str | None = None,
        stderr: str | None = None,
        **kwargs
    ):
        super().__init__(message, kwargs)
        self.code = code
        self.stderr = stderr


class ProviderError(PolyToolError):
    """Error from LLM provider."""
    
    def __init__(
        self,
        message: str,
        provider: str | None = None,
        model: str | None = None,
        **kwargs
    ):
        super().__init__(message, kwargs)
        self.provider = provider
        self.model = model


class MCPError(PolyToolError):
    """Error connecting to or calling MCP server."""
    
    def __init__(self, message: str, server: str | None = None, **kwargs):
        super().__init__(message, kwargs)
        self.server = server


class ValidationError(PolyToolError):
    """Error validating tool arguments or schema."""
    pass


