"""
PolyTool + LiteLLM Direct Integration

This example shows how to use PTC with direct LiteLLM calls
(no agent framework required).

Requirements:
    pip install polytool litellm
"""

import asyncio
import json
import litellm
from polytool import create_execute_code_tool, tool


# Define your tools
@tool
async def get_weather(city: str) -> str:
    """Get weather for a city."""
    # Mock implementation
    weather = {
        "tokyo": "72°F, sunny",
        "london": "55°F, cloudy",
        "new york": "65°F, partly cloudy",
        "paris": "60°F, rainy",
    }
    return weather.get(city.lower(), f"Weather not available for {city}")


@tool
async def search_restaurants(city: str, cuisine: str = "any") -> list[str]:
    """Search for restaurants in a city."""
    # Mock implementation
    return [f"{cuisine.title()} Restaurant 1 in {city}", f"{cuisine.title()} Restaurant 2 in {city}"]


async def main():
    print("=== PolyTool + LiteLLM Direct Integration ===")
    print()
    
    # Create PTC tool
    ptc = create_execute_code_tool(
        tools=[get_weather, search_restaurants],
        sandbox_type="restricted",
    )
    
    print(f"PTC Tool created with {len(ptc.tools)} tools available")
    print()
    
    # Build tools list for LiteLLM
    # Include both PTC and direct tool schemas
    tools = [
        ptc.schema,  # PTC tool
        get_weather.tool.to_openai_schema(),  # Direct tools
        search_restaurants.tool.to_openai_schema(),
    ]
    
    # Simple query - LLM will likely use direct call
    print("--- Simple Query ---")
    messages = [
        {"role": "system", "content": """You have access to tools.
For simple tasks, call tools directly.
For complex tasks requiring multiple tools, use execute_code to write Python."""},
        {"role": "user", "content": "What's the weather in Tokyo?"}
    ]
    
    response = await litellm.acompletion(
        model="gpt-4o",
        messages=messages,
        tools=tools,
    )
    
    # Handle response
    if response.choices[0].message.tool_calls:
        for tc in response.choices[0].message.tool_calls:
            print(f"Tool called: {tc.function.name}")
            args = json.loads(tc.function.arguments)
            
            if tc.function.name == "execute_code":
                # Run PTC
                result = await ptc.run(args["code"])
            elif tc.function.name == "get_weather":
                result = await get_weather.tool.execute(**args)
            else:
                result = await search_restaurants.tool.execute(**args)
            
            print(f"Result: {result}")
    else:
        print(f"Direct response: {response.choices[0].message.content}")
    
    print()
    
    # Complex query - LLM will likely use PTC
    print("--- Complex Query ---")
    messages = [
        {"role": "system", "content": """You have access to tools.
For simple tasks, call tools directly.
For complex tasks requiring multiple tools, use execute_code to write Python.

Available in execute_code:
- get_weather(city) - Get weather
- search_restaurants(city, cuisine) - Find restaurants

Use print() for output in execute_code."""},
        {"role": "user", "content": "Get the weather for Tokyo, London, and Paris, then find Italian restaurants in the warmest city."}
    ]
    
    response = await litellm.acompletion(
        model="gpt-4o",
        messages=messages,
        tools=tools,
    )
    
    if response.choices[0].message.tool_calls:
        for tc in response.choices[0].message.tool_calls:
            print(f"Tool called: {tc.function.name}")
            args = json.loads(tc.function.arguments)
            
            if tc.function.name == "execute_code":
                print(f"Code:\n{args['code'][:200]}...")
                result = await ptc.run(args["code"])
                print(f"Result: {result}")
            else:
                print(f"Args: {args}")


if __name__ == "__main__":
    asyncio.run(main())

