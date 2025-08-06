# my_tool_server.py
from mcp.server.fastmcp import FastMCP
import random

mcp = FastMCP("MyCustomToolServer")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Adds two integers together."""
    print(f"[Server] Adding {a} + {b}")
    return a + b

# ... (add other tools if you want, but 'add' is enough for the test)

if __name__ == "__main__":
    print("Starting custom tool server on http://localhost:8000/sse...")
    mcp.run(transport="sse")