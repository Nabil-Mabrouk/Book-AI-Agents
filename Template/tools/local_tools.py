# tools/local_tools.py
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """Gets the current weather for a specific city."""
    print(f"TOOL: Getting weather for {city}")
    # In a real application, this would call a weather API.
    if city.lower() == "boston":
        return "The weather in Boston is 72 degrees and sunny."
    return f"Sorry, I don't have the weather for {city}."