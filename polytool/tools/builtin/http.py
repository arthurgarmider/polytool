"""HTTP tools for PolyTool."""

from __future__ import annotations

from typing import Any, Annotated

import httpx

from polytool.tools.decorator import tool


@tool
async def http_get(
    url: Annotated[str, "URL to fetch"],
    headers: Annotated[dict[str, str] | None, "Optional headers"] = None,
    timeout: Annotated[float, "Timeout in seconds"] = 30.0,
) -> dict[str, Any]:
    """
    Make an HTTP GET request.
    
    Returns a dict with 'status_code', 'headers', and 'body'.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=timeout)
        
        # Try to parse JSON, fallback to text
        try:
            body = response.json()
        except Exception:
            body = response.text
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": body,
        }


@tool
async def http_post(
    url: Annotated[str, "URL to post to"],
    json: Annotated[dict[str, Any] | None, "JSON body"] = None,
    data: Annotated[dict[str, Any] | None, "Form data"] = None,
    headers: Annotated[dict[str, str] | None, "Optional headers"] = None,
    timeout: Annotated[float, "Timeout in seconds"] = 30.0,
) -> dict[str, Any]:
    """
    Make an HTTP POST request.
    
    Returns a dict with 'status_code', 'headers', and 'body'.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=json,
            data=data,
            headers=headers,
            timeout=timeout,
        )
        
        try:
            body = response.json()
        except Exception:
            body = response.text
        
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": body,
        }


