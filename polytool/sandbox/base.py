"""Base sandbox protocol for PolyTool."""

from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

from polytool.core.types import ExecutionResult, Tool
from polytool.core.config import get_settings

if TYPE_CHECKING:
    from polytool.tools.registry import ToolRegistry


class Sandbox(Protocol):
    """Protocol for code execution sandboxes."""
    
    async def execute(
        self,
        code: str,
        tools: list[Tool] | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        """
        Execute code in the sandbox.
        
        Args:
            code: Python code to execute
            tools: Tools to make available in the sandbox
            timeout: Execution timeout in seconds
        
        Returns:
            ExecutionResult with stdout, stderr, and return value
        """
        ...
    
    async def __aenter__(self) -> "Sandbox":
        """Enter async context."""
        ...
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        ...


def get_sandbox(sandbox_type: str | None = None) -> Sandbox:
    """
    Get a sandbox instance based on configuration.
    
    Args:
        sandbox_type: Override sandbox type ("e2b", "restricted", "docker")
    
    Returns:
        Appropriate Sandbox instance
    """
    settings = get_settings()
    stype = sandbox_type or settings.sandbox_type
    
    if stype == "e2b":
        try:
            from polytool.sandbox.e2b import E2BSandbox
            return E2BSandbox()
        except ImportError:
            # Fall back to restricted if E2B not installed
            from polytool.sandbox.restricted import RestrictedSandbox
            return RestrictedSandbox()
    
    elif stype == "restricted":
        from polytool.sandbox.restricted import RestrictedSandbox
        return RestrictedSandbox()
    
    elif stype == "docker":
        raise NotImplementedError("Docker sandbox not yet implemented")
    
    else:
        raise ValueError(f"Unknown sandbox type: {stype}")


