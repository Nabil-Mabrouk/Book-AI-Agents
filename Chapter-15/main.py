# main.py
import asyncio
import sys
import os
from dotenv import load_dotenv
from manager import AnalystManager

async def main():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Please set it in your .env file.")
        sys.exit(1)

    # Allow user to specify symbols as command-line arguments, default to BTC
    symbols = sys.argv[1:] if len(sys.argv) > 1 else ["BTC"]
    
    # Initialize the manager with the list of symbols to track
    manager = AnalystManager(symbols_to_track=symbols)
    await manager.run()

if __name__ == "__main__":
    asyncio.run(main())

# usage: python main.py BTC ETH SOL

