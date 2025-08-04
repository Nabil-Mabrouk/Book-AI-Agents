# Chapter-02/hello_agent.py
"""
A simple script to demonstrate the basic execution of an AI agent.

This file shows how to define an agent with a specific goal, provide it
with a user's question, and use a Runner to get the AI's response.
It's a foundational example of an agent's lifecycle.
"""
import asyncio
import os
from dotenv import load_dotenv
from agents import Agent, Runner

async def main():
    """
    The main function where we define and run our agent.

    This function orchestrates the entire process, from setting up the
    environment to printing the agent's final answer.
    """
    # Load environment variables from the .env file. This is a best practice
    # for managing sensitive information like API keys securely, keeping them
    # separate from the source code.
    load_dotenv()

    # Before proceeding, we check if the necessary API key is available.
    # The agent cannot function without it.
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Please add it to your .env file.")
        return

    # 1. Define the Agent: This is the blueprint for our AI assistant.
    # We give it a name and, most importantly, a set of instructions.
    # These instructions are the primary guide for the LLM's behavior,
    # defining its personality, its goal, and any constraints it must follow.
    assistant_agent = Agent(
        name="AssistantAgent",
        instructions="You are a helpful and friendly assistant. Please answer questions concisely.",
    )

    # 2. Define the User's Query: This is the specific input or task
    # that we want our agent to work on.
    user_query = "What is the tallest mountain in the world?"
    print(f"👤 User: {user_query}")

    # 3. Run the Agent: The Runner is the engine that brings the agent to
    # life. The `Runner.run()` method takes our agent definition and the
    # user's input, handles the underlying API calls to the LLM, and
    # orchestrates the entire process from start to finish.
    result = await Runner.run(assistant_agent, user_query)

    # 4. Print the Final Output: The `result` object returned by the runner
    # contains useful information about the execution, including logs and
    # intermediate steps. For this example, we are interested in the
    # `final_output`, which holds the agent's direct response to the user.
    print(f"🤖 Assistant: {result.final_output}")


if __name__ == "__main__":
    # This block is the standard entry point for a Python script. When the
    # script is executed directly, the `main()` async function is run.
    # Using `asyncio.run()` is the modern way to execute the top-level
    # async function.
    asyncio.run(main())