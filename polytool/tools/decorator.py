"""@tool decorator for registering native tools."""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Callable, TypeVar, get_type_hints, get_origin, get_args, Annotated

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from polytool.core.types import Tool, ToolSource

F = TypeVar("F", bound=Callable[..., Any])


def tool(func: F | None = None, *, name: str | None = None, description: str | None = None) -> F | Callable[[F], F]:
    """Decorator to register a function as a tool."""
    def decorator(fn: F) -> F:
        tool_name = name or fn.__name__
        tool_description = description or (fn.__doc__ or "").strip() or f"Tool: {tool_name}"
        
        parameters = _generate_schema(fn)
        
        tool_obj = Tool(
            name=tool_name,
            description=tool_description,
            parameters=parameters,
            source=ToolSource.NATIVE,
        )
        tool_obj.set_executor(fn)
        
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return fn(*args, **kwargs)
        
        wrapper.tool = tool_obj  # type: ignore
        wrapper.__polytool__ = True  # type: ignore
        
        return wrapper  # type: ignore
    
    if func is not None:
        return decorator(func)
    return decorator


def _generate_schema(func: Callable[..., Any]) -> dict[str, Any]:
    """Generate JSON Schema from function signature."""
    sig = inspect.signature(func)
    
    try:
        hints = get_type_hints(func, include_extras=True)
    except Exception:
        hints = {}
    
    properties: dict[str, Any] = {}
    required: list[str] = []
    
    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls") or param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        
        hint = hints.get(param_name)
        prop_schema = _type_to_schema(hint, param_name)
        
        if get_origin(hint) is Annotated:
            args = get_args(hint)
            for arg in args[1:]:
                if isinstance(arg, str):
                    prop_schema["description"] = arg
                elif isinstance(arg, FieldInfo) and arg.description:
                    prop_schema["description"] = arg.description
        
        if param.default is not inspect.Parameter.empty:
            prop_schema["default"] = param.default
        else:
            required.append(param_name)
        
        properties[param_name] = prop_schema
    
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    
    return schema


def _type_to_schema(hint: Any, name: str = "") -> dict[str, Any]:
    """Convert Python type hint to JSON Schema."""
    if hint is None:
        return {"type": "string"}
    
    origin = get_origin(hint)
    if origin is Annotated:
        args = get_args(hint)
        return _type_to_schema(args[0], name)
    
    if hint is type(None):
        return {"type": "null"}
    
    if hint is str:
        return {"type": "string"}
    elif hint is int:
        return {"type": "integer"}
    elif hint is float:
        return {"type": "number"}
    elif hint is bool:
        return {"type": "boolean"}
    elif hint is list or origin is list:
        items_schema = {"type": "string"}
        if origin is list:
            args = get_args(hint)
            if args:
                items_schema = _type_to_schema(args[0])
        return {"type": "array", "items": items_schema}
    elif hint is dict or origin is dict:
        return {"type": "object"}
    
    if isinstance(hint, type) and issubclass(hint, BaseModel):
        return hint.model_json_schema()
    
    return {"type": "string"}


def get_tool_from_func(func: Callable[..., Any]) -> Tool | None:
    """Extract Tool from a decorated function."""
    if hasattr(func, "tool") and isinstance(func.tool, Tool):
        return func.tool
    return None
