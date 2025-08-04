# Chapter-04/handoff_agent.py

"""
An example of a handoff (or triage) multi-agent workflow.

This script demonstrates a powerful pattern where a "manager" agent, called
a TriageAgent, analyzes an incoming request and delegates it to the most
appropriate "specialist" agent from a team. This allows for the creation
of robust systems that can handle a wide variety of tasks by routing them
to experts.
"""
import asyncio
import os

from dotenv import load_dotenv

from agents import Agent, Runner, trace, handoff


# --- Specialist Agent Definitions ---

# 1. The Math Specialist
# This agent is an expert in a specific domain: mathematics.
math_agent = Agent(
    name="MathAgent",
    # The `handoff_description` is critical. It's the "advertisement" that
    # the TriageAgent reads to understand what this specialist is capable of.
    # It must be clear and accurately describe the agent's function.
    handoff_description=(
        "This agent is an expert in mathematics. Use it for any questions "
        "involving numbers, calculations, or mathematical concepts."
    ),
    instructions="You are a math genius. Answer the user's question clearly and show your work.",
    output_type=str,
    model="gpt-4o-mini",
)

# 2. The Creative Writing Specialist
# This agent is an expert in a different domain: creative writing.
writing_agent = Agent(
    name="CreativeWritingAgent",
    handoff_description=(
        "This agent is a talented creative writer. Use it for requests that "
        "involve writing stories, poems, or other creative text."
    ),
    instructions="You are a creative writer. Fulfill the user's request with flair and imagination.",
    output_type=str,
    model="gpt-4o-mini",
)


# --- The Triage (Manager) Agent ---
# This agent's only job is to analyze the user's request and delegate it.
# It does not answer the question itself, acting purely as a router.
triage_agent = Agent(
    name="TriageAgent",
    instructions=(
        "You are a triage agent. Your job is to analyze the user's request "
        "and delegate it to the appropriate specialist agent. Do not answer "
        "the question yourself."
    ),
    # The `handoffs` parameter defines the team of specialists that this
    # agent can delegate to. The agent will use their `handoff_description`
    # fields to make its routing decision.
    handoffs=[handoff(math_agent), handoff(writing_agent)],
    model="gpt-4o-mini",
)


async def run_test(query: str):
    """Helper function to run a test query against the triage agent."""
    print("--- Testing Query ---")
    print(f"👤 User: {query}")

    # The trace block will clearly show the TriageAgent's decision-making
    # process and the subsequent execution by the chosen specialist.
    with trace(f"Handoff test for query: {query[:20]}"):
        result = await Runner.run(triage_agent, query)
        print(f"🤖 Final Response: {result.final_output}")

        # The result object allows us to verify which agent handled the
        # final request, confirming that our routing logic worked as expected.
        print(f"✅ Handled by: {result.last_agent.name}")
    print("-" * 25 + "\n")


async def main():
    """Sets up the environment and runs two test cases to demonstrate the handoff logic."""
    # Load the OPENAI_API_KEY from the .env file for secure key management.
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set.")
        return

    # Test 1: A math question.
    # We expect the TriageAgent to route this query to the MathAgent.
    await run_test("What is the square root of 256?")

    # Test 2: A creative writing prompt.
    # We expect the TriageAgent to route this query to the CreativeWritingAgent.
    await run_test("Write a short poem about the moon.")


if __name__ == "__main__":
    # Standard entry point to run the async main function of the script.
    asyncio.run(main())