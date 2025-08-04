# Chapter-06/local_context_example.py

"""
An example of using local context to create stateful agents.

This script demonstrates a powerful pattern for making agents aware of
application-specific data (like the current logged-in user) without
including that data in the main prompt to the LLM. The local context is
passed securely to tools, allowing them to behave differently based on
this information.
"""
import asyncio
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from agents import Agent, Runner, function_tool, RunContextWrapper


# 1. Define the structure of our local context data.
# A dataclass is a perfect, lightweight way to create a structured object
# for holding our application's state.
@dataclass
class UserContext:
    """A container for user-specific data passed into an agent run."""
    user_id: str
    permissions_level: str


# 2. Create a tool that requires this local context.
@function_tool
async def get_user_dashboard(wrapper: RunContextWrapper[UserContext]) -> str:
    """
    Fetches the dashboard URL for the current user, using local context.

    The type hint `RunContextWrapper[UserContext]` is the key mechanism. It
    tells the Runner that this tool needs access to the `UserContext` object
    that was passed into the run.
    """
    # Inside the tool, we can securely access the context via `wrapper.context`.
    # This data is not seen by the LLM unless the tool explicitly returns it.
    user_id = wrapper.context.user_id
    permissions = wrapper.context.permissions_level
    print(
        f"🛠️ [Tool Call] Fetching dashboard for user '{user_id}' with "
        f"permissions '{permissions}'..."
    )

    # The tool's logic can change based on the provided context, enabling
    # personalized and permission-aware behavior.
    if permissions == "admin":
        return f"https://company.com/dashboards/admin?user={user_id}"
    else:
        return f"https://company.com/dashboards/user?user={user_id}"


# 3. Define the agent and specify its context type.
# The generic type hint `Agent[UserContext]` establishes a formal contract,
# indicating that this agent is designed to work with our `UserContext` object.
context_aware_agent = Agent[UserContext](
    name="ContextAwareAgent",
    instructions=(
        "You are a helpful assistant. When asked for the dashboard, use the "
        "provided tool to get the URL and present it to the user."
    ),
    tools=[get_user_dashboard],
    model="gpt-4o-mini",
)


async def main():
    """Demonstrates running the same agent with different contexts."""
    # Load the OPENAI_API_KEY from the .env file for secure key management.
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set.")
        return

    # 4. Create different context objects for different runs.
    # This simulates two different users interacting with the system.
    admin_user = UserContext(user_id="u-123", permissions_level="admin")
    standard_user = UserContext(user_id="u-456", permissions_level="standard")

    # 5. Pass the context object into the Runner.
    # The `context=...` parameter is how we inject our local data into the run.
    # The Runner then makes this context available to tools that request it.
    print("--- Running for Admin User ---")
    # Expected outcome: The tool will use the 'admin_user' context and return an admin URL.
    await Runner.run(context_aware_agent, "Get my dashboard link.", context=admin_user)

    print("\n--- Running for Standard User ---")
    # Expected outcome: The tool will use the 'standard_user' context and return a standard URL.
    await Runner.run(context_aware_agent, "Get my dashboard link.", context=standard_user)


if __name__ == "__main__":
    # Standard entry point to run the async main function of the script.
    asyncio.run(main())