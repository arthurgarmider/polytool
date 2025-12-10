"""
PolyTool Quickstart Example

This example shows basic usage of PolyTool with custom tools.
The LLM will decide when to use direct tool calls vs PTC.
"""

import asyncio
from polytool import Agent, tool


# Define a simple tool
@tool
async def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Mock implementation
    weather_data = {
        "tokyo": "72°F, sunny",
        "london": "55°F, cloudy",
        "new york": "65°F, partly cloudy",
    }
    return weather_data.get(city.lower(), f"Weather data not available for {city}")


@tool
async def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    # Simple safe eval for math
    allowed = set("0123456789+-*/(). ")
    if not all(c in allowed for c in expression):
        raise ValueError("Invalid characters in expression")
    return eval(expression)


async def main():
    # Create agent with tools
    agent = Agent(
        model="gpt-4o",
        tools=[get_weather, calculate],
    )
    
    print("=== Simple Query (Direct Call) ===")
    result = await agent.run("What's the weather in Tokyo?")
    print(f"Output: {result.output}")
    print(f"Tool calls: {result.usage.tool_calls}, PTC: {result.ptc_used}")
    print()
    
    print("=== Complex Query (PTC) ===")
    result = await agent.run(
        "Get the weather for Tokyo, London, and New York, "
        "then tell me which city has the highest temperature."
    )
    print(f"Output: {result.output}")
    print(f"Tool calls: {result.usage.tool_calls}, PTC: {result.ptc_used}")
    print(f"Tokens used: {result.usage.total_tokens}")


if __name__ == "__main__":
    asyncio.run(main())


