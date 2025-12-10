"""Sandbox execution for PolyTool."""

from polytool.sandbox.base import Sandbox, get_sandbox
from polytool.sandbox.restricted import RestrictedSandbox

__all__ = [
    "Sandbox",
    "get_sandbox",
    "RestrictedSandbox",
]

# E2B is optional
try:
    from polytool.sandbox.e2b import E2BSandbox
    __all__.append("E2BSandbox")
except ImportError:
    pass


