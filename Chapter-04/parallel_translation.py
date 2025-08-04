# Chapter-04/parallel_translation.py

"""
An example of a parallel multi-agent workflow using asyncio.

This script demonstrates how to run multiple, independent agents concurrently.
Two specialist translator agents are created and run at the same time to
translate a piece of text into two different languages. This pattern is
highly efficient for tasks that don't depend on each other, as it can
significantly reduce the total execution time compared to running them
one after another.
"""
import asyncio
import os

from dotenv import load_dotenv

from agents import Agent, Runner, trace


# --- Agent Definitions ---
# We create two specialist agents. Since their tasks are independent,
# they are perfect candidates for parallel execution.

# Agent 1: The Spanish translator.
spanish_translator = Agent(
    name="SpanishTranslator",
    instructions=(
        "Translate the user's text to Spanish. "
        "Return only the translation."
    ),
    output_type=str,
    model="gpt-4o-mini",
)

# Agent 2: The French translator.
french_translator = Agent(
    name="FrenchTranslator",
    instructions=(
        "Translate the user's text to French. "
        "Return only the translation."
    ),
    output_type=str,
    model="gpt-4o-mini",
)


async def main():
    """Orchestrates the parallel execution of the translator agents."""
    # Load the OPENAI_API_KEY from the .env file for secure key management.
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set.")
        return

    user_message = "AI agents are the future of software development."
    print(f"👤 Original Message: '{user_message}'\n")

    # The trace block will show the concurrent runs happening together.
    with trace("Parallel Translation Workflow"):
        print("Running translators in parallel...")

        # --- The Core of the Parallel Pattern ---

        # 1. Create "tasks" for each agent run.
        # Calling an `async` function like `Runner.run` doesn't execute it
        # immediately. Instead, it creates a "coroutine" object—a work
        # order that can be run later.
        spanish_task = Runner.run(spanish_translator, user_message)
        french_task = Runner.run(french_translator, user_message)

        # 2. Run the tasks concurrently with `asyncio.gather`.
        # `asyncio.gather` is the magic here. It takes all our prepared
        # tasks and tells the event loop to run them all at the same time.
        # It then waits until the last task is complete before returning.
        results = await asyncio.gather(spanish_task, french_task)

        # 3. Unpack the results.
        # `asyncio.gather` guarantees that the list of results is in the
        # same order as the tasks we passed in, making it safe to unpack.
        spanish_result, french_result = results

        print("\n--- Translations ---")
        print(f"🇪🇸 Spanish: {spanish_result.final_output}")
        print(f"🇫🇷 French: {french_result.final_output}")


if __name__ == "__main__":
    # Standard entry point to run the async main function of the script.
    asyncio.run(main())