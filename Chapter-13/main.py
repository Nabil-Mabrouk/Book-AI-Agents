# main.py
import asyncio
import sys
import os
from dotenv import load_dotenv
from manager import ResearchManager

async def main():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Please set it in your .env file.")
        return

    if len(sys.argv) < 2:
        print("Usage: python main.py \"your research topic\"")
        sys.exit(1)
    
    user_query = " ".join(sys.argv[1:])
    
    manager = ResearchManager()
    await manager.run(user_query)

if __name__ == "__main__":
    asyncio.run(main())