# Chapter-11/dynamic_filter_example.py
"""
Demonstrates how to use a **dynamic tool filter** to create a sophisticated,
context-aware access control policy for agents.

Unlike a static filter, a dynamic filter is a function that runs every time
an agent tries to discover tools. It can inspect the context of the request—such
as the name of the agent making the call—and decide on a tool-by-tool basis
whether to grant or deny access.

Key features demonstrated:
1.  A filter function (`dynamic_filter_for_experts`) that implements role-based access control.
2.  The filter allows an "Expert" agent to access a specific tool (`get_weather_forecast`).
3.  The filter blocks a "Novice" agent from accessing the same tool.
4.  The filter is passed directly to the `MCPServerSse` connection.

Prerequisites:
- Requires a tool server (like the one in `my_tool_server.py`) to be running
  and offering both an "add" and a "get_weather_forecast" tool.
"""

import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerSse, ToolFilterContext
from mcp.types import Tool as MCPTool

# ------------------------------------------------------------------
# 1. The Dynamic Filter Function
# ------------------------------------------------------------------

def dynamic_filter_for_experts(context: ToolFilterContext, tool: MCPTool) -> bool:
    """
    A dynamic filter that only allows 'expert' agents to access weather tools.

    This function is called by the framework for each tool the server offers.

    Args:
        context: An object containing metadata about the run, including the
                 agent instance making the call (`context.agent`).
        tool: The specific tool from the server that is being evaluated.

    Returns:
        True if the agent is allowed to see this tool, False otherwise.
    """
    # Check if the agent's name contains "Expert". This is our role-check.
    is_expert = "Expert" in context.agent.name

    # This is the core policy logic.
    if "weather" in tool.name and not is_expert:
        # This print statement helps us see the filter in action during the run.
        print(
            f"🛡️  [Filter]: Blocking tool '{tool.name}' for "
            f"non-expert agent '{context.agent.name}'."
        )
        return False  # Block this tool

    # If the logic above doesn't block the tool, we allow it by default.
    return True


# ------------------------------------------------------------------
# 2. Main Orchestration Logic
# ------------------------------------------------------------------
async def main():
    """
    Connects to a server with the dynamic filter and runs two agents with
    different roles to demonstrate the filter's effect.
    """
    print("🔌 Connecting to server with a DYNAMIC, role-based filter...")
    async with MCPServerSse(
        params={"url": "http://localhost:8000/sse"},
        # Pass the function directly as the filter.
        tool_filter=dynamic_filter_for_experts
    ) as filtered_server:
        print("✅ Successfully connected to filtered tool server.")

        # 1. Create two agents with different roles (names).
        #    They both connect to the same filtered server instance.
        novice_agent = Agent(
            name="BasicAssistant",
            model="gpt-4-turbo",
            mcp_servers=[filtered_server]
        )
        expert_agent = Agent(
            name="WeatherExpert",
            model="gpt-4-turbo",
            mcp_servers=[filtered_server]
        )

        # 2. Run the NOVICE agent.
        #    When this agent tries to discover tools, our dynamic filter will
        #    see its name ("BasicAssistant") and block the weather tool.
        print("\n--- 🚫 Running NOVICE agent ---")
        result_novice = await Runner.run(
            starting_agent=novice_agent,
            input="What is the weather in London?"
        )
        print(f"🤖 Novice Agent Final Answer: {result_novice.final_output}")


        # 3. Run the EXPERT agent.
        #    When this agent discovers tools, the filter will see its name
        #    ("WeatherExpert") and will ALLOW access to the weather tool.
        print("\n--- ➡️ Running EXPERT agent ---")
        result_expert = await Runner.run(
            starting_agent=expert_agent,
            input="What is the weather in London?"
        )
        print(f"🤖 Expert Agent Final Answer: {result_expert.final_output}")

# ------------------------------------------------------------------
# 3. Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())