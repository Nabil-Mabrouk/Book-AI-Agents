# agents/research_agent.py
from agents import Agent, WebSearchTool # Import the built-in tool

# We no longer need to import a custom tool from the tools/ directory.

research_agent = Agent(
    name="ResearchAgent",
    instructions=(
        "You are an expert research assistant. Your goal is to use the web "
        "search tool to find information that answers the user's query."
    ),
    # Instantiate the pre-built tool class and add it to the agent's toolbelt.
    tools=[WebSearchTool()],
    model="gpt-4o-mini",
)