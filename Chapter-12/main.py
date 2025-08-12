# main.py
import asyncio
from manager import ResearchManager
import os
from dotenv import load_dotenv
async def main():
    """The main entry point for the application."""

    load_dotenv()

    # Before proceeding, we check if the necessary API key is available.
    # The agent cannot function without it.
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Please add it to your .env file.")
        return

    query = input("Please enter your research query: ")
    
    manager = ResearchManager()
    await manager.run(query)

if __name__ == "__main__":
    asyncio.run(main())