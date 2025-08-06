# static_filter_example.py
"""
Demonstrates how an agent can use a **static tool filter** to limit its own
access to a server's available tools.

This is a powerful **security and scoping feature**. It allows a general-purpose
agent to connect to a powerful tool server but restricts its capabilities to
only what is necessary for its specific task, reducing the risk of unintended
behavior or misuse.

Key features demonstrated:
1.  Uses `create_static_tool_filter` to define an **allowlist** of tools (`add`).
2.  Applies this filter to an `MCPServerSse` connection via the `tool_filter` parameter.
3.  Shows the agent successfully using an allowed tool.
4.  Shows the agent being unable to use a tool that was blocked by the filter.

Prerequisites:
- Requires a tool server (like the one in `my_tool_server.py`) to be running
  and offering both an "add" and a "get_weather_forecast" tool.
"""

import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerSse, create_static_tool_filter

# ------------------------------------------------------------------
# 1. Main Orchestration Logic
# ------------------------------------------------------------------
async def main():
    """
    Connects to a tool server with a filter and runs two tests to
    demonstrate allowed and blocked tool usage.
    """
    # 1. Define a static filter to ONLY allow the 'add' tool.
    #    If `allowed_tool_names` is specified, all other tools offered by the
    #    server are automatically blocked. The agent will not even know they exist.
    static_filter = create_static_tool_filter(
        allowed_tool_names=["add"]
    )
    print("🛡️  Connecting to server with a static filter (only 'add' is allowed)...")

    # When connecting, we pass the filter to the server configuration.
    # The server will still offer all its tools, but this client connection
    # will only be able to "see" the ones that pass through the filter.
    async with MCPServerSse(
        params={"url": "http://localhost:8000/sse"},
        tool_filter=static_filter
    ) as filtered_server:
        print("✅ Successfully connected to filtered tool server.")

        # This agent's perception of the world is limited by the filter.
        # To this agent, the server *only* has an "add" tool.
        agent = Agent(
            name="LimitedAgent",
            model="gpt-4-turbo",
            instructions="You are an assistant with limited tools.",
            mcp_servers=[filtered_server]
        )

        # 2. This task should SUCCEED because the 'add' tool is on the allowlist.
        print("\n--- ➡️ Running task requiring an ALLOWED tool ---")
        result_allowed = await Runner.run(
            starting_agent=agent,
            input="What is 11 + 12?"
        )
        print(f"🤖 Final Answer: {result_allowed.final_output}")


        # 3. This task should FAIL because 'get_weather_forecast' is blocked.
        #    The agent will search for a tool to get the weather, find none
        #    (because it's filtered out), and report that it cannot complete
        #    the request.
        print("\n--- 🚫 Running task requiring a BLOCKED tool ---")
        result_blocked = await Runner.run(
            starting_agent=agent,
            input="What is the weather like in New York?"
        )
        print(f"🤖 Final Answer: {result_blocked.final_output}")

# ------------------------------------------------------------------
# 2. Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())