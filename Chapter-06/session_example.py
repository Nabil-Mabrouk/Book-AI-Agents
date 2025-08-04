# Chapter-06/session_example.py

"""
An example of creating a stateful agent with conversation memory.

This script demonstrates how to use a `Session` object to give an agent
memory across multiple turns of a conversation. By passing the same session
object into each run, the agent can access the history of the entire
conversation, allowing it to remember previous interactions and answer
context-aware questions.

The `SQLiteSession` implementation provides persistent storage, meaning the
conversation history is saved to a file and will be available even if the
script is stopped and restarted with the same session ID.
"""
import asyncio
import os

from dotenv import load_dotenv

from agents import Agent, Runner, trace, SQLiteSession


# A simple agent for our demonstration. We use a basic agent to keep the
# focus on the session and memory mechanism itself.
chatty_agent = Agent(
    name="ChattyAgent",
    instructions="You are a friendly and chatty assistant.",
    model="gpt-4o-mini",
)


async def main():
    """Demonstrates a multi-turn conversation with persistent memory."""
    # Load the OPENAI_API_KEY from the .env file for secure key management.
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set.")
        return

    # 1. Initialize the Session.
    # We give it a unique ID. All turns using this ID belong to the same
    # conversation. The `SQLiteSession` will create a `conversations.db`
    # file in your directory to store the history persistently.
    session_id = "my-first-real-conversation"
    session = SQLiteSession(session_id=session_id)
    print(f"Using session ID: {session_id}")

    # --- Turn 1 ---
    # This is the first interaction. The Runner will save both the user's
    # query and the agent's response to the session history.
    print("\n--- Turn 1 ---")
    query1 = "My favorite color is blue."
    print(f"👤 User: {query1}")
    # We pass the session object to the Runner.
    await Runner.run(chatty_agent, query1, session=session)

    # --- Turn 2 ---
    # In the second turn, we use the *same* session object. The Runner will
    # automatically load the history from Turn 1 and provide it as context
    # to the LLM before processing the new query.
    print("\n--- Turn 2 ---")
    query2 = "What is my favorite color?"
    print(f"👤 User: {query2}")
    result2 = await Runner.run(chatty_agent, query2, session=session)
    # The agent should remember the information from the previous turn!
    print(f"🤖 Assistant: {result2.final_output}")

    # --- Turn 3 ---
    # The context continues to build with each turn. The history now contains
    # the first two interactions, giving the agent even more context.
    print("\n--- Turn 3 ---")
    query3 = "Why might someone like that color?"
    print(f"👤 User: {query3}")
    await Runner.run(chatty_agent, query3, session=session)
    # Note: This line prints the result from Turn 2 again. To see the new
    # response from Turn 3, you would capture the result from the line above,
    # for example: `result3 = await Runner.run(...)`.
    print(f"🤖 Assistant: {result2.final_output}")

    # You can inspect the full conversation history from the session at any time.
    history = await session.get_items()
    print(f"\nFull conversation history contains {len(history)} messages.")

    # To start a new conversation with the same ID, you can clear the history.
    # This is useful for resetting a user's session.
    # await session.clear_session()
    # print("Session cleared.")


if __name__ == "__main__":
    # Standard entry point to run the async main function of the script.
    asyncio.run(main())