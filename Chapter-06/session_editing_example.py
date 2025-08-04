# Chapter-06/session_editing_example.py

"""
An example of programmatically editing an agent's session memory.

This script demonstrates an advanced technique where a developer can fetch an
agent's conversation history, modify it, and then update the session. This
is a powerful tool for correcting mistakes made by the user or the agent,
injecting system-level context, or summarizing long conversations to manage
token limits while preserving key information.
"""
import asyncio
import os

from dotenv import load_dotenv

from agents import Agent, Runner, SQLiteSession


# A simple agent for our demonstration. We use a basic agent to clearly show
# the effect of directly manipulating its memory.
fact_agent = Agent(
    name="FactAgent",
    instructions="Remember the fact the user tells you and answer questions about it.",
    model="gpt-4o-mini",
)


async def main():
    """Demonstrates fetching, editing, and updating a session's history."""
    # Load the OPENAI_API_KEY from the .env file for secure key management.
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set.")
        return

    session_id = "session-editing-demo"
    session = SQLiteSession(session_id=session_id)
    # We clear the session at the start to ensure this demo is repeatable.
    await session.clear_session()

    # --- The User Makes a Mistake ---
    # In this step, the user provides incorrect information, and the agent
    # stores this "bad fact" in its memory.
    print("--- The Mistake ---")
    mistake_query = "The capital of Australia is Sydney."
    print(f"👤 User: {mistake_query}")
    await Runner.run(fact_agent, mistake_query, session=session)

    # --- The Developer Intervenes by Editing ---
    # This section shows how we can programmatically correct the record.
    print("\n--- Correcting the Record by Editing ---")

    # 1. Fetch the entire conversation history. This returns a list of
    #    serializable message objects (e.g., dictionaries).
    all_items = await session.get_items()
    print(f"Retrieved {len(all_items)} items from history.")

    # 2. Modify the user's original mistaken message (the first item).
    #    This is a direct, surgical modification of the agent's memory.
    all_items[0]['content'] = "The capital of Australia is Canberra."
    print("Edited the user's original message.")

    # 3. Remove the assistant's now-incorrect acknowledgement (the second item).
    #    This is important for maintaining a consistent and logical history.
    del all_items[1]
    print("Removed the assistant's outdated reply.")

    # 4. Clear the session and add the corrected items back.
    #    This atomic operation ensures the session is updated with our changes.
    await session.clear_session()
    await session.add_items(all_items)
    print("Cleared and updated the session with the corrected history.")

    # --- Verifying the Correction ---
    # Now, we ask the agent the same question. It will build its context from
    # the *edited* history, allowing it to provide the correct answer.
    print("\n--- The Verification ---")
    result_check = await Runner.run(
        fact_agent, "What is the capital of Australia?", session=session
    )
    print(f"🤖 Assistant (with corrected info): {result_check.final_output}")


if __name__ == "__main__":
    # Standard entry point to run the async main function of the script.
    asyncio.run(main())