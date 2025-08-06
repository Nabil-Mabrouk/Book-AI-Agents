# Chapter-11/my_tool_server.py
"""
Demonstrates a **streamlined way to create a networked MCP Tool Server**
using the `FastMCP` high-level framework.

This pattern significantly reduces the boilerplate code required to create
and deploy a tool server, making it ideal for rapid development.

This script shows how to:
1.  Use the `@mcp.tool()` decorator to easily expose Python functions as tools.
2.  Automatically infer a tool's schema (name, description, parameters) from
    the function's signature, type hints, and docstring.
3.  Start a production-ready network server with a simple `mcp.run()` command.
"""

from mcp.server.fastmcp import FastMCP
import random

# ------------------------------------------------------------------
# 1. Server and Tool Definitions
# ------------------------------------------------------------------

# `FastMCP` is a high-level wrapper that simplifies server creation.
mcp = FastMCP(
    "MyCustomToolServer",
)

# The `@mcp.tool()` decorator automatically registers the decorated function
# as a discoverable tool. It intelligently uses Python's type hints and
# the function's docstring to build the formal tool schema that will be
# advertised to connecting agents.
@mcp.tool()
def add(a: int, b: int) -> int:
    """Adds two integers together and returns the result."""
    print(f"⚙️  [Server] Adding {a} + {b}")
    return a + b

@mcp.tool()
def get_weather_forecast(city: str) -> str:
    """Returns a fake weather forecast for a given city."""
    print(f"🌦️  [Server] Getting forecast for {city}")
    forecasts = ["Sunny", "Cloudy", "Rainy with a chance of meatballs"]
    return f"The forecast for {city} is: {random.choice(forecasts)}."

# ------------------------------------------------------------------
# 2. Server Execution
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting custom tool server via mcp.run()...")
    # This single command starts a production-ready web server (like Uvicorn)
    # and makes the registered tools available over the specified network
    # transport. The default URL for SSE is http://localhost:8000/sse.
    mcp.run(transport="sse")