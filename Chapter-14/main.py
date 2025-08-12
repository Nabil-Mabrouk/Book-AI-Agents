# main.py
import asyncio, sys, os
from dotenv import load_dotenv
from manager import GitHubTrendManager

async def main():
    load_dotenv()
    if not all(os.getenv(key) for key in ["OPENAI_API_KEY", "GITHUB_API_TOKEN"]):
        print("Error: OPENAI_API_KEY and GITHUB_API_TOKEN must be set in your .env file.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} \"your_topic\""); sys.exit(1)
    
    user_topic = " ".join(sys.argv[1:])
    await GitHubTrendManager().run(user_topic)

if __name__ == "__main__":
    asyncio.run(main())