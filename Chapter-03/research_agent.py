# Chapter-03/research_agent.py

"""
An agent example that uses a pre-built tool for web searches.

This script demonstrates how to equip an agent with a tool that allows it
to access up-to-date information from the internet, making it capable of
answering questions about recent events.
"""
import asyncio
import os

from dotenv import load_dotenv

from agents import Agent, Runner, trace
# Import the pre-built tool from the local 'agents' library.
from agents import WebSearchTool


# 1. Define the Research Agent
# We equip the agent with an instance of the `WebSearchTool`. This gives
# the agent the capability to perform web searches to answer questions.
research_assistant_agent = Agent(
    name="ResearchAssistant",
    instructions=(
        "You are a helpful research assistant. Use the web search tool to "
        "find answers to the user's questions, especially if they relate "
        "to recent events or specific facts."
    ),
    tools=[WebSearchTool()],
    model="gpt-4o-mini",
)


async def main():
    """
    Sets up and runs the research assistant agent for a single query.
    """
    # Load the OPENAI_API_KEY from the .env file for secure key management.
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set.")
        return

    # The user's query is about a recent event, which is a perfect use case
    # for an agent with web search capabilities, as this information is not
    # part of the model's static training data.
    user_query = "What were the main announcements from the latest Apple event?"
    print(f"👤 User: {user_query}")

    # The trace block will help visualize the agent's process: receiving the
    # query, deciding to use the WebSearchTool, executing the search, and
    # synthesizing the findings into a coherent answer.
    with trace("Research Agent Workflow"):
        result = await Runner.run(research_assistant_agent, user_query)

    # The final output is the agent's answer, generated based on the
    # information it found on the web.
    print(f"🤖 Assistant: {result.final_output}")


if __name__ == "__main__":
    # Standard entry point to run the async main function of the script.
    asyncio.run(main())